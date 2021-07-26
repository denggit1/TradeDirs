# coding:utf-8

import os
import time
import pymysql
import logging
from pathlib import Path
import sys
sys.path.append('/root/TradeDirs/exchange_service/')
import BinanceDMService


class CloseProcess(object):
    def __init__(self, api_name):
        self.pwd = "Mysql_123"
        self.api_name = api_name
        self.user = self.api_name.split("_")[0]
        self.order_count = 10
        self.pos_count = 10
        # dm
        self.key_tuple = self.get_access_secret(self.api_name)
        self.trade_obj = BinanceDMService.BinanceDm(self.key_tuple[0], self.key_tuple[1], "https://fapi.binance.com")
        # LOG
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
                            filename="/root/TradeDirs/freq/{}/logs/{}.log".format(self.user, "stop"))
        self.logger = logging.getLogger()

    """ 组件模块 """

    # 获取密钥
    def get_access_secret(self, user_name):
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db='trade')
        cur = conn.cursor()
        sql = 'SELECT access_key, secret_key, pass_phrase FROM `key_table` where user_name = %s;'
        cur.execute(sql, user_name)
        key_tuple = cur.fetchone()
        conn.commit()
        conn.close()
        return key_tuple

    def monitor_weight(self):
        # self.logger.info(self.trade_obj.weight)
        # 如果 weight > 1500 ，时间等待至下一分钟
        if self.trade_obj.weight > 1000:
            sleep_time = int(time.time()) // 60 * 60 + 60 - time.time()
            if sleep_time > 0.0:
                time.sleep(sleep_time)

    """ 撤单模块 """

    def get_open(self, dm):
        # 强制获取挂单 40
        for i in range(self.order_count):
            try:
                all_open = dm.get_open_orders("")
                self.monitor_weight()
                self.logger.info("{} 挂单获取 {}".format(self.api_name, i))
                return all_open
            except: pass
            time.sleep(3)
        return []

    def delete_order(self, all_open, dm):
        # 构建 50
        temp_symbol = set()
        for open in all_open: temp_symbol.add(open["symbol"])
        # 撤单
        for each in temp_symbol:
            try:
                dm.delete_all_order(each)
                self.monitor_weight()
            except: pass

    def delete_all_order(self):
        # 撤单直到没有挂单为止 130
        all_open = [{'symbol': 'BTCUSDT'}]
        while all_open != []:
            all_open = self.get_open(self.trade_obj)
            if all_open == []: break
            self.delete_order(all_open, self.trade_obj)
            time.sleep(3)

    """ 平仓模块 """

    def get_pos(self, dm):
        # 强制获取持仓 5
        position_list = []
        for i in range(self.pos_count):
            try:
                position_list = dm.get_position()
                self.monitor_weight()
                self.logger.info("{} 持仓获取 {}".format(self.api_name, i))
                break
            except: pass
            time.sleep(3)
        # 处理float
        all_pos = []
        for position in position_list:
            num = float(position['positionAmt'])
            if num != 0.0:
                if int(num) == num: num = int(num)
                position['positionAmt'] = num
                all_pos.append(position)
        return all_pos

    def delete_pos(self, all_pos, dm):
        # 平仓 float 50
        for position in all_pos:
            if position['positionAmt'] > 0.0:
                try:
                    dm.post_market_order(position["symbol"], "SELL", str(abs(position['positionAmt'])),
                                         "m_{}".format(int(time.time() * 1000)), reduce_only="true")
                    self.monitor_weight()
                except: pass
            elif position['positionAmt'] < 0.0:
                try:
                    dm.post_market_order(position["symbol"], "BUY", str(abs(position['positionAmt'])),
                                         "m_{}".format(int(time.time() * 1000)), reduce_only="true")
                    self.monitor_weight()
                except: pass

    def delete_all_pos(self):
        # 下单直到没有持单为止 60
        all_pos = [{'symbol': 'BTCUSDT'}]
        while all_pos != []:
            all_pos = self.get_pos(self.trade_obj)
            if all_pos == []: break
            self.delete_pos(all_pos, self.trade_obj)
            time.sleep(3)

    """ 进程模块 """

    def kill_process(self):
        os.popen("ps -ef|grep " + self.user + "_freq.py|awk '{print $2}'|xargs kill -9")
        os.popen("ps -ef|grep " + self.user + "_ws.py|awk '{print $2}'|xargs kill -9")
        time.sleep(1)

    """ 主模块 """

    # kill -> delete_all_order -> delete_all_pos
    def main(self):
        self.logger.info("{} 正在执行 STOP".format(self.api_name))
        self.kill_process()
        self.delete_all_order()
        self.delete_all_pos()
        self.logger.info("{} 执行完成 STOP".format(self.api_name))


if __name__ == '__main__':
    name = Path(__file__).name
    user = name.split("_")[0]
    user_name = "{}_bian_api".format(user)
    cp = CloseProcess(user_name)
    cp.main()

