# -*- encoding: UTF-8 -*-  # 声明文件编码为UTF-8

# 导入必要的库
import talib as tl  # 导入talib库，用于技术分析指标计算
import pandas as pd  # 导入pandas库，用于数据处理
import logging  # 导入logging库，用于日志记录
from strategy import enter  # 导入enter模块，用于交易信号判断


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
    origin_data = data  # 保存原始数据副本
    if len(data) < threshold:  # 检查数据量是否足够
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, threshold))  # 使用format()方法格式化字符串
        return
    # 计算60日移动平均线，并添加到数据中
    data['ma60'] = pd.Series(tl.MA(data['收盘'].values, 60), index=data.index.values)

    # 如果指定了结束日期，筛选出该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)  # 创建布尔掩码
        data = data.loc[mask]  # 使用掩码筛选数据

    data = data.tail(n=threshold)  # 获取最后threshold天的数据

    breakthrough_row = None  # 初始化突破点数据行

    # 遍历每一行数据寻找突破点
    for index, row in data.iterrows():
        # 检查是否出现了突破60日均线的情况（开盘价在均线下方，收盘价在均线上方）
        if row['开盘'] < row['ma60'] <= row['收盘']:
            # 检查成交量是否符合要求
            if enter.check_volume(code_name, origin_data, row['日期'], threshold):
                breakthrough_row = row  # 记录突破点

    # 如果没有找到突破点，返回False
    if breakthrough_row is None:
        return False

    # 将数据分为突破点前后两部分
    data_front = data.loc[(data['日期'] < breakthrough_row['日期'])]  # 突破点之前的数据
    data_end = data.loc[(data['日期'] >= breakthrough_row['日期'])]  # 突破点之后的数据

    # 检查突破点之前的数据是否符合平台条件
    for index, row in data_front.iterrows():
        # 检查收盘价是否在均线的合理范围内（-5%到20%之间）
        if not (-0.05 < (row['ma60'] - row['收盘']) / row['ma60'] < 0.2):
            return False

    return True  # 所有条件都满足，返回True







