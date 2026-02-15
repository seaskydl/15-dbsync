from sqlite_utils import Database

class Syncsvr(object):
  db_path = ''
  db = None

  def __init__(self, db_path):
    self.db_path = db_path
    self.db = Database(db_path)

  def tables(self):
    if self.db is None:
      return []

    return self.db.table_names()

  def fetch(self, table, condition=None):
    if condition is None:
      return list(self.db[table].rows)
    else:
      return list(self.db[table].rows_where(condition))

