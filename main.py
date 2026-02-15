import fire
from wakepy import keep
import sys, asyncio
if sys.platform == 'win32':
  asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Applications(object):
  def __welcome__(self):
    print("WELCOME TO DATA MANIPULATE TOOL")

  def __init__(self):
    self.__welcome__()

  async def makedata(self, *argc, **argv):
    from apps.makedata import run
    await run(*argc, **argv)

  async def sync(self, *argc, **argv):
    from apps.sync import run
    await run(*argc, **argv)

  async def syncsvc(self, *argc, **argv):
    from apps.syncsvc import run
    await run(*argc, **argv)

  async def synccli(self, *argc, **argv):
    from apps.synccli import run
    await run(*argc, **argv)

if __name__ == "__main__":
  with keep.running():
    fire.Fire(Applications)
