from math import pi
from bokeh.plotting import figure
import numpy as np
from common.indicator import EMA
import pandas as pd
import talib
from bokeh.layouts import column
from bokeh.io import output_file, show, save
from bokeh.models import ColumnDataSource, HoverTool, RangeTool, CDSView, BooleanFilter, DataRange1d, LinearAxis, \
    Range1d, CustomJS
from datetime import datetime
from common.time_utils import timestamp_to_datetime


class Signal:

    def __init__(self, data, marker='inverted_triangle', color='#10B479'):
        """
        信号
        :param data: 信号集数据
        :param marker: 标记类型
        :param color: 颜色
        """
        self.data = data
        self.marker = marker
        self.color = color

    @staticmethod
    def signal_below_price(data, price, func):
        """
        计算信号标记位置使其位于价格底部

        :param data:    信号数据
        :param price:   价格数据
        :param func:    目标信号判断条件方法
        :return: 位于价格底部的信号集合数据
        """
        signal = []
        for date, value in data.iteritems():
            if func(value):
                # signal.append(price[date] * 0.99)
                signal.append(price[date])
            else:
                signal.append(np.nan)
        return signal

    @staticmethod
    def signal_above_price(data, price, func):
        """
        计算信号标记位置使其位于价格顶部

        :param data:    信号数据
        :param price:   价格数据
        :param func:    目标信号判断条件方法
        :return: 位于价格顶部的信号集合数据
        """
        signal = []
        for date, value in data.iteritems():
            if func(value):
                # signal.append(price[date] * 1.01)
                signal.append(price[date])
            else:
                signal.append(np.nan)
        return signal


