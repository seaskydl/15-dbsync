from common.util import progress as bar, shuffle_str
from database.models import User, Task, Log, Account, Course, Exam

TABLES = {
  "User": User,
  "Task": Task,
  "Log": Log,
  "Account": Account,
  "Course": Course,
  "Exam": Exam
}

async def make_update(name, mdl, count):
  STEP = 100 / count
  checkpoint = 0
  for i in range(count):
    checkpoint = int(STEP * (i+1))
    bar(checkpoint, f"MAKE DATA {name}:")
    await mdl.create(name=f"{i+1}-{shuffle_str()}")
  if checkpoint != 100:
    bar(100, f"MAKE DATA {name}:")

async def process(*argc, **argv):
  count = argv.get("count", 100)

  if len(argc) == 0:
    for name, mdl in TABLES.items():
      await make_update(name, mdl, count)
  else:
    for arg in argc:
      if (mdl :=arg.lower()) in TABLES:
        await make_update(mdl, count)
