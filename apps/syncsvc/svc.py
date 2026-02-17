import signal
import zmq
import msgpack
from dataclasses import dataclass
from zmq.asyncio import Context
from common.storage import Storage, IGNORE_TABLES
from common.logger import logger
from common.util import utctime, get_settings, set_settings

@dataclass
class SYNC_ORCH :
  CLIENT = 0 #default
  SERVER = 1

class Syncsvc(object):
  def __init__(self, dbpath, host="*", port=55555, timeout=1000):
    self.host = host
    self.port = port
    self.timeout = timeout
    self.is_running = True
    self.db = Storage(dbpath, True)

  async def run(self, *argc, **argv):
    if not self.db.inited:
      return

    self.ctx = Context.instance()
    self.socket = self.ctx.socket(zmq.ROUTER)
    self.socket.bind(f"tcp://{self.host}:{self.port}")
    self.poller = zmq.Poller()
    self.poller.register(self.socket, zmq.POLLIN)

    # 信号处理，确保优雅退出
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)
    logger.info(f"SERVICE STARTED @ tcp://{self.host}:{self.port}")

    now = utctime()
    while self.is_running:
      try:
        # 使用 Poller 避免阻塞，允许程序响应退出信号
        socks = dict(self.poller.poll(self.timeout))
        if self.socket in socks:
          # ROUTER 模式接收/发送需处理 multipart 消息
          identity, _, content = await self.socket.recv_multipart()

          # 处理业务逻辑
          content = msgpack.unpackb(content)
          if (orch := content.get('strategy', SYNC_ORCH.CLIENT)) == SYNC_ORCH.SERVER:
            lst_sync_at = get_settings(tbl, "lst_sync_at", section=identity)
            condition = f"updated_at <= '{now}'" if lst_sync_at is None else f"updated_at > '{lst_sync_at}' and updated_at <= '{now}'"
          else:
            condition = content.get('condition')

          logger.info(f"REQ from {identity.decode('utf-8')}, orchester by {'CLIENT' if orch == 0 else 'SERVER'}, tables: {content.get('tbl')}")
          if (tbl := content.get('tbl')) == 'all':
            data = {tbl:self.db.fetch(tbl, condition) for tbl in self.db.tables if tbl not in IGNORE_TABLES}
          else:
            data = self.db.fetch(tbl, condition)
          await self.socket.send_multipart([identity, b'', msgpack.packb(data)])
          if content.get('strategy', SYNC_ORCH.CLIENT) == SYNC_ORCH.SERVER:
            set_settings(tbl, "lst_sync_at", now, section=identity)
      except zmq.ZMQError as e:
        if e.errno == zmq.ETERM: break # 终端上下文
        logger.error(f"ZMQ Error: {e}")
    self.cleanup()

  def _signal_handler(self, sig, frame):
    self.is_running = False

  def cleanup(self):
    self.socket.close()
    self.ctx.term()
    logger.info("SERVICE STOPPED.")