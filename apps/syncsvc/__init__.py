from common.logger import logger
from .svc import Syncsvc

# 1. svc port, 2. table for svc, 3. username, 3. password
async def run(*argc, **argv):
  if (src := argv.get('s', argv.get('src'))) is None:
    logger.error(f"SOURCE DB MUST BE PROVIDED")
    return

  host = argv.get('h', argv.get('host', '*'))
  port = argv.get('p', argv.get('port', 5555))

  # 2. Create a socket from the asyncio context
  TIME_OUT = argv.get('t', argv.get('timeout', 10000)) #ms
  svc = Syncsvc(src, host, port, TIME_OUT)
  await svc.run(*argc, **argv)
