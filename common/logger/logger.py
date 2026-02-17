import sys, os
from loguru import logger
from common.util import getFilePath, getFolder, loadJson

CFG = {
  "Console": {
    "Enable": True,
    "Level": "INFO"
  },
  "File": {
    "Enable": False,
    "Level": "WARNING",
    "Rotation": "10MB",
    "Retention": "7 days"
  }
}


class Logger:
  def __init__(self):
    #self._file_set = config.LOGURU_FILE
    #self._console_set = config.LOGURU_CONSOLE
    pass

  def get_log_path(self, message: str) -> str:
    log_level = message.record["level"].name.lower()
    log_file = f"{log_level}.log"
    log_path = os.path.join(self.log_dir, log_file)
    return log_path

  def cleanLogs(self):
      # 清理日志目录下所有log文件
      # 要删除文件的目录
      directory = getFolder("logs")

      # 列出目录下所有文件和文件夹
      files_and_folders = os.listdir(directory)

      # 过滤出所有.log文件
      log_files = [file for file in files_and_folders if file.endswith('.log')]

      # 删除每一个.txt文件
      for txt_file in log_files:
        file_path = os.path.join(directory, txt_file)
        if os.path.isfile(file_path):
          os.remove(file_path)

  def configure(self):
    # 清除所有现有的日志处理器（如果有的话）
    logger.remove()

    # 控制台输出
    CONFIG = loadJson(getFilePath("log.json", "config"))
    CFG.update(CONFIG)

    CFG_CONSOLE = CFG.get("Console", {})
    if CFG_CONSOLE.get("Enable", False):
      level = CFG_CONSOLE.get("Level", "INFO")
      logger.add(
        sink=sys.stderr,
        format="[<green>{time:YYYYMMDD HH:mm:ss}</green>|{level:<8}| <level>{message}</level>",
        level=level
      )
      '''
      "<cyan>{module}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
      '''

    # 文件保存
    CFG_FILE = CFG.get("File", {})
    if CFG_FILE.get("Enable", False):

      #清理日志目录下所有log文件
      self.cleanLogs()

      # 设置输出日志文件名
      log_path = getFilePath('{time:YYYY-MM-DD}.log', 'logs')
      level     = CFG_FILE.get("Level", "WARNING") #cfgMgr.config("Log", "File", "Level", default="WARNING")
      rotation  = CFG_FILE.get("Rotation", "10MB") #cfgMgr.config("Log", "File", "Rotation", default="10MB")
      retention = CFG_FILE.get("Retention", "7 days") #cfgMgr.config("Log", "File", "Retention", default="7 days")

      logger.add(
        log_path,
        rotation=rotation,
        retention=retention,
        compression='zip',
        encoding="utf-8",
        enqueue=True,
        format="[{time:YYYYMMDD HH:mm:ss} {level:<6} | {file}:{module}.{function}:{line}]  {message}",
        level=level,
        backtrace=True
      )

configurator = Logger()
configurator.configure()
