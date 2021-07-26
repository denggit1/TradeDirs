#!/usr/bin/env python

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


# global
global_tick_price = None
symbol = "BTC-USDT"


def generate_signature(host, method, params, request_path, secret_key):
    """Generate signature of huobi future.

    Args:
        host: api domain url.PS: colo user should set this host as 'api.hbdm.com',not colo domain.
        method: request method.
        params: request params.
        request_path: "/notification"
        secret_key: api secret_key

    Returns:
        singature string.

    """
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


async def subscribe(url, access_key, secret_key, subs, callback=None, auth=False):
    """ Huobi Future subscribe websockets.

    Args:
        url: the url to be signatured.
        access_key: API access_key.
        secret_key: API secret_key.
        subs: the data list to subscribe.
        callback: the callback function to handle the ws data received.
        auth: True: Need to be signatured. False: No need to be signatured.

    """
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
            # print(f"send: {msg_str}")
        for sub in subs:
            sub_str = json.dumps(sub)
            await websocket.send(sub_str)
            # print(f"send: {sub_str}")
        while True:
            rsp = await websocket.recv()
            data = json.loads(gzip.decompress(rsp).decode())
            # print(f"recevie<--: {data}")
            if "op" in data and data.get("op") == "ping":
                pong_msg = {"op": "pong", "ts": data.get("ts")}
                await websocket.send(json.dumps(pong_msg))
                # print(f"send: {pong_msg}")
                continue
            if "ping" in data:
                pong_msg = {"pong": data.get("ping")}
                await websocket.send(json.dumps(pong_msg))
                # print(f"send: {pong_msg}")
                continue
            rsp = await callback(data)


async def handle_ws_data(*args, **kwargs):
    """ callback function
    Args:
        args: values
        kwargs: key-values.
    """
    # Tick变动时，运行逻辑判断
    global global_tick_price, symbol
    for each in args:
        if each.get('ch', '') == "market.{}.kline.1min".format(symbol):
            tick_price = each['tick']['close']
            if tick_price != global_tick_price:
                on_tick(tick_price)
                global_tick_price = tick_price
        elif each.get('topic', '') == 'orders_cross.{}'.format(symbol).lower():
            on_order(each)
        elif each.get('topic', '') == 'positions_cross.{}'.format(symbol).lower():
            on_position(each)


def on_tick(tick_price):
    print("运行逻辑判断", tick_price)


def on_order(data_dict):
    print("\n订单变动", data_dict, "\n")


def on_position(data_dict):
    print("\n持仓变动", data_dict, "\n")


def market_ws(access_key, secret_key):
    global symbol
    market_url = 'ws://api.hbdm.vn/linear-swap-ws'
    market_subs = [
        {
            "sub": "market.{}.kline.1min".format(symbol),
        },
    ]
    while True:
        try:
            asyncio.get_event_loop().run_until_complete(
                subscribe(market_url, access_key, secret_key, market_subs, handle_ws_data, auth=False))
        except Exception as e:
            traceback.print_exc()
            print('websocket connection error. reconnect rightnow')


def order_ws(access_key, secret_key):
    global symbol
    order_url = 'wss://api.hbdm.vn/linear-swap-notification'
    order_subs = [
        {
            "op": "sub",
            "topic": "orders_cross.{}".format(symbol)
        },
        {
            "op": "sub",
            "topic": "positions_cross.{}".format(symbol)
        },
    ]
    while True:
        try:
            asyncio.get_event_loop().run_until_complete(
                subscribe(order_url, access_key, secret_key, order_subs, handle_ws_data, auth=True))
        # except (websockets.exceptions.ConnectionClosed):
        except Exception as e:
            traceback.print_exc()
            print('websocket connection error. reconnect rightnow')


if __name__ == "__main__":
    # input your access_key and secret_key below:
    access_key = "b6f67606-ntmuw4rrsr-7ba04364-"
    secret_key = ""
    # ws
    symbol = "UNI-USDT"
    order_ws(access_key, secret_key)

