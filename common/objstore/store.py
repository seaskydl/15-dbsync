
from .objcore import Objcore

class Objstore():
  _objects = {}
  def __init__(self):
    self._objects = {}

  def reg_obj(self, obj):
    if not isinstance(obj, Objcore):
      raise Exception("Add obj faild, obj is NOT a Objcore instance")

    if obj.id in self._objects:
      return obj

    self._objects[obj.id] = obj
    return obj

  def instance(self, id):
    return self._objects.get(id)

  def get_inst(self, cls, *args, **kwargs):
    return self.reg_obj(cls(*args, **kwargs))
