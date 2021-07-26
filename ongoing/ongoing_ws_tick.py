# coding:utf-8
# ws

import time
import pymysql
import requests
import sys
sys.path.append('/root/TradeDirs/exchange_service/')
from binance_f.subscriptionclient import SubscriptionClient


class Websocket(object):
    # 初始化
    def __init__(self):
        self.conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd="Mysql_123", db="freq")
        self.conn_two = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd="Mysql_123", db="freq")
        # 日志
        self.log_path = "/root/TradeDirs/ongoing/logs/tick.log"

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
                self.conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd="Mysql_123", db="freq")
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
                self.conn_two = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd="Mysql_123", db="freq")
                status = True
            except:
                status = False
            time.sleep(1)

    # 追加日志
    def logger_info(self, text):
        with open(self.log_path, "a") as f:
            f.write("{} - {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), text))

    # 更新tick函数
    def update_tick(self, event):
        # 获取已有的列表
        self.run_conn_test()
        cur = self.conn.cursor()
        cur.execute("SELECT trade_code FROM `freq_param`;")
        param_tuple = cur.fetchall()
        param_list = [p[0] for p in param_tuple]
        # 数据更新
        for item in event:
            if item.symbol in param_list:
                cur.execute("UPDATE `freq_param` SET ticker_dfp=%s where trade_code=%s;", [item.close, item.symbol])
        # self.logger_info("已更新：{}".format([item.symbol for item in event]))
        # 关闭流
        self.conn.commit()
        cur.close()

    # 启动网络套接字回调函数
    def tick_callback(self, data_type, event):
        if data_type == "payload":
            if event[0].eventType == "24hrMiniTicker":
                self.update_tick(event)
            else:
                pass
        else:
            pass

    # 网页获取
    def get_tick_data(self):
        host_url = "https://fapi.binance.com"
        url = host_url + "/fapi/v1/ticker/price"
        headers = {
            'Connection': 'close',
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
        }
        response = requests.get(url=url, headers=headers, timeout=3)
        weight = int(response.headers.get("X-MBX-USED-WEIGHT-1M", "0"))
        data = response.json()
        self.run_conn_two_test()
        cur = self.conn_two.cursor()
        # 数据更新
        for item in data:
            if item["symbol"] in ["BTCUSDT", 'ETHUSDT', 'BCHUSDT', 'XRPUSDT', 'EOSUSDT', 'LTCUSDT', 'TRXUSDT', 'ETCUSDT', 'LINKUSDT', 'XLMUSDT', 'ADAUSDT', 'XMRUSDT', 'DASHUSDT', 'ZECUSDT', 'XTZUSDT', 'BNBUSDT', 'ATOMUSDT', 'ONTUSDT', 'IOTAUSDT', 'BATUSDT', 'VETUSDT', 'NEOUSDT', 'QTUMUSDT', 'IOSTUSDT', 'THETAUSDT', 'ALGOUSDT', 'ZILUSDT', 'KNCUSDT', 'ZRXUSDT', 'COMPUSDT', 'OMGUSDT', 'DOGEUSDT', 'SXPUSDT', 'KAVAUSDT', 'BANDUSDT', 'RLCUSDT', 'WAVESUSDT', 'MKRUSDT', 'SNXUSDT', 'DOTUSDT', 'DEFIUSDT', 'YFIUSDT', 'BALUSDT', 'CRVUSDT', 'TRBUSDT', 'YFIIUSDT', 'RUNEUSDT', 'SUSHIUSDT', 'SRMUSDT', 'BZRXUSDT', 'EGLDUSDT', 'SOLUSDT', 'ICXUSDT', 'STORJUSDT', 'BLZUSDT', 'UNIUSDT', 'AVAXUSDT', 'FTMUSDT', 'HNTUSDT', 'ENJUSDT', 'FLMUSDT', 'TOMOUSDT', 'RENUSDT', 'KSMUSDT', 'NEARUSDT', 'AAVEUSDT', 'FILUSDT', 'RSRUSDT', 'LRCUSDT', 'MATICUSDT', 'OCEANUSDT', 'CVCUSDT', 'BELUSDT', 'CTKUSDT', 'AXSUSDT', 'ALPHAUSDT', 'ZENUSDT', 'SKLUSDT', 'GRTUSDT', '1INCHUSDT', 'BTCBUSD', 'AKROUSDT', 'CHZUSDT', 'SANDUSDT', 'ANKRUSDT', 'LUNAUSDT', 'BTSUSDT', 'LITUSDT', 'UNFIUSDT', 'DODOUSDT', 'REEFUSDT', 'RVNUSDT', 'SFPUSDT', 'XEMUSDT', 'COTIUSDT', 'CHRUSDT', 'MANAUSDT', 'ALICEUSDT', 'HBARUSDT', 'ONEUSDT', 'LINAUSDT', 'STMXUSDT', 'DENTUSDT', 'CELRUSDT', 'HOTUSDT', 'MTLUSDT', 'OGNUSDT', 'BTTUSDT', 'NKNUSDT', 'SCUSDT', 'DGBUSDT', '1000SHIBUSDT', 'ICPUSDT']:
                cur.execute("UPDATE `freq_param` SET ticker_dfp=%s where trade_code=%s;",
                            [item["price"], item["symbol"]])
        self.conn_two.commit()
        cur.close()
        # 限频处理
        if weight > 1000:
            sleep_time = int(time.time()) // 60 * 60 + 60 - time.time()
            if sleep_time > 0.0:
                time.sleep(sleep_time)

    # 启动socket
    def run_socket(self):
        self.logger_info("实时价格监测已启动！")
        sub_client = SubscriptionClient()
        sub_client.subscribe_all_miniticker_event(self.tick_callback)
        while True:
            try:
                self.get_tick_data()
            except Exception as e:
                pass
            time.sleep(6)


if __name__ == '__main__':
    ws = Websocket()
    ws.run_socket()

