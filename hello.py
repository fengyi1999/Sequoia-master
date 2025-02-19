# 尝试获取单个股票数据
import data_fetcher
import logging

# 设置日志
#logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

# 测试获取股票数据
code_name = ('603229', '奥翔药业')
result = data_fetcher.fetch(code_name)  # 注意这里需要使用 data_fetcher.fetch
print(result)