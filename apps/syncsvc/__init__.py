import zmq, msgpack
from zmq.asyncio import Context
from common.syncsvr import Syncsvr
IGNORE_TABLES = ('sqlite_sequence')

# 1. Create the asyncio-aware context
ctx = Context.instance()

# 1. svc port, 2. table for svc, 3. username, 3. password
async def run(*argc, **argv):
  if (src := argv.get('s', argv.get('src'))) is None:
    print(f">>>ERR: SOURCE DB MUST BE PROVIDED")
    return
  _src = Syncsvr(src)

  host = argv.get('h', argv.get('host', '*'))
  port = argv.get('p', argv.get('port', 5555))

  username = argv.get('username')
  password = argv.get('password')

  # 2. Create a socket from the asyncio context
  sock = ctx.socket(zmq.ROUTER)
  sock.bind(f"tcp://{host}:{port}")
  print(f"ZeroMQ server running on tcp://*:{port}")

  try:
    while True:
      # 3. Use 'await' with normally blocking methods
      print("Waiting command")
      try:
        id, _, res = await sock.recv_multipart()
        #{'tbl': tbl, 'condition':condition}
        res = msgpack.unpackb(res)
        print("Message received:", res)
        condition = res.get('condition')
        if (tbl := res.get('tbl')) == 'all':
          data = {tbl:_src.fetch(tbl, condition) for tbl in _src.tables() if tbl not in IGNORE_TABLES}
        else:
          data = _src.fetch(tbl, condition)
        await sock.send_multipart([id, b'', msgpack.packb(data)])
      except zmq.Again:
        # 如果设置了超时，这里可以处理超时
        continue
      except zmq.ZMQError as e:
        if e.errno == zmq.ETERM:
          return   # Shutting down, quit
        else:
          raise
  except zmq.ContextTerminated:
    # 收到关闭信号，退出循环
    print("Context terminated, breaking loop")
  except KeyboardInterrupt:
    print("Interrupted, cleaning up...")
  finally:
    # 无论如何，最后关闭 Socket 和 Context
    sock.close()
    ctx.term()
