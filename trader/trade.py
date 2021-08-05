from datetime import datetime, timedelta
import time
import pandas as pd
from email.mime.text import MIMEText
from smtplib import SMTP_SSL
import trader.config as config

# sleep
def next_run_time(time_interval, ahead_time=1):
    if time_interval.endswith('m'):
        now_time = datetime.now()
        time_interval = int(time_interval.strip('m'))

        target_min = (int(now_time.minute / time_interval) + 1) * time_interval
        if target_min < 60:
            target_time = now_time.replace(minute=0, second=0, microsecond=0)
        else:
            if now_time.hour == 23:
                target_time = now_time.replace(hour=0, minute=0, second=0, microsecond=0)
                target_time += timedelta(days=1)
            else:
                target_time = now_time.replace(hour=now_time.hour + 1, minute=0, second=0, microsecond=0)

        # sleep直到靠近目标时间之前
        if (target_time - datetime.now()).seconds < ahead_time + 1:
            print('距离target_time不足', ahead_time, '秒，下下个周期再运行')
            target_time += timedelta(minutes=time_interval)
        print('下次运行时间', target_time)
        return target_time
    else:
        exit('time_interval doesn\'t end with m')

    return datetime.now()


# 获取okex的k线数据
def get_okex_candle_data(exchange, symbol, time_interval):
    # 抓取数据
    content = exchange.fetch_ohlcv(symbol, timeframe=time_interval, since=0)

    # 整理数据
    df = pd.DataFrame(content, dtype=float)
    df.rename(columns={0: 'MTS', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'}, inplace=True)
    df['candle_begin_time'] = pd.to_datetime(df['MTS'], unit='ms')
    # 北京时间 = 格林威治时间 + 8小时
    df['candle_begin_time_GMT8'] = df['candle_begin_time'] + timedelta(hours=8)
    df = df[['candle_begin_time_GMT8', 'open', 'high', 'low', 'close', 'volume']]

    return df


def place_order(exchange, order_type, buy_or_sell, symbol, price, amount):
    """
    下单
    :param exchange: 交易所
    :param order_type: limit, market
    :param buy_or_sell: buy, sell
    :param symbol: 买卖品种
    :param price: 当market订单的时候，price无效
    :param amount: 买卖量
    :return:
    """
    for i in range(5):
        try:
            # 限价单
            if order_type == 'limit':
                # 买
                if buy_or_sell == 'buy':
                    order_info = exchange.create_limit_buy_order(symbol, amount, price)  # 买单
                # 卖
                elif buy_or_sell == 'sell':
                    order_info = exchange.create_limit_sell_order(symbol, amount, price)  # 卖单
            # 市价单
            elif order_type == 'market':
                # 买
                if buy_or_sell == 'buy':
                    order_info = exchange.create_market_buy_order(symbol=symbol, amount=amount)  # 买单
                # 卖
                elif buy_or_sell == 'sell':
                    order_info = exchange.create_market_sell_order(symbol=symbol, amount=amount)  # 卖单
            else:
                pass

            print('下单成功：', order_type, buy_or_sell, symbol, price, amount)
            print('下单信息：', order_info, '\n')
            return order_info

        except Exception as e:
            print('下单报错，1s后重试', e)
            time.sleep(1)
    print('下单报错次数过多，程序终止')
    exit()


class QQMail:
    user = config.QQMAIL_USER  # 发件人邮箱
    pwd = config.QQMAIL_PWD  # 授权码  https://jingyan.baidu.com/article/29697b91072c51ab20de3c3f.html

    def __init__(self):
        self.smtp = SMTP_SSL('smtp.qq.com', 465)
        self.smtp.login(self.user, self.pwd)

    def send_message(self, to, subject, content):
        msg = MIMEText(content)

        msg['Subject'] = subject  # 标题
        msg['From'] = self.user  # 发件人
        msg['To'] = to  # 收件人

        self.smtp.send_message(msg)

    def quit(self):
        self.smtp.quit()


# 自动发送邮件
def auto_send_email(to_address, subject, content):
    mail = QQMail()
    mail.send_message(to_address, subject, content)
    mail.quit()
