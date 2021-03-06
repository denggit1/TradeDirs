# coding:utf-8
# @author:D

import time
import pymysql
import json
import logging
import traceback
import numpy as np
import sys
sys.path.append('/root/TradeDirs/exchange_service/')
import BinanceDMService


class HighFreqWeb(object):
    """
    高频交易网页执行端
    """
    # 初始化
    def __init__(self, api_name="***_bian_api", trade_name="freq***", code="***USDT", user_conn=None):
        # 设定
        self.pwd = "Mysql_123"
        self.db = "freq"
        self.api_name = api_name
        self.trade_name = trade_name
        self.code = code
        self.user_db = self.api_name.split("_")[0]
        self.max_count = 7
        self.rake_back = "x-BdQyJ3cv-"
        self.error = None
        # 交易对象
        self.offset = True
        key_tuple = self.get_access_secret(self.api_name)
        self.trade_obj = BinanceDMService.BinanceDm(key_tuple[0], key_tuple[1], "https://fapi.binance.com/")
        # conn
        self.user_conn = user_conn
        # on_init
        self.on_init()

    # init
    def on_init(self):
        # 设置杠杆
        try:
            self.trade_obj.post_leverage(self.code, 20)
            self.monitor_weight()
            time.sleep(1)
        except: pass

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

    # 查询秘钥
    def get_access_secret(self, user_name):
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db='trade')
        cur = conn.cursor()
        sql = 'SELECT access_key, secret_key, pass_phrase FROM `key_table` where user_name = %s;'
        cur.execute(sql, user_name)
        key_tuple = cur.fetchone()
        conn.close()
        return key_tuple

    # 获取需要上传的订单
    def get_upload_orders(self):
        sql = "SELECT handle, trade_code, side, price, quantity, client_id FROM `freq_orders` where " \
              "api_name=%s and trade_name=%s and trade_code=%s and web_status='0';"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.trade_name, self.code])
        upload_orders = cur.fetchall()
        self.user_conn.commit()
        cur.close()
        return upload_orders

    # 获取需要监测的ID
    def get_client_id_list(self):
        sql = "SELECT client_id FROM `freq_orders` where " \
              "api_name=%s and trade_name=%s and trade_code=%s and finish_status='0' and handle='limit_order';"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.trade_name, self.code])
        client_id_tuple = cur.fetchall()
        self.user_conn.commit()
        cur.close()
        client_id_list = []
        for c in client_id_tuple:
            client_id_list.append(c[0])
        return client_id_list

    # 更新 上传状态
    def update_web_status(self, client_id):
        sql = "update `freq_orders` set web_status='1' where " \
              "api_name=%s and trade_name=%s and trade_code=%s and client_id=%s;"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.trade_name, self.code, client_id])
        self.user_conn.commit()
        cur.close()

    # 更新 交易状态
    def update_trade_status(self, client_id):
        sql = "update `freq_orders` set trade_status='FILLED' where " \
              "api_name=%s and trade_name=%s and trade_code=%s and client_id=%s;"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.trade_name, self.code, client_id])
        self.user_conn.commit()
        cur.close()

    # 更新 完成状态
    def update_finish_status(self, client_id):
        sql = "update `freq_orders` set finish_status='1' where " \
              "api_name=%s and trade_name=%s and trade_code=%s and client_id=%s;"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.trade_name, self.code, client_id])
        self.user_conn.commit()
        cur.close()

    # 获取中索引
    def get_mid_index(self):
        sql = "SELECT mid_index, trade_arr, up_id, down_id, sum_num FROM `freq_trade` where " \
              "api_name=%s and trade_name=%s and trade_code=%s;"
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.trade_name, self.code])
        temp = cur.fetchone()
        mid_index = int(temp[0])
        trade_arr = np.array(json.loads(temp[1]))
        up_id = temp[2]
        dn_id = temp[3]
        sum_num = abs(float(temp[4]))
        self.user_conn.commit()
        cur.close()
        return mid_index, trade_arr, up_id, dn_id, sum_num

    # 获取tick价格
    def get_tick_price(self):
        sql = "SELECT ticker_dfp FROM `freq_param` where api_name=%s and trade_name=%s and trade_code=%s;"
        self.run_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.trade_name, self.code])
        tick_price = float(cur.fetchone()[0])
        self.user_conn.commit()
        cur.close()
        return tick_price

    """ MYSQL END | API START """

    # 查询状态
    def select_status(self, client_id):
        sql = 'select orderStatus, cumulativeFilledQty, side from ws_orders where ' \
              'user_name=%s and symbol=%s and clientOrderId=%s order by eventTime desc, id desc;'
        self.run_user_conn_test()
        cur = self.user_conn.cursor()
        cur.execute(sql, [self.api_name, self.code, self.rake_back + client_id])
        temp = cur.fetchone()
        self.user_conn.commit()
        cur.close()
        if temp == None:
            status_exeQty = None
        else:
            status_exeQty = temp
        return status_exeQty

    # 查询订单
    def return_data_dict(self, client_id):
        status_exeQty = self.select_status(client_id)
        if status_exeQty != None:
            data_dict = {"clientOrderId": client_id, "status": status_exeQty[0],
                         "executedQty": status_exeQty[1], "side": status_exeQty[2]}
        else:
            data_dict = {}
        return data_dict

    # 下单函数
    def post_order(self, symbol, side, price, quantity, client_id):
        data_dict = {}
        while "clientOrderId" not in data_dict.keys():
            try:
                data_dict = self.trade_obj.post_limit_order(
                    symbol, side, price, quantity, client_id, rake_back=self.rake_back)
                self.monitor_weight()
                if data_dict.get("code", "") == -4015:
                    break
            except Exception as e:
                pass
            time.sleep(1)
            if "clientOrderId" in data_dict.keys():
                break
            # 查询订单
            data_dict = self.return_data_dict(client_id)
        self.update_web_status(client_id)

    # 处理余单
    def handling_excess_orders(self, order_dict, executed_qty):
        if order_dict["side"] == "SELL":
            # 市价买入多余单
            client_m_id = "market_{}".format(str(int(time.time() * 1000)))
            data_dict = {}
            while "clientOrderId" not in data_dict.keys():
                try:
                    data_dict = self.trade_obj.post_market_order(
                        self.code, "BUY", executed_qty, client_m_id, "true", rake_back=self.rake_back)
                    self.monitor_weight()
                except Exception as e:
                    pass
                time.sleep(1)
                if "clientOrderId" in data_dict.keys():
                    break
                # 查询订单
                data_dict = self.return_data_dict(client_m_id)
        elif order_dict["side"] == "BUY":
            # 市价卖出多余单
            client_m_id = "market{}".format(str(int(time.time() * 1000)))
            data_dict = {}
            while "clientOrderId" not in data_dict.keys():
                try:
                    data_dict = self.trade_obj.post_market_order(
                        self.code, "SELL", executed_qty, client_m_id, "true", rake_back=self.rake_back)
                    self.monitor_weight()
                except Exception as e:
                    pass
                time.sleep(1)
                if "clientOrderId" in data_dict.keys():
                    break
                # 查询订单
                data_dict = self.return_data_dict(client_m_id)

    # 撤单函数
    def del_order(self, client_id):
        order_dict = {"status": "NEW"}
        # 撤销订单 and FILLED
        while (order_dict.get("status", "") != "CANCELED") and (order_dict.get("status", "") != "FILLED"):
            try:
                order_dict = self.trade_obj.delete_order(self.code, client_id, rake_back=self.rake_back)
                self.monitor_weight()
                if order_dict.get("code", "") == -2011:
                    break
            except Exception as e:
                pass
            time.sleep(1)
            # canceled
            if order_dict == "CANCELED" or order_dict == "FILLED":
                break
            # order_dict
            order_dict = self.return_data_dict(client_id)
            # code: -2011
            if order_dict == {}:
                break
        # 处理余单
        if "executedQty" in order_dict.keys():
            executed_qty = str(order_dict["executedQty"])
            if executed_qty != "0":
                self.handling_excess_orders(order_dict, executed_qty)
        # 更新数据库
        self.update_web_status(client_id)
        self.update_finish_status(client_id)

    # 获取交易状态
    def get_trade_status(self, client_id):
        try:
            trade_status = self.return_data_dict(client_id).get("status", "")
        except Exception as e:
            trade_status = ""
        return trade_status

    # 监测成交
    def monitor_client_id(self):
        client_id_tuple = self.get_client_id_list()
        for client_id in client_id_tuple:
            trade_status = self.get_trade_status(client_id)
            if trade_status == "FILLED":
                self.update_trade_status(client_id)
                self.update_finish_status(client_id)

    # 插入止损单
    # def insert_error_order(self, user_name, trade_status, trade_type, trade_num):
    #     """ 插入订单 """
    #     self.run_conn_test()
    #     cur = self.conn.cursor()
    #     sql = "insert into `email_orders` (strategy, trade_status, trade_type, trade_num, his_time, " \
    #           "email_status, surplus) value (%s, %s, %s, %s, %s, 'no', 'yes');"
    #     cur.execute(sql, [user_name, trade_status, trade_type, trade_num, time.strftime('%Y%m%d%H%M%S')])
    #     self.conn.commit()
    #     cur.close()

    """ API END | RUN START """

    def trade_main(self, direction):
        # 查询未上传订单
        upload_orders = self.get_upload_orders()
        # 上传订单 and 更新状态
        if direction == "ALL":
            for order in upload_orders:
                if order[0] == "limit_order":
                    self.post_order(order[1], order[2], order[3], order[4], order[5])
                elif order[0] == "del_order":
                    self.del_order(order[5])
        else:
            for order in upload_orders:
                if order[0] == "limit_order":
                    if order[2] == direction:
                        self.post_order(order[1], order[2], order[3], order[4], order[5])
                    else:
                        self.update_web_status(order[5])
                        self.update_finish_status(order[5])
                elif order[0] == "del_order":
                    self.del_order(order[5])
        # 监测成交
        self.monitor_client_id()

    def main(self):
        # 查询档位
        mid_index, trade_arr, up_id, dn_id, sum_num = self.get_mid_index()
        if mid_index >= (15 + self.max_count):
            self.trade_main("BUY")
            # # 监测上上行档位止损
            # stop_price = float(trade_arr[27][0])
            # tick_price = self.get_tick_price()
            # if tick_price > stop_price:
            #     # 撤销订单
            #     order_dict = {"status": "NEW"}
            #     while (order_dict.get("status", "") != "CANCELED") and (order_dict.get("status", "") != "FILLED"):
            #         try:
            #             order_dict = self.trade_obj.delete_order(self.code, dn_id, rake_back="")
            #             if order_dict.get("code", "") == -2011:
            #                 break
            #         except Exception as e:
            #             pass
            #         time.sleep(1)
            #         # canceled
            #         if order_dict == "CANCELED" or order_dict == "FILLED":
            #             break
            #         # order_dict
            #         order_dict = self.return_data_dict(dn_id)
            #         # code: -2011
            #         if order_dict == {}:
            #             break
            #     # 处理余单
            #     if "executedQty" in order_dict.keys():
            #         executed_qty = str(order_dict["executedQty"])
            #         if executed_qty != "0":
            #             self.handling_excess_orders(order_dict, executed_qty)
            #     # 市价订单
            #     client_m_id = "market_{}".format(str(int(time.time() * 1000)))
            #     data_dict = {}
            #     while "clientOrderId" not in data_dict.keys():
            #         try:
            #             data_dict = self.trade_obj.post_market_order(self.code, "BUY", sum_num, client_m_id, "true", rake_back="")
            #         except Exception as e:
            #             pass
            #         time.sleep(1)
            #         if "clientOrderId" in data_dict.keys():
            #             break
            #         # 查询订单
            #         data_dict = self.return_data_dict(client_m_id)
            #     # self.insert_error_order(self.api_name, "stop", "buy", sum_num)
            #     self.offset = False
        elif mid_index <= (15 - self.max_count):
            self.trade_main("SELL")
            # # 监测下下行档位止损
            # stop_price = float(trade_arr[3][0])
            # tick_price = self.get_tick_price()
            # if tick_price < stop_price:
            #     # 撤销订单
            #     order_dict = {"status": "NEW"}
            #     while (order_dict.get("status", "") != "CANCELED") and (order_dict.get("status", "") != "FILLED"):
            #         try:
            #             order_dict = self.trade_obj.delete_order(self.code, up_id, rake_back="")
            #             if order_dict.get("code", "") == -2011:
            #                 break
            #         except Exception as e:
            #             pass
            #         time.sleep(1)
            #         # canceled
            #         if order_dict == "CANCELED" or order_dict == "FILLED":
            #             break
            #         # order_dict
            #         order_dict = self.return_data_dict(up_id)
            #         # code: -2011
            #         if order_dict == {}:
            #             break
            #     # 处理余单
            #     if "executedQty" in order_dict.keys():
            #         executed_qty = str(order_dict["executedQty"])
            #         if executed_qty != "0":
            #             self.handling_excess_orders(order_dict, executed_qty)
            #     # 市价订单
            #     client_m_id = "market_{}".format(str(int(time.time() * 1000)))
            #     data_dict = {}
            #     while "clientOrderId" not in data_dict.keys():
            #         try:
            #             data_dict = self.trade_obj.post_market_order(self.code, "SELL", sum_num, client_m_id, "true", rake_back="")
            #         except Exception as e:
            #             pass
            #         time.sleep(1)
            #         if "clientOrderId" in data_dict.keys():
            #             break
            #         # 查询订单
            #         data_dict = self.return_data_dict(client_m_id)
            #     # self.insert_error_order(self.api_name, "stop", "sell", sum_num)
            #     self.offset = False
        else:
            self.trade_main("ALL")

    def monitor_weight(self):
        # 如果 weight > 800 ，时间等待至下一分钟
        if self.trade_obj.weight > 1000:
            sleep_time = int(time.time()) // 60 * 60 + 60 - time.time()
            if sleep_time > 0.0:
                time.sleep(sleep_time)

    def run(self):
        while self.offset:
            try:
                self.main()
            except Exception as e:
                error = traceback.format_exc()
                error = error.replace(" ", "").replace("\n", " ")
                if error != self.error:
                    logging.info("{} WEB: {}".format(self.code, error))
                    self.error = error
            time.sleep(2)


if __name__ == '__main__':
    hfw = HighFreqWeb()
    hfw.run()

