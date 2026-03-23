from hashlib import md5

def makeid(id: str):
  return md5(id.encode("utf-8")).hexdigest()

class Objcore():
  _id = "_obj_core_"

  def __init__(self, *args, **kwargs):
    self._id = kwargs.get("id") or self._id

  @property
  def id(self):
    return self._id

'''
class test(Objcore):
  def __init__(self, id):
    super().__init__(id)


if __name__ == "__main__":
  t = test("AAAAA")
  print(t.id)
'''
