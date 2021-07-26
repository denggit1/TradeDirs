# coding:utf-8
# @Date:2019-11-06 15:00:00

import base64
import datetime
import hashlib
import hmac
import json
import urllib
import urllib.parse
import urllib.request
import requests


class Huobi(object):
    def __init__(self, URL, ACCESS_KEY, SECRET_KEY):
        # 此处填写APIKEY
        self.ACCESS_KEY = ACCESS_KEY
        self.SECRET_KEY = SECRET_KEY
        # API 请求地址 https://api.huobi.pro
        self.MARKET_URL = URL
        self.TRADE_URL = URL

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
        response = requests.get(url, postdata, headers=headers, timeout=5)
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
        response = requests.post(url, postdata, headers=headers, timeout=10)
        try:
            if response.status_code == 200:
                return response.json()
            else:
                return
        except BaseException as e:
            print("httpPost failed, detail is:%s,%s" % (response.text, e))
            return

    def api_key_get(self, params, request_path):
        method = 'GET'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params.update({'AccessKeyId': self.ACCESS_KEY,
                       'SignatureMethod': 'HmacSHA256',
                       'SignatureVersion': '2',
                       'Timestamp': timestamp})
        host_url = self.TRADE_URL
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
    def get_kline(self, symbol, period, size=150):
        """
        获取KLine
        :param symbol
        :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year }
        :param size: 可选值： [1,2000]
        :return:
        """
        params = {'symbol': symbol,
                  'period': period,
                  'size': size}
        url = self.MARKET_URL + '/market/history/kline'
        return self.http_get_request(url, params)

    # 获取marketdepth
    def get_depth(self, symbol, this_type):
        """
        :param symbol
        :param this_type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
        :return:
        """
        params = {'symbol': symbol,
                  'type': this_type}
        url = self.MARKET_URL + '/market/depth'
        return self.http_get_request(url, params)

    # 获取tradedetail
    def get_trade(self, symbol):
        """
        :param symbol
        :return:
        """
        params = {'symbol': symbol}
        url = self.MARKET_URL + '/market/trade'
        return self.http_get_request(url, params)

    # Tickers detail
    def get_tickers(self):
        """ :return: """
        params = {}
        url = self.MARKET_URL + '/market/tickers'
        return self.http_get_request(url, params)

    # 获取merge ticker
    def get_ticker(self, symbol):
        """
        :param symbol:
        :return:
        """
        params = {'symbol': symbol}
        url = self.MARKET_URL + '/market/detail/merged'
        return self.http_get_request(url, params)

    # 获取 Market Detail 24小时成交量数据
    def get_detail(self, symbol):
        """
        :param symbol
        :return:
        """
        params = {'symbol': symbol}
        url = self.MARKET_URL + '/market/detail'
        return self.http_get_request(url, params)

    def get_symbols(self, long_polling=None):
        """ 获取支持的交易对 """
        params = {}
        if long_polling:
            params['long-polling'] = long_polling
        path = '/v1/common/symbols'
        return self.api_key_get(params, path)

    # Get available currencies
    def get_currencies(self):
        """ :return: """
        params = {}
        url = self.MARKET_URL + '/v1/common/currencys'
        return self.http_get_request(url, params)

    # Get all the trading assets
    def get_trading_assets(self):
        """ :return: """
        params = {}
        url = self.MARKET_URL + '/v1/common/symbols'
        return self.http_get_request(url, params)

    """ Trade/Account>API """
    def get_accounts(self):
        """ 获取account """
        path = "/v1/account/accounts"
        params = {}
        return self.api_key_get(params, path)

    # 获取账户ID
    def get_type_accounts(self, this_type):
        """
        :param this_type: spot：现货， margin：逐仓杠杆，otc：OTC 账户，point：点卡，super-margin：全仓杠杆账户
        :return: account_id
        """
        account_id = None
        account_data = self.get_accounts()['data']
        for account in account_data:
            if account['type'] == this_type:
                account_id = account['id']
        return account_id

    # 获取当前账户资产
    def get_balance(self, acct_id=None):
        """
        :param acct_id
        :return:
        """
        if not acct_id:
            accounts = self.get_accounts()
            acct_id = accounts['data'][0]['id']
        url = "/v1/account/accounts/{0}/balance".format(acct_id)
        params = {"account-id": acct_id}
        return self.api_key_get(params, url)

    def get_currency_balance(self, spot_id, currency):
        """
        获取币种所在账户id的数量
        :param spot_id: spot
        :param currency: usdt
        :return: balance
        """
        balance_data = self.get_balance(spot_id)['data']['list']
        balance = 0
        for b in balance_data:
            if b['currency'] == currency:
                balance += float(b['balance'])
        return balance

    # 创建并执行订单
    def send_order(self, acct_id, _type, amount, source='api', symbol='ethusdt', price=0):
        """
        :param acct_id:
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param amount:
        :param source: 如果使用借贷资产交易，请在下单接口,请求参数source中填写'margin-api'
        :param symbol:
        :param price:
        :return:
        """
        # try:
        #     accounts = self.get_accounts()
        #     acct_id = accounts['data'][0]['id']
        # except BaseException as e:
        #     print('get acct_id error.%s' % e)
        #     acct_id = None
        params = {"account-id": acct_id,
                  "amount": amount,
                  "symbol": symbol,
                  "type": _type,
                  "source": source}
        if price:
            params["price"] = price
        url = '/v1/order/orders/place'
        return self.api_key_post(params, url)

    # 撤销订单
    def cancel_order(self, order_id):
        """
        :param order_id:
        :return:
        """
        params = {}
        url = "/v1/order/orders/{0}/submitcancel".format(order_id)
        return self.api_key_post(params, url)

    # 查询某个订单
    def order_info(self, order_id):
        """
        :param order_id:
        :return:
        """
        params = {}
        url = "/v1/order/orders/{0}".format(order_id)
        return self.api_key_get(params, url)

    # 查询某个订单的成交明细
    def order_matchresults(self, order_id):
        """
        :param order_id:
        :return:
        """
        params = {}
        url = "/v1/order/orders/{0}/matchresults".format(order_id)
        return self.api_key_get(params, url)

    # 查询当前委托、历史委托
    def orders_list(self, symbol, states, types=None,
                    start_date=None, end_date=None, _from=None, direct=None, size=None):
        """
        :param symbol:
        :param states: 可选值 {pre-submitted 准备提交, submitted 已提交, partial-filled 部分成交,
                               partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销}
        :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param start_date:
        :param end_date:
        :param _from:
        :param direct: 可选值{prev 向前，next 向后}
        :param size:
        :return:
        """
        params = {'symbol': symbol,
                  'states': states}
        if types:
            params['types'] = types
        if start_date:
            params['start-date'] = start_date
        if end_date:
            params['end-date'] = end_date
        if _from:
            params['from'] = _from
        if direct:
            params['direct'] = direct
        if size:
            params['size'] = size
        url = '/v1/order/orders'
        return self.api_key_get(params, url)

    # 查询当前成交、历史成交
    def orders_matchresults(self, symbol, types=None,
                            start_date=None, end_date=None, _from=None, direct=None, size=None):
        """
        :param symbol:
        :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param start_date:
        :param end_date:
        :param _from:
        :param direct: 可选值{prev 向前，next 向后}
        :param size:
        :return:
        """
        params = {'symbol': symbol}
        if types:
            params['types'] = types
        if start_date:
            params['start-date'] = start_date
        if end_date:
            params['end-date'] = end_date
        if _from:
            params['from'] = _from
        if direct:
            params['direct'] = direct
        if size:
            params['size'] = size
        url = '/v1/order/matchresults'
        return self.api_key_get(params, url)

    # 查询所有当前帐号下未成交订单
    def open_orders(self, account_id, symbol, side='', size=10):
        """ 查询所有当前帐号下未成交订单 """
        params = {}
        url = "/v1/order/openOrders"
        if symbol:
            params['symbol'] = symbol
        if account_id:
            params['account-id'] = account_id
        if side:
            params['side'] = side
        if size:
            params['size'] = size
        return self.api_key_get(params, url)

    # 批量取消符合条件的订单
    def cancel_open_orders(self, account_id, symbol, side='', size=10):
        """ 批量取消符合条件的订单 """
        params = {}
        url = "/v1/order/orders/batchCancelOpenOrders"
        if symbol:
            params['symbol'] = symbol
        if account_id:
            params['account-id'] = account_id
        if side:
            params['side'] = side
        if size:
            params['size'] = size
        return self.api_key_post(params, url)

    # 提现API
    """
    def withdraw(self, address, amount, currency, fee=0, addr_tag=""):
        # 申请提现虚拟币
        # :param address: address_id
        # :param amount:
        # :param currency:btc, ltc, bcc, eth, etc ...(火币Pro支持的币种)
        # :param fee:
        # :param addr_tag: addr-tag
        # :return: {
        #           "status": "ok",
        #           "data": 700
        #         }
        params = {'address': address,
                  'amount': amount,
                  "currency": currency,
                  "fee": fee,
                  "addr-tag": addr_tag}
        url = '/v1/dw/withdraw/api/create'

        return self.api_key_post(params, url)

    def cancel_withdraw(self, address_id):
        # 申请取消提现虚拟币
        # :param address_id:
        # :return: {
        #           "status": "ok",
        #           "data": 700
        #         }
        params = {}
        url = '/v1/dw/withdraw-virtual/{0}/cancel'.format(address_id)
        return self.api_key_post(params, url)
    """

    """ 合约划转API """

    # 现货账户划入至合约账户
    def futures_pro(self, this_type, amount, currency='eth'):
        """
        :param this_type: 从合约账户到现货账户：futures-to-pro，从现货账户到合约账户:：pro-to-futures
        :param amount: 划转数量
        :param currency: 币种
        :return:
        """
        params = {"currency": currency,
                  "amount": amount,
                  "type": this_type}
        url = "/v1/futures/transfer"
        return self.api_key_post(params, url)

    """ 借贷API """
    def send_margin_order(self, amount, source, symbol, _type, price=0):
        """
        创建并执行借贷订单
        :param amount:
        :param source: 'margin-api'
        :param symbol:
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param price:
        :return:
        """
        try:
            accounts = self.get_accounts()
            acct_id = accounts['data'][0]['id']
        except BaseException as e:
            print('get acct_id error.%s' % e)
            acct_id = None
        source = source
        params = {"account-id": acct_id,
                  "amount": amount,
                  "symbol": symbol,
                  "type": _type,
                  "source": 'margin-api'}
        if price:
            params["price"] = price
        url = '/v1/order/orders/place'
        return self.api_key_post(params, url)

    # 现货账户划入至借贷账户
    def exchange_to_margin(self, symbol, currency, amount):
        """
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {"symbol": symbol,
                  "currency": currency,
                  "amount": amount}
        url = "/v1/dw/transfer-in/margin"
        return self.api_key_post(params, url)

    # 借贷账户划出至现货账户
    def margin_to_exchange(self, symbol, currency, amount):
        """
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {"symbol": symbol,
                  "currency": currency,
                  "amount": amount}
        url = "/v1/dw/transfer-out/margin"
        return self.api_key_post(params, url)

    # 申请借贷
    def get_margin(self, symbol, currency, amount):
        """
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {"symbol": symbol,
                  "currency": currency,
                  "amount": amount}
        url = "/v1/margin/orders"
        return self.api_key_post(params, url)

    # 归还借贷
    def repay_margin(self, order_id, amount):
        """
        :param order_id:
        :param amount:
        :return:
        """
        params = {"order-id": order_id,
                  "amount": amount}
        url = "/v1/margin/orders/{0}/repay".format(order_id)
        return self.api_key_post(params, url)

    # 借贷订单
    def loan_orders(self, symbol, currency, start_date="", end_date="", start="", direct="", size=""):
        """ direct: prev 向前，next 向后 """
        params = {"symbol": symbol,
                  "currency": currency}
        if start_date:
            params["start-date"] = start_date
        if end_date:
            params["end-date"] = end_date
        if start:
            params["from"] = start
        if direct and direct in ["prev", "next"]:
            params["direct"] = direct
        if size:
            params["size"] = size
        url = "/v1/margin/loan-orders"
        return self.api_key_get(params, url)

    # 借贷账户详情,支持查询单个币种
    def margin_balance(self, symbol):
        """
        :param symbol:
        :return:
        """
        params = {}
        url = "/v1/margin/accounts/balance"
        if symbol:
            params['symbol'] = symbol
        return self.api_key_get(params, url)


if __name__ == '__main__':
    h = Huobi("https://api.huobi.pro", "", "")
    print(h.MARKET_URL)