def make_range_tool(date, close, x_range=None, source=None):
    """
    时间范围选择工具
    :param date:
    :param close:
    :param x_range:
    :param source:
    """
    select = figure(title="", plot_height=100, plot_width=1500, x_axis_type="datetime", y_axis_type=None, tools="", toolbar_location=None, background_fill_color="#efefef")

    range_tool = RangeTool(x_range=x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2

    select.line(date, close)
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    select.toolbar.active_multi = range_tool

    return select


def make_macd_plot(source, x_range=None, up_color='#10B479', down_color='#DD253E', vbar_width=0.5):
    """
    创建一个MACD图表
    :param source: 数据源，需要的列：macd, macd_hist, macd_signal, colors_macd
    :param x_range:
    :param up_color:
    :param down_color:
    :param vbar_width:
    """
    TOOLS = "crosshair,pan,wheel_zoom,box_zoom,reset,save"

    p = figure(x_axis_type="datetime", plot_width=1500, plot_height=240, title="MACD (line + histogram)", tools=TOOLS)
    if x_range:
        p.x_range = x_range

    up = [True if val > 0 else False for val in source.data['macd_hist']]
    down = [True if val < 0 else False for val in source.data['macd_hist']]

    # MACD线柱颜色
    view_upper = CDSView(source=source, filters=[BooleanFilter(up)])
    view_lower = CDSView(source=source, filters=[BooleanFilter(down)])

    # MACD线柱
    vbar_macd_hist_top = p.vbar(x='date', top='macd_hist', bottom=0, width=vbar_width, color=up_color, source=source, view=view_upper)
    vbar_macd_hist_bottom = p.vbar(x='date', top=0, bottom='macd_hist', width=vbar_width, color=down_color, source=source, view=view_lower)

    line_macd = p.line(x='date', y='macd', line_width=1, color='black', source=source, legend_label='macd', muted_color='black', muted_alpha=0)
    line_signal = p.line(x='date', y='macd_signal', line_width=1, color='orange', source=source, legend_label='signal', muted_color='orange', muted_alpha=0)

    p.legend.location = "top_left"
    p.legend.border_line_alpha = 0
    p.legend.background_fill_alpha = 0
    p.legend.click_policy = "mute"

    # 悬浮提示
    hover_tool = HoverTool(
        tooltips="""
                <div">
                    <div><b>MACD：</b><span style="font-size: 10px; color: @colors_macd;">@macd{0.000}</span></div>
                    <div><b>MACD Signal：</b><span style="font-size: 10px; color: @colors_macd;">@macd_signal{0.000}</span></div>
                    <div><b>MACD Hist：</b><span style="font-size: 10px; color: @colors_macd;">@macd_hist{0.000}</span></div>
                    <div><b>Date：</b>@date{%F %T}</div>
                    <div><b>Y：</b>$y{0.000}</div>
                </div>
            """,

        formatters={
            '@date': 'datetime',  # use 'datetime' formatter for 'date' field
        },

        mode='vline',

        # 是否显示箭头
        show_arrow=True,

        renderers=[line_macd]
    )
    p.add_tools(hover_tool)

    return p


def make_force_index_plot(source, color='#7922AD', x_range=None):
    """
    强力指数
    :param source: 列格式：date, efi, colors_efi
    :param color:
    :param x_range:
    :param source:
    """
    TOOLS = "crosshair,pan,wheel_zoom,box_zoom,reset,save"

    p = figure(x_axis_type="datetime", title="Force Index", plot_width=1500, plot_height=240, tools=TOOLS, toolbar_location='right', x_range=x_range)

    line = p.line(x='date', y='efi', line_width=1, color=color, source=source)

    # 悬浮提示
    hover_tool = HoverTool(

        tooltips="""
            <div">
                <div><b>EFI：</b><span style="font-size: 10px; color: @colors_efi;">@efi{0,0}</span></div>
                <div><b>Date：</b>@date{%F %T}</div>
                <div><b>Y：</b>$y{0.000}</div>
            </div>
        """,

        formatters={
            '@date': 'datetime',  # use 'datetime' formatter for 'date' field
        },

        # display a tooltip whenever the cursor is vertically in line with a glyph
        # "mouse":only when the mouse is directly over a glyph
        # "vline":	whenever the a vertical line from the mouse position intersects a glyph
        # "hline":	whenever the a horizontal line from the mouse position intersects a glyph
        mode='vline',

        # 是否显示箭头
        show_arrow=True,

        # line_policy='nearest',

        renderers=[line]
    )
    p.add_tools(hover_tool)

    return p


def make_candlestick_plot(df, period=None, signals=None, title='', filename=None, ema=(5, 10, 20), ema_color=('#C09A1C', '#7922AD', '#167BE1'), source=None):
    """
    蜡烛图
    :param df: 数据集，格式：date, open, high, low, close, volume
    :param period: 时间周期，默认，单位毫秒
    :param signals: 信号集
    :param title: 标题
    :param filename: 文件名
    :param ema: 移动平均线
    :param ema_color: 移动平均线颜色
    :param source: 数据源
    """

    inc = df.close > df.open
    dec = df.open > df.close

    w = period * 0.5 if period else 24 * 60 * 60 * 1000  # half day in ms

    # TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
    TOOLS = "crosshair,pan,wheel_zoom,box_zoom,reset,save"

    # 蜡烛图
    p_candlestick = figure(x_axis_type="datetime", plot_width=1500, plot_height=450, tools=TOOLS, title=title, x_range=(df.date.iloc[0], df.date.iloc[-1]))
    # p_candlestick.sizing_mode = 'stretch_both'  # 全屏
    p_candlestick.xaxis.major_label_orientation = pi / 4  # x轴标题倾斜
    p_candlestick.grid.grid_line_alpha = 0.3

    # 绘制影线
    p_candlestick.segment(x0='date', y0='high', x1='date', y1='low', color="black", source=source)

    # 绘制柱体
    p_candlestick.vbar(df.date[inc], w, df.open[inc], df.close[inc], fill_color="#10B479", line_color="black")
    p_candlestick.vbar(df.date[dec], w, df.open[dec], df.close[dec], fill_color="#DD253E", line_color="black")

    # 绘制EMA
    ema_lines = []

    if ema:
        for index in range(0, len(ema)):

            key = 'ema%s' % ema[index]

            if key not in df:
                df[key] = EMA(df.close, ema[index])

            line = p_candlestick.line(x='date', y=key, line_color=ema_color[index], legend_label='EMA%s' % (ema[index]), source=source)

            ema_lines.append(line)

    # 绘制信号
    if signals:
        for signal in signals:
            p_candlestick.scatter(df.date, signal.data, marker=signal.marker, size=20, color=signal.color, alpha=0.6)

    if filename:
        output_file(filename, title=title, mode='inline')

    # show(p_candlestick)

    # 图例
    p_candlestick.legend.location = "top_left"
    p_candlestick.legend.border_line_alpha = 0
    p_candlestick.legend.background_fill_alpha = 0
    p_candlestick.legend.click_policy = "hide"

    return p_candlestick, ema_lines


def plot_middle_period(path, symbol):
    """
    绘制中周期图标
    :param path:    数据表路径，列格式：date, open, high, low, close, volume
    :param symbol：  交易对名称
    """
    df = pd.read_csv(path, parse_dates=True, index_col=0)

    df["date"] = df.index

    up_color = '#10B479'
    down_color = '#DD253E'

    # 计算涨幅
    pre_close = df.close.shift(1)
    df['increase'] = (df.close - pre_close) / pre_close * 100

    # EMA
    df['ema5'] = EMA(df.close, 5)
    df['ema10'] = EMA(df.close, 10)
    df['ema20'] = EMA(df.close, 20)

    # 开高低收价格颜色
    df['colors_open'] = np.where((df.open - pre_close) > 0, up_color, down_color)
    df['colors_high'] = np.where((df.high - pre_close) > 0, up_color, down_color)
    df['colors_low'] = np.where((df.low - pre_close) > 0, up_color, down_color)
    df['colors_close'] = np.where((df.close - pre_close) > 0, up_color, down_color)

    # 均线颜色
    df['colors_ema5'] = np.where((df['ema5'].diff()) > 0, up_color, down_color)
    df['colors_ema10'] = np.where((df['ema10'].diff()) > 0, up_color, down_color)
    df['colors_ema20'] = np.where((df['ema20'].diff()) > 0, up_color, down_color)

    # EFI颜色
    df['colors_efi'] = np.where(df['efi'] > 0, up_color, down_color)

    # 做多信号
    long_signal = Signal(Signal.signal_below_price(df['signals'], df['low'], lambda signals: 'buy' in signals), 'triangle', '#10B479')

    # 做空信号
    short_signal = Signal(Signal.signal_above_price(df['signals'], df['high'], lambda signals: 'short' in signals), 'inverted_triangle', '#DD253E')

    filename = 'triple_filter_trade_system_middle.html'

    title = '%s 三重滤网交易系统' % symbol

    # 数据源
    source = ColumnDataSource(df)

    # ETH/USDT 5分钟K线图
    p_candlestick, ema_lines = make_candlestick_plot(df, period=5 * 60 * 1000, signals=[long_signal, short_signal], title=title, source=source)

    # 强力指数图
    p_efi = make_force_index_plot(source, x_range=p_candlestick.x_range)

    # 悬浮提示
    hover_tool = HoverTool(

        tooltips="""
        <div">
            <div><b>Open：</b><span style="font-size: 10px; color: @colors_open;">@open{0.000}</span></div>
            <div><b>High：</b><span style="font-size: 10px; color: @colors_high;">@high{0.000}</span></div>
            <div><b>Low：</b><span style="font-size: 10px; color: @colors_low;">@low{0.000}</span></div>
            <div><b>Close：</b><span style="font-size: 10px; color: @colors_close;">@close{0.000}</span></div>
            <div><b>Increase：</b><span style="font-size: 10px; color: @colors_close;">@increase{0.00}%</span></div>
            <div><b>Volume：</b><span style="font-size: 10px; color: @colors_close;">@volume{0,0}</span></div>
            <div><b>EMA5：</b><span style="font-size: 10px; color: @colors_ema5;">@ema5{0.000}</span></div>
            <div><b>EMA10：</b><span style="font-size: 10px; color: @colors_ema10;">@ema10{0.000}</span></div>
            <div><b>EMA20：</b><span style="font-size: 10px; color: @colors_ema20;">@ema20{0.000}</span></div>
            <div><b>EFI：</b><span style="font-size: 10px; color: @colors_efi;">@efi{0,0}</span></div>
            <div><b>Date：</b>@date{%F %T}</div>
            <div><b>Y：</b>$y{0.000}</div>
        </div>
        """,

        formatters={
            '@date': 'datetime',
        },

        mode='vline',

        # 是否显示箭头
        show_arrow=True,

        renderers=[ema_lines[0]],

        # point_policy='snap_to_data',
    )
    p_candlestick.add_tools(hover_tool)

    range_tool = make_range_tool(df.date, df.close, x_range=p_candlestick.x_range, source=source)

    layout = column(range_tool, p_candlestick, p_efi)

    output_file(filename, title=title, mode='inline')

    show(layout)


def plot_long_period(path, symbol):
    """
    绘制长周期图标
    :param path:    数据表路径，列格式：date, open, high, low, close, volume
    :param symbol：  交易对名称
    """

    df = pd.read_csv(path, index_col=0, parse_dates=['Open time'], date_parser=lambda x: timestamp_to_datetime(x))

    df.rename(columns={'Open time': 'date',
                       'Open': 'open',
                       'High': 'high',
                       'Low': 'low',
                       'Close': 'close',
                       'Volume': 'volume',
                       }, inplace=True)

    # pd.to_datetime有bug，转换出来的时间不对
    # df["date"] = pd.to_datetime(df.index, unit='ms')  # 表格时间戳默认毫秒值
    df['date'] = df.index

    up_color = '#10B479'
    down_color = '#DD253E'

    # 计算涨幅
    pre_close = df.close.shift(1)
    df['increase'] = (df.close - pre_close) / pre_close * 100

    # EMA
    df['ema5'] = EMA(df.close, 5)
    df['ema10'] = EMA(df.close, 10)
    df['ema20'] = EMA(df.close, 20)

    # 开高低收价格颜色
    df['colors_open'] = np.where((df.open - pre_close) > 0, up_color, down_color)
    df['colors_high'] = np.where((df.high - pre_close) > 0, up_color, down_color)
    df['colors_low'] = np.where((df.low - pre_close) > 0, up_color, down_color)
    df['colors_close'] = np.where((df.close - pre_close) > 0, up_color, down_color)

    # 均线颜色
    df['colors_ema5'] = np.where((df['ema5'].diff()) > 0, up_color, down_color)
    df['colors_ema10'] = np.where((df['ema10'].diff()) > 0, up_color, down_color)
    df['colors_ema20'] = np.where((df['ema20'].diff()) > 0, up_color, down_color)

    # MACD
    macd, macd_signal, macd_hist = talib.MACD(df.close.to_numpy(), fastperiod=12, slowperiod=26, signalperiod=9)
    df['macd'] = macd
    df['macd_signal'] = macd_signal
    df['macd_hist'] = macd_hist

    # MACD颜色
    df['colors_macd'] = np.where((df['macd_hist']) > 0, up_color, down_color)

    filename = 'triple_filter_trade_system_long.html'

    title = '%s 三重滤网交易系统' % symbol

    # 数据源
    source = ColumnDataSource(df)

    # ETH/USDT 长周期K线图
    p_candlestick, ema_lines = make_candlestick_plot(df, period=30 * 60 * 1000, title=title, source=source)

    # MACD图表
    p_macd = make_macd_plot(source, x_range=p_candlestick.x_range)

    # 悬浮提示
    hover_tool = HoverTool(

        tooltips="""
        <div">
            <div><b>Open：</b><span style="font-size: 10px; color: @colors_open;">@open{0.000}</span></div>
            <div><b>High：</b><span style="font-size: 10px; color: @colors_high;">@high{0.000}</span></div>
            <div><b>Low：</b><span style="font-size: 10px; color: @colors_low;">@low{0.000}</span></div>
            <div><b>Close：</b><span style="font-size: 10px; color: @colors_close;">@close{0.000}</span></div>
            <div><b>Increase：</b><span style="font-size: 10px; color: @colors_close;">@increase{0.00}%</span></div>
            <div><b>Volume：</b><span style="font-size: 10px; color: @colors_close;">@volume{0,0}</span></div>
            <div><b>EMA5：</b><span style="font-size: 10px; color: @colors_ema5;">@ema5{0.000}</span></div>
            <div><b>EMA10：</b><span style="font-size: 10px; color: @colors_ema10;">@ema10{0.000}</span></div>
            <div><b>EMA20：</b><span style="font-size: 10px; color: @colors_ema20;">@ema20{0.000}</span></div>
            <div><b>MACD：</b><span style="font-size: 10px; color: @colors_macd;">@macd{0.000}</span></div>
            <div><b>MACD Signal：</b><span style="font-size: 10px; color: @colors_macd;">@macd_signal{0.000}</span></div>
            <div><b>MACD Hist：</b><span style="font-size: 10px; color: @colors_macd;">@macd_hist{0.000}</span></div>
            <div><b>Date：</b>@date{%F %T}</div>
            <div><b>Y：</b>$y{0.000}</div>
        </div>
        """,

        formatters={
            '@date': 'datetime',
        },

        mode='vline',

        # 是否显示箭头
        show_arrow=True,

        renderers=[ema_lines[0]],
    )
    p_candlestick.add_tools(hover_tool)

    range_tool = make_range_tool(df.date, df.close, x_range=p_candlestick.x_range, source=source)

    layout = column(range_tool, p_candlestick, p_macd)

    output_file(filename, title=title, mode='inline')

    show(layout)


if __name__ == "__main__":
    plot_middle_period('../triple_filter_trade_system_record.csv', 'ETH/USDT')
    # plot_long_period('../data/ETHUSDT/ETHUSDT-30m.csv', 'ETH/USDT')
