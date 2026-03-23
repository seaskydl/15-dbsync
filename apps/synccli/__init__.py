from .client import Client

async def run(*argc, **argv):
  CFG_FILE = "./config/client.toml"
  client = Client(CFG_FILE)
  await client.start()
  return
