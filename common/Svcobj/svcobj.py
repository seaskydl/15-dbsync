import zmq
from common.pattern import Singleton
from common.zmqsvc import Zmq_cli, Zmq_svc
from common.objstore import Objstore, Objcore, makeid

class Svcobj_cli(Zmq_cli, Objcore):
  def __init__(self, *args, **kwargs):
    kwargs['mode'] = kwargs.get("mode", zmq.DEALER) or zmq.DEALER
    super().__init__(*args, **kwargs)

  async def on_resp(self, *args, **kwargs):
    return await super().on_resp(*args, **kwargs)

class Svcobj_svc(Zmq_svc, Objcore):
  def __init__(self, *args, **kwargs):
    kwargs["mode"] = kwargs.get("mode", zmq.ROUTER) or zmq.ROUTER
    super().__init__(*args, **kwargs)

@Singleton
class Svc_store(Objstore):
  def __init__(self):
    super().__init__()

  def getInstance(self, cls, name, host, port, mode=None):
    id = makeid(f"{host}{port}{mode}")
    if (inst := self.instance(id)) is None:
      inst = cls(name=name, host=host, port=port, mode=mode, id=id)
      return self.reg_obj(inst)

    return inst

store_inst = Svc_store()
