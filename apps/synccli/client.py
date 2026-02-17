from dataclasses import dataclass
import signal, zmq, msgpack
from zmq.asyncio import Context
from common.util import progress as pbar, get_settings, set_settings, utctime
from common.logger import logger
from common.storage import Storage

@dataclass
class SYNC_ORCH :
  CLIENT = 0 #default
  SERVER = 1

class Synccli(object):
  _is_running = False

  def __init__(self, dbpath, name, host="*", port=55555):
    self.name = name
    self.host = host
    self.port = port
    self.db = Storage(dbpath, True)

  def init(self):
    self.ctx = Context.instance()
    self.socket = self.ctx.socket(zmq.DEALER)
    self.socket.setsockopt(zmq.IDENTITY, self.name.encode('utf-8'))
    self.socket.connect(f"tcp://{self.host}:{self.port}")

    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)

    self._is_running = True

  def _signal_handler(self, sig, frame):
    logger.info("USER BREAK, EXIT")
    self._is_running = False

  @property
  def is_running(self):
    return self._is_running

  async def run(self, *argc, **argv):
    if not self.db.inited:
      return

    tbls = argv.get('t', argv.get('table', ''))
    if tbls in ('', 'all'):
      tbls = []
    else:
      tbls = tbls.split(',')

    now = utctime()
    if tbls:
      idx = 0
      for tbl in tbls:
        if (lst_sync_at := get_settings(tbl, "lst_sync_at", section="remote")) is not None:
          condition = f"updated_at <= '{now}' and updated_at > '{lst_sync_at}'"
        else:
          condition = f"updated_at <= '{now}'"

        req = msgpack.packb({'tbl': tbl, 'condition':condition})
        idx += 1
        pbar(0, f"No.{idx} [{tbl}]")
        await self.socket.send_multipart([b'', req])
        try:
          _, data = await self.socket.recv_multipart()
          records = msgpack.unpackb(data)
        except zmq.ZMQError as e:
          if e.errno == zmq.ETERM:
            return   # Shutting down, quit
          else:
            raise
        if not records:
          logger.info(f"No.{idx} [{tbl}]: NO DATA TO SYNC")
          return
        pbar(50, f"No.{idx} [{tbl}]")
        self.db.save(tbl, records)
        pbar(100, f"No.{idx} [{tbl}]")
        set_settings(tbl, "lst_sync_at", now, section="remote")
    else:
      tbl = 'all'
      if (lst_sync_at := get_settings(tbl, "lst_sync_at", section="remote")) is not None:
        condition = f"updated_at > '{lst_sync_at}' and updated_at <= '{now}'"
      else:
        condition = f"updated_at <= '{now}'"

      req = msgpack.packb({'tbl': tbl, 'condition':condition})
      await self.socket.send_multipart([b'', req])
      try:
        _, res = await self.socket.recv_multipart()
      except zmq.ZMQError as e:
        if e.errno == zmq.ETERM:
          return   # Shutting down, quit
        else:
          raise

      res = msgpack.unpackb(res)
      idx = 0
      for _tbl, records in res.items():
        idx += 1
        if not records:
          logger.info(f"No.{idx} [{tbl}]: HAS NO DATA TO SYNC")
          continue

        pbar(50, f"No.{idx} [{_tbl}]")
        self.db.save(_tbl, records)
        pbar(100, f"No.{idx} [{_tbl}]")
      set_settings(tbl, "lst_sync_at", now, section="remote")

  def cleanup(self):
    logger.info("SYNC CLIENT CLEAN UP...")
    self.socket.close()
    self.ctx.term()
    logger.info("SYNC CLIENT STOPPED.")

  def __del__(self):
    self.cleanup()

  async def __aenter__(self):
    self.init()
    return self

  async def __aexit__(self, exc_type, exc, tb):
    self.cleanup()