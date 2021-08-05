import pandas as pd


def signal_moving_average(df: pd.DataFrame, para=[5, 60]):
    """
    简单的移动平均线策略
    当短期均线由下向上穿过长期均线的时候，买入；然后由上向下穿过的时候，卖出。
    :param df: 原始数据
    :param para: 参数，[ma_short, ma_long]
    :return:
    """
    # ===计算指标
    ma_short = para[0]
    ma_long = para[1]

    # 计算均线
    df['ma_short'] = df['close'].rolling(ma_short, min_periods=1).mean()
    df['ma_long'] = df['close'].rolling(ma_long, min_periods=1).mean()

    # ===找出买入信号
    condition1 = df['ma_short'] > df['ma_long']  # 短期均线 > 长期均线
    condition2 = df['ma_short'].shift(1) <= df['ma_long'].shift(1)  # 之前的短期均线 <= 长期均线
    df.loc[condition1 & condition2, 'signal'] = 1

    # ===找出卖出信号
    condition1 = df['ma_short'] < df['ma_long']  # 短期均线 < 长期均线
    condition2 = df['ma_short'].shift(1) >= df['ma_long'].shift(1)  # 之前的短期均线 >= 长期均线
    df.loc[condition1 & condition2, 'signal'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    df.drop(['ma_short', 'ma_long'], axis=1, inplace=True)

    # ===由signal计算出实际的每天持有仓位
    # signal的计算运用了收盘价，是每根K线收盘之后产生的信号，到第二根开盘的时候才买入，仓位才会改变。
    df['pos'] = df['signal'].shift()
    df['pos'].fillna(method='ffill', inplace=True)
    df['pos'].fillna(value=0, inplace=True)

    return df
