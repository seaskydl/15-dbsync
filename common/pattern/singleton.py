# _*_ coding:utf-8 _*_
#
# author: Jasonli
#
# No.   Date     Name   Desc
#------ -------- ------ -------------------------------
#
# class Sngleton implement the Singleton design pattern
# empower the sub class also to be a Singleton model
#
# sampel:
# 1.def sub class with Singleton wrapper
# @Singleton
# class Myclass(object):
#   pass, ...put your code here
#
# 2.Instance Myclass and use it.
# a = MyClass()
# b = MyClass()
# a.a = 'a
# print(a is b, id(a), id(b), a.a, b.a), # output True, id_of_a, id_of_b(The same as id_of_a), a, a

class Singleton(object):
  def __init__(self, cls):
    self._cls = cls
    self._instance = {}

  def __call__(self, *args, **kwargs):
    if self._cls not in self._instance:
      self._instance[self._cls] = self._cls(*args, **kwargs)
    return self._instance[self._cls]

def test():
  @Singleton
  class MyClass(object):
    def __init__(self, version) -> None:
      super().__init__()
      self.version = version

  a = MyClass("")
  b = MyClass("")

  a.a = 'a'
  print(a is b, id(a), id(b), a.a, b.a)  # 输出 True 1970422854000 1970422854000 a a

if __name__ == "__main__":
  test()
