# -*- encoding: UTF-8 -*-  # 声明文件编码为UTF-8

# 导入必要的库
import akshare as ak  # 导入akshare库，用于获取股票数据
import logging  # 导入logging库，用于日志记录
import talib as tl  # 导入talib库，用于技术分析指标计算

import concurrent.futures  # 导入并发处理库，用于多线程执行


def is_target_market_stock(stock_code):
    """判断股票是否属于目标市场（沪深主板、中小板、创业板）
    
    Args:
        stock_code: 股票代码
        
    Returns:
        布尔值，True表示属于目标市场，False表示不属于
    """
    # 沪市主板：600开头、601开头、603开头、605开头
    # 深市主板：000开头
    # 中小板：002开头（已合并到深市主板，但保留板块概念）
    # 创业板：300开头、301开头
    
    # 去除股票代码中可能的前缀
    if '.' in stock_code:
        stock_code = stock_code.split('.')[0]
    
    # 判断股票代码前缀
    if (stock_code.startswith('600') or 
        stock_code.startswith('601') or 
        stock_code.startswith('603') or 
        stock_code.startswith('605') or 
        stock_code.startswith('000') or 
        stock_code.startswith('002') or 
        stock_code.startswith('300') or 
        stock_code.startswith('301')):
        return True
    
    return False


def fetch(code_name):
    """获取单个股票的历史数据
    Args:
        code_name: 包含股票代码和名称的元组
    Returns:
        处理后的股票数据DataFrame
    """
    stock = code_name[0]  # 从元组中获取股票代码
    
    # 检查股票是否属于目标市场
    if not is_target_market_stock(stock):
        logging.debug(f"股票：{stock} 不在目标市场范围内（沪深主板、中小板、创业板），略过...")
        return
    
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
