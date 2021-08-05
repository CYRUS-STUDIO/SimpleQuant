from datetime import datetime


def timestamp_to_datetime(timestamp, unit='ms') -> datetime:
    if unit == 'ms':
        return datetime.fromtimestamp(int(timestamp[:-3]))
    else:
        return datetime.fromtimestamp(int(timestamp))

