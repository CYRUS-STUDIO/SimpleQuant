import pandas as pd


# 强力指数 = 今日成交量 * （今日收盘价 - 昨日收盘价）
def FI(close: pd.Series, volume: pd.Series):
    return pd.Series(close.diff() * volume, name='FI')


def EFI(close, volume, span=2):
    return EMA(FI(close, volume), span)


def EMA(data, span):
    return pd.Series.ewm(data, span=span).mean()


