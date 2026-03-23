from common.logger import logger
from common.config import Config
from common.storage import Storage
from common.zmqsvc import OK, FAIL
from common.Svcobj import Svcobj_svc
from common.const import SYNC_DIR

class Service(Svcobj_svc):
  def __init__(self, cfg_file):
    _db = None
    try:
      self.cfg_file = cfg_file
      cfg = Config(self.cfg_file)()
      self._dbpath = cfg.get("server").get("database")
      assert(self._dbpath is not None)
      self._db = Storage(self._dbpath)
      super().__init__(**{k:v for k,v in cfg.get("server").items() if k in ("name", "host", "port", "mode")})
    except Exception as e:
      logger.error(f"SERVICE OBJ INIT FAILED: {str(e)}")

  @property
  def db(self):
    return self._db

CFG_FILE = "./config/service.toml"
service = Service(CFG_FILE)

@service.route(SYNC_DIR.PULL)
async def on_pull(self, identity, cmd, req):
  try:
    table = req.get("table")
    condition = req.get("condition")

    assert(table is not None)
    assert(condition is not None)

    if table in ("*", "all", "ALL"):
      data = { table: self.db.fetch(table, condition) for table in self.db.tables if table is not None }
    else:
      data = { table: self.db.fetch(table, condition)}

    return OK({"tables": data}) #
  except Exception as e:
    return FAIL(f"CMD {cmd}, ERR {str(e)}")

@service.route(SYNC_DIR.PUSH)
async def on_push(self, identity, cmd, req):
  try:
    tables = req.get("tables", {}) or {}
    for table, records in tables.items():
      if not records:
          logger.info(f"NO [{table}]: HAS NO DATA TO SYNC")
          continue

      self.db.save(table, records)

    return OK()
  except Exception as e:
    return FAIL(f"CMD {cmd}, ERR {str(e)}")
