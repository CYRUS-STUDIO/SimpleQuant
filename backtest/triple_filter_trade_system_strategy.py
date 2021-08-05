"""
    三重滤网交易系统回测
    - 长周期 MACD Hist变化作为趋势判断依据，中周期强力指数指标
    -
"""

from backtest.core import Broker, BaseStrategy, BarData, ArrayManager
import pandas as pd

from backtest.core.bar_generater import BarGenerator
from backtest.core.order import Direction
from common.indicator import EMA, EFI
from common.kline_utils import period
import talib
import numpy as np
from datetime import datetime

class Queue:

    def __init__(self, size):
        self.size = size
        self.list = []

    def push(self, data):
        if len(self.list) > self.size:
            self.list.pop()
        self.list.append(data)

    @property
    def empty(self):
        return len(self.list) <= 0

    @property
    def average(self):
        """
        求平均值
        """
        return 0 if self.empty else np.average(self.list)


class TripleFilterTradeSystemStrategy(BaseStrategy):
    # 可调优的参数
    params = {
        # 时间周期参数
        'long_period': 30,  # 长周期（分钟）
        'middle_period': 5,  # 中周期（分钟）
        # 移动平均线参数
        'ema_short_window': 5,
        'ema_long_window': 10,
        # 止损百分比
        'stop_percent': 0.02,
        # 高位回撤自动止盈百分比
        'fall_back_percent': 0.85,
        # 每次交易金额
        'amount': 3000,
        # 每次交易仓位百分比
        'trade_percent': 0.8,
    }

    # MACD参数
    macd_fast_period = 12
    macd_slow_period = 26
    macd_signal_period = 9

    # 用于统计平均EMA穿透值的队列
    ema_break_queue_size = 15
    ema_break_down = Queue(ema_break_queue_size)
    ema_break_up = Queue(ema_break_queue_size)

    # 做多趋势，持续在EMA以下挂单买入
    keep_buy = False
    # 做空趋势，持续在EMA以上挂单做空
    keep_short = False

    # 当前趋势
    trend = None
    # 信号集合
    signals = []

    # 最高点
    max_high = None
    # 最低点
    min_low = None

    def __init__(self, data):
        super(TripleFilterTradeSystemStrategy, self).__init__(data)
        self.am = ArrayManager(size=1050)  # 计算产生的信号..

        self.middle_period = self.params['middle_period']
        self.long_period = self.params['long_period']

        # 长周期K线回调
        self.bg_long = BarGenerator(self.long_period, self.on_long_bar)
        # 中中期K线回调
        self.bg_middle = BarGenerator(self.middle_period, self.on_middle_bar)

        print("策略参数：%s" % self.params)

    def get_trade_amount(self):
        """
        获取交易金额
        """
        return self.params['amount']
        # return self.broker.cash * self.params['trade_percent']

    def on_start(self):
        print("策略开始运行..")

    def on_stop(self):
        print("策略停止运行..")

    def next_bar(self, bar: BarData):
        """
        这里是核心，整个策略都在这里实现..
        :param bar:
        :return:
        """
        # print(bar)

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        # print('minute', bar)

        df = self.am.get_dataframe()

        self.bg_long.update_bar(bar)
        self.bg_middle.update_bar(bar)

        # 开仓后记录最高点和最低点
        if self.pos > 0:
            if self.max_high is None or df.high.iloc[-1] > self.max_high:
                self.max_high = df.high.iloc[-1]
        elif self.pos < 0:
            if self.min_low is None or df.low.iloc[-1] < self.min_low:
                self.min_low = df.low.iloc[-1]
        else:
            # 平仓后重置最高点和最低点
            self.max_high = None
            self.min_low = None

        # 高位回撤自动止盈
        if self.max_high and df.low.iloc[-1] <= self.max_high * (1 - self.params['fall_back_percent']):
            self.signals.append('sell')

        # 低位回升自动止盈
        if self.min_low and df.high.iloc[-1] >= self.min_low * (1 + self.params['fall_back_percent']):
            self.signals.append('cover')

        # 处理交易信号
        self.handle_signals()

    def on_long_bar(self, bar: BarData):
        """
        长周期行情数据回调
        """

        # 周期数据转换
        df = period(self.am.get_dataframe(), '%sT' % self.long_period, 'open_time')
        if df.index.__len__() < 2:
            return
        # print('long', df.tail(n=1))

        # 计算长周期MACD
        macd, signal, hist = talib.MACD(df['close'].to_numpy(), self.macd_fast_period, self.macd_slow_period, self.macd_signal_period)

        # 判断当前趋势
        if hist[-1] and hist[-2]:
            if hist[-1] > hist[-2]:
                trend = 'up'
            elif hist[-1] < hist[-2]:
                trend = 'down'
            else:
                trend = 'down' if hist[-1] > 0 else 'up'

        # 趋势反转
        if self.trend == 'up' and trend == 'down':
            # 平多信号
            self.signals.append('sell')

        if self.trend == 'down' and trend == 'up':
            # 平空信号
            self.signals.append('cover')

        self.trend = trend

        # print(df.datetime.iloc[-1], '当前趋势：', self.trend, hist[-2], hist[-1])

    def on_middle_bar(self, bar: BarData):
        """
        中周期行情数据回调
        """
        # 周期数据转换
        df = period(self.am.get_dataframe(), '%sT' % self.middle_period, 'open_time')
        # print('middle', df.tail(n=1))

        # 持续在EMA下买入
        if self.keep_buy and self.pos == 0:
            self.create_buy_order()
        else:
            self.keep_buy = False

        # 持续在EMA上卖空
        if self.keep_short and self.pos == 0:
            self.create_short_order()
        else:
            self.keep_short = False

        self.calculate_signals(df)

        self.record(index=df.index[-1], open=df.open.iloc[-1], high=df.high.iloc[-1], low=df.low.iloc[-1], close=df.close.iloc[-1], volume=df.volume.iloc[-1],
                    trend=self.trend, signals=str(self.signals), max_high=self.max_high, min_low=self.min_low,
                    ema_break_up=self.ema_break_up.average, ema_break_down=self.ema_break_down.average)

    def calculate_signals(self, df: pd.DataFrame):
        """
        计算交易信号
        """

        # 计算EMA
        ema_short = EMA(df['close'], self.params['ema_short_window'])
        ema_long = EMA(df['close'], self.params['ema_long_window'])

        # 计算中周期强力指数
        efi = EFI(df['close'], df['volume'])

        if self.trend == 'up':
            # 上升趋势

            # 统计EMA平均下跌穿透值
            if df['low'].iloc[-1] < ema_short.iloc[-1]:
                self.ema_break_down.push(abs(df['low'].iloc[-1] - ema_short.iloc[-1]))

            # 上涨趋势，2日强力指数下降到0以下，做多
            if efi.iloc[-2] >= 0 > efi.iloc[-1]:
                self.signals.append('buy')

        elif self.trend == 'down':
            # 下降趋势

            # 统计EMA平均上涨穿透值
            if df['high'].iloc[-1] > ema_long.iloc[-1]:
                self.ema_break_up.push(abs(df['high'].iloc[-1] - ema_long.iloc[-1]))

            # 下跌趋势，2日强力指数上升到0以上，做空
            if efi.iloc[-2] <= 0 < efi.iloc[-1]:
                self.signals.append('short')

        self.record(index=df.index[-1], efi=efi.iloc[-1])

    def handle_signals(self):
        """
        处理信号集合
        """

        # 处理交易信号
        if self.signals:

            # 信号去重
            self.signals = np.unique(self.signals).tolist()

            for signal in self.signals:
                self.handle_signal(signal)

        self.signals.clear()

    def handle_signal(self, signal):
        """
        处理交易信号
        """
        current_price = self.am.close_array[-1]

        # 做多
        if signal == 'buy':
            if self.pos <= 0:
                self.create_buy_order()
                # 持续做多直到做多成功或者趋势反转
                self.keep_buy = True
            self.keep_short = False

        # 平多
        elif signal == 'sell':
            if self.pos > 0:
                self.cancel_all()
                self.sell(current_price * 0.99, self.pos)
            self.keep_buy = False

        # 做空
        elif signal == 'short':
            if self.pos >= 0:
                self.create_short_order()
                # 持续做空直到做空成功或者趋势反转
                self.keep_short = True
            self.keep_buy = False

        # 平空
        elif signal == 'cover':
            if self.pos < 0:
                self.cancel_all()
                self.cover(current_price * 1.01, abs(self.pos))
            self.keep_short = False

    def create_buy_order(self):
        """
        做多
        """
        current_price = self.am.close_array[-1]

        self.cancel_all()

        # 如果持有空头仓位先平空
        if self.pos < 0:
            self.cover(current_price, abs(self.pos))

        # 做多
        price = current_price - self.ema_break_down.average
        shares = self.get_trade_amount() / price
        self.buy(price, shares)

        # 止损单
        stop_price = price * (1 - self.params['stop_percent'])
        self.create_stop_order(stop_price, shares, Direction.SELL)

    def create_short_order(self):
        """
        做空
        """
        current_price = self.am.close_array[-1]

        self.cancel_all()

        # 如果持有多头仓位先平多
        if self.pos > 0:
            self.sell(current_price, abs(self.pos))

        # 做空
        price = current_price + self.ema_break_up.average
        shares = self.get_trade_amount() / price
        self.short(price, shares)

        # 止损单
        stop_price = price * (1 + self.params['stop_percent'])
        self.create_stop_order(stop_price, shares, Direction.COVER)


