from datetime import datetime, timezone

def timestr(fmt='%Y-%m-%d %H:%M:%S', tz=None):
    if tz is None:
        return datetime.now().strftime(fmt)
    else:
        return datetime.now(tz).strftime(fmt)

def utctime(fmt='%Y-%m-%d %H:%M:%S'):
    return timestr(fmt, timezone.utc)