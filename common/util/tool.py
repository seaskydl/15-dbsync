import sys

def progress(percent, msg=''):
    print("\r", end="")
    print(f"{msg} {percent}% {'▋' * (percent >> 1)}{' DONE\r\n' if percent >= 100 else ''}", end="")
    sys.stdout.flush()
