# coding:utf-8
# @Date:2019-11-06 15:00:00

import base64
import datetime
import hashlib
import hmac
import json
import time
import urllib
import urllib.parse
import urllib.request
import requests


class HbUServer(object):
    def __init__(self, URL, ACCESS_KEY, SECRET_KEY):
        # 此处填写APIKEY
        self.ACCESS_KEY = ACCESS_KEY
        self.SECRET_KEY = SECRET_KEY
        # API 请求地址 https://api.hbdm.com
        self.MARKET_URL = URL
        self.TRADE_URL = URL
        self.timeout = 5
        self.rate_limit_dict = {}

    """ Utils-Start """

    def http_get_request(self, url, params, add_to_headers=None):
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/39.0.2171.71 Safari/537.36',
        }
        if add_to_headers:
            headers.update(add_to_headers)
        postdata = urllib.parse.urlencode(params)
        response = requests.get(url, postdata, headers=headers, timeout=self.timeout)
        self.rate_limit_dict = response.headers
        try:
            if response.status_code == 200:
                return response.json()
            else:
                return
        except BaseException as e:
            print("httpGet failed, detail is:%s,%s" % (response.text, e))
            return

    def http_post_request(self, url, params, add_to_headers=None):
        headers = {
            "Accept": "application/json",
            'Content-Type': 'application/json'
        }
        if add_to_headers:
            headers.update(add_to_headers)
        postdata = json.dumps(params)
        response = requests.post(url, postdata, headers=headers, timeout=self.timeout)
        self.rate_limit_dict = response.headers
        try:
            if response.status_code == 200:
                return response.json()
            else:
                return
        except BaseException as e:
            print("httpPost failed, detail is:%s,%s" % (response.text, e))
            return

    def api_key_get(self, params, request_path, host_url=''):
        method = 'GET'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params.update({'AccessKeyId': self.ACCESS_KEY,
                       'SignatureMethod': 'HmacSHA256',
                       'SignatureVersion': '2',
                       'Timestamp': timestamp})
        if host_url == '': host_url = self.TRADE_URL
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params['Signature'] = self.create_sign(params, method, host_name, request_path, self.SECRET_KEY)

        url = host_url + request_path
        return self.http_get_request(url, params)

    def api_key_post(self, params, request_path):
        method = 'POST'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params_to_sign = {'AccessKeyId': self.ACCESS_KEY,
                          'SignatureMethod': 'HmacSHA256',
                          'SignatureVersion': '2',
                          'Timestamp': timestamp}
        host_url = self.TRADE_URL
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params_to_sign['Signature'] = self.create_sign(params_to_sign, method, host_name, request_path, self.SECRET_KEY)
        url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
        return self.http_post_request(url, params)

    def create_sign(self, params, method, host_url, request_path, secret_key):
        sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)
        payload = [method, host_url, request_path, encode_params]
        payload = '\n'.join(payload)
        payload = payload.encode(encoding='UTF8')
        secret_key = secret_key.encode(encoding='UTF8')
        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        signature = signature.decode()
        return signature

    """ Utils-End """

    # 获取指数数据
    def get_swap_index(self, symbol="BTC-USDT"):
        params = {'contract_code': symbol}
        url = self.MARKET_URL + '/linear-swap-api/v1/swap_index'
        return self.http_get_request(url, params)

    # 获取限频数据
    def get_rate_limit(self):
        self.post_valuation()
        new_dict = {}
        this_dict = self.rate_limit_dict
        new_dict["one_max_count"] = this_dict["ratelimit-limit"]
        new_dict["req_time_step"] = this_dict["ratelimit-interval"]
        new_dict["ratelimit-remaining"] = this_dict["ratelimit-remaining"]
        new_dict["over_reset_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
            float(this_dict["ratelimit-reset"]) / 1000.0))
        return new_dict

    # 获取K线数据
    def get_kline(self, symbol, period, size=150):
        """
        获取KLine
        :param symbol
        :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year }
        :param size: 可选值： [1,2000]
        :return:
        """
        params = {'contract_code': symbol,
                  'period': period,
                  'size': size}
        url = self.MARKET_URL + '/linear-swap-ex/market/history/kline'
        return self.http_get_request(url, params)

    # 获取深度数据
    def get_depth(self, symbol, this_type):
        """
        :param symbol
        :param this_type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
        :return:
        """
        params = {'contract_code': symbol,
                  'type': this_type}
        url = self.MARKET_URL + '/linear-swap-ex/market/depth'
        return self.http_get_request(url, params)

    # 获取swap_contract_info
    def get_swap_contract_info(self, symbol):
        params = {'contract_code': symbol}
        url = self.MARKET_URL + '/linear-swap-api/v1/swap_contract_info'
        return self.http_get_request(url, params)

    # 获取UID
    def get_uid(self):
        params = {}
        return self.api_key_get(params, '/v2/user/uid', "https://api.huobi.pro")

    # 获取市场最新成交
    def get_trade(self, symbol):
        """
        :param symbol
        :return:
        """
        params = {'contract_code': symbol}
        url = self.MARKET_URL + '/linear-swap-ex/market/trade'
        return self.http_get_request(url, params)

    # 获取聚合行情
    def get_ticker(self, symbol):
        """
        :param symbol:
        :return:
        """
        params = {'contract_code': symbol}
        url = self.MARKET_URL + '/linear-swap-ex/market/detail/merged'
        return self.http_get_request(url, params)

    """ Trade/Account>API """

    # 创建并执行订单
    def post_accounts(self, symbol=""):
        """ 获取account """
        url = "/linear-swap-api/v1/swap_cross_account_info"
        if symbol == "": params = {}
        else: params = {"contract_code": symbol}
        return self.api_key_post(params, url)

    # 获取总资产估值换算
    def post_valuation(self, coin=""):
        """ 获取account """
        url = "/linear-swap-api/v1/swap_balance_valuation"
        if coin == "": params = {}
        else: params = {"valuation_asset": coin}
        return self.api_key_post(params, url)

    # 获取持仓
    def post_position(self, symbol=""):
        """ 获取account """
        url = "/linear-swap-api/v1/swap_cross_position_info"
        if symbol == "": params = {}
        else: params = {"contract_code": symbol}
        return self.api_key_post(params, url)

    # 获取信息持仓
    def post_account_position(self, coin="USDT"):
        """ 获取account """
        url = "/linear-swap-api/v1/swap_cross_position_info"
        params = {"margin_account": coin}
        return self.api_key_post(params, url)

    # 创建并执行订单
    def post_send_order(self, symbol, offset, direction, amount, acct_id,
                        lever_rate=20, order_price_type='optimal_20', price=0):
        params = {"client_order_id": acct_id,
                  "volume": amount,
                  "contract_code": symbol,
                  "offset": offset,
                  "direction": direction,
                  "lever_rate": lever_rate,
                  "order_price_type": order_price_type}
        if price:
            params["price"] = price
        url = '/linear-swap-api/v1/swap_cross_order'
        return self.api_key_post(params, url)

    # 创建并执行订单
    def post_stop_order(self, contract_code, offset, direction, volume, trigger_type, trigger_price,
                        order_price_type='optimal_20', lever_rate=20):
        params = {
            "trigger_type": trigger_type,
            "volume": volume,
            "contract_code": contract_code,
            "offset": offset,
            "direction": direction,
            "lever_rate": lever_rate,
            "order_price_type": order_price_type,
            "trigger_price": trigger_price
        }
        url = '/linear-swap-api/v1/swap_cross_trigger_order'
        return self.api_key_post(params, url)

    # 创建并执行订单
    def post_win_los_order(self, contract_code, side, volume, los_price, win_price,
                           order_price_type='optimal_20'):
        params = {
            "contract_code": contract_code,
            "direction": side,
            "volume": volume,
            "sl_trigger_price": los_price,
            "sl_order_price_type": order_price_type,
            "tp_trigger_price": win_price,
            "tp_order_price_type": order_price_type,
        }
        url = '/linear-swap-api/v1/swap_cross_tpsl_order'
        return self.api_key_post(params, url)

    # 创建并执行订单
    def post_send_batch_order(self, params):
        url = '/linear-swap-api/v1/swap_cross_batchorder'
        return self.api_key_post(params, url)

    # 撤销订单
    def post_cancel_order(self, symbol, client_order_id):
        params = {"contract_code": symbol,
                  "client_order_id": client_order_id}
        url = "/linear-swap-api/v1/swap_cross_cancel"
        return self.api_key_post(params, url)

    # 撤销所有订单
    def post_cancel_all_order(self, symbol):
        params = {"contract_code": symbol}
        url = "/linear-swap-api/v1/swap_cross_cancelall"
        return self.api_key_post(params, url)

    # 获取订单信息
    def post_this_order(self, symbol, cid):
        params = {"contract_code": symbol, "client_order_id": cid}
        url = "/linear-swap-api/v1/swap_cross_order_info"
        return self.api_key_post(params, url)

    # 获取未成交委托
    def post_open_orders(self, symbol):
        params = {"contract_code": symbol}
        url = "/linear-swap-api/v1/swap_cross_openorders"
        return self.api_key_post(params, url)

    # 获取历史委托
    def post_his_orders(self, symbol, trade_type=0, this_type=1, status=0, create_date=90):
        params = {"contract_code": symbol,
                  "trade_type": trade_type,
                  "type": this_type,
                  "status": status,
                  "create_date": create_date}
        url = "/linear-swap-api/v1/swap_cross_hisorders"
        return self.api_key_post(params, url)

    # 获取历史成交
    def post_matchresults_orders(self, symbol, trade_type=0, create_date=90):
        params = {"contract_code": symbol,
                  "trade_type": trade_type,
                  "create_date": create_date}
        url = "/linear-swap-api/v1/swap_cross_matchresults"
        return self.api_key_post(params, url)

    """ 合约划转API """

    # 现货账户划入至合约账户
    def futures_pro(self, amount, this_from="spot", this_to="linear-swap", currency="usdt", margin_account='USDT'):
        # params
        params = {"from": this_from,
                  "to": this_to,
                  "currency": currency,
                  "amount": amount,
                  "margin-account": margin_account}
        request_path = "/v2/account/transfer"
        # 现货接口
        method = 'POST'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params_to_sign = {'AccessKeyId': self.ACCESS_KEY,
                          'SignatureMethod': 'HmacSHA256',
                          'SignatureVersion': '2',
                          'Timestamp': timestamp}
        host_url = "https://api.huobi.pro"
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params_to_sign['Signature'] = self.create_sign(params_to_sign, method, host_name, request_path, self.SECRET_KEY)
        url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
        return self.http_post_request(url, params)


if __name__ == '__main__':
    hus = HbUServer("https://api.hbdm.com", "b6f67606-ntmuw4rrsr-7b773", "5f5848b1-317f865a-e7-253cb")
    limit_dict = hus.get_rate_limit()
    print(limit_dict)

