from tortoise import Tortoise
# coding=utf-8

class Database(object):
  def __init__(self, db_url="sqlite://data/data.db", modules={'models': ['database.models']}):
    self._db_url = db_url
    self._modules = modules
    assert( self.init_chk() )

  def init_chk(self):
    try:
      #import aiosqlite
      #ver = aiosqlite.__version__
      #print(f"当前 aiosqlite 的版本是: {ver}")
      #if ver[2:4] > '21':
      #  print(f"ERR: aiosqlite {ver} is NOT support yet, please use version <= 0.21.0")
      #  return False
      return True
    except AttributeError:
        print("模块 aiosqlite 没有 __version__ 属性")
        return False

  async def init_db(self, db_url="sqlite://data/data.db", modules={'models': ['database.models']}):
    await Tortoise.init(
        db_url=db_url, #'sqlite://storage/iidr.db',
        modules=modules, #{'models': ['database.models']}
        use_tz=False,
        timezone="Asia/Shanghai"
      )
    await Tortoise.generate_schemas()

  async def close_db(self):
    await Tortoise.close_connections()

  async def __aenter__(self):
    assert( self._db_url is not None)
    assert( self._modules is not None)
    await Tortoise.init(
        db_url=self._db_url,    #'sqlite://storage/iidr.db',
        modules=self._modules,  #{'models': ['database.models']}
      )
    await Tortoise.generate_schemas()
    return self

  async def __aexit__(self, exc_type, exc, tb):
    await Tortoise.close_connections()