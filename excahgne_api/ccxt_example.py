import ccxt
import trader.config  as config

# =====创建交易所

# 查看支持的交易所
# print(ccxt.exchanges)

# 创建交易所对象
exchange = ccxt.okex5()

# 设置代理
exchange.proxies = {
    'http': config.HTTP_PROXY,
    'https': config.HTTPS_PROXY,
}

# 设置apiKey和apiSecret
exchange.apiKey = config.OKEX_APIKEY
exchange.secret = config.OKEX_SECRET
exchange.password = config.OKEX_PASSWORD  # okex特有的参数Passphrase，如果不设置会报错：AuthenticationError: requires `password`

# 加载市场信息
exchange.load_markets()

# 查看支持的交易对
# print(exchange.symbols)

# =====Public API

# 获取盘口数据
# order_book = exchange.fetch_order_book(symbol=symbol)
# print(order_book)

# l2_order_book = exchange.fetch_l2_order_book(symbol=symbol)
# print(l2_order_book)

# =====获取账户资产
# 查询余额
# balance = exchange.fetch_balance()
# print(balance['info'])
# print(balance['free'])  # 可用资金
# print(balance['used'])  # 在途资金
# print(balance['total'])  # 总资金

# balance_margin = exchange.fetch_balance({'type': 'trading'})  # 获取margin账户资产
# print(balance_margin['USDT'])  # USDT这个资产的数量

# =====下单交易
# 下单参数
# symbol = 'ETH/USDT'
# pirce = 1000
# amount = 0.01

# print('ohlcv', exchange.fetch_ohlcv(symbol, timeframe='1m'))

# 下单类型：
# market：margin交易市价单
# limit：margin交易限价单
# exchange market：exchange交易市价单
# exchange limit：exchange交易限价单

# 限价单
# order_info = exchange.create_limit_buy_order(symbol, amount, pirce, {'type': 'limit'})  # margin买单
# order_info = exchange.create_limit_sell_order(symbol, amount, pirce, {'type': 'limit'})  # margin卖单

# 市价单，市价单不需要输入价格
# order_info = exchange.create_market_buy_order(symbol, amount, {'type': 'market'})  # margin买单
# order_info = exchange.create_market_sell_order(symbol, amount, {'type': 'market'})  # margin买单

# 返回内容的数据结构：https://github.com/ccxt/ccxt/wiki/Manual#placing-orders
# print(order_info['id'])
# print(order_info['info'])

# 获取待成交的订单
# open_orders = exchange.fetch_open_orders()
# print(open_orders)

# 取消订单
# exchange.cancel_order(open_orders[0]['info']['ordId'], symbol=symbol)


# =====隐式api调用

# 打印交易所所有隐式api
# print(dir(exchange))

# 策略委托下单
# 提供单向止盈止损委托 、双向止盈止损委托、计划委托
# response = exchange.private_post_trade_order_algo({
#     'instId': 'ETH-USDT',       # 产品ID
#     'tdMode': 'isolated',       # 逐仓
#     'side': 'sell',             # 订单方向 buy：买 sell：卖
#     'ordType': 'conditional',   # 单向止盈止损
#     'sz': 0.01,                 # 委托数量
#     'slTriggerPx': 999,         # 止损触发价
#     "slOrdPx": 999              # 止损委托价
# })
# print(response)


# 获取当前账户下未触发的策略委托单列表
response = exchange.private_get_trade_orders_algo_pending({
    'instId': 'ETH-USDT',  # 产品ID
    'ordType': 'conditional',  # 单向止盈止损
})
print(response)

if response['data']:
    cancel_algos = []
    for order in response['data']:
        cancel_algos.append({
            'algoId': order['algoId'],  # 策略委托单ID
            'instId': order['instId'],  # 产品ID
        })
    # 撤销策略委托订单，每次最多可以撤销10个策略委托单
    response = exchange.private_post_trade_cancel_algos(cancel_algos)
    print(response)
