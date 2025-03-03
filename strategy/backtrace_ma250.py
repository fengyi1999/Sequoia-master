# -*- encoding: UTF-8 -*-

import logging  # 导入日志库
from strategy import turtle_trade  # 导入海龟交易策略模块


# "停机坪"策略 - 寻找涨停后横盘整理的股票，为再次上涨做准备
def check(code_name, data, end_date=None, threshold=15):
    origin_data = data  # 保存原始数据，用于后续海龟交易系统验证

    # 如果指定了结束日期，只考虑该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]

    # 检查数据量是否足够
    if len(data) < threshold:
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, threshold))
        return

    # 只取最近threshold天（默认15天）的数据
    data = data.tail(n=threshold)

    flag = False  # 初始化标志为False

    # 遍历数据，寻找涨停日
    for index, row in data.iterrows():
        try:
            # 判断涨幅是否超过9.5%（接近涨停）
            if float(row['p_change']) > 9.5:
                # 判断该涨停日是否满足海龟交易系统的入场条件
                if turtle_trade.check_enter(code_name, origin_data, row['日期'], threshold):
                    # 检查涨停后的整理形态是否符合"停机坪"特征
                    if check_internal(code_name, data, row):
                        flag = True
        except KeyError as error:
            logging.debug("{}处理异常：{}".format(code_name, error))

    return flag


# 检查涨停后的整理形态是否符合"停机坪"特征
def check_internal(code_name, data, limitup_row):
    # 获取涨停日的收盘价
    limitup_price = limitup_row['收盘']
    
    # 获取涨停日之后的数据
    limitup_end = data.loc[(data['日期'] > limitup_row['日期'])]
    
    # 只考虑涨停后的3天
    limitup_end = limitup_end.head(n=3)
    
    # 如果涨停后数据不足3天，返回False
    if len(limitup_end.index) < 3:
        return False

    # 获取涨停后第一天的数据
    consolidation_day1 = limitup_end.iloc[0]
    
    # 获取涨停后第二天和第三天的数据
    consolidation_day23 = limitup_end = limitup_end.tail(n=2)

    # 检查涨停后第一天的特征：
    # 1. 收盘价和开盘价都高于涨停价（在高位）
    # 2. 当日振幅小于3%（横盘整理特征）
    if not(consolidation_day1['收盘'] > limitup_price and consolidation_day1['开盘'] > limitup_price and
        0.97 < consolidation_day1['收盘'] / consolidation_day1['开盘'] < 1.03):
        return False

    # 获取涨停后第三天的收盘价作为参考价格
    threshold_price = limitup_end.iloc[-1]['收盘']

    # 检查涨停后第二天和第三天的特征：
    for index, row in consolidation_day23.iterrows():
        try:
            # 1. 当日振幅小于3%（横盘整理）
            # 2. 涨跌幅在-5%到5%之间（波动不大）
            # 3. 收盘价和开盘价都高于涨停价（维持在高位）
            if not (0.97 < (row['收盘'] / row['开盘']) < 1.03 and -5 < row['p_change'] < 5
                    and row['收盘'] > limitup_price and row['开盘'] > limitup_price):
                return False
        except KeyError as error:
            logging.debug("{}处理异常：{}".format(code_name, error))

    # 所有条件满足，记录该股票信息并返回True
    logging.debug("股票{0} 涨停日期：{1}".format(code_name, limitup_row['日期']))

    return True

