# -*- encoding: UTF-8 -*-

import data_fetcher
import settings
import strategy.enter as enter
from strategy import turtle_trade, climax_limitdown
from strategy import backtrace_ma250
from strategy import breakthrough_platform
from strategy import parking_apron
from strategy import low_backtrace_increase
from strategy import keep_increasing
from strategy import high_tight_flag
from strategy import low_atr
import akshare as ak
import push
import logging
import time
import datetime
import os
import pandas as pd


def prepare():
    logging.info("************************ process start ***************************************")
    print(">>> 开始执行 prepare 流程...")

    # 获取日志文件名和选股文件名
    log_filename, sel_filename = generate_log_and_sel_filenames()

    all_data = ak.stock_zh_a_spot_em()
    subset = all_data[['代码', '名称']]
    stocks = [tuple(x) for x in subset.values]
    statistics(all_data, stocks)

    strategies = {
        
        '放量上涨': enter.check_volume,
        '均线多头': keep_increasing.check,
        '停机坪': parking_apron.check,
        '回踩年线': backtrace_ma250.check,
        '突破平台': breakthrough_platform.check,
        '无大幅回撤': low_backtrace_increase.check,
        
        '海龟交易法则': turtle_trade.check_enter,
        '高而窄的旗形': high_tight_flag.check,
        '低ATR成长策略': low_atr.check_low_increase,
        '低回撤稳步上涨策略': low_backtrace_increase.check,
    }

    if datetime.datetime.now().weekday() == 0:
        strategies['均线多头'] = keep_increasing.check

    process(stocks, strategies, sel_filename)

    print(">>> prepare 流程执行完毕...")
    logging.info("************************ process   end ***************************************")

def process(stocks, strategies, sel_filename):
    stocks_data = data_fetcher.run(stocks)
    for strategy, strategy_func in strategies.items():
        print(f">>> 开始执行策略: {strategy}")
        check(stocks_data, strategy, strategy_func, sel_filename)
        time.sleep(2)

def check(stocks_data, strategy, strategy_func, sel_filename):
    end = settings.config['end_date']
    m_filter = check_enter(end_date=end, strategy_fun=strategy_func)
    results = dict(filter(m_filter, stocks_data.items()))
    print(f">>> 策略 {strategy} 筛选结果数量: {len(results)}")
    if len(results) > 0:
        push.strategy('**************"{0}"**************\n{1}\n**************"{0}"**************\n'.format(strategy, list(results.keys())))
        
        # 生成.txt文件
        selected_stocks = [(stock_name, stock_code) for stock_name, stock_code in results.keys()]
        save_to_excel(selected_stocks, sel_filename)


def check_enter(end_date=None, strategy_fun=enter.check_volume):
    """创建股票筛选过滤器函数
    Args:
        end_date: 结束日期，默认为None
        strategy_fun: 策略函数，默认为check_volume
    Returns:
        function: 返回一个过滤器函数
    """
    def end_date_filter(stock_data):
        """内部过滤器函数
        Args:
            stock_data: 包含股票代码和历史数据的元组
        Returns:
            bool: 是否满足策略条件
        """
        if end_date is not None:
            # 检查股票是否在指定日期前已上市
            if end_date < stock_data[1].iloc[0].日期:  
                # 使用logging.debug()记录调试信息
                # format()方法用于字符串格式化：
                # {}是占位符，会被format()中的参数依次替换
                # stock_data[0]是股票代码，end_date是结束日期
                logging.debug("{}在{}时还未上市".format(stock_data[0], end_date))
                return False
        # 调用策略函数检查股票是否满足条件
        return strategy_fun(stock_data[0], stock_data[1], end_date=end_date)

    return end_date_filter  # 返回过滤器函数


# 统计数据
def statistics(all_data, stocks):
    limitup = len(all_data.loc[(all_data['涨跌幅'] >= 9.5)])
    limitdown = len(all_data.loc[(all_data['涨跌幅'] <= -9.5)])

    up5 = len(all_data.loc[(all_data['涨跌幅'] >= 5)])
    down5 = len(all_data.loc[(all_data['涨跌幅'] <= -5)])

    msg = "涨停数：{}   跌停数：{}\n涨幅大于5%数：{}  跌幅大于5%数：{}".format(limitup, limitdown, up5, down5)
    push.statistics(msg)

def generate_log_and_sel_filenames():
    import os
    import datetime
    
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    
    # 修正：使用正确的logs文件夹名称
    log_filename = f"./logs/log_{date_str}_{time_str}.log"
    
    # 确保selection目录存在
    sel_dir = "./selection"
    os.makedirs(sel_dir, exist_ok=True)
    
    sel_filename = f"{sel_dir}/selection_{date_str}_{time_str}.xlsx"
    
    return log_filename, sel_filename

def save_to_excel(stocks_data, filename):
    """
    将股票数据保存为Excel文件
    
    Args:
        stocks_data: 包含股票名称和代码的列表或字典
        filename: 保存的文件名
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 准备数据，假设stocks_data是一个包含(名称, 代码)元组的列表
    new_df = pd.DataFrame(stocks_data, columns=[ '代码','名称'])
    
    # 确保股票代码不省略前导零
    # 将代码列转换为字符串类型，并确保保留前导零
    new_df['代码'] = new_df['代码'].astype(str).str.zfill(6)
    
    # 检查文件是否已存在
    if os.path.exists(filename):
        try:
            # 读取现有的Excel文件，不使用index_col参数，以读取所有列
            existing_df = pd.read_excel(filename, engine='openpyxl')
            
            # 如果现有文件中包含序号列，需要去除它
            if '序号' in existing_df.columns:
                existing_df = existing_df.drop(columns=['序号'])
            # 如果第一列没有列名，可能是索引列，尝试去除
            if existing_df.columns[0] == 'Unnamed: 0':
                existing_df = existing_df.iloc[:, 1:]
            
            # 确保现有数据的股票代码也是正确格式（有前导零）
            if '代码' in existing_df.columns:
                existing_df['代码'] = existing_df['代码'].astype(str).str.zfill(6)
            
            # 合并现有数据和新数据
            # 使用concat函数合并两个DataFrame，忽略索引
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # 去重（如果需要）- 基于名称和代码列去重
            combined_df = combined_df.drop_duplicates(subset=['名称', '代码'])
            
            # 保存合并后的数据，不使用索引列
            combined_df.to_excel(filename, index=False, engine='openpyxl')
            
            print(f"已将新的选股结果追加至: {filename}")
        except Exception as e:
            print(f"读取或更新现有文件时出错: {e}")
            # 如果出错，创建新文件
            new_df.to_excel(filename, index=False, engine='openpyxl')
            print(f"已创建新的选股结果文件: {filename}")
    else:
        # 如果文件不存在，直接创建新文件
        new_df.to_excel(filename, index=False, engine='openpyxl')
        print(f"已创建新的选股结果文件: {filename}")




