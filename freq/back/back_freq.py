# coding:utf-8
# @author:D

import time
import pymysql
import threading
import logging
from pathlib import Path
import sys
sys.path.append('/root/TradeDirs/exchange_service/')
# 引用API
from freq_db import HighFreqDb
from freq_web import HighFreqWeb


# 数据库连接
user_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd="Mysql_123")


# freq
def trade(api_name, trade_name, code, dfp, num):
    """
    运行高频交易
    :param api_name: 用户示例：quan_bian_api     str
    :param trade_name: 策略示例：freq14+         str
    :param code: 合约代码示例：XRPUSDT           str
    :param dfp: 默认初始价格示例：0.2333         str
    :param num: 交易USDT数量示例：0.1            str
    :return: None
    """
    global user_conn
    dfp, num = float(dfp), float(num)
    hd = HighFreqDb(api_name=api_name, trade_name=trade_name, code=code, dfp=dfp, num=num, user_conn=user_conn)
    hw = HighFreqWeb(api_name=api_name, trade_name=trade_name, code=code, user_conn=user_conn)
    thread_db = threading.Thread(target=hd.run)
    thread_web = threading.Thread(target=hw.run)
    thread_db.start()
    time.sleep(3)
    thread_web.start()
    thread_db.join()
    thread_web.join()
    return None


# in freq
def get_param(user_name, sql_pwd="Mysql_123", sql_db="freq"):
    """
    获取参数元组
    :param sql_pwd: pwd
    :param sql_db: db
    :return: 参数元组
    """
    sql = "SELECT api_name, trade_name, trade_code, ticker_dfp, trade_num_usd FROM `freq_param` where api_name=%s;"
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=sql_pwd, db=sql_db)
    cur = conn.cursor()
    cur.execute(sql, user_name)
    param_tuple = cur.fetchall()
    conn.commit()
    conn.close()
    return param_tuple


# 运行函数
def run(user_name):
    """
    运行函数
    :return: None
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
                        filename="/root/TradeDirs/freq/{}/logs/freq.log".format(user_name.split("_")[0]))
    logging.info("高频策略启动。。。")
    thread_result = []
    param_tuple = get_param(user_name)
    for i in range(len(param_tuple)):
        p = threading.Thread(target=trade, args=(
            param_tuple[i][0], param_tuple[i][1], param_tuple[i][2], param_tuple[i][3], param_tuple[i][4]))
        thread_result.append(p)
    for i in range(len(thread_result)):
        thread_result[i].start()
        time.sleep(1)
    while True:
        for i in range(len(thread_result)):
            if thread_result[i].isAlive() == False:
                thread_result[i] = threading.Thread(target=trade, args=(
                    param_tuple[i][0], param_tuple[i][1], param_tuple[i][2], param_tuple[i][3], param_tuple[i][4]))
                thread_result[i].start()
                time.sleep(1)
        time.sleep(3)


if __name__ == '__main__':
    name = Path(__file__).name
    user = name.split("_")[0]
    user_name = "{}_bian_api".format(user)
    run(user_name)

