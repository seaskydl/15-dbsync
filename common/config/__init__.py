import tomllib
from common.pattern import Singleton

@Singleton
class Config(object):
  _cfg = None
  def __init__(self, fn, client=False):
    with open(fn, "rb") as f:
      self._cfg = tomllib.load(f)
      self.build()
      self.verify(client)

  def verify(self, client=False):
    if client:
      if self._cfg.get("client", {}).get("name") is None:
        raise Exception("CLIENT NAME IS NOT DEFINED")

      if not self._cfg.get("task"):
        raise Exception("NO CLIENT IS DEFINED")

  def build(self):
    def_svr = self._cfg.get("server", {})
    def_tgr = self._cfg.get("trigger", {})

    for name, task in self._cfg.get("task", {}).items():
      svr_inf = {**def_svr}
      svr_inf.update(task.get("server", {}))
      task["server"] = svr_inf
      tgr_inf = {**def_tgr}
      tgr_inf.update(task.get("trigger", {}))
      task["trigger"] = tgr_inf

  def __call__(self, *args, **kwds):
    return self._cfg