# coding:utf-8
# @date: 2020-06-02
# @author: D

import time
import uuid
import math
import hmac
import json
import hashlib
import requests
import urllib.parse
from requests.auth import AuthBase


# 错误信息
class AuthenticationError(Exception):
    pass


# request请求附带accessToken
class AccessTokenAuth(AuthBase):
    def __init__(self, accessToken):
        self.token = accessToken

    def __call__(self, r):
        if (self.token):
            r.headers['access-token'] = self.token
        return r


# 密钥加密传输
class APIKeyAuthWithExpires(AuthBase):
    def __init__(self, apiKey, apiSecret):
        self.apiKey = apiKey
        self.apiSecret = apiSecret

    def __call__(self, r):
        expires = int(round(time.time()) + 5)
        r.headers['api-expires'] = str(expires)
        r.headers['api-key'] = self.apiKey
        r.headers['api-signature'] = self.generate_signature(self.apiSecret, r.method, r.url, expires, r.body or '')
        return r

    def generate_signature(self, secret, verb, url, nonce, data):
        parsedURL = urllib.parse.urlparse(url)
        path = parsedURL.path
        if parsedURL.query:
            path = path + '?' + parsedURL.query
        message = verb + path + str(nonce) + data
        signature = hmac.new(bytes(secret, 'utf8'), bytes(message, 'utf8'), digestmod=hashlib.sha256).hexdigest()
        return signature


