# coding:utf-8

import pymysql
import time
import sys
sys.path.append('/root/TradeDirs/exchange_service/')
import BinanceDMService


class Cap(object):
    def __init__(self, user_name):
        self.user_name = user_name + '_bian_api'
        self.pwd = 'Mysql_123'

    def select_balance(self):
        """ 1、查询 """
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db='trade')
        cur = conn.cursor()
        sql = "SELECT * FROM `key_balance` where user_name=%s and this_time>=%s;"
        ts = time.strftime('%Y%m%d')
        cur.execute(sql, [self.user_name, ts])
        data = cur.fetchone()
        conn.close()
        # 转换bool
        if data == None:
            # 未接收今日mb
            bool_val = False
        else:
            # 已接收今日mb
            bool_val = True
        return bool_val

    def get_access_secret(self, user_name):
        """ 查询秘钥（access_key, secret_key, pass_phrase） """
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db='trade')
        cur = conn.cursor()
        sql = 'SELECT access_key, secret_key, pass_phrase FROM `key_table` where user_name = %s;'
        cur.execute(sql, user_name)
        key_tuple = cur.fetchone()
        conn.close()
        return key_tuple

    def get_mb_ts(self):
        """ 2、获取 balance and ts """
        keys = self.get_access_secret(self.user_name)
        key_obj = BinanceDMService.BinanceDm(keys[0], keys[1], "https://fapi.binance.com/")
        res = key_obj.get_account().get("assets", [])
        mb = None
        ts = None
        for r in res:
            if r["asset"] == "USDT":
                mb = r["marginBalance"]
                ts = time.time()
        mb = round(float(mb), 3)
        ts = time.strftime('%Y%m%d', time.localtime(float(ts)))
        return mb, ts

    def insert_balance(self, mb, ts):
        """ 3、插入 """
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db='trade')
        cur = conn.cursor()
        sql = "INSERT INTO `key_balance` (user_name, balance, this_time) VALUE (%s,%s,%s);"
        cur.execute(sql, [self.user_name, mb, ts])
        conn.commit()
        conn.close()

    def run(self):
        """ 4、执行程序 """
        bool_val = self.select_balance()
        # 未接收时运行
        if bool_val == False:
            mb, ts = self.get_mb_ts()
            self.insert_balance(mb, ts)
        else:
            pass


def main():
    """ 多用户更新 """
    user_list = ['ft', "tt"]
    for i in range(3):
        for user in user_list:
            cp = Cap(user)
            try:
                cp.run()
            except Exception as e:
                pass
            time.sleep(1)


if __name__ == '__main__':
    main()

