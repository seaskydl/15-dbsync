import signal
import zmq, msgpack
import uuid
import asyncio
import zstandard as zstd
from zmq.asyncio import Context
#from common.const import SYNC_DIR
from common.util import call_func
from common.logger import logger
from common.util import info_tag, encrypt

SOCKET_TYPE = {
  zmq.PAIR	 : "PAIR",    #Pair	一对一双向通信（很少用于生产）
  zmq.PUB	   : "PUB",	    #Publisher	发布消息（广播）
  zmq.SUB	   : "SUB",	    #Subscriber	订阅消息（广播接收）
  zmq.REQ	   : "REQ",	    #Request	请求端（同步请求/响应模式）
  zmq.REP	   : "REP",	    #Reply	响应端（同步请求/响应模式）
  zmq.DEALER : "DEALER",	#Dealer	异步 REQ（高级模式）
  zmq.ROUTER : "ROUTER",	#Router	异步 REP（高级模式）
  zmq.PULL   : "PULL",    #Pull	从 Push 接收消息
  zmq.PUSH   : "PUSH",    #Push	向 Pull 发送消息
  zmq.XPUB   : "XPUB",    #Extended Publisher	PUB 的扩展版本，可接收订阅事件
  zmq.XSUB   : "XSUB",    #Extended Subscriber	SUB 的扩展版本，可发送订阅事件
  zmq.STREAM : "STREAM" 	#Stream	TCP 流模式（可用于与非 ZMQ 客户端通信）
}

CHUNK = 1024 * 1024
COMPRESS_THRESHOLD = 64 * 1024

_zstd = zstd.ZstdCompressor()
_zstd_d = zstd.ZstdDecompressor()

def compress(data: bytes) -> bytes:
  return _zstd.compress(data)

def decompress(data: bytes) -> bytes:
  return _zstd_d.decompress(data)

def chunk_bytes(data, size=CHUNK):
  for i in range(0, len(data), size):
    yield data[i:i+size]

