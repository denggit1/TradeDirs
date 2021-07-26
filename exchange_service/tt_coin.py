# coding:utf-8
# @author: D

import time
import pymysql
import logging
import traceback
import redis
from threading import Thread, Lock
from pathlib import Path
import sys
sys.path.append('/root/TradeDirs/exchange_service/')
import HuobiUDMService


class TaTrade(object):
    # 初始化
    def __init__(self, user_coin, quantity=30.0, acc="b6f67606-ntmuw4rrs3", sec=""):
        # 内置参数
        user, coin = user_coin.split("_")
        pair_list = coin.split("-")
        pair = pair_list[0]
        self.api_name = "{}_huobi_api".format(user)
        self.trade_code = "{}-USDT".format(pair.upper())
        # 仓位15U，间隔
        self.quantity = quantity
        self.rate_list = [0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2, 0.225, 0.25]
        # 比率，状态列表，各列表
        self.index = 0
        self.status_list = []
        self.up_price_list, self.up_num_list, self.dn_price_list, self.dn_num_list = [], [], [], []
        # 交易对象
        # key_tuple = self.get_access_secret(self.api_name)
        self.host = "https://api.hbdm.com"
        self.trade_obj = HuobiUDMService.HbUServer(self.host, acc, sec)
        # 日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
                            filename="/root/TradeDirs/logs/{}.log".format(user_coin))
        self.logger = logging.getLogger()
        # 停止时间，价格精度，数量精度，仓位精度
        self.sleep = 3
        self.price_precis, self.contract_size = self.get_tick_len()
        self.num_precis = 0
        self.quantity = self.quantity / self.contract_size
        # init
        self.init_trade()

    """ 数据库查询函数 """

    # 低于20 限频处理
    def look_limit(self, limit=30):
        ratelimit = int(self.trade_obj.rate_limit_dict.get("ratelimit-remaining", 0))
        if ratelimit < limit:
            self.logger.info("限频处理：{}".format(ratelimit))
            time.sleep(self.sleep)
        return None

    # 获取精度
    def get_tick_len(self):
        tick_len, contract_size = "", 0
        while tick_len == "":
            try:
                tick_list = self.trade_obj.get_swap_contract_info(self.trade_code)['data']
                self.look_limit()
                for each in tick_list:
                    if each.get('contract_code', "") == self.trade_code:
                        tick_len = len(str(float(each["price_tick"])).split(".")[1])
                        contract_size = float(each["contract_size"])
                print(tick_len, contract_size)
            except: tick_len = ""
            time.sleep(self.sleep)
        self.logger.info("读取精度：{} and {}".format(tick_len, contract_size))
        return tick_len, contract_size

    # 获取tick价格
    def get_tick(self):
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        tick_price = r.get(self.trade_code)
        return float(tick_price)

    """ 查询订单状态 """

    # 查询当前状态
    def get_this_status(self, client_id):
        data_dict = {}
        while data_dict == {}:
            try:
                data_dict = self.trade_obj.post_this_order(self.trade_code, client_id)
                self.look_limit()
                data_dict = data_dict.get("data", [{"trade_volume": 0.0}])[0]
            except: data_dict = {}
            time.sleep(self.sleep)
        trade_status = data_dict.get("status", "")
        return trade_status

    # 线程查询状态
    def get_trade_status(self, client_id, status_list, lock):
        data_dict = {}
        while data_dict == {}:
            try:
                data_dict = self.trade_obj.post_this_order(self.trade_code, client_id)
                self.look_limit()
                data_dict = data_dict.get("data", [{"trade_volume": 0.0}])[0]
                # print(data_dict)
            except: data_dict = {}
            time.sleep(self.sleep)
        trade_status = data_dict.get("status", "")
        # 线程锁
        lock.acquire()
        status_list.append([client_id, trade_status])
        lock.release()

    # 获取状态列表 - (1准备提交 2准备提交 3已提交 4部分成交 5部分成交已撤单 6全部成交 7已撤单 11撤单中)
    def get_status_list(self):
        status_list, lock, thread_result = [], Lock(), []
        for each in self.status_list:
            thread_result.append(Thread(target=self.get_trade_status, args=(each[0], status_list, lock)))
        for t in thread_result: t.start()
        for t in thread_result: t.join()
        return status_list

    """ 获取上下行价格与仓位 """

    # 获取 up_price_list, up_num_list, dn_price_list, dn_num_list
    def get_close_up_dn_list(self, price):
        rate_list = self.rate_list
        start_price = price
        up_price_list = [start_price]
        up_num_list = [0.0]
        dn_price_list = [start_price]
        dn_num_list = [0.0]
        for i in range(len(rate_list)):
            up_price = round(start_price * (1.0 + rate_list[i]), self.price_precis)
            up_num = round(pow(2, i) * self.quantity / up_price, self.num_precis)
            up_price_list.append(up_price)
            up_num_list.append(up_num)
            dn_price = round(start_price * (1.0 - rate_list[i]), self.price_precis)
            dn_num = round(pow(2, i) * self.quantity / dn_price, self.num_precis)
            dn_price_list.append(dn_price)
            dn_num_list.append(dn_num)
        self.logger.info("平仓重置：({} {}) ({} {})".format(up_price_list, up_num_list, dn_price_list, dn_num_list))
        return up_price_list, up_num_list, dn_price_list, dn_num_list

    # 获取 up_price_list, up_num_list, dn_price_list, dn_num_list
    def get_buy_up_dn_list(self, price):
        rate_list = self.rate_list
        start_price = round(price / (1.0 - rate_list[0]), self.price_precis)
        up_price_list = [start_price]
        up_num_list = [0.0]
        dn_price_list = [start_price]
        dn_num_list = [0.0]
        for i in range(len(rate_list)):
            up_price = round(start_price * (1.0 + rate_list[i]), self.price_precis)
            up_num = round(pow(2, i) * self.quantity / up_price, self.num_precis)
            up_price_list.append(up_price)
            up_num_list.append(up_num)
            dn_price = round(start_price * (1.0 - rate_list[i]), self.price_precis)
            dn_num = round(pow(2, i) * self.quantity / dn_price, self.num_precis)
            dn_price_list.append(dn_price)
            dn_num_list.append(dn_num)
        self.logger.info("买入重置：({} {}) ({} {})".format(up_price_list, up_num_list, dn_price_list, dn_num_list))
        return up_price_list, up_num_list, dn_price_list, dn_num_list

    # 获取 up_price_list, up_num_list, dn_price_list, dn_num_list
    def get_sell_up_dn_list(self, price):
        rate_list = self.rate_list
        start_price = round(price / (1.0 + rate_list[0]), self.price_precis)
        up_price_list = [start_price]
        up_num_list = [0.0]
        dn_price_list = [start_price]
        dn_num_list = [0.0]
        for i in range(len(rate_list)):
            up_price = round(start_price * (1.0 + rate_list[i]), self.price_precis)
            up_num = round(pow(2, i) * self.quantity / up_price, self.num_precis)
            up_price_list.append(up_price)
            up_num_list.append(up_num)
            dn_price = round(start_price * (1.0 - rate_list[i]), self.price_precis)
            dn_num = round(pow(2, i) * self.quantity / dn_price, self.num_precis)
            dn_price_list.append(dn_price)
            dn_num_list.append(dn_num)
        self.logger.info("卖入重置：({} {}) ({} {})".format(up_price_list, up_num_list, dn_price_list, dn_num_list))
        return up_price_list, up_num_list, dn_price_list, dn_num_list

    """ 订单操作函数 """

    # 处理多余订单 - 市价交易单
    def market_trade(self, offset, side, quantity, client_id):
        # 下单阶段
        data_dict = {}
        while data_dict == {}:
            try:
                data_dict = self.trade_obj.post_send_order(self.trade_code, offset, side, int(quantity), client_id)
                self.look_limit()
            except: data_dict = {}
            time.sleep(self.sleep)
        self.logger.info("市价订单：{} {} {} {}".format(offset, side, quantity, client_id))
        return None

    # 挂单
    def market_limit(self, offset, side, price, quantity, client_id):
        data_dict = {}
        while data_dict == {}:
            try:
                data_dict = self.trade_obj.post_send_order(self.trade_code, offset, side, int(quantity), client_id,
                                                           order_price_type="limit", price=price)
                self.look_limit()
                # print(data_dict)
            except: data_dict = {}
            time.sleep(self.sleep)
        self.logger.info("限价挂单：{} {} {} {} {}".format(offset, side, price, quantity, client_id))
        return None

    # 止损止盈计划单
    def market_stop(self, side, price, quantity, win_price):
        data_dict = {}
        while data_dict == {}:
            try:
                data_dict = self.trade_obj.post_win_los_order(self.trade_code, side, int(quantity), price, win_price)
                self.look_limit()
            except: data_dict = {}
            time.sleep(self.sleep)
        status = data_dict.get("status", "")
        if status != "ok":
            self.market_trade("close", side, quantity, "{}".format(int(time.time() * 1000)))
        self.logger.info("计划止损：{} {} {}".format(side, quantity, price))
        return None

    # 撤销所有挂单
    def clear_all_orders(self):
        # 撤销指令
        data_dict = {}
        while data_dict == {}:
            try:
                data_dict = self.trade_obj.post_cancel_all_order(self.trade_code)
                self.look_limit()
            except: data_dict = {}
            time.sleep(self.sleep)
        return None

    # 撤销单个挂单 - ok
    def clear_one_orders(self, client_id):
        # 撤销指令
        data_dict = {}
        while data_dict == {}:
            try:
                data_dict = self.trade_obj.post_cancel_order(self.trade_code, client_id)
                self.look_limit()
                # print("撤销指令", data_dict)
            except:
                data_dict = {}
            time.sleep(self.sleep)
        self.logger.info("撤销订单：{}".format(client_id))
        # 查询误成交数量
        executed_qty, side, offset = data_dict.get("trade_volume", ""), data_dict.get("direction", ""), \
                                     data_dict.get("offset", "")
        # print("误成交数量", executed_qty, side, offset)
        while executed_qty == "":
            try:
                select_dict = self.trade_obj.post_this_order(self.trade_code, client_id)
                self.look_limit()
                select_dict = select_dict.get("data", [{"trade_volume": 0.0}])[0]
                executed_qty, side, offset = select_dict.get("trade_volume", ""),\
                                             select_dict.get("direction", ""), select_dict.get("offset", "")
            except:
                executed_qty = ""
            time.sleep(self.sleep)
        self.logger.info("错误订单：{} {} {}".format(executed_qty, side, offset))
        # print("查询接口", executed_qty, side, offset)
        # 清除多余单
        if float(executed_qty) != 0.0:
            if side == "buy":
                if offset == "open":
                    self.market_trade("close", "sell", executed_qty, "{}".format(int(time.time() * 1000)))
                elif offset == "close":
                    self.market_trade("open", "sell", executed_qty, "{}".format(int(time.time() * 1000)))
            elif side == "sell":
                if offset == "open":
                    self.market_trade("close", "buy", executed_qty, "{}".format(int(time.time() * 1000)))
                elif offset == "close":
                    self.market_trade("open", "buy", executed_qty, "{}".format(int(time.time() * 1000)))
        return None

    # 多线程下单
    def thread_orders(self, up_price, up_num, up_id, dn_price, dn_num, dn_id):
        # 多线程下单
        thread_result = [
            Thread(target=self.market_limit, args=("open", "sell", up_price, up_num, up_id)),
            Thread(target=self.market_limit, args=("open", "buy", dn_price, dn_num, dn_id)),
        ]
        for t in thread_result: t.start()
        for t in thread_result: t.join()

    """ 策略逻辑 """

    # 初始化 - 返回上行CID与下行CID
    def init_trade(self):
        self.logger.info("初始化中：。。。")
        # 索引重置 读取上下索引价格 unix
        unix_time = int(time.time() * 1000)
        self.index = 0
        tick_price = self.get_tick()
        self.up_price_list, self.up_num_list, \
        self.dn_price_list, self.dn_num_list = self.get_close_up_dn_list(tick_price)
        # 价格为索引价格；开仓数量为 索引倍数；2 sell；价格为索引价格；开仓数量为 索引倍数；1 buy
        up_price = self.up_price_list[1]
        up_num = self.up_num_list[1]
        up_id = "2{}".format(unix_time)
        dn_price = self.dn_price_list[1]
        dn_num = self.dn_num_list[1]
        dn_id = "1{}".format(unix_time)
        # 多线程下单
        self.thread_orders(up_price, up_num, up_id, dn_price, dn_num, dn_id)
        self.status_list = [[up_id], [dn_id]]

    # 查询双CID是否成交
    def main(self):
        self.status_list = self.get_status_list()
        # 第一个订单成交，撤销第二个订单，反之则
        if self.status_list[0][1] == 6 or self.status_list[1][1] == 6:
            if self.status_list[0][1] == 6:
                this_id = self.status_list[0][0]
                delete_id = self.status_list[1][0]
                self.clear_one_orders(delete_id)
            else:
                this_id = self.status_list[1][0]
                delete_id = self.status_list[0][0]
                self.clear_one_orders(delete_id)
            # unix
            unix_time = int(time.time() * 1000)
            # open sell 成交
            if this_id[0] == "2":
                # 若之前是开多的，那么是平仓单成交
                if self.index < 0:
                    old_filled_price = self.dn_price_list[abs(self.index) - 1]
                    self.up_price_list, self.up_num_list, \
                    self.dn_price_list, self.dn_num_list = self.get_sell_up_dn_list(old_filled_price)
                    self.index = 1
                    self.logger.info("平多成空：{} index#{}".format(this_id, self.index))
                # 反之是加仓单成交
                else:
                    # 撤销平空单
                    self.clear_one_orders("3{}".format(delete_id[1:]))
                    self.index += 1
                    self.logger.info("开空成交：{} index#{}".format(this_id, self.index))
                # 平仓单
                cl_price = self.up_price_list[abs(self.index) - 1]
                cl_num = round(sum(self.up_num_list[:abs(self.index) + 1]), self.num_precis)
                cl_id = "3{}".format(unix_time)
                # 开仓单
                dn_price = cl_price
                dn_num = round(self.quantity / dn_price, self.num_precis)
                dn_id = "1{}".format(unix_time)
                # 加仓单
                if abs(self.index) + 1 < len(self.up_price_list):
                    up_price = self.up_price_list[abs(self.index) + 1]
                    up_num = self.up_num_list[abs(self.index) + 1]
                    up_id = "2{}".format(unix_time)
                    # 平仓单挂单
                    self.market_limit("close", "buy", cl_price, cl_num, cl_id)
                # 止损单
                else:
                    up_price, up_num, up_id = "0", "0", "9{}".format(unix_time)
                    # 止损止盈挂单
                    stop_price = round(self.up_price_list[-1] * (1.0 + self.rate_list[0]), self.price_precis)
                    self.market_stop("buy", stop_price, cl_num, cl_price)
                    while True: time.sleep(3600)
                # 多线程下单
                self.thread_orders(up_price, up_num, up_id, dn_price, dn_num, dn_id)
                self.status_list = [[up_id], [dn_id]]
            # open buy 成交
            elif this_id[0] == "1":
                # 若之前是开空的，那么是平仓单成交
                if self.index > 0:
                    old_filled_price = self.up_price_list[abs(self.index) - 1]
                    self.up_price_list, self.up_num_list, \
                    self.dn_price_list, self.dn_num_list = self.get_buy_up_dn_list(old_filled_price)
                    self.index = -1
                    self.logger.info("平空成多：{} index#{}".format(this_id, self.index))
                # 反之是加仓单成交
                else:
                    # 撤销平多单
                    self.clear_one_orders("4{}".format(delete_id[1:]))
                    self.index -= 1
                    self.logger.info("开多成交：{} index#{}".format(this_id, self.index))
                # 平仓单
                cl_price = self.dn_price_list[abs(self.index) - 1]
                cl_num = round(sum(self.dn_num_list[:abs(self.index) + 1]), self.num_precis)
                cl_id = "4{}".format(unix_time)
                # 开仓单
                up_price = cl_price
                up_num = round(self.quantity / up_price, self.num_precis)
                up_id = "2{}".format(unix_time)
                # 加仓单
                if abs(self.index) + 1 < len(self.dn_price_list):
                    dn_price = self.dn_price_list[abs(self.index) + 1]
                    dn_num = self.dn_num_list[abs(self.index) + 1]
                    dn_id = "1{}".format(unix_time)
                    # 平仓单挂单
                    self.market_limit("close", "sell", cl_price, cl_num, cl_id)
                # 止损单
                else:
                    dn_price, dn_num, dn_id = "0", "0", "9{}".format(unix_time)
                    # 止损止盈订单
                    stop_price = round(self.dn_price_list[-1] * (1.0 - self.rate_list[0]), self.price_precis)
                    self.market_stop("sell", stop_price, cl_num, cl_price)
                    while True: time.sleep(3600)
                # 多线程下单
                self.thread_orders(up_price, up_num, up_id, dn_price, dn_num, dn_id)
                self.status_list = [[up_id], [dn_id]]
        return None

    # 运行函数
    def run(self):
        while True:
            try:
                self.main()
            except Exception as e:
                error = traceback.format_exc()
                error = error.replace(" ", "").replace("\n", " ")
                logging.info("出现异常：{}".format(error))
            time.sleep(self.sleep)


if __name__ == '__main__':
    name = Path(__file__).name
    user_coin = name.split(".")[0]
    t = TaTrade(user_coin)
    t.run()

