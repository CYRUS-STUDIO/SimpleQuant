"""
    Base Strategy for CTA.
"""

import numpy as np
import pandas as pd
from .data import BarData
from .order import *


class BaseStrategy(object):
    broker = None  # 经纪人..
    data = None

    record_data = pd.DataFrame()

    def __init__(self, data: pd.DataFrame):
        super(BaseStrategy, self).__init__()
        self.data = data

    def record(self, index, **kwargs):
        """
        记录自定义数据
        :param index:
        :param kwargs:
        """
        for key, value in kwargs.items():
            if key not in self.record_data.columns:
                self.record_data[key] = np.nan
            self.record_data.loc[index, key] = value

    def output_record(self, path):
        """
        数据记录数据文件
        :param path: 文件输出路径
        """
        self.record_data.to_csv(path)

    def on_start(self):
        """
        策略开始运行.
        :return:
        """

    def on_stop(self):
        """
        策略运行结束.
        :return:
        """

    def next_bar(self, bar: BarData):
        raise NotImplementedError("请在子类中实现该方法..")

    @property
    def pos(self):
        return self.broker.pos

    def cancel_all(self):
        self.broker.cancel_all()

    def buy(self, price, volume):
        """
        期货中做多，或者现货买
        :param price: 价格
        :param volume: 数量
        :return:
        """
        self.broker.buy(price, volume)

    def sell(self, price, volume):
        """
        期货合约平多，现货中的卖
        :param price: 价格
        :param volume: 数量
        :return:
        """
        self.broker.sell(price, volume)

    def short(self, price, volume):
        """
        期货做空，
        :param price: 价格
        :param volume: 数量
        :return:
        """

        self.broker.short(price, volume)

    def cover(self, price, volume):
        """
        做空平仓,
        :param price: 价格
        :param volume: 数量
        :return:
        """

        self.broker.cover(price, volume)

    def create_stop_order(self, price, volume, direction: Direction):
        """
        创建止损/止盈订单
        :param price:
        :param volume:
        :param direction:
        :return:
        """
        self.broker.create_stop_order(price, volume, direction)

