import signal
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from common.logger import logger
from common.config import Config
from .task import Task

class Client(object):
  _is_running = False
  def __init__(self, cfg_file):
    self.cfg_file = cfg_file

  @property
  def is_running(self):
    return self._is_running

  @property
  def is_initialied(self):
    return self._is_running

  def stop(self):
    self._is_running = False

  def _signal_handler(self, sig, frame):
    logger.info("USER REQUEST STOP, PLEASE WAIT CLIENT CLEAN UP")
    self.stop()

  def initialize(self):
    try:
      if self.is_initialied:
        return True

      signal.signal(signal.SIGINT, self._signal_handler)
      signal.signal(signal.SIGTERM, self._signal_handler)

      self._is_running = True
      return True
    except Exception as e:
      logger.error(f"INITIALIZED FAILED: {str(e)}")
      return False

  def load_config(self, *argc, **argv):
    try:
      self._cfg = Config(self.cfg_file, True)()
      self.name = self._cfg.get("client", {}).get("name")
      return True
    except Exception as e:
      print(str(e))
      return False

  async def start(self):
    try:
      if not self.initialize():
        return False

      if not self.load_config():
        logger.error(f"LOAD CONFIG FAILED: {self.cfg_file}")
        return False

      sched = AsyncIOScheduler()
      for name, tsk_cfg in self._cfg.get("task", {}).items():
        Task(self.name, name, tsk_cfg)(sched)

      sched.start()
      logger.info("SYNC CLIENT STARTED, PRESS Ctrl+C TO EXIT")

      while self.is_running:
        await asyncio.sleep(10)

      sched.shutdown()
      logger.info("SYNC CLIENT WAS STOPPED")
    except Exception as e:
      logger.error(f"SYNC CLI EXP: {str(e)}")
