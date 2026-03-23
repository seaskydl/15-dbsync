from common.logger import logger
#from .svc import Syncsvc
from .service import service

# 1. svc port, 2. table for svc, 3. username, 3. password
async def run(*argc, **argv):
  await service.start()
  return
