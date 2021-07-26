# coding:utf-8

import datetime
import uuid
import urllib.parse
import asyncio
import websockets
import json
import hmac
import base64
import hashlib
import gzip
import traceback
import redis


# global
global_symbol_list = ["BTC-USDT", "UNI-USDT"]
global_tick_dict = {}
global_redis = redis.Redis(host='localhost', port=6379, decode_responses=True)


# sign
def generate_signature(host, method, params, request_path, secret_key):
    host_url = urllib.parse.urlparse(host).hostname.lower()
    sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
    encode_params = urllib.parse.urlencode(sorted_params)
    payload = [method, host_url, request_path, encode_params]
    payload = "\n".join(payload)
    payload = payload.encode(encoding="UTF8")
    secret_key = secret_key.encode(encoding="utf8")
    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)
    signature = signature.decode()
    return signature


# sub
async def subscribe(url, access_key, secret_key, subs, callback=None, auth=False):
    async with websockets.connect(url) as websocket:
        if auth:
            timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            data = {
                "AccessKeyId": access_key,
                "SignatureMethod": "HmacSHA256",
                "SignatureVersion": "2",
                "Timestamp": timestamp
            }
            sign = generate_signature(url, "GET", data, "/linear-swap-notification", secret_key)
            data["op"] = "auth"
            data["type"] = "api"
            data["Signature"] = sign
            msg_str = json.dumps(data)
            await websocket.send(msg_str)
        for sub in subs:
            sub_str = json.dumps(sub)
            await websocket.send(sub_str)
        while True:
            rsp = await websocket.recv()
            data = json.loads(gzip.decompress(rsp).decode())
            # print(f"recevie<--: {data}")
            if "op" in data and data.get("op") == "ping":
                pong_msg = {"op": "pong", "ts": data.get("ts")}
                await websocket.send(json.dumps(pong_msg))
                continue
            if "ping" in data:
                pong_msg = {"pong": data.get("ping")}
                await websocket.send(json.dumps(pong_msg))
                continue
            rsp = await callback(data)


# handle
async def handle_ws_data(*args, **kwargs):
    # Tick变动时，运行逻辑判断
    global global_symbol_list, global_tick_dict, global_redis
    for each in args:
        ch = each.get('ch', '')
        if ch != '':
            symbol = ch.split(".")[1]
            if symbol in global_symbol_list:
                tick_price = each['tick']['close']
                if tick_price != global_tick_dict.get(symbol, ''):
                    global_redis.set(symbol, tick_price)
                    #print(symbol, tick_price)
                    global_tick_dict[symbol] = tick_price


def market_ws(access_key, secret_key, host="api.hbdm.vn"):
    global global_symbol_list
    market_url = 'ws://{}/linear-swap-ws'.format(host)
    market_subs = [{"sub": "market.{}.kline.1min".format(symbol)} for symbol in global_symbol_list]
    while True:
        try:
            asyncio.get_event_loop().run_until_complete(
                subscribe(market_url, access_key, secret_key, market_subs, handle_ws_data, auth=False))
        except Exception as e:
            traceback.print_exc()
            print('websocket connection error. reconnect rightnow')


if __name__ == "__main__":
    # symbol
    global_symbol_list = ["BTC-USDT", "UNI-USDT", "ETH-USDT", "LTC-USDT", "BCH-USDT", "XRP-USDT", "TRX-USDT", "EOS-USDT", "ETC-USDT"]
    market_ws("", "", host="api.hbdm.com")

