# -*- encoding: UTF-8 -*-

import talib as tl
import pandas as pd
import logging


# 持续上涨策略（判断MA30是否持续向上）
def check(code_name, data, end_date=None, threshold=30):
    # 检查数据量是否足够
    if len(data) < threshold:
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, threshold))
        return
    
    # 计算30日移动平均线
    data['ma30'] = pd.Series(tl.MA(data['收盘'].values, 30), index=data.index.values)

    # 如果指定了结束日期，只考虑该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]

    # 只取最近threshold天（默认30天）的数据
    data = data.tail(n=threshold)

    # 将时间周期分为三段，检查每段的均线走势
    step1 = round(threshold/3)       # 第一段结束点
    step2 = round(threshold*2/3)     # 第二段结束点

    # 判断均线是否持续上升，且最终值比初始值高出20%以上
    if data.iloc[0]['ma30'] < data.iloc[step1]['ma30'] < \
        data.iloc[step2]['ma30'] < data.iloc[-1]['ma30'] and data.iloc[-1]['ma30'] > 1.2*data.iloc[0]['ma30']:
        return True
    else:
        return False

