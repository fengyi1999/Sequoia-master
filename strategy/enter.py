# -*- encoding: UTF-8 -*-

import talib as tl
import pandas as pd
import logging


# 策略1：突破策略 - 收盘价从下向上突破指定区间内最高价
def check_breakthrough(code_name, data, end_date=None, threshold=30):
    max_price = 0  # 初始化最高价
    
    # 如果指定了结束日期，只考虑该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]
    
    # 获取最近threshold+1天数据
    data = data.tail(n=threshold+1)
    if len(data) < threshold + 1:
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, threshold))
        return False

    # 获取最后一天的收盘价和开盘价
    last_close = float(data.iloc[-1]['收盘'])
    last_open = float(data.iloc[-1]['开盘'])

    # 获取倒数第二天的数据
    data = data.head(n=threshold)
    second_last_close = data.iloc[-1]['收盘']

    # 计算区间内的最高收盘价
    for index, row in data.iterrows():
        if row['收盘'] > max_price:
            max_price = float(row['收盘'])

    # 入场条件：
    # 1. 最后一天收盘价突破前期最高价
    # 2. 倒数第二天收盘价小于前期最高价（确认是刚刚突破，而不是已经突破很久）
    # 3. 最后一天开盘价小于前期最高价（确认是在当天突破的）
    # 4. 当日涨幅大于6%（强势突破）
    if last_close > max_price > second_last_close and max_price > last_open \
            and last_close / last_open > 1.06:
        return True
    else:
        return False


# 策略2：均线策略 - 判断收盘价是否高于N日均线
def check_ma(code_name, data, end_date=None, ma_days=250):
    # 检查数据量是否足够
    if data is None or len(data) < ma_days:
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, ma_days))
        return False

    # 计算指定日数的移动平均线
    ma_tag = 'ma' + str(ma_days)
    data[ma_tag] = pd.Series(tl.MA(data['收盘'].values, ma_days), index=data.index.values)

    # 如果指定了结束日期，只考虑该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]

    # 获取最后一天的收盘价和对应的均线值
    last_close = data.iloc[-1]['收盘']
    last_ma = data.iloc[-1][ma_tag]
    
    # 入场条件：收盘价高于均线（表明股价处于均线上方，可能是上升趋势）
    if last_close > last_ma:
        return True
    else:
        return False


# 策略3：新股策略 - 判断股票上市时间是否小于指定天数
def check_new(code_name, data, end_date=None, threshold=60):
    # 简单判断数据量是否小于阈值天数
    size = len(data.index)
    if size < threshold:
        return True  # 数据少于threshold天，可能是新股
    else:
        return False


# 策略4：放量策略 - 成交量是否大于5日均量2倍以上
def check_volume(code_name, data, end_date=None, threshold=60):
    # 检查数据量是否足够
    if len(data) < threshold:
        logging.debug("{0}:样本小于250天...\n".format(code_name))
        return False
    
    # 计算5日成交量均线
    data['vol_ma5'] = pd.Series(tl.MA(data['成交量'].values, 5), index=data.index.values)

    # 如果指定了结束日期，只考虑该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]
    if data.empty:
        return False
    
    # 获取最后一天的涨跌幅
    p_change = data.iloc[-1]['p_change']
    
    # 条件1：涨幅至少2%且收盘价高于开盘价（表示上涨）
    if p_change < 2 or data.iloc[-1]['收盘'] < data.iloc[-1]['开盘']:
        return False
    
    # 获取最近threshold+1天的数据
    data = data.tail(n=threshold + 1)
    if len(data) < threshold + 1:
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, threshold))
        return False

    # 获取最后一天的收盘价和成交量
    last_close = data.iloc[-1]['收盘']
    last_vol = data.iloc[-1]['成交量']

    # 计算成交额（收盘价 * 成交量 * 100股）
    amount = last_close * last_vol * 100

    # 条件2：成交额至少2亿元（过滤小盘股和流动性差的股票）
    if amount < 200000000:  # 2亿
        return False

    # 获取前threshold天的数据
    data = data.head(n=threshold)

    # 获取5日均量
    mean_vol = data.iloc[-1]['vol_ma5']

    # 计算量比（当日成交量/5日均量）
    vol_ratio = last_vol / mean_vol
    
    # 条件3：量比至少2倍（表示放量）
    if vol_ratio >= 2:
        msg = "*{0}\n量比：{1:.2f}\t涨幅：{2}%\n".format(code_name, vol_ratio, p_change)
        logging.debug(msg)
        return True
    else:
        return False


# 策略5：连续放量策略 - 连续window_size天成交量都大于5日均量3倍
def check_continuous_volume(code_name, data, end_date=None, threshold=60, window_size=3):
    stock = code_name[0]
    name = code_name[1]
    
    # 计算5日成交量均线
    data['vol_ma5'] = pd.Series(tl.MA(data['成交量'].values, 5), index=data.index.values)
    
    # 如果指定了结束日期，只考虑该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]
    
    # 获取最近threshold+window_size天的数据
    data = data.tail(n=threshold + window_size)
    if len(data) < threshold + window_size:
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, threshold+window_size))
        return False

    # 获取最后一天的收盘价和成交量
    last_close = data.iloc[-1]['收盘']
    last_vol = data.iloc[-1]['成交量']

    # 分离数据：前threshold天用于计算基准均量，后window_size天用于检查连续放量
    data_front = data.head(n=threshold)
    data_end = data.tail(n=window_size)

    # 获取5日均量基准
    mean_vol = data_front.iloc[-1]['vol_ma5']

    # 检查最近window_size天是否都满足放量条件（成交量/5日均量 >= 3）
    for index, row in data_end.iterrows():
        if float(row['成交量']) / mean_vol < 3.0:
            return False

    # 所有条件满足，记录日志并返回True
    msg = "*{0} 量比：{1:.2f}\n\t收盘价：{2}\n".format(code_name, last_vol/mean_vol, last_close)
    logging.debug(msg)
    return True
