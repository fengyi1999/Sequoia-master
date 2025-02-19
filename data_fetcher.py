# -*- encoding: UTF-8 -*-  # 声明文件编码为UTF-8

# 导入必要的库
import akshare as ak  # 导入akshare库，用于获取股票数据
import logging  # 导入logging库，用于日志记录
import talib as tl  # 导入talib库，用于技术分析指标计算

import concurrent.futures  # 导入并发处理库，用于多线程执行


def fetch(code_name):
    """获取单个股票的历史数据
    Args:
        code_name: 包含股票代码和名称的元组
    Returns:
        处理后的股票数据DataFrame
    """
    stock = code_name[0]  # 从元组中获取股票代码
    # 使用akshare获取股票历史数据，包括参数：股票代码、日期频率、开始日期、复权方式
    data = ak.stock_zh_a_hist(symbol=stock, period="daily", start_date="20240201",adjust="qfq")

    # 如果没有获取到数据，记录日志并返回None
    if data is None or data.empty:
        logging.debug("股票："+stock+" 没有数据，略过...")  # 使用logging.debug()记录调试信息
        return

    # 计算股票的日涨跌幅，使用talib的ROC（变动率指标）函数
    data['p_change'] = tl.ROC(data['收盘'], 1)

    return data  # 返回处理后的数据


def run(stocks):
    """并发获取多个股票的历史数据
    Args:
        stocks: 股票代码和名称的元组列表
    Returns:
        包含所有股票数据的字典
    """
    stocks_data = {}  # 初始化存储所有股票数据的字典
    # 创建线程池，最大工作线程数为8
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        # 为每个股票创建一个future对象，key为future，value为股票信息
        future_to_stock = {executor.submit(fetch, stock): stock for stock in stocks}
        # 当future完成时获取结果
        for future in concurrent.futures.as_completed(future_to_stock):
            stock = future_to_stock[future]  # 获取当前处理的股票信息
            try:
                data = future.result()  # 获取future的执行结果
                if data is not None:
                    # 将成交量列转换为double类型
                    data = data.astype({'成交量': 'double'})
                    stocks_data[stock] = data  # 将数据存入字典
            except Exception as exc:
                # 如果发生异常，打印错误信息
                # 使用%s和%r格式化字符串：%s为字符串，%r为对象的字符串表示
                print('%s(%r) generated an exception: %s' % (stock[1], stock[0], exc))

    return stocks_data  # 返回所有股票数据字典
