import zmq, msgpack
from zmq.asyncio import Context
from common.util import GracefulShutdown
from common.storage import Storage, IGNORE_TABLES

from .svc import Syncsvc

# 1. Create the asyncio-aware context
ctx = Context.instance()

# 1. svc port, 2. table for svc, 3. username, 3. password
async def run(*argc, **argv):
  if (src := argv.get('s', argv.get('src'))) is None:
    print(f">>>ERR: SOURCE DB MUST BE PROVIDED")
    return

  host = argv.get('h', argv.get('host', '*'))
  port = argv.get('p', argv.get('port', 5555))

  # 2. Create a socket from the asyncio context
  TIME_OUT = 10000 #ms
  svc = Syncsvc(src, host, port, TIME_OUT)
  await svc.run()
