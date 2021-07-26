# coding:utf-8

import os
import time
import pymysql
import logging
import sys
sys.path.append('/root/TradeDirs/exchange_service/')
import BinanceDMService


class UpdateHouse(object):
    def __init__(self):
        self.pwd = 'Mysql_123'
        # conn
        self.conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db="trade")
        self.conn_freq = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db="freq")
        # 日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
                            filename="/root/TradeDirs/ongoing/logs/info.log")
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

    # 获取status=1
    def get_status_user(self):
        self.run_conn_freq()
        cur = self.conn_freq.cursor()
        cur.execute("select user_name from web_pos where syn_offset=1;")
        temp_list = cur.fetchall()
        self.conn_freq.commit()
        cur.close()
        user_list = [t[0] for t in temp_list]
        return user_list

    # 获取用户信息
    def get_all_info(self, user_list):
        self.run_conn_trade()
        cur = self.conn.cursor()
        cur.execute("select user_name, access_key, secret_key, pass_phrase, stime from key_table where "
                    "user_name in %s;", (user_list, ))
        temp_list = cur.fetchall()
        self.conn.commit()
        cur.close()
        return temp_list

    # 更新用户信息
    def update_pp_st(self, user_name, pass_phrase, stime):
        self.run_conn_trade()
        cur = self.conn.cursor()
        cur.execute("update key_table set pass_phrase=%s, stime=%s where "
                    "user_name = %s;", [pass_phrase, stime, user_name])
        self.conn.commit()
        cur.close()
        return None

    # 获取 marginBalance, positionInitialMargin
    def get_balance(self, trade_obj):
        balance = {}
        while balance == {}:
            try:
                balance = trade_obj.get_account()
                break
            except: balance = {}
            time.sleep(3)
        # 处理
        marginBalance = None
        positionInitialMargin = None
        for b in balance["assets"]:
            if b["asset"] == "USDT":
                marginBalance = float(b["marginBalance"])
                positionInitialMargin = float(b["positionInitialMargin"])
                break
        return round(marginBalance, 3), round(positionInitialMargin, 3)

    def run(self):
        user = self.get_status_user()
        info = self.get_all_info(user)
        for each in info:
            trade_obj = BinanceDMService.BinanceDm(each[1], each[2], "https://fapi.binance.com")
            marginBalance, positionInitialMargin = self.get_balance(trade_obj)
            self.update_pp_st(each[0], marginBalance, positionInitialMargin)
            # self.logger.info("更新数据：{} {} {}".format(each[0], marginBalance, positionInitialMargin))
            time.sleep(6)
        return None

    def start(self):
        self.logger.info("初始化")
        while True:
            try: self.run()
            except Exception as e: print(e)
            time.sleep(0.1)


if __name__ == '__main__':
    uh = UpdateHouse()
    uh.start()

