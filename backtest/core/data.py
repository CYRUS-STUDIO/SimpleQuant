
class BarData(object):
    """
    K 线数据模型.
    """
    def __init__(self, datetime, open_price, high_price, low_price, close_price, volume):
        self.datetime = datetime
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume

    def __str__(self):
        return f"{self.datetime} {self.open_price} {self.high_price} {self.low_price} {self.close_price} {self.volume}"


class TradeData(object):
    pass