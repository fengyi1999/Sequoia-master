# -*- encoding: UTF-8 -*-  # 声明文件编码为UTF-8
import logging  # 导入logging库，用于日志记录
import settings  # 导入settings模块，用于获取配置信息


# 高而窄的旗形
def check(code_name, data, end_date=None, threshold=60):
    """高而窄的旗形形态检查函数
    Args:
        code_name: 股票代码和名称的元组
        data: 股票历史数据DataFrame
        end_date: 结束日期，默认为None
        threshold: 样本天数阈值，默认60天
    Returns:
        bool: 是否满足高而窄的旗形形态
    """
    # 检查股票是否在龙虎榜上且有机构参与
    if code_name[0] not in settings.top_list:
        return False

    # 如果指定了结束日期，筛选出该日期之前的数据
    if end_date is not None:
        mask = (data['日期'] <= end_date)  # 创建布尔掩码
        data = data.loc[mask]  # 使用掩码筛选数据
    data = data.tail(n=threshold)  # 获取最后threshold天的数据

    # 检查数据量是否足够
    if len(data) < threshold:
        logging.debug("{0}:样本小于{1}天...\n".format(code_name, threshold))  # 使用format()方法格式化字符串
        return False

    data = data.tail(n=14)  # 获取最后14天的数据
    low = data['最低'].min()  # 计算14天内的最低价
    ratio_increase = data.iloc[-1]['最高'] / low  # 计算最高价相对最低价的涨幅比率
    # 如果涨幅比率小于1.9倍，不满足条件
    if ratio_increase < 1.9:
        return False

    previous_p_change = 0.0  # 初始化前一天涨幅
    # 检查是否有连续两天涨幅大于等于9.5%
    for _p_change in data['p_change'].values:
        if _p_change >= 9.5:  # 如果当天涨幅大于等于9.5%
            if previous_p_change >= 9.5:  # 如果前一天也大于等于9.5%
                return True  # 满足条件，返回True
            else:
                previous_p_change = _p_change  # 记录当天涨幅
        else:
            previous_p_change = 0.0  # 重置前一天涨幅

    return False  # 不满足任何条件，返回False
