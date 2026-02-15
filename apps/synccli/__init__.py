import zmq, msgpack
from zmq.asyncio import Context
from common.util import progress as pbar, get_settings, set_settings, utctime
from common.synccli import Synccli

# 1. Create the asyncio-aware context
ctx = Context.instance()

# 1. svc port, 2. table for svc, 3. username, 3. password
async def run(*argc, **argv):
  if (dst := argv.get('d', argv.get('o', argv.get('dest')))) is None:
    print(f">>>ERR: TARGET DB MUST BE PROVIDED")
    return
  _dst = Synccli(dst)

  host = argv.get('h', argv.get('host', 'localhost'))
  port = argv.get('p', argv.get('port', 5555))

  sock = ctx.socket(zmq.DEALER)
  sock.setsockopt(zmq.IDENTITY, b'synccli01')
  sock.connect(f"tcp://{host}:{port}")

  # 3 models:
  #   1. without specify tables, server will return all tabels from server
  #   2. specify table
  #   3.
  tbls = argv.get('t', argv.get('table', ''))
  if tbls == '':
    tbls = []
  else:
    tbls = tbls.split(',')
  now = utctime()
  if tbls:
    idx = 0
    for tbl in tbls:
      if (lst_sync_at := get_settings(tbl, "lst_sync_at", section="remote")) is not None:
        condition = f"updated_at <= '{now}' and updated_at > '{lst_sync_at}'"
      else:
        condition = f"updated_at <= '{now}'"

      req = msgpack.packb({'tbl': tbl, 'condition':condition})
      idx += 1
      pbar(0, f"No.{idx} [{tbl}]")
      await sock.send_multipart([b'', req])
      try:
        _, data = await sock.recv_multipart()
        records = msgpack.unpackb(data)
        print("records:", records)
      except zmq.ZMQError as e:
        if e.errno == zmq.ETERM:
          return   # Shutting down, quit
        else:
          raise

      pbar(50, f"No.{idx} [{tbl}]")
      _dst.save(tbl, records)
      pbar(100, f"No.{idx} [{tbl}]")
      set_settings(tbl, "lst_sync_at", now, section="remote")
  else:
      tbl = 'all'
      if (lst_sync_at := get_settings(tbl, "lst_sync_at", section="remote")) is not None:
        condition = f"updated_at <= '{now}' and updated_at > '{lst_sync_at}'"
      else:
        condition = f"updated_at <= '{now}'"

      req = msgpack.packb({'tbl': tbl, 'condition':condition})
      await sock.send_multipart([b'', req])
      try:
        _, res = await sock.recv_multipart()
      except zmq.ZMQError as e:
        if e.errno == zmq.ETERM:
          return   # Shutting down, quit
        else:
          raise

      res = msgpack.unpackb(res)
      idx = 1
      for _tbl, records in res.items():
        pbar(50, f"No.{idx} [{_tbl}]")
        _dst.save(_tbl, records)
        pbar(100, f"No.{idx} [{_tbl}]")
        idx += 1
      set_settings(tbl, "lst_sync_at", now, section="remote")

  sock.close()
  ctx.term()