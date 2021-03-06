# coding:utf-8
# @author:D

import time
import json
import pymysql
import logging
import traceback
import numpy as np


class HighFreqDb(object):
    """
    高频交易程序
    分离至数据库
    """
    # 初始化
    def __init__(self, api_name="***_bian_api", trade_name="freq***", code="***USDT", dfp=100.0, num=0.1, user_conn=None):
        # 设定
        self.pwd = "Mysql_123"
        self.db = "freq"
        self.api_name = api_name
        self.trade_name = trade_name
        self.code = code
        self.user_db = self.api_name.split("_")[0]
        # fp, num
        self.dft_fp = dfp
        self.trade_num = num
        self.error = None
        # conn
        self.user_conn = user_conn
        # 列表、精度
        np.set_printoptions(suppress=True)
        self.hf_list = self.get_hf_list()
        self.price_precision, self.num_precision = self.get_precision()
        # mid
        self.first_price, self.trade_arr, self.mid_index,\
        self.up_id, self.down_id, self.last_order, self.sum_num = self.get_all_freq()

    # 测试连接
    def run_conn_test(self):
        try:
            self.user_conn.ping()
            self.user_conn.select_db(self.db)
            status = True
        except:
            status = False
        # 无法ping通时重连直到重连成功
        while status == False:
            try:
                self.user_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd)
                self.user_conn.select_db(self.db)
                status = True
            except:
                status = False
            time.sleep(1)

    # 测试连接
    def run_user_conn_test(self):
        try:
            self.user_conn.ping()
            self.user_conn.select_db(self.user_db)
            status = True
        except:
            status = False
        # 无法ping通时重连直到重连成功
        while status == False:
            try:
                self.user_conn = pymysql.connect(
                    host='127.0.0.1', port=3306, user='root', passwd=self.pwd)
                self.user_conn.select_db(self.user_db)
                status = True
            except:
                status = False
            time.sleep(1)

    """ INIT END | MYSQL START """

    # 扩展：输入比例，获得列表
    def get_new_list(self, rate):
        itd = []
        itm = [0.0]
        itu = []
        for i in range(1, 15 + 1):
            itu.append(round(itm[0] + rate * i, 3))
            itd.append(round(itm[0] - rate * (15 + 1 - i), 3))
        new_list = itd + itm + itu
        return new_list

    # 查询列表
    def get_hf_list(self):
        self.run_conn_test()
        cur = self.user_conn.cursor()
        cur.execute("SELECT hf_list FROM `freq_list` where freq_name=%s;", self.trade_name)
        hf_list = json.loads(cur.fetchone()[0])
        self.user_conn.commit()
        cur.close()
        return hf_list

    # 查询精度
    def get_precision(self):
        self.run_conn_test()
        cur = self.user_conn.cursor()
        cur.execute("SELECT price_precision, num_precision FROM `code_precision` where trade_code=%s;", self.code)
        precision_tuple = cur.fetchone()
        self.user_conn.commit()
        cur.close()
        price_precision = int(precision_tuple[0])
        num_precision = int(precision_tuple[1])
        return price_precision, num_precision

    # 查询所有freq
    def get_all_freq(self):
        sql = "SELECT first_price, trade_arr, mid_index, up_id, down_id, last_order, sum_num FROM `freq_trade` where " \
              "api_name=%s and trade_name=%s and trade_code=%s;"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.trade_name, self.code])
        temp = cur.fetchone()
        if temp == None:
            first_price = self.dft_fp
            trade_arr, mid_index = self.cpt_new_arr(first_price, 'mid')
            up_id = None
            down_id = None
            last_order = None
            sum_num = 0.0
            cur.execute(
                "insert into freq_trade (api_name, trade_name, trade_code, first_price, trade_arr, mid_index, sum_num) "
                "value (%s, %s, %s, %s, %s, %s, %s);", [self.api_name, self.trade_name, self.code, first_price,
                                                        json.dumps(trade_arr.tolist()), mid_index, str(sum_num)])
        else:
            first_price = float(temp[0])
            trade_arr = np.array(json.loads(temp[1]))
            mid_index = int(temp[2])
            up_id = temp[3]
            down_id = temp[4]
            last_order = temp[5]
            sum_num = float(temp[6])
        self.user_conn.commit()
        cur.close()
        return first_price, trade_arr, mid_index, up_id, down_id, last_order, sum_num

    # 更新 数组、价格初始值
    def update_arr_fp(self):
        sql = "UPDATE freq_trade SET trade_arr=%s, first_price=%s where " \
              "api_name=%s and trade_name=%s and trade_code=%s;"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [json.dumps(self.trade_arr.tolist()), self.first_price,
                          self.api_name, self.trade_name, self.code])
        self.user_conn.commit()
        cur.close()

    # 更新 中索引
    def update_mid_index(self):
        sql = "UPDATE freq_trade SET mid_index=%s where api_name=%s and trade_name=%s and trade_code=%s;"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.mid_index, self.api_name, self.trade_name, self.code])
        self.user_conn.commit()
        cur.close()

    # 更新 上、下行订单id
    def update_up_dn(self):
        sql = "UPDATE freq_trade SET up_id=%s, down_id=%s where api_name=%s and trade_name=%s and trade_code=%s;"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.up_id, self.down_id, self.api_name, self.trade_name, self.code])
        self.user_conn.commit()
        cur.close()

    # 更新 交易方向、总数量
    def update_ls_sn(self):
        sql = "UPDATE freq_trade SET last_order=%s, sum_num=%s where api_name=%s and trade_name=%s and trade_code=%s;"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.last_order, self.sum_num, self.api_name, self.trade_name, self.code])
        self.user_conn.commit()
        cur.close()

    # 插入订单
    def insert_order(self, side, price, quantity,  client_id):
        sql = "insert into `freq_orders` (api_name, trade_name, trade_code, handle, " \
              "side, price, quantity, client_id, trade_status, web_status, finish_status) VALUE " \
              "(%s, %s, %s, %s, %s, %s, %s, %s, %s, '0', '0');"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.trade_name, self.code, "limit_order",
                          side, price, quantity, client_id, "NEW"])
        self.user_conn.commit()
        cur.close()

    # 插入撤单
    def insert_del(self, client_id):
        sql = "insert into `freq_orders` (api_name, trade_name, trade_code, handle, " \
              "client_id, web_status, finish_status) VALUE (%s, %s, %s, %s, %s, '0', '0');"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.trade_name, self.code, "del_order", client_id])
        self.user_conn.commit()
        cur.close()

    # 查询交易状态
    def select_trade_status(self, client_id):
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute("SELECT trade_status FROM `freq_orders` where api_name=%s and trade_name=%s and trade_code=%s "
                    "and handle=%s and client_id=%s;", [self.api_name, self.trade_name, self.code,
                                                        "limit_order", client_id])
        trade_status = cur.fetchone()[0]
        self.user_conn.commit()
        cur.close()
        return trade_status

    """ MYSQL END | API START """

    # 生成 数组、中索引
    def cpt_new_arr(self, price, ud):
        # 默认 fs and hf
        hf_list = self.hf_list
        init_index = hf_list.index(0.0)
        if ud == 'up':
            fs_price = price / (1.0 + hf_list[init_index + 1])
        elif ud == 'down':
            fs_price = price / (1.0 + hf_list[init_index - 1])
        else:
            fs_price = price
        mid_index = init_index
        result = []
        for f in hf_list:
            result.append(round(fs_price * (1.0 + f), self.price_precision))
        mul_list = [0]
        init_num = 1
        multiply_rate = 2
        for i in range(hf_list.index(0.0)):
            mul_list.append(-init_num * pow(multiply_rate, i))
            mul_list.insert(0, init_num * pow(multiply_rate, i))
        trade_arr = np.hstack((np.array(result).reshape(-1, 1), np.array(mul_list).reshape(-1, 1)))
        return trade_arr, mid_index

    # 转换个数
    def transform_num(self, money, price):
        indivi_num = round(money / round(float(price), self.price_precision), self.num_precision)
        return indivi_num

    # 上行开空
    def up_sell(self):
        time.sleep(0.002)
        self.up_id = "{}_{}".format(self.trade_name.replace("+", ""), int(time.time() * 1000))
        price = round(float(self.trade_arr[self.mid_index + 1][0]), self.price_precision)
        money = abs(float(self.trade_arr[self.mid_index + 1][1])) * self.trade_num
        indivi_num = self.transform_num(money, price)
        self.insert_order("SELL", price, indivi_num, self.up_id)

    # 下行开多
    def down_buy(self):
        time.sleep(0.002)
        self.down_id = "{}_{}".format(self.trade_name.replace("+", ""), int(time.time() * 1000))
        price = round(float(self.trade_arr[self.mid_index - 1][0]), self.price_precision)
        money = abs(float(self.trade_arr[self.mid_index - 1][1])) * self.trade_num
        indivi_num = self.transform_num(money, price)
        self.insert_order("BUY", price, indivi_num, self.down_id)

    """ API END | TRADE START """

    # 交易函数
    def main(self):
        if self.up_id == None and self.down_id == None:
            # 下行订单
            self.down_buy()
            # 上行订单
            self.up_sell()
            # 更新挂单id
            self.update_up_dn()
        else:
            # 根据id获取状态
            up_status = self.select_trade_status(self.up_id)
            down_status = self.select_trade_status(self.down_id)
            if up_status == "FILLED":
                # 上行成交，撤销下行
                self.insert_del(self.down_id)
                self.down_id, self.up_id = "", ""
                # 此单为平仓
                if self.last_order == "BUY":
                    # 重置 价格初始值、交易数组、中索引
                    self.first_price = round(float(self.trade_arr[self.mid_index + 1][0]), self.price_precision)
                    self.trade_arr, self.mid_index = self.cpt_new_arr(self.first_price, 'up')
                    self.update_arr_fp()
                    # 计算总量并增加索引
                    indivi_num = self.transform_num(self.trade_num, self.trade_arr[self.mid_index + 1][0])
                    self.sum_num = -indivi_num
                    self.mid_index += 1
                else:
                    # 计算总量并增加索引
                    indivi_num = self.transform_num(
                        abs(float(self.trade_arr[self.mid_index + 1][1])) * self.trade_num,
                        self.trade_arr[self.mid_index + 1][0])
                    self.sum_num -= indivi_num
                    self.mid_index += 1
                # 此单为卖 并更新
                self.update_mid_index()
                self.last_order = "SELL"
                self.update_ls_sn()
                # 重开下行 平空 开多（将总数变为 +1 ）
                time.sleep(0.002)
                self.down_id = "{}_{}".format(self.trade_name.replace("+", ""), int(time.time() * 1000))
                price = round(float(self.trade_arr[self.mid_index - 1][0]), self.price_precision)
                indivi_num = self.transform_num(self.trade_num, price)
                num = round(abs(indivi_num - self.sum_num), self.num_precision)
                self.insert_order("BUY", price, num, self.down_id)
                # 重开上行 开空
                self.up_sell()
                # 更新挂单id
                self.update_up_dn()
            elif down_status == "FILLED":
                # 下行成交，撤销上行
                self.insert_del(self.up_id)
                self.down_id, self.up_id = "", ""
                # 此单为平仓
                if self.last_order == "SELL":
                    # 重置 价格初始值、交易数组、中索引
                    self.first_price = round(float(self.trade_arr[self.mid_index - 1][0]), self.price_precision)
                    self.trade_arr, self.mid_index = self.cpt_new_arr(self.first_price, 'down')
                    self.update_arr_fp()
                    # 计算总量并增加索引
                    indivi_num = self.transform_num(self.trade_num, self.trade_arr[self.mid_index - 1][0])
                    self.sum_num = indivi_num
                    self.mid_index -= 1
                else:
                    # 计算总量并增加索引
                    indivi_num = self.transform_num(
                        abs(float(self.trade_arr[self.mid_index - 1][1])) * self.trade_num,
                        self.trade_arr[self.mid_index - 1][0])
                    self.sum_num += indivi_num
                    self.mid_index -= 1
                # 此单为买 并更新
                self.update_mid_index()
                self.last_order = "BUY"
                self.update_ls_sn()
                # 重开上行 平多, 开空（将总数变为 -1 ）
                time.sleep(0.002)
                self.up_id = "{}_{}".format(self.trade_name.replace("+", ""), int(time.time() * 1000))
                price = round(float(self.trade_arr[self.mid_index + 1][0]), self.price_precision)
                indivi_num = self.transform_num(self.trade_num, price)
                num = round(abs(-indivi_num - self.sum_num), self.num_precision)
                self.insert_order("SELL", price, num, self.up_id)
                # 重开下行 开多
                self.down_buy()
                # 更新挂单id
                self.update_up_dn()
        return None

    """ TRADE END | RUN START"""

    # 运行函数
    def run(self):
        while True:
            try:
                self.main()
            except Exception as e:
                error = traceback.format_exc()
                error = error.replace(" ", "").replace("\n", " ")
                if error != self.error:
                    logging.info("{} DB: {}".format(self.code, error))
                    self.error = error
            time.sleep(1)


if __name__ == '__main__':
    hfd = HighFreqDb()
    hfd.run()

