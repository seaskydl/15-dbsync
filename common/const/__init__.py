from dataclasses import dataclass

@dataclass
class SYNC_DIR:
  PULL = "pull"
  PUSH = "push"
  BOTH = "both"

@dataclass
class SYNC_ORCH :
  CLIENT = 0 #default
  SERVER = 1