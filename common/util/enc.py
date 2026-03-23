import random

def info_tag(useEnc=False):
  ENC_SRC = "CENOPRTY"
  STR_SRC = "ABDFGHIJKLMQSUVWSZ"
  return f"{''.join(random.choices(STR_SRC, k=random.randint(2, 5)))}{random.choice(ENC_SRC if useEnc else STR_SRC)}"

def encrypt(data):
  #TODO:
  return data

def decrypt(data):
  return data