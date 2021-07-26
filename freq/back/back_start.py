# coding:utf-8

import os
import time
import logging
import pymysql
from pathlib import Path


class StartProcess(object):
    def __init__(self, api_name):
        self.api_name = api_name
        self.user = self.api_name.split("_")[0]
        # 参数
        self.process_list = ["ws", "freq"]
        # LOG
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
                            filename="/root/TradeDirs/freq/{}/logs/{}.log".format(self.user, "start"))
        self.logger = logging.getLogger()

    def init_table(self):
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd="Mysql_123")
        # freq
        conn.select_db("freq")
        # 查询预设参数
        cur = conn.cursor()
        cur.execute('select trade_usdt, strategy from web_pos where user_name = %s;', self.api_name)
        temp = cur.fetchone()
        conn.commit()
        cur.close()
        trade_usd, trade_type = temp
        table_num_usd = int(round(0.024 * float(trade_usd), 0))
        # start
        cur = conn.cursor()
        # 清除参数
        sql = 'delete from freq_param where api_name = %s;'
        # 插入参数
        insert_sql = 'insert into freq_param (api_name , trade_name, trade_code, ticker_dfp, trade_num_usd) ' \
                     '(select %s, trade_name, trade_code, ticker_dfp, %s from freq_param wheream where api_name = %s);'
        cur.execute(sql, self.api_name)
        cur.execute(insert_sql, [self.api_name, table_num_usd, "{}_bian_api".format(trade_type)])
        conn.commit()
        cur.close()
        # user
        conn.select_db(self.user)
        cur = conn.cursor()
        # 清空表
        cur.execute("truncate freq_orders;")
        cur.execute("truncate freq_trade;")
        cur.execute("truncate ws_orders;")
        conn.commit()
        cur.close()
        conn.close()

    def main(self):
        self.logger.info("{} 正在执行 START".format(self.api_name))
        # init
        self.init_table()
        # 运行双进程
        for each in self.process_list:
            os.popen("nohup /usr/bin/python3 /root/TradeDirs/freq/{}/{}_{}.py > /dev/null 2>&1 &".format(
                self.user, self.user, each))
            time.sleep(1)
        self.logger.info("{} 执行完成 START".format(self.api_name))


if __name__ == '__main__':
    name = Path(__file__).name
    user = name.split("_")[0]
    user_name = "{}_bian_api".format(user)
    sp = StartProcess(user_name)
    sp.main()

