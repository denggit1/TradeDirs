# coding:utf-8
# ws

import time
import pymysql
import traceback
from pathlib import Path
import sys
sys.path.append('/root/TradeDirs/exchange_service/')
import BinanceDMService
from binance_f.subscriptionclient import SubscriptionClient


class Websocket(object):
    # 初始化
    def __init__(self, user_name):
        self.pwd = "Mysql_123"
        self.user_name = user_name
        self.filled_list = []
        self.count = 0
        self.user_db = self.user_name.split("_")[0]
        # conn
        self.conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd="Mysql_123", db=self.user_db)
        self.conn_two = self.conn
        # dm
        self.key_tuple = self.get_access_secret(self.user_name)
        self.client_dm = BinanceDMService.BinanceDm(self.key_tuple[0], self.key_tuple[1], "https://fapi.binance.com")
        # 日志
        self.log_path = "/root/TradeDirs/freq/{}/logs/ws.log".format(self.user_name.split("_")[0])
        # init
        self.position_side()

    # 单向持仓
    def position_side(self):
        res = {}
        while res == {}:
            try:
                res = self.client_dm.post_position_side()
                self.monitor_weight()
            except Exception as e:
                pass
            time.sleep(2)
        return res

    # 监测限频
    def monitor_weight(self):
        # 如果 weight > 1500 ，时间等待至下一分钟
        if self.client_dm.weight > 1000:
            sleep_time = int(time.time()) // 60 * 60 + 60 - time.time()
            if sleep_time > 0.0:
                time.sleep(sleep_time)

    # 追加日志
    def logger_info(self, text):
        with open(self.log_path, "a") as f:
            f.write("{} - {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), text))

    # 测试连接
    def run_conn_test(self):
        try:
            self.conn.ping()
            status = True
        except:
            status = False
        # 无法ping通时重连直到重连成功
        while status == False:
            try:
                self.conn = pymysql.connect(
                    host='127.0.0.1', port=3306, user='root', passwd="Mysql_123", db=self.user_db)
                status = True
            except:
                status = False
            time.sleep(1)

    # 测试连接
    def run_conn_two_test(self):
        try:
            self.conn_two.ping()
            status = True
        except:
            status = False
        # 无法ping通时重连直到重连成功
        while status == False:
            try:
                self.conn_two = pymysql.connect(
                    host='127.0.0.1', port=3306, user='root', passwd="Mysql_123", db=self.user_db)
                status = True
            except:
                status = False
            time.sleep(1)

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

    # ws key
    def get_listen_key(self):
        listen_key = ""
        while listen_key == "":
            try:
                listen_key = self.client_dm.post_listen_key()["listenKey"]
                self.monitor_weight()
            except Exception as e:
                pass
            time.sleep(2)
        return listen_key

    # 侦查成交
    def detection_filled(self):
        # 1、先获取orders
        try:
            all_orders = self.client_dm.get_all_orders("")
            self.monitor_weight()
        except Exception as e:
            all_orders = []
        # 2、循环判断order
        for order_dict in all_orders:
            if order_dict.get("status", "") == "FILLED" and order_dict.get("clientOrderId", "")[11:15] == "freq" and \
                    order_dict.get("clientOrderId", "") not in self.filled_list:
                # 3、符合要求的order进行数据库查询状态
                code = order_dict.get("symbol", "")
                client_id = order_dict.get("clientOrderId", "")
                select_sql = 'select orderStatus from ws_orders where ' \
                             'user_name=%s and symbol=%s and clientOrderId=%s order by eventTime desc, id desc;'
                self.run_conn_two_test()
                cur = self.conn_two.cursor()
                cur.execute(select_sql, [self.user_name, code, client_id])
                temp = cur.fetchone()
                self.conn_two.commit()
                cur.close()
                # 4、根据检查状态进行插入数据
                status = temp if temp == None else temp[0]
                if status != "FILLED":
                    sql = "insert ignore into ws_orders (user_name, eventTime, symbol, clientOrderId, side, `type`, " \
                          "origQty, avgPrice, orderStatus, orderId, cumulativeFilledQty, no_repeat) value " \
                          "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    update_time = order_dict.get("updateTime", "")
                    order_status = order_dict.get("status", "")
                    result = [
                        self.user_name, update_time, code, client_id, order_dict.get("side", ""),
                        order_dict.get("type", ""),
                        order_dict.get("origQty", ""), order_dict.get("avgPrice", ""), order_status,
                        order_dict.get("orderId", ""), order_dict.get("executedQty", ""),
                        "{}_{}_{}_{}_{}".format(self.user_name, update_time, code, client_id, order_status)
                    ]
                    self.run_conn_two_test()
                    cur = self.conn_two.cursor()
                    cur.execute(sql, result)
                    self.conn_two.commit()
                    cur.close()
                # 5、添加已进行操作的order防止重复操作
                self.filled_list.append(order_dict.get("clientOrderId", ""))

    # 处理 冗余
    def delete_redund(self):
        # ws 冗余
        select_sql = 'select symbol, count(symbol) from ws_orders where user_name = %s group by symbol;'
        delete_sql = 'delete from ws_orders where user_name = %s and symbol = %s order by id LIMIT %s;'
        self.run_conn_two_test()
        cur = self.conn_two.cursor()
        cur.execute(select_sql, self.user_name)
        temp = cur.fetchall()
        self.conn_two.commit()
        cur.close()
        for symbol, count in temp:
            new_count = int(count) - 20
            new_count = 0 if new_count < 0 else new_count
            self.run_conn_two_test()
            cur = self.conn_two.cursor()
            cur.execute(delete_sql, [self.user_name, symbol, new_count])
            self.conn_two.commit()
            cur.close()
        # freq 冗余
        select_sql = 'select trade_code, count(trade_code) from freq_orders where api_name=%s group by trade_code;'
        delete_sql = 'delete from freq_orders where api_name=%s and trade_code=%s limit %s;'
        self.run_conn_two_test()
        cur = self.conn_two.cursor()
        cur.execute(select_sql, self.user_name)
        temp = cur.fetchall()
        self.conn_two.commit()
        cur.close()
        for symbol, count in temp:
            new_count = int(count) - 20
            new_count = 0 if new_count < 0 else new_count
            self.run_conn_two_test()
            cur = self.conn_two.cursor()
            cur.execute(delete_sql, [self.user_name, symbol, new_count])
            self.conn_two.commit()
            cur.close()

    # 处理 order
    def handle_order(self, event):
        result = [
            self.user_name, event.eventTime, event.symbol, event.clientOrderId, event.side, event.type,
            event.origQty, event.avgPrice, event.orderStatus, event.orderId, event.cumulativeFilledQty,
            "{}_{}_{}_{}_{}".format(
                self.user_name, event.eventTime, event.symbol, event.clientOrderId, event.orderStatus)
        ]
        sql = "insert ignore into ws_orders (user_name, eventTime, symbol, clientOrderId, side, `type`, " \
              "origQty, avgPrice, orderStatus, orderId, cumulativeFilledQty, no_repeat) value " \
              "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        # execute
        self.run_conn_test()
        cur = self.conn.cursor()
        cur.execute(sql, result)
        self.conn.commit()
        cur.close()

    # 启动网络套接字回调函数
    def callback(self, data_type, event):
        if data_type == "payload":
            if event.eventType == "ACCOUNT_UPDATE":
                pass
            elif event.eventType == "ORDER_TRADE_UPDATE":
                self.handle_order(event)
            else:
                pass
        else:
            pass

    # 启动socket
    def run_socket(self):
        self.logger_info("连接正在运行。。。")
        # ws key
        listen_key = self.get_listen_key()
        # bm对象
        sub_client = SubscriptionClient(api_key=self.key_tuple[0], secret_key=self.key_tuple[1])
        sub_client.subscribe_user_data_event(listen_key, self.callback)
        # 延长有效期
        while True:
            try:
                self.detection_filled()
            except Exception as e:
                error = traceback.format_exc()
                error = error.replace(" ", "").replace("\n", " ")
                self.logger_info(error)
            self.count += 1
            time.sleep(60)
            if self.count >= 30:
                try:
                    self.logger_info("进行延长连接。。。")
                    self.get_listen_key()
                    self.count = 0
                    self.delete_redund()
                except Exception as e:
                    error = traceback.format_exc()
                    error = error.replace(" ", "").replace("\n", " ")
                    self.logger_info(error)


if __name__ == '__main__':
    name = Path(__file__).name
    user = name.split("_")[0]
    user_name = "{}_bian_api".format(user)
    ws = Websocket(user_name)
    ws.run_socket()

