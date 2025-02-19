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
        #'海龟交易法则': turtle_trade.check_enter,
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
        
        # 生成.sel文件
        with open(sel_filename, "a", encoding="gbk") as f:  # 追加模式
            for code in results.keys():
                f.write(code[0] + "\n")


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
    """生成日志文件名和选股文件名"""
    
    base_dir = "logs"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    today_str = datetime.date.today().strftime("%Y%m%d")
    
    # 查找当前日期已有的日志文件
    existing_logs = [f for f in os.listdir(base_dir) if f.startswith(today_str) and f.endswith(".log")]
    
    run_count = len(existing_logs) + 1
    
    log_filename = os.path.join(base_dir, f"{today_str}-{run_count}.log")
    sel_filename = os.path.join(base_dir, f"{today_str}-{run_count}.sel")
    
    return log_filename, sel_filename