class Zzmq(object):
  host = None
  port = None
  mode = zmq.DEALER
  name = None
  ctx = None
  socket = None

  _inited = False

  def __init__(self, *args, **kwargs):
    self.name = kwargs.get("name")
    self.host = kwargs.get("host")
    self.port = kwargs.get("port")
    self.mode =  kwargs.get("mode", zmq.DEALER) or zmq.DEALER

    self.use_compress = kwargs.get('use_compress', True)
    self.max_retries =  kwargs.get('max_retries', 3)

    super().__init__(*args, **kwargs)

  @property
  def inited(self):
    return self._inited

  def initialize(self):
    self._inited = True
    return True

  #client function
  async def send_request(self, cmd, data):
    # 序列化 data
    packed = msgpack.packb(data, use_bin_type=True)
    msg_id = uuid.uuid4().hex

    meta = {
      "compressed": False,
      "algo": None,
    }

    if self.use_compress and len(packed) >= COMPRESS_THRESHOLD:
      packed = compress(packed)
      meta["compressed"] = True
      meta["algo"] = "zstd"

    meta_bytes = msgpack.packb(meta, use_bin_type=True)
    chunks = list(chunk_bytes(packed))

    # START
    await self.socket.send_multipart([
      cmd.encode(),
      msg_id.encode(),
      b"START",
      meta_bytes,
      chunks[0]
    ])

    # BODY
    for chunk in chunks[1:]:
      await self.socket.send_multipart([
        cmd.encode(),
        msg_id.encode(),
        b"BODY",
        chunk
      ])

    # END
    await self.socket.send_multipart([
      cmd.encode(),
      msg_id.encode(),
      b"END"
    ])

    return msg_id

  async def _wait_ack(self, msg_id, timeout=5000):
    end_time = asyncio.get_event_loop().time() + timeout / 1000

    while True:
      if asyncio.get_event_loop().time() >= end_time:
        raise TimeoutError("wait_ack timeout")

      socks = dict(await self.poller.poll(timeout=100))
      if not socks:
        continue

      if self.socket in socks:
        parts = await self.socket.recv_multipart()
        # ACK 格式: [b"ACK"][msg_id][b"DONE"]
        if len(parts) == 3 and parts[0] == b"ACK":
          r_msg_id = parts[1].decode()
          if r_msg_id == msg_id:
            return

        # 如果不是 ACK，可以缓存起来（简单起见这里直接丢弃或忽略）

  #CLIENT FUNCTION
  @logger.catch
  async def recv_response(self, msg_id, timeout=5000):
    """等待指定 msg_id 的回复"""
    end_time = asyncio.get_event_loop().time() + timeout / 1000
    while True:
      now = asyncio.get_event_loop().time()
      if now >= end_time:
        raise TimeoutError("recv_reply timeout")

      socks = dict(await self.poller.poll(timeout=100))
      if not socks:
        continue

      if self.socket in socks:
        parts = await self.socket.recv_multipart()
        cmd, r_msg_id, flag = parts[:3]

        cmd = cmd.decode()
        r_msg_id = r_msg_id.decode()
        flag = flag.decode()

        # 不是我们要的消息，忽略（理论上不会发生）
        if r_msg_id != msg_id:
          continue

        if flag == "START":
          meta_bytes = parts[3]
          payload = parts[4]
          meta = msgpack.unpackb(meta_bytes, raw=False)
          self.buffers[msg_id] = [payload]
          self.cmd_map[msg_id] = (cmd, meta)

        elif flag == "BODY":
          payload = parts[3]
          self.buffers[msg_id].append(payload)

        elif flag == "END":
          cmd, meta = self.cmd_map[msg_id]
          packed = b"".join(self.buffers[msg_id])

          if meta.get("compressed"):
            packed = decompress(packed)
          data = msgpack.unpackb(packed, raw=False)

          # 清理
          del self.buffers[msg_id]
          del self.cmd_map[msg_id]

          return cmd, data

  #server function
  async def send_response(self, identity, cmd, msg_id, data):
    packed = msgpack.packb(data, use_bin_type=True)

    meta = {"compressed": False, "algo": None}
    if len(packed) >= COMPRESS_THRESHOLD:
      print("compressing data")
      packed = compress(packed)
      meta["compressed"] = True
      meta["algo"] = "zstd"

    meta_bytes = msgpack.packb(meta, use_bin_type=True)
    chunks = list(chunk_bytes(packed))

    # START
    await self.socket.send_multipart([
      identity,
      cmd.encode(),
      msg_id.encode(),
      b"START",
      meta_bytes,
      chunks[0]
    ])

    # BODY
    for chunk in chunks[1:]:
      await self.socket.send_multipart([
        identity,
        cmd.encode(),
        msg_id.encode(),
        b"BODY",
        chunk
      ])

    # END
    await self.socket.send_multipart([
      identity,
      cmd.encode(),
      msg_id.encode(),
      b"END"
    ])

  def cleanup(self):
    self.socket.close()
    self.ctx.term()
    logger.info("SERVICE STOPPED SUCCESSFULLY.")

  def __del__(self):
    self.cleanup()

  async def __aenter__(self):
    self.initialize()
    return self

  async def __aexit__(self, exc_type, exc, tb):
    self.cleanup()

  def __enter__(self):
    self.initialize()
    return self

  def __exit__(self, exc_type, exc, tb):
    self.cleanup()

class Zmq_cli(Zzmq):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.buffers = {}
    self.cmd_map = {}

  def initialize(self):
    self.ctx = Context.instance()
    self.socket = self.ctx.socket(self.mode) #zmq.DEALER
    self.socket.setsockopt(zmq.IDENTITY, self.name.encode('utf-8'))
    self.socket.connect(f"tcp://{self.host}:{self.port}")

    self.poller = zmq.asyncio.Poller()
    self.poller.register(self.socket, zmq.POLLIN)

    return super().initialize()

  async def on_resp(self, *args, **kwargs):
    return True

  #Client funcion
  async def request(self, cmd, data, cbf=None, *args, **kwargs):
    try:
      for attempt in range(1, self.max_retries + 1):
        try:
          msg_id = await self.send_request(cmd, data)
          timeout = kwargs.get("timeout", 5000)
          await self._wait_ack(msg_id, timeout=timeout)
          cmd, data = await self.recv_response(msg_id, timeout=100000)
          return await call_func(cbf or self.on_resp, cmd, data, *args, **kwargs)
        except TimeoutError:
          if attempt == self.max_retries:
            raise
          # 简单重传策略：超时就重发
          # 这里可以加 backoff 等
        except zmq.ZMQError as e:
          if e.errno == zmq.ETERM:
            return False   # Shutting down, quit
          else:
            raise

    except Exception as e:
      logger.error(f"REQ: {str(e)}")
      return False

