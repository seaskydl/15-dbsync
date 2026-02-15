from common.util import progress as pbar, get_settings, set_settings, utctime
from common.storage import Storage, IGNORE_TABLESs

IGNORE_TABLES = ('sqlite_sequence')
async def sync(src, dst, tbls=None):
  _src = Storage(src)
  _dst = Storage(dst)

  if tbls is None:
    tbls = _src.tables()
  elif not isinstance(tbls, list):
    tbls = [tbls]

  if len(tbls) == 0:
    return

  now = utctime()
  idx = 0
  for tbl in tbls:
    if tbl in IGNORE_TABLES:
      continue
    idx += 1
    if (lst_sync_at := get_settings(tbl, "lst_sync_at")) is not None:
      condition = f"updated_at <= '{now}' and updated_at > '{lst_sync_at}'"
    else:
      condition = f"updated_at <= '{now}'"

    pbar(0, f"No.{idx} [{tbl}]")
    records = _src.fetch(tbl, condition)
    pbar(50, f"No.{idx} [{tbl}]")
    _dst.save(tbl, records)
    set_settings(tbl, "lst_sync_at", now)
    pbar(100, f"No.{idx} [{tbl}]")

async def run(*argc, **argv):
  if (src := argv.get('s', argv.get('src'))) is None:
    print(f">>>ERR: SOURCE DB MUST BE PROVIDED")
    return

  if (dst := argv.get('d', argv.get('o', argv.get('dest')))) is None:
    print(f">>>ERR: TARGET DB MUST BE PROVIDED")
    return

  if (src == dst):
    print(f">>>ERR: TARGET DB MUST NOT BE SAME AS SOURCE DB")
    return

  print(f"WILL TRY TO SYNC DATA FROM [{src}] TO [{dst}]")
  tbls = argv.get('t', argv.get('table', '')).split(',')

  await sync(src, dst, tbls)

  print("FINISHED.")