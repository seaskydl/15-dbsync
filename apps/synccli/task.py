import zmq
from datetime import datetime, timedelta
from rich.progress import Progress
from common.logger import logger
from common.util import get_settings, set_settings, utctime
from common.storage import Storage
from common.Svcobj import store_inst, Svcobj_cli
from common.const import SYNC_DIR

class Task(object):
  def __init__(self, cli_name, task_name, cfg, *args, **argv):
    self._cli_name = cli_name
    self._task_name = task_name
    self._name = cfg.get("name")
    self._dbpath = cfg.get("database")
    self.db = None
    self._tables = cfg.get("tables", "")
    self.trigger = cfg.get('trigger')
    self._direction = cfg.get("direction", SYNC_DIR.PULL)
    self._svc_func = {
       SYNC_DIR.PULL: self.req_pull,
       SYNC_DIR.PUSH: self.req_push,
     }.get(self._direction)
    assert(self._svc_func is not None)

    self._cli = store_inst.getInstance(Svcobj_cli, self._cli_name, cfg.get("server").get("host"), cfg.get("server").get("port"), zmq.DEALER)

  def __call__(self, sched, *args, **kwds):
    run_at = datetime.now()
    if self.trigger.get("delay") is not None:
      run_at += timedelta(seconds=self.trigger.get("delay"))

    sched.add_job(self.run, self.trigger.get("type"), **self.trigger.get("args"), next_run_time=run_at, args=args, kwargs=kwds)

  async def on_resp(self, *args, **kwargs):
    if self._direction == SYNC_DIR.PULL:
      [cmd, res] = args

      if res.get("code") != 0:
        return False

      res = res.get("data", {})
      for _tbl, records in res.get("table", {}).items():
        if records:
          self.db.save(_tbl, records)

    elif self._direction == SYNC_DIR.PUSH:
      pass

    return True

  async def req_pull(self, *args, **kwargs):
    try:
      now = utctime()
      progress = kwargs.get("_progress")
      task = kwargs.get("_task")

      if self._tables and self._tables != "*":
        idx = 0
        progress_step = 100
        if task_size := len(self._tables):
          progress_step = 100 / task_size

        for tbl in self._tables:
          if (lst_sync_at := get_settings(tbl, "lst_sync_at", section=SYNC_DIR.PULL)) is not None:
            condition = f"updated_at <= '{now}' and updated_at > '{lst_sync_at}'"
          else:
            condition = f"updated_at <= '{now}'"

          idx += 1
          if not await self._cli.request(SYNC_DIR.PULL, {'table': tbl, 'condition':condition}, cbf=self.on_resp, progress=progress, task=task):
            logger.error(f"{self._cli_name}.{self._name} {SYNC_DIR.PULL} FAILED, TBL: {tbl}")
            continue

          set_settings(tbl, "lst_sync_at", now, section="pull")
          progress.update(task, advance=progress_step)
        return True
      else:
        tbl = 'all'
        if (lst_sync_at := get_settings(tbl, "lst_sync_at", section=SYNC_DIR.PULL)) is not None:
          condition = f"updated_at > '{lst_sync_at}' and updated_at <= '{now}'"
        else:
          condition = f"updated_at <= '{now}'"

        progress.update(task, advance=30)
        if not await self._cli.request(SYNC_DIR.PULL, {'table': tbl, 'condition':condition}, cbf=self.on_resp, progress=progress, task=task):
          logger.error(f"{self._cli_name}.{self._name} {SYNC_DIR.PULL} FAILED, TBL: {tbl}")
          return False

        set_settings(tbl, "lst_sync_at", now, section="pull")
        progress.update(task, advance=70)

        return True
    except Exception as e:
      print(f"PULL EXP: {str(e)}")
      return False

  async def req_push(self, *args, **kwargs):
    try:
      now = utctime()

      if not self._tables or self._tables in ("*", "all", "ALL"):
        self._tables = self.db.tables

      for idx, table in enumerate(self._tables):
        if (lst_sync_at := get_settings(table, "lst_sync_at", section="push")) is not None:
          condition = f"updated_at <= '{now}' and updated_at > '{lst_sync_at}'"
        else:
          condition = f"updated_at <= '{now}'"

        records = self.db.fetch(table, condition)
        if not await self._cli.request(SYNC_DIR.PUSH, {'tables': {table: records}}, cbf=self.on_resp):
          logger.error(f"{self._cli_name}.{self._name} {SYNC_DIR.PUSH} FAILED, TBL: {table}")
    except Exception as e:
      print(f"PUSH EXP: {str(e)}")
      return False

  async def run(self, *args, **kwargs):
    progress = Progress()
    progress.start()
    try:
      with Progress() as progress:
        task = progress.add_task(f"[cyan]TASK {self._name}:", total=100)
        if self.db is None:
          self.db = Storage(self._dbpath)

        if not self.db.inited:
          raise Exception(f"DB NOT INITED")

        if not self._cli.inited:
          self._cli.initialize()

        kwargs['_progress'] = progress
        kwargs['_task'] = task
        await self._svc_func(*args, **kwargs)

        progress.update(task, advance=100)
    except Exception as e:
      logger.error(f"{self._name} START FAILED: {str(e)}")

    finally:
      progress.stop()