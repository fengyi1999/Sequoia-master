# -*- encoding: UTF-8 -*-
import logging


# 低回撤稳步上涨策略 - 寻找持续上涨且中途没有大幅回撤的股票
def check(code_name, data, end_date=None, threshold=60):
    # 如果指定了结束日期，只考虑该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)
        data = data.loc[mask]
    
    # 只取最近threshold天（默认60天）的数据
    data = data.tail(n=threshold)

    # 检查数据量是否足够
    if len(data) < threshold:
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, threshold))
        return False

    # 计算整个周期的涨幅比率（最后一天收盘价与第一天收盘价的比率）
    ratio_increase = (data.iloc[-1]['收盘'] - data.iloc[0]['收盘']) / data.iloc[0]['收盘']
    
    # 筛选条件1：整体涨幅至少60%
    if ratio_increase < 0.6:
        return False

    # 检查是否存在大幅回撤
    # flag = True  # 允许有一次"洗盘"的标志（注释掉的逻辑）
    
    # 遍历每一天（从第二天开始），检查是否有大幅回撤
    for i in range(1, len(data)):
        # 以下任一条件满足即视为大幅回撤：
        # 1. 单日跌幅超过7%
        # 2. 当日高开低走，且跌幅超过7%
        # 3. 连续两日累计跌幅超过10%
        # 4. 连续两日高开低走，累计跌幅超过10%
        if data.iloc[i - 1]['p_change'] < -7 \
                or (data.iloc[i]['收盘'] - data.iloc[i]['开盘'])/data.iloc[i]['开盘'] * 100 < -7 \
                or data.iloc[i - 1]['p_change'] + data.iloc[i]['p_change'] < -10 \
                or (data.iloc[i]['收盘'] - data.iloc[i - 1]['开盘']) / data.iloc[i - 1]['开盘'] * 100 < -10:
            return False
            # 注释掉的代码允许一次"洗盘"：
            # if flag:
            #     flag = False  # 第一次发现大回撤，标记为已使用容错机会
            # else:
            #     return False  # 第二次发现大回撤，返回False

    # 如果通过所有检查，返回True
    return True
