# coding: utf-8
# @date: 2019-11-25
# @author: D

import re
import time
import hmac
import hashlib
import urllib.parse
import requests


class BinanceDm(object):
    def __init__(self, access_key, secret_key, api_host):
        """ 初始化 """
        self.url = api_host
        self.access_key = access_key
        self.secret_key = secret_key
        self.timeout = 3
        self.weight = 0

    """
    SIGN GET POST START
    """

    def create_sign(self, params_dict, secret_key):
        """ 生成 signature 参数 """
        signature = hmac.new(
            bytes(secret_key.encode('utf-8')),
            bytes(urllib.parse.urlencode(params_dict).encode('utf-8')),
            digestmod=hashlib.sha256
        ).hexdigest()
        return signature

    def http_get_request(self, url, params, add_to_headers=None):
        """ 处理 get 链接 """
        headers = {
            'Connection': 'close',
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
        }
        if add_to_headers:
            headers.update(add_to_headers)
        postdata = urllib.parse.urlencode(params)
        response = requests.get(url, postdata, headers=headers, timeout=self.timeout)
        self.weight = int(response.headers.get("X-MBX-USED-WEIGHT-1M", "0"))
        return response.json()

    def http_post_request(self, url, params, add_to_headers=None):
        """ api post 请求 """
        headers = {
            'Connection': 'close',
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
        }
        if add_to_headers:
            headers.update(add_to_headers)
        postdata = urllib.parse.urlencode(params)
        response = requests.post(url, postdata, headers=headers, timeout=self.timeout)
        self.weight = int(response.headers.get("X-MBX-USED-WEIGHT-1M", "0"))
        return response.json()

    """
    API START
    """

    def api_key_get(self, host_url, request_path, params_dict, access_key, secret_key):
        """ api get 请求 """
        params_dict['signature'] = self.create_sign(params_dict, secret_key)
        add_headers = {'X-MBX-APIKEY': access_key}
        url = host_url + request_path
        return self.http_get_request(url, params_dict, add_headers)

    def api_key_post(self, host_url, request_path, params_dict, access_key, secret_key):
        """ api post 请求 """
        params_dict['signature'] = self.create_sign(params_dict, secret_key)
        add_headers = {'X-MBX-APIKEY': access_key}
        url = host_url + request_path
        return self.http_post_request(url, params_dict, add_headers)

    """
    DELETE API
    """

    def api_key_delete(self, host_url, request_path, params_dict, access_key, secret_key):
        """ api delete 请求 """
        params_dict['signature'] = self.create_sign(params_dict, secret_key)
        add_headers = {'X-MBX-APIKEY': access_key}
        url = host_url + request_path
        headers = {
            'Connection': 'close',
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
        }
        headers.update(add_headers)
        postdata = urllib.parse.urlencode(params_dict)
        response = requests.delete(url, data=postdata, headers=headers, timeout=self.timeout)
        self.weight = int(response.headers.get("X-MBX-USED-WEIGHT-1M", "0"))
        return response.json()

    """
    GET API HOST 
    """

    def get_api_host(self, official_host):
        """
        获取 HOST 地址
        :param official_host: 官网
        :return: api_host
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/75.0.3770.90 Safari/537.36'
        }
        res = requests.get(url=official_host, headers=headers).text
        find = re.compile('"API_ACCELERATE_HOST_PUBLIC":"(.*?)",')
        group_url = find.search(res)
        api_host = group_url.group(1)
        return api_host

    """
    SIGN GET POST API END
    """

    def get_exchange_info(self):
        """
        查询访问限制
        :return: res
        """
        request_path = "/fapi/v1/exchangeInfo"
        params = {}
        return self.http_get_request(self.url + request_path, params)

    def get_time(self, time_type="local"):
        """
        获取服务器时间
        :return: {'serverTime': 1023456789000}    utc + 8
        """
        if time_type == "local":
            time_dict = {'serverTime': int(time.time() * 1000)}
            return time_dict
        else:
            request_path = '/fapi/v1/time'
            params_dict = {}
            return self.http_get_request(self.url + request_path, params_dict)

    def get_kline(self, symbol, interval, limit=500):
        """
        获取 K线 数据
        :param symbol: 交易对
        :param interval: 1m, 1h
        :param limit: max_1500
        :return: kline_data
        """
        request_path = '/fapi/v1/klines'
        params_dict = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        return self.http_get_request(self.url + request_path, params_dict)

    def get_account(self):
        """
        获取账户余额信息
        :return: dict{"totalWalletBalance": "总钱包", "maxWithdrawAmount": "可用余额"}
        """
        request_path = "/fapi/v2/account"
        params_dict = {
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def get_balance(self):
        """
        获取余额信息
        :return: list [{'asset': 'USDT', 'balance': '61.88038946', 'withdrawAvailable': '60.37887882']
        """
        request_path = "/fapi/v2/balance"
        params_dict = {
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def get_position(self):
        """
        获取持仓信息
        :return: list [{'symbol': 'ETHUSDT', 'positionAmt': '0.001', 'leverage': '20'}]
        """
        request_path = "/fapi/v2/positionRisk"
        params_dict = {
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def get_open_orders(self, symbol):
        """
        获取当前挂单
        :param symbol: 交易对
        :return: res
        """
        request_path = '/fapi/v1/openOrders'
        params_dict = {
            "symbol": symbol,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def post_leverage(self, symbol, leverage):
        """
        调整开仓杠杆
        :param symbol: BTCUSDT
        :param leverage: 目标杠杆倍数：1 到 125 整数
        :return: response
        """
        request_path = '/fapi/v1/leverage'
        params_dict = {
            "symbol": symbol,
            "leverage": leverage,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def post_order(self, symbol, side, quantity, order_type='MARKET'):
        """
        交易下单接口
        :param symbol: BTCUSDT
        :param side: BUY, SELL
        :param quantity: trade_num
        :param order_type: LIMIT, MARKET
        :return: response
        """
        request_path = '/fapi/v1/order'
        params_dict = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def post_market_order(self, symbol, side, quantity, client_id, reduce_only="false",
                          rake_back="x-BdQyJ3cv-", order_type='MARKET'):
        """
        交易下单接口
        :param symbol: BTCUSDT
        :param side: BUY, SELL
        :param quantity: trade_num
        :param order_type: LIMIT, MARKET
        :param reduce_only: reduce_only
        :param rake_back: reduce_only
        :param client_id: id
        :return: response
        """
        request_path = '/fapi/v1/order'
        params_dict = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "newClientOrderId": rake_back + client_id,
            "reduceOnly": reduce_only,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def post_stop_market_order(self, symbol, side, stop_price, quantity, client_id,
                               reduce_only="false", rake_back="x-BdQyJ3cv-", order_type='STOP_MARKET'):
        """
        交易下单接口
        :param symbol: BTCUSDT
        :param side: BUY, SELL
        :param stop_price: float
        :param quantity: trade_num
        :param order_type: LIMIT, MARKET
        :param reduce_only: reduce_only
        :param rake_back: reduce_only
        :param client_id: id
        :return: response
        """
        request_path = '/fapi/v1/order'
        params_dict = {
            "symbol": symbol,
            "stopPrice": stop_price,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "newClientOrderId": rake_back + client_id,
            "reduceOnly": reduce_only,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def post_stop_limit_order(self, symbol, side, stop_price, quantity, price, client_id,
                               reduce_only="false", rake_back="x-BdQyJ3cv-", order_type='STOP'):
        """
        交易下单接口
        :param symbol: BTCUSDT
        :param side: BUY, SELL
        :param stop_price: float
        :param quantity: trade_num
        :param price: price
        :param order_type: LIMIT, MARKET
        :param reduce_only: reduce_only
        :param rake_back: id
        :param client_id: id
        :return: response
        """
        request_path = '/fapi/v1/order'
        params_dict = {
            "symbol": symbol,
            "stopPrice": stop_price,
            "side": side,
            "quantity": quantity,
            "price": price,
            "type": order_type,
            "newClientOrderId": rake_back + client_id,
            "reduceOnly": reduce_only,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def post_limit_order(self, symbol, side, price, quantity, client_id,
                         reduce_only="false", rake_back="x-BdQyJ3cv-", time_in_force="GTC", order_type='LIMIT'):
        """
        交易下单接口
        :param symbol: BTCUSDT
        :param side: BUY, SELL
        :param price: float
        :param quantity: trade_num
        :param reduce_only: reduce_only
        :param time_in_force: GTC
        :param client_id: newClientOrderId
        :param rake_back: newClientOrderId
        :param order_type: LIMIT, MARKET
        :return: response
        """
        request_path = '/fapi/v1/order'
        params_dict = {
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
            "type": order_type,
            "timeInForce": time_in_force,
            "newClientOrderId": rake_back + client_id,
            "reduceOnly": reduce_only,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def post_data_id_link(self, symbol, start_time, end_time, data_type="T_TRADE"):
        request_path = '/sapi/v1/futuresHistDataId'
        params_dict = {
            "symbol": symbol,
            "startTime": start_time,
            "endTime": end_time,
            "dataType": data_type,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def get_data_id_link(self, download_id):
        request_path = '/sapi/v1/downloadLink'
        params_dict = {
            "downloadId": download_id,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def delete_order(self, symbol, this_id, rake_back="x-BdQyJ3cv-", id_type="client_id"):
        """
        撤销 order_id 订单
        :param symbol: 交易对
        :param this_id: 订单id
        :param id_type: id_type
        :param rake_back: rake_back
        :return: res
        """
        if id_type == "client_id":
            params_dict = {
                "symbol": symbol,
                "origClientOrderId": rake_back + this_id,
                "timestamp": self.get_time()['serverTime'],
            }
        else:
            params_dict = {
                "symbol": symbol,
                "orderId": this_id,
                "timestamp": self.get_time()['serverTime'],
            }
        request_path = '/fapi/v1/order'
        return self.api_key_delete(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def delete_all_order(self, symbol):
        """
        撤销 全部 订单
        :param symbol: 交易对
        :return: res
        """
        params_dict = {
            "symbol": symbol,
            "timestamp": self.get_time()['serverTime'],
        }
        request_path = '/fapi/v1/allOpenOrders'
        return self.api_key_delete(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def get_user_trades(self, symbol):
        """
        账户成交历史
        :param symbol: 交易对
        :return: res
        """
        request_path = "/fapi/v1/userTrades"
        params_dict = {
            "symbol": symbol,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def get_this_orders(self, symbol, this_id, rake_back="x-BdQyJ3cv-", id_type="client_id"):
        """
        根据id获取订单
        :param symbol: 交易对
        :param this_id: id号
        :param id_type: id类型
        :param rake_back: rake_back
        :return: res
        """
        if id_type == "client_id":
            params_dict = {
                "symbol": symbol,
                "origClientOrderId": rake_back + this_id,
                "timestamp": self.get_time()['serverTime'],
            }
        else:
            params_dict = {
                "symbol": symbol,
                "orderId": this_id,
                "timestamp": self.get_time()['serverTime'],
            }
        request_path = "/fapi/v1/order"
        return self.api_key_get(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def get_all_orders(self, symbol, startTime=""):
        """
        所有交易订单
        :param symbol: 交易对
        :return: res
        """
        request_path = "/fapi/v1/allOrders"
        params_dict = {
            "symbol": symbol,
            "limit": 1000,
            "timestamp": self.get_time()['serverTime'],
        }
        if startTime:
            params_dict["startTime"] = startTime
        return self.api_key_get(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def post_listen_key(self):
        """ post ws key """
        request_path = "/fapi/v1/listenKey"
        params_dict = {
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post(self.url, request_path, params_dict, self.access_key, self.secret_key)

    def delete_listen_key(self):
        """ delete ws key """
        params_dict = {
            "timestamp": self.get_time()['serverTime'],
        }
        request_path = '/fapi/v1/listenKey'
        return self.api_key_delete(self.url, request_path, params_dict, self.access_key, self.secret_key)

    """
    bnBao API
    """

    # 查询产品
    def get_bao_product(self):
        request_path = '/sapi/v1/lending/daily/product/list'
        params_dict = {
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    # 查询仓位
    def get_bao_position(self, asset=""):
        request_path = '/sapi/v1/lending/daily/token/position'
        params_dict = {
            "asset": asset,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    # 查询活动仓位
    def get_act_bao_position(self, asset=""):
        request_path = '/sapi/v1/lending/project/position/list'
        params_dict = {
            "asset": asset,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    # 申购产品
    def post_bao_purchase(self, productId, amount):
        request_path = '/sapi/v1/lending/daily/purchase'
        params_dict = {
            "productId": productId,
            "amount": amount,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    # 赎回产品
    def post_bao_redeem(self, productId, amount, type='FAST'):
        request_path = '/sapi/v1/lending/daily/redeem'
        params_dict = {
            "productId": productId,
            "amount": amount,
            "type": type,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    """
    SPOT API
    """

    def get_main_transfer(self, asset, start_time, end_time, size):
        """
        现货合约主账户记录划转API
        :param asset: USDT
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param size: 100
        :return: res
        """
        request_path = '/sapi/v1/sub-account/transfer/subUserHistory'
        params_dict = {
            "asset": asset,
            "startTime": start_time,
            "endTime": end_time,
            "limit": size,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def get_all_capital(self):
        """
        查询现货资产
        :return: res
        """
        request_path = '/sapi/v1/capital/config/getall'
        params_dict = {
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def post_main_transfer(self, asset, amount):
        """
        现货合约划转给主账户API
        :param asset: USDT
        :param amount: 划转数量
        :return: res
        """
        request_path = '/sapi/v1/sub-account/transfer/subToMaster'
        params_dict = {
            "asset": asset,
            "amount": amount,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def post_sub_to_sub_transfer(self, email, asset, amount):
        """
        子账号划转给子账号API
        :param email: 接收者子邮箱地址
        :param asset: USDT
        :param amount: 划转数量
        :return: res
        """
        request_path = '/sapi/v1/sub-account/transfer/subToSub'
        params_dict = {
            "toEmail": email,
            "asset": asset,
            "amount": amount,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def get_transfer(self, asset, start_time, end_time, size):
        """
        现货合约划转API
        :param asset: USDT
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param size: 100
        :return: res
        """
        request_path = '/sapi/v1/futures/transfer'
        params_dict = {
            "asset": asset,
            "startTime": start_time,
            "endTime": end_time,
            "size": size,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def post_transfer(self, asset, amount, one_two_type):
        """
        现货合约划转API
        :param asset: USDT
        :param amount: 划转数量
        :param one_two_type: 1、现货到合约，2、合约到现货
        :return: res
        """
        request_path = '/sapi/v1/futures/transfer'
        params_dict = {
            "asset": asset,
            "amount": amount,
            "type": one_two_type,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def get_spot_balances(self):
        """
        现货资产接口
        :return: res
        """
        request_path = '/api/v3/account'
        params_dict = {
            "timestamp": self.get_time()['serverTime'],
        }
        res = self.api_key_get("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)
        balances = res["balances"]
        balance_list = []
        for balance in balances:
            if balance["asset"] in ["BNB", "USDT", "DOT", "ADA", "BTC", "ETH", "ZEC", "XRP", "LINK", "BCH", "LTC", "ETC"]:
                balance_list.append(balance)
        return balance_list

    def post_spot_market(self, symbol, side, quantity, client_id, rake_back="x-RCJK2W6S-", order_type='MARKET'):
        """
        交易下单接口
        :param symbol: BTCUSDT
        :param side: BUY, SELL
        :param quantity: trade_num
        :param order_type: LIMIT, MARKET
        :param rake_back: x-PA4YH7ET-
        :param client_id: id
        :return: response
        """
        request_path = '/api/v3/order'
        params_dict = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "newClientOrderId": rake_back + client_id,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post("https://api.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    """ DAPI """

    def get_dapi_account(self):
        """
        获取账户余额信息
        :return: dict{"totalWalletBalance": "总钱包", "maxWithdrawAmount": "可用余额"}
        """
        request_path = "/dapi/v1/account"
        params_dict = {
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def get_dapi_position(self):
        """
        获取持仓信息
        :return: list [{'symbol': 'ETHUSDT', 'positionAmt': '0.001', 'leverage': '20'}]
        """
        request_path = "/dapi/v1/positionRisk"
        params_dict = {
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def get_dapi_all_orders(self, symbol, limit=100):
        """
        所有交易订单
        :param symbol: 交易对
        :param limit: limit
        :return: res
        """
        request_path = "/dapi/v1/allOrders"
        params_dict = {
            "symbol": symbol,
            "limit": limit,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def get_dapi_open_orders(self, symbol):
        """
        获取当前挂单
        :param symbol: 交易对
        :return: res
        """
        request_path = '/dapi/v1/openOrders'
        params_dict = {
            "symbol": symbol,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_get("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def get_dapi_this_orders(self, symbol, this_id, rake_back="x-BdQyJ3cv-", id_type="client_id"):
        """
        根据id获取订单
        :param symbol: 交易对
        :param this_id: id号
        :param id_type: id类型
        :param rake_back: rake_back
        :return: res
        """
        if id_type == "client_id":
            params_dict = {
                "symbol": symbol,
                "origClientOrderId": rake_back + this_id,
                "timestamp": self.get_time()['serverTime'],
            }
        else:
            params_dict = {
                "symbol": symbol,
                "orderId": this_id,
                "timestamp": self.get_time()['serverTime'],
            }
        request_path = "/dapi/v1/order"
        return self.api_key_get("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def post_dapi_stop_limit_order(self, symbol, side, stop_price, quantity, price, client_id,
                                   reduce_only="false", rake_back="x-BdQyJ3cv-", order_type='STOP'):
        """
        交易下单接口
        :param symbol: BTCUSDT
        :param side: BUY, SELL
        :param stop_price: float
        :param quantity: trade_num
        :param price: price
        :param order_type: LIMIT, MARKET
        :param reduce_only: reduce_only
        :param rake_back: reduce_only
        :param client_id: id
        :return: response
        """
        request_path = '/dapi/v1/order'
        params_dict = {
            "symbol": symbol,
            "stopPrice": stop_price,
            "side": side,
            "quantity": quantity,
            "price": price,
            "type": order_type,
            "newClientOrderId": rake_back + client_id,
            "reduceOnly": reduce_only,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def post_dapi_limit_order(self, symbol, side, price, quantity, client_id,
                              reduce_only="false", rake_back="x-BdQyJ3cv-", time_in_force="GTC", order_type='LIMIT'):
        """
        交易下单接口
        :param symbol: BTCUSDT
        :param side: BUY, SELL
        :param price: float
        :param quantity: trade_num
        :param reduce_only: reduce_only
        :param time_in_force: GTC
        :param rake_back: GTC
        :param client_id: newClientOrderId
        :param order_type: LIMIT, MARKET
        :return: response
        """
        request_path = '/dapi/v1/order'
        params_dict = {
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
            "type": order_type,
            "timeInForce": time_in_force,
            "newClientOrderId": rake_back + client_id,
            "reduceOnly": reduce_only,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    # 撤销单
    def delete_dapi_one_order(self, symbol, this_id, rake_back="x-BdQyJ3cv-", id_type="client_id"):
        if id_type == "client_id":
            params_dict = {
                "symbol": symbol,
                "origClientOrderId": rake_back + this_id,
                "timestamp": self.get_time()['serverTime'],
            }
        else:
            params_dict = {
                "symbol": symbol,
                "orderId": this_id,
                "timestamp": self.get_time()['serverTime'],
            }
        request_path = '/dapi/v1/order'
        return self.api_key_delete("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def delete_dapi_all_order(self, symbol):
        """
        撤销 全部 订单
        :param symbol: 交易对
        :return: res
        """
        params_dict = {
            "symbol": symbol,
            "timestamp": self.get_time()['serverTime'],
        }
        request_path = '/dapi/v1/allOpenOrders'
        return self.api_key_delete("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def post_dapi_market_order(self, symbol, side, quantity, client_id, reduce_only="false",
                               rake_back="x-BdQyJ3cv-", order_type='MARKET'):
        """
        交易下单接口
        :param symbol: BTCUSDT
        :param side: BUY, SELL
        :param quantity: trade_num
        :param order_type: LIMIT, MARKET
        :param reduce_only: reduce_only
        :param rake_back: reduce_only
        :param client_id: id
        :return: response
        """
        request_path = '/dapi/v1/order'
        params_dict = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "newClientOrderId": rake_back + client_id,
            "reduceOnly": reduce_only,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    def post_dapi_stop_market_order(self, symbol, side, stop_price, quantity, client_id,
                                    reduce_only="false", rake_back="x-BdQyJ3cv-", order_type='STOP_MARKET'):
        """
        交易下单接口
        :param symbol: BTCUSDT
        :param side: BUY, SELL
        :param stop_price: float
        :param quantity: trade_num
        :param order_type: LIMIT, MARKET
        :param reduce_only: reduce_only
        :param rake_back: reduce_only
        :param client_id: id
        :return: response
        """
        request_path = '/dapi/v1/order'
        params_dict = {
            "symbol": symbol,
            "stopPrice": stop_price,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "newClientOrderId": rake_back + client_id,
            "reduceOnly": reduce_only,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post("https://dapi.binance.com", request_path, params_dict, self.access_key, self.secret_key)

    """ TICK API """

    # 获取 tick
    def get_tick_price(self, symbol):
        request_path = "/fapi/v1/ticker/price"
        params_dict = {
            "symbol": symbol,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.http_get_request(self.url + request_path, params_dict)

    # 获取 tick
    def get_spot_tick_price(self):
        request_path = "/api/v3/ticker/price"
        params_dict = {
        }
        return self.http_get_request("https://api.binance.com" + request_path, params_dict)

    # 获取 tick
    def get_dapi_tick_price(self, symbol):
        request_path = "/dapi/v1/ticker/price"
        params_dict = {
            "symbol": symbol,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.http_get_request("https://dapi.binance.com" + request_path, params_dict)

    def post_position_side(self, dualSidePosition="false"):
        """
        :param symbol: BTCUSDT
        :return: response
        """
        request_path = '/fapi/v1/positionSide/dual'
        params_dict = {
            "dualSidePosition": dualSidePosition,
            "timestamp": self.get_time()['serverTime'],
        }
        return self.api_key_post(self.url, request_path, params_dict, self.access_key, self.secret_key)


def test():
    bm = BinanceDm("5d0A9VogYA6j56nKXUU2O9Ob",
                   "PmOdV912yFRKFMLsYNMGe8ilqHy393aY0YXdc",
                   "https://fapi.binance.com")
    # print(bm.post_bao_purchase("BUSD001", 1))
    time.sleep(3)
    print(bm.get_bao_position())
    return None

