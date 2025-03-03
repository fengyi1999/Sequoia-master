# -*- encoding: UTF-8 -*-  # 声明文件编码为UTF-8

# 导入必要的库
import talib as tl  # 导入talib库，用于技术分析指标计算
import pandas as pd  # 导入pandas库，用于数据处理
import logging  # 导入logging库，用于日志记录
from datetime import datetime, timedelta  # 导入日期处理库

# 回踩年线策略 - 寻找突破年线后回踩确认支撑的股票
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
    if len(data) < 250:  # 检查数据量是否足够计算250日均线（年线）
        logging.debug("{0}:样本小于250天...\n".format(code_name))
        return
    # 计算250日移动平均线（年线）
    data['ma250'] = pd.Series(tl.MA(data['收盘'].values, 250), index=data.index.values)

    # 获取数据的起始日期
    begin_date = data.iloc[0].日期
    
    # 如果指定了结束日期，检查该股票在结束日期时是否已上市
    if end_date is not None:
        if end_date < begin_date:  # 该股票在end_date时还未上市
            logging.debug("{}在{}时还未上市".format(code_name, end_date))
            return False

    # 如果指定了结束日期，只考虑该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]

    # 只取最近threshold天（默认60天）的数据
    data = data.tail(n=threshold)

    # 获取最后一天的收盘价
    last_close = data.iloc[-1]['收盘']

    # 初始化区间最低点和最高点（默认为最后一天的数据）
    lowest_row = data.iloc[-1]   # 区间最低点
    highest_row = data.iloc[-1]  # 区间最高点
    
    # 近期低点，用于检测回踩
    recent_lowest_row = data.iloc[-1]

    # 遍历数据，找出区间内的最高点和最低点
    for index, row in data.iterrows():
        if row['收盘'] > highest_row['收盘']:
            highest_row = row
        elif row['收盘'] < lowest_row['收盘']:
            lowest_row = row

    # 确保最高点和最低点的成交量不为0（排除异常数据）
    if lowest_row['成交量'] == 0 or highest_row['成交量'] == 0:
        return False

    # 将数据分为两段：最高点之前和最高点之后
    data_front = data.loc[(data['日期'] < highest_row['日期'])]  # 最高点之前的数据
    data_end = data.loc[(data['日期'] >= highest_row['日期'])]   # 最高点之后的数据

    # 确保前半段数据不为空
    if data_front.empty:
        return False
        
    # 条件1：前半段必须是从年线以下向上突破年线（形成有效突破）
    if not (data_front.iloc[0]['收盘'] < data_front.iloc[0]['ma250'] and
            data_front.iloc[-1]['收盘'] > data_front.iloc[-1]['ma250']):
        return False

    # 确保后半段数据不为空
    if not data_end.empty:
        # 条件2：后半段必须在年线以上运行（回踩不破年线）
        for index, row in data_end.iterrows():
            if row['收盘'] < row['ma250']:
                return False
            # 找出后半段的最低点（回踩点）
            if row['收盘'] < recent_lowest_row['收盘']:
                recent_lowest_row = row

    # 处理日期格式，计算回踩点与最高点之间的时间间隔
    if isinstance(recent_lowest_row['日期'], str):
        date_value = datetime.strptime(recent_lowest_row['日期'], '%Y-%m-%d').date()
    else:
        date_value = recent_lowest_row['日期']
        
    date_diff = date_value - \
                datetime.date(datetime.strptime(highest_row['日期'], '%Y-%m-%d'))

    # 条件3：回踩时间在10到50天之间（不能太快也不能太慢）
    if not(timedelta(days=10) <= date_diff <= timedelta(days=50)):
        return False
        
    # 计算成交量比率和回踩价格比率
    vol_ratio = highest_row['成交量']/recent_lowest_row['成交量']  # 最高点成交量/回踩点成交量
    back_ratio = recent_lowest_row['收盘'] / highest_row['收盘']   # 回踩价格/最高价格
    
    # 条件4：回踩伴随缩量（至少缩量50%），且回踩幅度要足够（回踩至最高点的80%以下）
    if not (vol_ratio > 2 and back_ratio < 0.8) :
        return False

    # 所有条件满足，返回True
    return True







