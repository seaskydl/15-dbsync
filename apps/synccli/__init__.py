import asyncio, tomllib
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from common.util import shuffle_str, utctime
from .client import Synccli

async def job(client, *argc, **argv):
  await client.run(*argc, **argv)
  print(f"JOB DONE AT {utctime()}\r\n")

def loadcfg():
  with open("./config/config.toml", "rb") as f:
    return tomllib.load(f)

async def run(*argc, **argv):
  cfg = loadcfg()

  cli_cfg = cfg.get('client')
  if (dst := argv.get('d', argv.get('o', argv.get('dest'))) or cli_cfg.get('database')) is None:
    print(f">>>ERR: TARGET DB MUST BE PROVIDED")
    return
  name = argv.get('n', argv.get('name', cli_cfg.get('name', shuffle_str(2, "N", {"prefix": "synccli"}))))
  argv['t'] = argv.get('t') or argv.get('table') or cli_cfg.get('tables')

  svr_cfg = cfg.get('server')
  host = argv.get('h', argv.get('host', 'localhost')) or svr_cfg.get('host')
  port = argv.get('p', argv.get('port', 5555)) or svr_cfg.get('port')

  client = Synccli(dst, name, host, port)
  sched = AsyncIOScheduler()

  #sched.add_job(job, 'interval', seconds=30, args=[client], kwargs=argv)
  sched.add_job(job, cli_cfg.get('trigger'), **cfg.get('trigger_args'), args=[client], kwargs=argv)
  print(f"SCHEDULE AS:")
  print(f"TRIGGER TYPE: {cli_cfg.get('trigger')}")
  for arg, val in cfg.get('trigger_args', {}).items():
    print(f"  {arg}: {val}")

  print("\r\n")
  async with client:
    sched.start()
    print("SYNC CLIENT STARTED...")
    print("PRESS Ctrl+C TO EXIT")
    while client.is_running:
      await asyncio.sleep(10)

  #async with client:
  #  await client.run(*argc, **argv)
  # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
