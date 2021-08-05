import pandas as pd


def period(df: pd.DataFrame, rule, on) -> pd.DataFrame:
    """
    DataFrame 转换周期
    :param df:
    :param rule: 时间周期，比如 '5T'（5分钟）、1H（1小时）
    :param on: 时间列
    :return:
    """
    period_df = df.resample(rule=rule, on=on).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
    })
    return period_df