if __name__ == '__main__':
    from common.time_utils import timestamp_to_datetime

    # 读取分钟数据
    df = pd.read_csv('ETHUSDT-1m.csv', converters={
        'Open time': timestamp_to_datetime,
        'Close time': timestamp_to_datetime
    })

    # 数据清洗
    df.rename(columns={
        'Open time': 'open_time',
        'Close time': 'close_time',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
    }, inplace=True)

    # 截取指定时间范围的数据
    df = df[df['open_time'] >= '2021-05-01']
    df = df[df['close_time'] <= '2021-06-01']

    df.reset_index(inplace=True, drop=True)
    # print(df)

    broker = Broker()
    broker.set_symbol('ETHUSDT')
    broker.set_strategy(TripleFilterTradeSystemStrategy) # 设置策略类
    broker.set_leverage(1.0)  # 杠杆比例
    broker.set_cash(3600)  # 1初始资金.
    broker.set_commission(7 / 10000)  # 手续费
    broker.set_backtest_data(df)  # 数据.
    broker.run()
    broker.calculate().to_csv('triple_filter_trade_system_backtest.csv', index=False)
    broker.output_record('triple_filter_trade_system_record.csv')

    # 参数优化， 穷举法， 遗传算法。
    # broker.optimize_strategy(long_period=[i for i in range(30, 60, 5)], short_period=[i for i in range(5, 30, 1)])
