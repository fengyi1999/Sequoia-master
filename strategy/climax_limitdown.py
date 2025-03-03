# -*- encoding: UTF-8 -*-

import talib as tl
import pandas as pd
import logging
from strategy import enter

# 放量跌停策略
def check(code_name, data, end_date=None, threshold=60):
    if len(data) < threshold:
        logging.debug("{0}:样本小于250天...\n".format(code_name))
        return False

    data['vol_ma5'] = pd.Series(tl.MA(data['成交量'].values, 5), index=data.index.values)

    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]
    if data.empty:
        return False
    p_change = data.iloc[-1]['p_change']
    if p_change > -9.5:
        return False

    data = data.tail(n=threshold + 1)
    if len(data) < threshold + 1:
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, threshold))
        return False

    # 最后一天收盘价
    last_close = data.iloc[-1]['收盘']
    # 最后一天成交量
    last_vol = data.iloc[-1]['成交量']

    amount = last_close * last_vol * 100

    # 成交额不低于2亿
    if amount < 200000000:
        return False

    data = data.head(n=threshold)

    mean_vol = data.iloc[-1]['vol_ma5']

    vol_ratio = last_vol / mean_vol
    if vol_ratio >= 4:
        msg = "*{0}\n量比：{1:.2f}\t跌幅：{2}%\n".format(code_name, vol_ratio, p_change)
        logging.debug(msg)
        return True
    else:
        return False

# 平台突破策略 - 寻找突破横盘整理区域的股票
def check(code_name, data, end_date=None, threshold=60):
    """平台突破策略检查函数
    
    Args:
        code_name: 股票代码和名称的元组
        data: 股票历史数据DataFrame
        end_date: 结束日期，默认为None
        threshold: 样本天数阈值，默认60天
        
    Returns:
        bool: 是否满足平台突破条件
    """
    # 保存原始数据，用于后续成交量检查
    origin_data = data
    
    # 检查数据量是否足够
    if len(data) < threshold:
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, threshold))
        return
        
    # 计算60日移动平均线
    data['ma60'] = pd.Series(tl.MA(data['收盘'].values, 60), index=data.index.values)

    # 如果指定了结束日期，只考虑该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]

    # 只取最近threshold天（默认60天）的数据
    data = data.tail(n=threshold)

    # 初始化突破点数据行
    breakthrough_row = None

    # 遍历每一行数据，寻找突破点
    for index, row in data.iterrows():
        # 检查是否出现了突破60日均线的情况：
        # 开盘价在均线下方，收盘价在均线上方（当天向上突破均线）
        if row['开盘'] < row['ma60'] <= row['收盘']:
            # 检查突破点的成交量是否放大（调用enter模块的check_volume函数）
            if enter.check_volume(code_name, origin_data, row['日期'], threshold):
                breakthrough_row = row  # 记录符合条件的突破点

    # 如果没有找到符合条件的突破点，返回False
    if breakthrough_row is None:
        return False

    # 将数据分为突破点前后两部分
    data_front = data.loc[(data['日期'] < breakthrough_row['日期'])]  # 突破点之前的数据
    data_end = data.loc[(data['日期'] >= breakthrough_row['日期'])]   # 突破点之后的数据

    # 检查突破点之前的数据是否符合平台整理的特征
    for index, row in data_front.iterrows():
        # 检查收盘价是否在均线的合理范围内（大体在均线附近波动）
        # 允许价格在均线下方最多5%，或者在均线上方最多20%
        if not (-0.05 < (row['ma60'] - row['收盘']) / row['ma60'] < 0.2):
            return False

    # 所有条件都满足，返回True
    return True