# BitMEX对象
class BitMEX(object):
    # 初始化
    def __init__(self, apiKey=None, apiSecret=None, base_url=None):
        """ https://www.bitmex.com/api/v1/ """
        self.base_url = base_url
        self.token = None
        self.apiKey = apiKey
        self.apiSecret = apiSecret

    """ init end | request start """

    # GET请求 ok
    def _curl_get(self, path, query=None, timeout=3):
        url = self.base_url + path
        auth = AccessTokenAuth(self.token)
        if self.apiKey:
            auth = APIKeyAuthWithExpires(self.apiKey, self.apiSecret)
        try:
            res = requests.get(url=url, auth=auth, params=query, timeout=timeout).json()
        except Exception as e:
            res = None
        return res

    # POST请求
    def _curl_post(self, path, postdict=None, timeout=3):
        url = self.base_url + path
        auth = AccessTokenAuth(self.token)
        if self.apiKey:
            auth = APIKeyAuthWithExpires(self.apiKey, self.apiSecret)
        try:
            res = requests.post(url=url, auth=auth, data=postdict, timeout=timeout).json()
        except Exception as e:
            res = None
        return res

    # DELETE请求
    def _curl_delete(self, path, postdict=None, timeout=3):
        url = self.base_url + path
        auth = AccessTokenAuth(self.token)
        if self.apiKey:
            auth = APIKeyAuthWithExpires(self.apiKey, self.apiSecret)
        try:
            res = requests.delete(url=url, auth=auth, data=postdict, timeout=timeout).json()
        except Exception as e:
            res = None
        return res

    """ request end | kline start """

    # 获取K线
    def get_kline(self, symbol, count, k="1m"):
        path = "trade/bucketed"
        query = {
            "binSize": k,
            "symbol": symbol,
            "reverse": "true",
            "count": count,
        }
        return self._curl_get(path=path, query=query)

    # 获取行情 ok
    def get_instrument(self, symbol):
        path = "instrument"
        instruments = self._curl_get(path=path, query={'filter': json.dumps({'symbol': symbol})})
        if len(instruments) == 0:
            print("Instrument not found: %s." % symbol)
            exit(1)
        instrument = instruments[0]
        if instrument["state"] != "Open":
            print("The instrument %s is no longer open. State: %s" % (symbol, instrument["state"]))
            exit(1)
        instrument['tickLog'] = int(math.fabs(math.log10(instrument['tickSize'])))
        return instrument

    # 行情价格 ok
    def ticker_data(self, symbol):
        data = self.get_instrument(symbol)
        ticker = {
            "last": data['lastPrice'],
            "buy": data['bidPrice'],
            "sell": data['askPrice'],
            "mid": (float(data['bidPrice']) + float(data['askPrice'])) / 2
        }
        return ticker

    # 行情订单 ok
    def recent_trades(self):
        path = "trade"
        return self._curl_get(path=path)

    # 行情深度 not ok
    def market_depth(self, symbol):
        path = "orderBook/L2"
        return self._curl_get(path=path, query={'symbol': symbol, "size": 0})

    # 买卖盘价 not ok
    def snapshot(self, symbol):
        order_book = self.market_depth(symbol)
        return {
            'bid': order_book[0]['bidPrice'],
            'ask': order_book[0]['askPrice'],
            'size_bid': order_book[0]['bidSize'],
            'size_ask': order_book[0]['askSize']
        }

    """ kline end | user start """

    # 查询余额
    def funds(self):
        return self._curl_get(path="user/margin")

    # 推送订单
    def place_order(self, symbol, quantity, price, clOrdID):
        endpoint = "order"
        postdict = {
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'clOrdID': clOrdID
        }
        return self._curl_post(path=endpoint, postdict=postdict)

    # 获取挂单
    def open_orders(self, symbol):
        path = "order"
        filter_dict = {'ordStatus.isTerminated': False}
        if symbol:
            filter_dict['symbol'] = symbol
        orders = self._curl_get(path=path, query={'filter': json.dumps(filter_dict)})
        return orders

    # 撤销订单
    def cancel(self, clOrdID):
        path = "order"
        postdict = {'clOrdID': clOrdID}
        return self._curl_delete(path=path, postdict=postdict)

    # 市价单
    def post_market_order(self, symbol, side, quantity, clOrdID, ordType="Market"):
        quantity = -abs(float(quantity)) if side == "SELL" else abs(float(quantity))
        endpoint = "order"
        postdict = {
            'symbol': symbol,
            'quantity': quantity,
            'clOrdID': clOrdID,
            'ordType': ordType,
        }
        return self._curl_post(path=endpoint, postdict=postdict)

    # 止损单
    def post_stop_market_order(self, symbol, side, stopPx, quantity, clOrdID, ordType="Stop"):
        quantity = -abs(float(quantity)) if side == "SELL" else abs(float(quantity))
        endpoint = "order"
        postdict = {
            'symbol': symbol,
            'quantity': quantity,
            'stopPx': stopPx,
            'clOrdID': clOrdID,
            'ordType': ordType,
            "execInst": "LastPrice",
        }
        return self._curl_post(path=endpoint, postdict=postdict)

    # 限价单
    def post_limit_order(self, symbol, side, price, quantity, clOrdID):
        quantity = -abs(float(quantity)) if side == "SELL" else abs(float(quantity))
        return self.place_order(symbol, quantity, price, clOrdID)

    # 撤销订单 ok
    def delete_order(self, symbol, clOrdID):
        code = symbol
        res = self.cancel(clOrdID)
        try:
            res_dict = res[0]
        except:
            res_dict = {"clOrdID": clOrdID}
        return res_dict

    # 获取所有挂单 ok
    def get_open_orders(self, symbol):
        return self.open_orders(symbol)

    # 获取订单信息 ok
    def get_this_orders(self, symbol, clOrdID):
        path = "order"
        filter_dict = {'clOrdID': clOrdID}
        if symbol:
            filter_dict['symbol'] = symbol
        orders = self._curl_get(path=path, query={'filter': json.dumps(filter_dict)})
        order_dict = {} if orders == [] else orders[0]
        return order_dict


if __name__ == '__main__':
    bm = BitMEX(
        apiKey="yjqSFGJXac92rNkuGcj2yp", apiSecret="1tt9jxE6NiEdnN_6CrWQomS_xTPGyw8PXF1z65ipK_8V_7",
        base_url="https://testnet.bitmex.com/api/v1/",
    )
    res = bm.delete_order("XBTUSD", "bitmex_8")
    print(res, len(res))

