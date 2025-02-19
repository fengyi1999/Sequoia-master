# -*- encoding: UTF-8 -*-

import utils
import logging
import work_flow
import settings
import schedule
import time
import datetime
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry





def setup_requests_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# 在 job 函数中添加错误处理
def job():
    try:
        if utils.is_weekday():
            work_flow.prepare()
    except Exception as e:
        logging.error(f"执行任务时出错: {str(e)}")
        time.sleep(5)  # 出错后等待一段时间再重试


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    handlers=[
        logging.FileHandler("sequoia.log"),
        logging.StreamHandler()
    ]
)
logging.getLogger().setLevel(logging.INFO)
settings.init()

# 临时禁用定时任务，直接执行策略流程
# if settings.config['cron']:
#     EXEC_TIME = "15:15"
#     schedule.every().day.at(EXEC_TIME).do(job)

#     while True:
#         schedule.run_pending()
#         time.sleep(1)
#else:  # 暂时注释掉else分支
work_flow.prepare()
