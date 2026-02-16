import json, string
from pathlib import Path
from random import choices

def getFolder(foldername="data", create_if_not_exist=True):
  folder = Path.cwd() / (foldername or "data")
  if create_if_not_exist:
    folder.mkdir(parents=True, exist_ok=True)
  return str(folder)

def getFilePath(filename, folder=None, create_if_not_exist=True):
  folder_path = Path(getFolder(folder, create_if_not_exist))
  return str(folder_path / filename)

def loadJson(filename, defval={}, folder=None, create_if_not_exist=True):
  try:
    if folder is not None:
       path = Path(getFilePath(filename, folder, create_if_not_exist))
    else:
      path = Path(filename)

    if not path.exists():
      return defval

    with path.open("r", encoding="utf-8") as file:
      return json.load(file) or defval
  except Exception as e:
    print(f"ERR {str(e)}")
    return defval

def dumpJson(filename, data, folder=None, create_if_not_exist=True):
  try:
    if folder is not None:
      path = Path(getFilePath(filename, folder, create_if_not_exist))
    else:
      path = Path(filename)

    with path.open("w", encoding="utf-8") as file:
      json.dump(data, file)
      return True

  except Exception as e:
    print(f"ERR {e}")
    return True

def get_settings(table, key, def_val=None, section="default"):
  SETTINGS_FILE = "meta.json"
  FOLDER = "config"
  settings = loadJson(SETTINGS_FILE, folder=FOLDER)
  cfg = settings[section] = settings.get(section, {})
  if def_val is None:
    return cfg.get(table, {}).get(key)
  else:
    return cfg.get(table, {}).get(key, def_val)

def get_all_settings(section=None, table=None, key=None, def_val=None):
  SETTINGS_FILE = "meta.json"
  FOLDER = "config"
  settings = loadJson(SETTINGS_FILE, folder=FOLDER)
  if section is None or section == "":
    return settings

  cfg = settings.get(section, {})
  if table is None or table == "":
    return cfg

  cfg_tbl = cfg.get(table, {})
  if key is None or key == "":
    return cfg_tbl

  if def_val is None:
    return cfg_tbl.get(key)
  else:
    return cfg_tbl.get(key, def_val)


def set_settings(table, key, val, section="default"):
  SETTINGS_FILE = "meta.json"
  FOLDER = "config"
  settings = loadJson(SETTINGS_FILE, folder=FOLDER)
  cfg = settings[section] = settings.get(section, {})
  cfg_tbl = cfg[table] = cfg.get(table, {})
  cfg_tbl[key] = val
  dumpJson(filename=SETTINGS_FILE, data=settings, folder=FOLDER)

def shuffle_str(k=10, pattern="NLU", opt=None):
  opt = opt or {}
  prefix = opt.get('prefix', '')
  suffix = opt.get('suffix', '')
  pattern = pattern or "NLU"
  space = f"{string.digits if 'N' in pattern else ''}{string.ascii_lowercase if 'L' in pattern else ''}{string.ascii_uppercase if 'U' in pattern else ''}"
  return f"{prefix}{''.join(choices(space, k=k))}{suffix}"
