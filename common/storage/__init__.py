from pathlib import Path
from sqlite_utils import Database
IGNORE_TABLES = ('sqlite_sequence')

class Storage(object):
  db_path = ''
  db = None

  def __init__(self, db_path, chk_exist=False):
    if chk_exist:
      if(Path(db_path).is_file()):
        raise Exception(f"FILE {db_path} NOT EXISTED")
    self.db_path = db_path
    self.db = Database(db_path)

  @property
  def tables(self):
    if self.db is None:
      return []

    return self.db.table_names()

  def fetch(self, table, condition=None):
    if condition is None:
      return list(self.db[table].rows)
    else:
      return list(self.db[table].rows_where(condition))

  def save(self, table, records, pk="id", alter=True):
    self.db[table].upsert_all(records, pk=pk, alter=alter)