def OK(data={}, msg='success', useEnc=False):
  return {
    'code': 0,
    'data': encrypt(data) if useEnc else data,
    'msg': msg,
    'tag': info_tag(useEnc)
  }

def FAIL(msg, data={}, useEnc=False):
  return {
    'code': 1,
    'data': encrypt(data) if useEnc else data,
    'msg': msg,
    'tag': info_tag(useEnc)
  }
class Zmq_svc(Zzmq):
  _is_running = False

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.buffers = {}
    self.cmd_map = {}
    self.identity_map = {}

    self.routers = {}   # cmd → handler

  # -------------------------
  # 自动注册 handler
  # -------------------------
  def route(self, cmd):
    def decorator(func):
      if cmd in self.routers:
        ERROR = f"DUPLICATE CMD[{cmd}] DEFINED"
        logger.error(ERROR)
        raise Exception(ERROR)

      self.routers[cmd] = func
      return func
    return decorator

  @property
  def is_running(self):
    return self._is_running

  @property
  def is_initialied(self):
    return self.is_running

  def stop(self):
    self._is_running = False

  def _signal_handler(self, sig, frame):
    logger.info("USER REQUEST STOP, PLEASE WAIT SERVICE CLEAN UP")
    self.stop()

  def initialize(self):
    if self.is_initialied:
      return True

    self.ctx = Context.instance()
    self.socket  = self.ctx.socket(self.mode) #zmq.ROUTER
    self.socket .bind(f"tcp://{self.host}:{self.port}")

    self.poller = zmq.asyncio.Poller()
    self.poller.register(self.socket, zmq.POLLIN)

    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)

    self._is_running = True

    return super().initialize()

  async def error_no_handler(self, instance, identity, cmd, data):
    return FAIL(f"DEV: {cmd} IS NOT SUPPORTED")

  async def start(self, timeout=1000):
    if not self.initialize():
      return False

    logger.success(f"SERVICE({self.name}) IS RUNNING AT: {self.host}:{self.port}, MODE: {SOCKET_TYPE.get(self.mode, "UNKNOWN")}")

    while self.is_running:
      try:
        # 使用 Poller 避免阻塞，允许程序响应退出信号
        socks = dict(await self.poller.poll(timeout))
        # 超时：检查是否需要退出
        if not socks:
          continue

        if self.socket in socks:
          # ROUTER 模式接收/发送需处理 multipart 消息
          parts = await self.socket.recv_multipart()
          identity, cmd, msg_id, flag = parts[:4]
          payloads = parts[4:]

          cmd = cmd.decode()
          msg_id = msg_id.decode()
          flag = flag.decode()

          if flag == "START":
            meta_bytes = payloads[0]
            payload = payloads[1]

            meta = msgpack.unpackb(meta_bytes, raw=False)

            self.buffers[msg_id] = [payload]
            self.cmd_map[msg_id] = (cmd, meta)
            self.identity_map[msg_id] = identity

          elif flag == "BODY":
            self.buffers[msg_id].append(payloads[0])

          elif flag == "END":
            cmd, meta = self.cmd_map[msg_id]
            identity = self.identity_map[msg_id]

            packed = b"".join(self.buffers[msg_id])
            if meta.get("compressed"):
              packed = decompress(packed)

            data = msgpack.unpackb(packed, raw=False)

            # 先发 ACK
            await self.socket.send_multipart([
                identity,
                b"ACK",
                msg_id.encode(),
                b"DONE"
            ])

            # -------------------------
            # 自动分发到 handler
            # 业务处理
            # -------------------------
            if (handler := self.routers.get(cmd, self.error_no_handler)):
                resp_data = await handler(self, identity.decode(), cmd, data)

            await self.send_response(self.identity_map[msg_id], cmd, msg_id, resp_data)

            # 清理
            del self.buffers[msg_id]
            del self.cmd_map[msg_id]
            del self.identity_map[msg_id]
      except zmq.ZMQError as e:
        if e.errno == zmq.ETERM:
          break # 终端上下文
        logger.error(f"ZMQ Error: {e}")

    self.cleanup()
