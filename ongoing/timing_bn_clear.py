# coding:utf-8

"""
清除历史记录
web_house web_pos key_table user
"""

import os
import time
import pymysql
import logging


class UpdateHouse(object):
    def __init__(self):
        self.pwd = 'Mysql_123'
        # conn
        self.conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db="trade")
        self.conn_freq = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db="freq")
        # 日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
                            filename="/root/TradeDirs/ongoing/logs/clear.log")
        self.logger = logging.getLogger()

    # trade
    def run_conn_trade(self):
        try:
            self.conn.ping()
            status = True
        except:
            status = False
        # 无法ping通时重连直到重连成功
        while status == False:
            try:
                self.conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db="trade")
                status = True
            except:
                status = False
            time.sleep(1)

    # freq
    def run_conn_freq(self):
        try:
            self.conn_freq.ping()
            status = True
        except:
            status = False
        # 无法ping通时重连直到重连成功
        while status == False:
            try:
                self.conn_freq = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db="freq")
                status = True
            except:
                status = False
            time.sleep(1)

    # run
    def get_user_tuple(self):
        self.run_conn_trade()
        cur = self.conn.cursor()
        sql = "select user_name from key_table where access_key in " \
              "(Select access_key From key_table Group By access_key Having Count(*) > 1) and " \
              "id not in (Select max(id) From key_table Group By access_key Having Count(*) > 1);"
        cur.execute(sql)
        temp = cur.fetchall()
        self.conn.commit()
        cur.close()
        return temp

    def run(self):
        self.logger.info("启动清理程序")
        user_tuple = self.get_user_tuple()
        temp_result = []
        for user_name_zero in user_tuple:
            user_name = user_name_zero[0]
            user = user_name.split("_")[0]
            os.popen("rm -rf /root/TradeDirs/freq/{}".format(user))
            # web_house web_pos
            self.run_conn_freq()
            cur = self.conn_freq.cursor()
            cur.execute("delete from web_house where user_name=%s;", user_name)
            cur.execute("delete from web_pos where user_name=%s;", user_name)
            self.conn_freq.commit()
            cur.close()
            # key_table user
            self.run_conn_trade()
            cur = self.conn.cursor()
            cur.execute("drop database {};".format(user))
            cur.execute("delete from key_table where user_name=%s;", user_name)
            self.conn.commit()
            cur.close()
            temp_result.append(user)
        self.conn_freq.close()
        self.conn.close()
        self.logger.info("清理程序完成 {}".format(temp_result))


if __name__ == '__main__':
    uh = UpdateHouse()
    uh.run()

