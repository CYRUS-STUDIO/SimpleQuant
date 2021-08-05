"""
    Broker 经纪人，负责处理处理撮合交易订单等功能.
"""
import collections
import itertools

import pandas as pd

from .order import *
from .strategy import BaseStrategy, BarData


class Broker(object):
    def __init__(self):
        super(Broker, self).__init__()

        # 策略实例.
        self.strategy_instance = None

        # 手续费
        self.commission = 7 / 10000

        # 杠杆的比例, 默认使用杠杆.
        self.leverage = 1.0

        # 滑点率，设置为万5
        self.slipper_rate = 5 / 10000

        # 购买的资产的估值，作为计算爆仓的时候使用.
        self.asset_value = 0

        # 最低保证金比例, 使用bitfinex 的为例子.
        self.min_margin_rate = 0.15

        # 初始本金.
        self.cash = 1_000_000

        self.strategy_class = None

        # 交易的数据.
        self.trades = []

        # 交易对名称
        self.symbol = ''

        # k线数据
        self.bar = None

        # 订单id记录
        self.order_id = 0

        # 交易id记录
        self.trade_id = 0

        # 当前提交的订单.
        self.active_orders = []

        # 当前提交的止盈/止损订单
        self.stop_orders = []

        # 回测的数据 dataframe数据
        self.backtest_data = None

        # 当前的持仓量
        self.pos = 0

        # 当前时间
        self.datetime = None

        # 是否是运行策略优化的方法。
        self.is_optimizing_strategy = False

        self.daily_results = {}

    def set_symbol(self, symbol):
        """
        设置交易对
        :param symbol: 交易对名称
        :return:
        """
        self.symbol = symbol

    def set_strategy(self, strategy_class: BaseStrategy):
        """
        设置要跑的策略类.
        :param strategy_class:
        :return:
        """
        self.strategy_class = strategy_class

    def set_leverage(self, leverage: float):
        """
        设置杠杆率.
        :param leverage:
        :return:
        """
        self.leverage = leverage

    def set_commission(self, commission: float):
        """
        设置手续费.
        :param commission:
        :return:
        """
        self.commission = commission

    def set_backtest_data(self, data: pd.DataFrame):
        self.backtest_data = data

    def set_cash(self, cash):
        self.cash = cash

    def cancel_all(self):
        self.cancel_active_orders()
        self.cancel_stop_orders()

    def cancel_active_orders(self):
        self.active_orders.clear()

    def cancel_stop_orders(self):
        self.stop_orders.clear()

    def generate_order_id(self):
        self.order_id += 1
        return self.order_id

    def generate_trade_id(self):
        self.trade_id += 1
        return self.trade_id

    def create_order(self, price, volume, direction: Direction, type: OrderType = OrderType.LIMIT) -> OrderData:
        order = OrderData()
        order.symbol = self.symbol
        order.direction = direction
        order.price = price
        order.volume = volume
        order.datetime = self.datetime
        order.type = type
        order.order_id = self.generate_order_id()
        return order

    def create_trade(self, price, volume, direction, order_id) -> TradeData:
        trade = TradeData()
        trade.symbol = self.symbol
        trade.direction = direction
        trade.price = price
        trade.volume = volume
        trade.datetime = self.datetime
        trade.order_id = order_id
        trade.trade_id = self.generate_trade_id()
        return trade

    def buy(self, price, volume):
        """
        这里生成订单.
        order需要包含的信息， order_id, order_price, volume, order_time.
        :param price:
        :param volume:
        :return:
        """
        print(f"{self.bar.datetime}，做多下单: {volume}@{price}, 持仓：{self.pos}")

        """
        在这里生成订单， 等待价格到达后成交.
        """
        self.active_orders.append(self.create_order(price, volume, Direction.LONG))

    def sell(self, price, volume):
        print(f"{self.bar.datetime}，做多平仓下单: {volume}@{price}, 持仓：{self.pos}")  #
        """
        在这里生成订单， 等待价格到达后成交.
        """
        self.active_orders.append(self.create_order(price, volume, Direction.SELL))

    def short(self, price, volume):
        print(f"{self.bar.datetime}，做空下单: {volume}@{price}, 持仓：{self.pos}")
        """
        在这里生成订单， 等待价格到达后成交.
        """
        self.active_orders.append(self.create_order(price, volume, Direction.SHORT))

    def cover(self, price, volume):
        print(f"{self.bar.datetime}，做空平仓下单: {volume}@{price}, 持仓：{self.pos}")
        """
        在这里生成订单， 等待价格到达后成交.
        """
        self.active_orders.append(self.create_order(price, volume, Direction.COVER))

    def create_stop_order(self, price, volume, direction: Direction):
        print(f"{self.bar.datetime}，止盈止损下单: {volume}@{price}, 持仓：{self.pos}")
        """
        在这里生成订单， 等待价格到达后成交.
        """
        self.stop_orders.append(self.create_order(price, volume, direction, OrderType.STOP))

    def run(self):

        self.trades = []  # 开始策略前，把trades设置为空列表，表示没有任何交易记录.
        self.active_orders = []  #
        self.strategy_instance = self.strategy_class(self.backtest_data)
        self.strategy_instance.broker = self
        self.strategy_instance.on_start()

        for index, candle in self.backtest_data.iterrows():
            bar = BarData(candle['open_time'], candle['open'],
                          candle['high'], candle['low'], candle['close'], candle['volume'])
            self.bar = bar
            self.datetime = bar.datetime
            self.check_order(bar)  # 检查订单是否成交..
            self.strategy_instance.next_bar(bar)  # 处理数据..

        self.strategy_instance.on_stop()

    def output(self, msg):
        """
        Output message of backtesting engine.
        """
        print(f"{datetime.now()}\t{msg}")

    # 统计成交的信息.. 夏普率、 盈亏比、胜率、 最大回撤 年化率/最大回撤
    def calculate(self) -> pd.DataFrame:

        # 拿到成交的信息，把成交的记录统计出来.

        columns = ['datetime', 'symbol',  'open', 'high', 'low', 'close', 'order_id', 'trade_id', 'price', 'volume', 'direction',
                   'balance', 'profit', 'pos', 'turnover', 'slippage', 'commission', 'trading_pnl']

        data = []

        # 持仓数量
        pos = 0
        # 持仓成本
        holding_cost = 0
        # 利润
        profit = 0

        for trade in self.trades:
            # K线数据
            kline = self.backtest_data[self.backtest_data.open_time == trade.datetime].iloc[0]
            # 成交额
            turnover = abs(trade.volume * self.leverage * trade.price)
            # 滑点费用
            slippage = turnover * self.slipper_rate
            # 手续费
            commission = turnover * self.commission

            # 平仓
            if (pos + trade.volume) == 0:
                # 交易利润 = （平仓价格 - 开仓价格）* 平仓数量
                trading_pnl = (trade.price - holding_cost) * pos if holding_cost != 0 else 0
                holding_cost = 0
            else:
                trading_pnl = 0
                holding_cost = trade.price

            # 利润
            profit = profit + trading_pnl - commission - slippage
            # 余额 = 本金 + 利润
            balance = self.cash + profit
            # 持仓数量
            pos += trade.volume

            data.append([trade.datetime, trade.symbol, kline.open, kline.high, kline.low, kline.close,
                         trade.order_id, trade.trade_id, trade.price, trade.volume, trade.direction,
                         balance, profit, pos, turnover, slippage, commission, trading_pnl])

        df = pd.DataFrame(data=data, columns=columns)

        return df

    def check_order(self, bar):
        """
        根据订单信息， 检查是否满足成交的价格， 然后生成交易的记录.
        :param bar:
        :return:
        """
        """
        在这里比较比较订单的价格与当前价格是否满足成交，如果满足，在这里撮合订单。
        """

        self.cross_limit_order()
        self.cross_stop_order()

    def cross_limit_order(self):
        long_cross_price = self.bar.low_price
        short_cross_price = self.bar.high_price
        long_best_price = self.bar.open_price
        short_best_price = self.bar.open_price

        for order in self.active_orders:

            # Check whether limit orders can be filled.
            long_cross = (
                    (order.direction == Direction.LONG or order.direction == Direction.COVER)
                    and order.price >= long_cross_price > 0
            )

            short_cross = (
                    (order.direction == Direction.SHORT or order.direction == Direction.SELL)
                    and order.price <= short_cross_price
                    and short_cross_price > 0
            )

            if not long_cross and not short_cross:
                continue

            if long_cross:
                trade_price = min(order.price, long_best_price)
                pos_change = order.volume
            else:
                trade_price = max(order.price, short_best_price)
                pos_change = -order.volume

            self.active_orders.remove(order)
            self.pos += pos_change
            trade = self.create_trade(trade_price, pos_change, order.direction, order.order_id)
            self.trades.append(trade)

    def cross_stop_order(self):
        """
        Cross stop order with last bar/tick data.
        """
        long_cross_price = self.bar.high_price
        short_cross_price = self.bar.low_price

        for order in self.stop_orders:

            # Check whether limit orders can be filled.
            long_cross = (
                    (order.direction == Direction.LONG or order.direction == Direction.COVER)
                    and order.price <= long_cross_price > 0
            )

            short_cross = (
                    (order.direction == Direction.SHORT or order.direction == Direction.SELL)
                    and order.price >= short_cross_price > 0
            )

            if not long_cross and not short_cross:
                continue

            if long_cross:
                trade_price = min(order.price, long_cross_price)
                pos_change = order.volume
            else:
                trade_price = max(order.price, short_cross_price)
                pos_change = -order.volume

            self.stop_orders.remove(order)
            self.pos += pos_change
            trade = self.create_trade(trade_price, pos_change, order.direction, order.order_id)
            self.trades.append(trade)

    def optimize_strategy(self, **kwargs):
        """
        优化策略， 参数遍历进行..
        :param kwargs:
        :return:
        """
        self.is_optimizing_strategy = True

        optkeys = list(kwargs)
        vals = iterize(kwargs.values())
        optvals = itertools.product(*vals)  #
        optkwargs = map(zip, itertools.repeat(optkeys), optvals)
        optkwargs = map(dict, optkwargs)  # dict value...

        # for params in optkwargs:
        #     print(params)

        # 参数列表, 要优化的参数, 放在这里.
        cash = self.cash
        leverage = self.leverage
        commission = self.commission
        for params in optkwargs:
            print(params)
            self.strategy_class.params = params
            self.set_cash(cash)
            self.set_leverage(leverage)
            self.set_commission(commission)
            self.run()

    def output_record(self, path):
        if self.strategy_instance:
            self.strategy_instance.output_record(path)


def iterize(iterable):
    '''Handy function which turns things into things that can be iterated upon
    including iterables
    '''
    niterable = list()
    for elem in iterable:
        if isinstance(elem, str):
            elem = (elem,)
        elif not isinstance(elem, collections.Iterable):
            elem = (elem,)

        niterable.append(elem)

    return niterable
