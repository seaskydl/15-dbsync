from sqlite_utils import Database

class Synccli(object):
  db_path = ''
  db = None

  def __init__(self, db_path):
    self.db_path = db_path
    self.db = Database(db_path)

  def tables(self):
    if self.db is None:
      return []

  def save(self, table, records, pk="id", alter=True):
    self.db[table].upsert_all(records, pk=pk, alter=alter)

