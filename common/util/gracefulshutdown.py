import signal

# 1. 设置信号处理函数
class GracefulShutdown:
  _exit_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    #print(f"收到退出信号 ({signum})，正在清理并退出...")
    self._exit_now = True

  @property
  def exit(self):
    return self._exit_now