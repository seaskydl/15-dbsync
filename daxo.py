from dataclasses import dataclass
import sys, asyncio
import fire
from wakepy import keep

if sys.platform == 'win32':
  asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@dataclass
class DAXO_INFO:
  NAME = "DAXO"
  DESC = "Data Autonomous eXecution Orchestrator"
  VERSION = "0.1.3"
  AUTHOR = "Jason"
  RELEASE = "15Feb2026"
  SINCE = "2023"
  LICENSE = "MIT"

class Applications(object):
  def __welcome__(self):
    print('''
    ██████╗  █████╗ ██╗  ██╗ ██████╗
    ██╔══██╗██╔══██╗██║ ██╔╝██╔═══██╗
    ██████╔╝███████║█████╔╝ ██║   ██║
    ██╔══██╗██╔══██║██╔═██╗ ██║   ██║
    ██████╔╝██║  ██║██║  ██╗╚██████╔╝
    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝

                    d a x o
            Data Power, Simplified.

                        Designed by Jason @Sydney
''')

  def __init__(self):
    self.__welcome__()

  #Making testing data only
  async def makedata(self, *argc, **argv):
    from apps.makedata import run
    await run(*argc, **argv)

  #初始化配置、环境、工作区
  async def init(self, *argc, **argv):
    pass
    print(argc)
    print(argv)

  #	显示版本、环境、状态
  async def info(self, *argc, **argv):
    print("\r\n")
    print("┌───────────────────────────────────────────────┐")
    print(f"│                   {DAXO_INFO.NAME}  v{DAXO_INFO.VERSION}                │")
    print(f"│     {DAXO_INFO.DESC}    │")
    print("│                                               │")
    print(f"│                     Release at {DAXO_INFO.RELEASE}      │")
    print(f"│                     License {DAXO_INFO.LICENSE}, since {DAXO_INFO.SINCE}   │")
    print("└───────────────────────────────────────────────┘")


  #配置管理（set/get/list）
  async def config(self, *argc, **argv):
    pass

  #查看当前数据状态、同步状态
  async def status(self, *argc, **argv):
    from common.util import get_all_settings
    settings = get_all_settings()

    def getDesc(client):
      return {
        "default": "(LOCAL)",
        "remote": "(ORCH by CLIENT)"
      }.get(client, "(CLIENT ID, ORCH by SERVER)")

    for client, data in settings.items():
      print(f"CLIENT: {client} {getDesc(client)}")
      print(" TABLE       LAST UPDATE")
      print(" ----------- -------------------")
      for tbl, d in data.items():
        for _, v in d.items():
          print(f" {tbl:<11} {v}")
      print("\r\n")

  #LOCAL SYNC TOOL
  async def sync(self, *argc, **argv):
    from apps.sync import run
    await run(*argc, **argv)

  #SYNC SVC
  async def servd(self, *argc, **argv):
    from apps.syncsvc import run
    await run(*argc, **argv)

  #SYNC CLIENT
  async def client(self, *argc, **argv):
    from apps.synccli import run
    await run(*argc, **argv)

if __name__ == "__main__":
  with keep.running():
    fire.Fire(Applications)
