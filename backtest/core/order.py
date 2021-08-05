from enum import Enum
from datetime import datetime


class Direction(Enum):
    """
    Direction of order/trade/position.
    """
    LONG = "多"
    SELL = "平多"
    SHORT = "空"
    COVER = "平空"


class OrderType(Enum):
    """
    Order type.
    """
    LIMIT = "限价"
    MARKET = "市价"
    STOP = "STOP"


class OrderData(object):
    """
    Order data contains information for tracking lastest status
    of a specific order.
    """

    symbol: str
    order_id: str

    type: OrderType = OrderType.LIMIT
    direction: Direction = None
    price: float = 0
    volume: float = 0
    traded: float = 0
    datetime: datetime = None


class TradeData(object):
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """

    symbol: str
    order_id: str
    trade_id: str
    direction: Direction = None

    price: float = 0
    volume: float = 0
    datetime: datetime = None
