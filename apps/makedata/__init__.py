from database import Database
from .process import process

async def run(*argc, **argv):
  async with Database():
    await process(*argc, **argv)