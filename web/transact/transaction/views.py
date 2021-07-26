from django.shortcuts import render, HttpResponse, redirect
from django.views.decorators.csrf import csrf_exempt
from Crypto.Cipher import AES
from binascii import a2b_hex
import pymysql
import hmac
import hashlib
import urllib.parse
from hashlib import sha1
import time
import json
from django.conf import settings
import os
import sys
sys.path.append('/root/TradeDirs/exchange_service/')
import BinanceDMService


# Create your views here.


# 首页
def index(request):
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')
        key_name = request.COOKIES.get("user", "")
        return render(request, 'transaction.html', {'username': username, 'key_name': key_name})
    else:
        return redirect('/transaction/login/')


# 退出
def delSession(request):
    if request.session.get('username', '') != '':
        del request.session['username']
        return redirect('/transaction/login/')
    else:
        return redirect('/transaction/login/')


# 登录
def login(request):
    if request.session.get('username', '') != '':
        return redirect('/transaction/')
    else:
        if request.method == 'POST':
            username = request.POST.get('username', '').strip()
            userpwd = request.POST.get('userpwd', '')
            s1 = sha1()
            s1.update(userpwd.encode())
            userpwd = s1.hexdigest()
            conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='web')
            cur = conn.cursor()
            sql = "SELECT * FROM `user_tbl` where username=%s and userpwd=%s;"
            cur.execute(sql, [username, userpwd])
            temp = cur.fetchone()
            conn.close()
            if temp != None:
                request.session['username'] = username
                respose = redirect('/transaction/freq_info/')
                respose.set_cookie("user", "")
                return respose
            else:
                return HttpResponse("用户名或密码错误！<a href='/transaction/login/'>点击返回登录界面</a>")
        else:
            return render(request, 'login.html')


# 设置cookie
def set_cookie(request):
    if request.session.get('username', '') != '':
        if request.method == "GET":
            user = request.GET.get('user', '')
            response = redirect('/transaction/senior/')
            response.set_cookie("user", user)
            return response
        else:
            return redirect('/transaction/')
    else:
        return redirect('/transaction/login/')


# 数据
def eth_data(request):
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')
        key_name = request.COOKIES.get("user", "")
        # db
        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='trade')
        cur = conn.cursor()
        sql = "SELECT count(*) FROM `bn_data` where ntime like '{}%';"
        # 遍历日期
        now_time = time.time()
        result = []
        for i in range(10):
            str_time = time.strftime('%Y%m%d', time.localtime(now_time - i * 24 * 3600))
            cur.execute(sql.format(str_time))
            count = cur.fetchone()[0]
            result.append([str_time, count])
        cur.execute("SELECT max(ntime) FROM `bn_data`;")
        max_time = cur.fetchone()[0]
        conn.close()
        # pid
        pid = os.popen('/root/TradeDirs/ps_aux_grep.sh').readlines()
        return render(request, 'eth_data.html',
                      {'username': username, 'key_name': key_name,
                       'max_time': max_time, 'result': result, 'pid': pid})
    else:
        return redirect('/transaction/login/')


# API管理
def key_time(request):
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')
        key_name = request.COOKIES.get("user", "")
        # db
        if request.method == 'POST':
            # 判断操作
            handle = request.POST.get('handle', '')
            user = request.POST.get('user', '')
            stime = request.POST.get('stime', '')
            google = request.POST.get('google', '')
            access = request.POST.get('access', '')
            secret = request.POST.get('secret', '')
            try:
                if user != '' and access != '' and secret != '':
                    if handle == 'update':
                        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root',
                                               passwd=settings.PWD, db='trade')
                        cur = conn.cursor()
                        sql = "UPDATE key_table SET access_key=%s, secret_key=%s, stime=%s, pass_phrase=%s" \
                              " WHERE user_name=%s;"
                        cur.execute(sql, [access, secret, stime, google, user])
                        conn.commit()
                        conn.close()
                    elif handle == 'hb_freq':
                        if secret == "1":
                            with open("/root/TradeDirs/downloads/hb_freq.ini", "w") as f: f.write("{}_{}".format(user, access))
                            os.popen("nohup /usr/bin/python3 /root/TradeDirs/downloads/hb_freq.py > /dev/null 2>&1 &")
                        else:
                            os.popen("ps -ef|grep hb_freq.py|awk '{print $2}'|xargs kill -9")
                    elif handle == 'look':
                        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD,
                                               db='trade')
                        cur = conn.cursor()
                        sql = "select user_name from key_table where access_key=%s order by id desc limit 1;"
                        cur.execute(sql, access)
                        temp = cur.fetchone()
                        conn.commit()
                        conn.close()
                        if temp:
                            user_name = temp[0]
                            return redirect('/transaction/set_cookie/?user={}'.format(user_name))
                    elif handle == 'insert':
                        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD,
                                               db='trade')
                        cur = conn.cursor()
                        sql = "INSERT INTO `key_table` (user_name, access_key, secret_key, pass_phrase, stime)" \
                              " VALUE (%s,%s,%s,%s,%s);"
                        cur.execute(sql, [user, access, secret, google, stime])
                        conn.commit()
                        conn.close()
                    elif handle == 'insert_house':
                        u = user.split("_")[0]
                        # conn
                        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD)
                        # trade
                        sql = "INSERT INTO `key_table` (user_name, access_key, secret_key, pass_phrase, stime)" \
                              " VALUE (%s,%s,%s,%s,%s);"
                        conn.select_db("trade")
                        cur = conn.cursor()
                        cur.execute(sql, [user, access, secret, google, stime])
                        conn.commit()
                        cur.close()
                        # 文件
                        os.system("cp -r /root/TradeDirs/freq/back /root/TradeDirs/freq/{}".format(u))
                        os.system("rename back {} /root/TradeDirs/freq/{}/*.py".format(u, u))
                        # freq
                        wh_sql = ('insert into web_house (user_name,trade_code,freq_stop,max_balance,'
                                  'sign_bl1,usdt_bl1,order_bl1,sign_hg1,usdt_hg1,order_hg1) value '
                                  '(%s,"ETHUSDT",1000000,0.0,0.0,0.0,"[]",0.0,0.0,"[]");')
                        conn.select_db("freq")
                        cur = conn.cursor()
                        cur.execute(wh_sql, user)
                        wp_sql = 'insert into web_pos (user_name,strategy,trade_code,trade_usdt,db_num,cal_offset,syn_offset) ' \
                                 'value (%s,"big","no","250","no","no","0");'
                        cur.execute(wp_sql, user)
                        conn.commit()
                        cur.close()
                        # user
                        create_sql = ('create database {};'.format(u))
                        cur = conn.cursor()
                        cur.execute(create_sql)
                        conn.commit()
                        cur.close()
                        # u
                        sql1 = ("""
                        CREATE TABLE `ws_orders` (
                            `id` int(30) NOT NULL AUTO_INCREMENT,
                            `user_name` varchar(100) DEFAULT NULL,
                            `eventTime` varchar(100) DEFAULT NULL,
                            `symbol` varchar(100) DEFAULT NULL,
                            `clientOrderId` varchar(100) DEFAULT NULL,
                            `side` varchar(100) DEFAULT NULL,
                            `type` varchar(100) DEFAULT NULL,
                            `origQty` varchar(100) DEFAULT NULL,
                            `avgPrice` varchar(100) DEFAULT NULL,
                            `orderStatus` varchar(100) DEFAULT NULL,
                            `orderId` varchar(100) DEFAULT NULL,
                            `cumulativeFilledQty` varchar(100) DEFAULT NULL,
                            `no_repeat` varchar(255) DEFAULT NULL,
                            PRIMARY KEY (`id`),
                            UNIQUE KEY `no_repeat` (`no_repeat`),
                            KEY `index_name` (`clientOrderId`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
                        """)
                        sql2 = ("""
                        CREATE TABLE `freq_trade` (
                            `id` int(20) NOT NULL AUTO_INCREMENT,
                            `api_name` varchar(255) DEFAULT NULL,
                            `trade_name` varchar(255) DEFAULT NULL,
                            `trade_code` varchar(255) DEFAULT NULL,
                            `first_price` varchar(255) DEFAULT NULL,
                            `trade_arr` varchar(2550) DEFAULT NULL,
                            `mid_index` varchar(255) DEFAULT NULL,
                            `up_id` varchar(255) DEFAULT NULL,
                            `down_id` varchar(255) DEFAULT NULL,
                            `last_order` varchar(255) DEFAULT NULL,
                            `sum_num` varchar(255) DEFAULT NULL,
                            PRIMARY KEY (`id`),
                            KEY `index_name` (`trade_code`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
                        """)
                        sql3 = ("""
                        CREATE TABLE `freq_orders` (
                            `id` int(20) NOT NULL AUTO_INCREMENT,
                            `api_name` varchar(255) DEFAULT NULL,
                            `trade_name` varchar(255) DEFAULT NULL,
                            `trade_code` varchar(255) DEFAULT NULL,
                            `handle` varchar(255) DEFAULT NULL,
                            `side` varchar(255) DEFAULT NULL,
                            `price` varchar(255) DEFAULT NULL,
                            `quantity` varchar(255) DEFAULT NULL,
                            `client_id` varchar(255) DEFAULT NULL,
                            `trade_status` varchar(255) DEFAULT NULL,
                            `web_status` varchar(255) DEFAULT NULL,
                            `finish_status` varchar(255) DEFAULT NULL,
                            PRIMARY KEY (`id`),
                            KEY `index_name` (`client_id`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
                        """)
                        conn.select_db(u)
                        cur = conn.cursor()
                        cur.execute(sql1)
                        cur.execute(sql2)
                        cur.execute(sql3)
                        conn.commit()
                        cur.close()
                        conn.close()
            except:
                pass
            time.sleep(1)
            return redirect('/transaction/key_time/')
        else:
            conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='trade')
            cur = conn.cursor()
            sql = "select user_name, stime, '', access_key, secret_key, pass_phrase, pwd from `key_table`;"
            cur.execute(sql)
            result1 = cur.fetchall()
            conn.close()
            sql = 'select user_name,strategy,trade_usdt from web_pos where syn_offset=1;'
            conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
            cur = conn.cursor()
            cur.execute(sql)
            freq_data = cur.fetchall()
            conn.close()
            # result
            user_freq = [each[0] for each in freq_data]
            result = []
            for each in result1:
                each = list(each)
                each[3] = each[3][:3] + '***'
                each[4] = each[4][:3] + '***'
                if each[0] in user_freq:
                   each[2] = "1"
                   try: each.append(int(float(each[1]) / float(each[5]) * 100.0))
                   except: each.append(0.0)
                   # 8 start
                   temp_d = freq_data[user_freq.index(each[0])]
                   init_usd = int(temp_d[2])
                   each.append(temp_d[1])
                   each.append(init_usd)
                   try: each.append(float(each[5]) - init_usd)
                   except: each.append("")
                   result.append(each)
                else:
                   each[5], each[1] = "", ""
                   each.append(0.0)
                   # 8 start
                   each.append("")
                   each.append("")
                   each.append("")
                   #if each[0][0] == "d": result.append(each)
            # result.sort(key=lambda x: x[2], reverse=True)
            # 构造
            new_result = sorted(result, key=lambda x: x[7], reverse=True)
            temp_result = []
            for each in new_result:
                each[0] = each[0].split("_")[0]
                temp_result.append(each)
            new_result = temp_result
            return render(request, 'key_time.html', {'username': username, 'result': new_result, 'key_name': key_name, "count": len(user_freq)})
    else:
        return redirect('/transaction/login/')


# 信号
def sign(request):
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')
        key_name = request.COOKIES.get("user", "")
        # db
        db_name = request.GET.get('db', '')
        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='trade')
        cur = conn.cursor()
        sign_sql = "select `strategy` from `sign_bn` group by `strategy`;"
        cur.execute(sign_sql)
        sign_result = cur.fetchall()
        sql = "SELECT `signal`, ntime, `status` FROM `sign_bn` where strategy=%s ORDER BY id DESC limit 20;"
        if db_name == '':
            db_name = sign_result[0][0]
        cur.execute(sql, db_name)
        result = cur.fetchall()
        conn.close()
        return render(request, 'sign.html',
                      {'username': username, 'key_name': key_name,
                       'db_name': db_name, 'result': result, 'sign_result': sign_result})
    else:
        return redirect('/transaction/login/')


# 币安仓位
def bnwh(request):
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')
        key_name = request.COOKIES.get("user", "")
        # bn obj
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=settings.PWD, db='trade')
        cur = conn.cursor()
        sql = 'SELECT access_key, secret_key, pass_phrase FROM `key_table` where user_name = %s;'
        cur.execute(sql, key_name)
        key_tuple = cur.fetchone()
        conn.close()
        bm = BinanceDMService.BinanceDm(key_tuple[0], key_tuple[1], "https://fapi.binance.com/")
        symbol_list = ["BTCUSDT", "ETHUSDT", "BCHUSDT", "XRPUSDT", "EOSUSDT", "LTCUSDT", "TRXUSDT", "ETCUSDT", "ADAUSDT", "BNBUSDT", "LINKUSDT", "VETUSDT"]
        # 合约 usdt/bnb
        try:
            if key_name[:3] == "btc":
                balance = bm.get_dapi_account().get("assets", [])
            else:
                balance = bm.get_account().get("assets", [])
        except:
            balance = [{"asset": "USDT", "marginBalance": "error", "positionInitialMargin": "error"}]
        time.sleep(0.2)
        # 现货 usdt/bnb
        try:
            spot_balance = bm.get_spot_balances()
        except:
            spot_balance = [{"asset": "USDT", "free": "error", "locked": "error"}]
        # ##
        symbol_dict = {"ZEC": 0.0, "XRP": 0.0, "LINK": 0.0, "BCH": 0.0, "LTC": 0.0, "ETH": 0.0, "ETC": 0.0}
        res = bm.get_spot_tick_price()
        for each in res:
            if each["symbol"] == "BTCUSDT":
                symbol_dict[each["symbol"].replace("BTC", "")] = 1.0 / float(each["price"])
            elif each["symbol"] in [name + "BTC" for name, price in symbol_dict.items()]:
                symbol_dict[each["symbol"].replace("BTC", "")] = float(each["price"])
        symbol_dict["BTC"] = 1.0
        sum_btc = 0.0
        for b in spot_balance:
            if b["asset"] in [name for name, price in symbol_dict.items()]:
                sum_btc += (float(b["free"]) + float(b["locked"])) * symbol_dict[b["asset"]]
            new_dict = {
                "asset": "{}_S".format(b["asset"]),
                "marginBalance": b["free"],
                "positionInitialMargin": b["locked"],
            }
            balance.append(new_dict)
        balance.append({"asset": "BTC_A", "marginBalance": sum_btc, "positionInitialMargin": "0"})
        balance.append({"asset": "USDT_R", "marginBalance": key_tuple[2], "positionInitialMargin": "0"})
        time.sleep(0.2)
        # 仓位
        try:
            positions = bm.get_position()
        except:
            positions = [{"symbol": "BTCUSDT", "positionAmt": "0", "entryPrice": "0"}]
        position = []
        for p in positions:
            if p["symbol"] in symbol_list:
                p["bzj"] = round(float(p["positionAmt"]) * float(p["entryPrice"]), 1)
                position.append(p)
        time.sleep(0.2)
        # 挂单
        open_orders = []
        try:
            if key_name[:3] == "btc":
                open_orders = bm.get_dapi_open_orders("BTCUSD_PERP")
            else:
                open_orders = bm.get_open_orders("")
            time.sleep(0.1)
        except:
            open_orders = []
        # 状态
        try:
            local_time = bm.get_time()["serverTime"]
            server_time = bm.get_time("web")["serverTime"]
            exchange_info = {
                "localTime": local_time,
                "serverTime": server_time,
                "usedWeight": bm.weight,
            }
        except:
            exchange_info = {}
        del bm
        # db sum_list order_tuple
        order_tuple = ()
        sum_dict = {}
        # tl - 5.0
        rate = 10.0
        if key_name == "ll_bian_api":
            for each in balance:
                each["marginBalance"] = float(each["marginBalance"]) * rate
                each["positionInitialMargin"] = float(each["positionInitialMargin"]) * rate
            for each in position:
                each["positionAmt"] = float(each["positionAmt"]) * rate
                each["bzj"] = float(each["bzj"]) * rate
        return render(request, 'bnwh.html',
                      {'username': username, 'balance': balance, 'position': position, 'sum_dict': sum_dict,
                       'open_orders': open_orders, 'order_tuple': order_tuple, "exchange_info": exchange_info,
                       "key_name": key_name})
    else:
        return redirect('/transaction/login/')


# 币安订单
def bnod(request):
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')

        key_name = request.COOKIES.get("user", "")
        # bn obj
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=settings.PWD, db='trade')
        cur = conn.cursor()
        sql = 'SELECT access_key, secret_key, pass_phrase FROM `key_table` where user_name = %s;'
        cur.execute(sql, key_name)
        key_tuple = cur.fetchone()
        conn.close()
        bm = BinanceDMService.BinanceDm(key_tuple[0], key_tuple[1], "https://fapi.binance.com/")
        try:
            # orders
            orders = []
            if key_name[:3] == "btc":
                res = bm.get_dapi_all_orders("BTCUSD_PERP")
            else:
                res = bm.get_all_orders("")
            for r in res:
                if r["status"] == "FILLED":
                    orders.append(r)
        except:
            orders = []
        # del
        del bm
        # tl - 5.0
        rate = 10.0
        if key_name == "ll_bian_api":
            for each in orders:
                each["origQty"] = round(float(each["origQty"]) * rate, 2)
        return render(request, 'bnod.html',
                      {'username': username, 'orders': orders,
                       'key_name': key_name})
    else:
        return redirect('/transaction/login/')


# 查询tick
def ws_tick(request):
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')

        key_name = request.COOKIES.get("user", "")
        code_sql = "select trade_code, max(ticker_dfp) from freq_param group by trade_code;"
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=settings.PWD, db='freq')
        cur = conn.cursor()
        cur.execute(code_sql)
        code_tuple = cur.fetchall()
        conn.close()
        return render(request, 'ws_tick.html',
                      {'username': username, 'key_name': key_name, 'code_tuple': code_tuple})
    else:
        return redirect('/transaction/login/')


# 高级权限
def senior(request):
    """
    权限操作
    POST方式
    """
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')

        key_name = request.COOKIES.get("user", "")
        # bn obj
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=settings.PWD, db='trade')
        cur = conn.cursor()
        sql = 'SELECT access_key, secret_key, pass_phrase FROM `key_table` where user_name = %s;'
        cur.execute(sql, key_name)
        key_tuple = cur.fetchone()
        conn.close()
        dm = BinanceDMService.BinanceDm(key_tuple[0], key_tuple[1], "https://fapi.binance.com/")
        
        if request.method == 'POST':
            try:
                trade_select = request.POST.get('trade', '')
                if trade_select == 'dapi':
                    symbol = request.POST.get('code', '')
                    side = request.POST.get('trade_direction', '')
                    trade_num = request.POST.get('trade_num', '')
                    price = request.POST.get('price', '')
                    reduce_only = request.POST.get('reduce_only', '')
                    if price == "market":
                        dm.post_dapi_market_order(symbol, side, trade_num, "w_{}".format(int(time.time() * 1000)), reduce_only)
                        time.sleep(3)
                        return redirect('/transaction/senior/')
                    elif price == "stop":
                        temp = trade_num.split("/")
                        p = temp[0]
                        num = temp[1]
                        dm.post_dapi_stop_market_order(symbol, side, p, num, "w_{}".format(int(time.time() * 1000)), reduce_only)
                        time.sleep(3)
                        return redirect('/transaction/bnwh/')
                    else:
                        dm.post_dapi_limit_order(symbol, side, price, trade_num, "w_{}".format(int(time.time() * 1000)), reduce_only)
                        time.sleep(3)
                        return redirect('/transaction/bnwh/')
                elif trade_select == 'dm':
                    symbol = request.POST.get('code', '')
                    side = request.POST.get('trade_direction', '')
                    trade_num = request.POST.get('trade_num', '')
                    price = request.POST.get('price', '')
                    reduce_only = request.POST.get('reduce_only', '')
                    if price == "market":
                        r=dm.post_market_order(symbol, side, trade_num, "w_{}".format(int(time.time() * 1000)), reduce_only)
                        print(r)
                        time.sleep(3)
                        return redirect('/transaction/senior/')
                    elif price == "stop":
                        temp = trade_num.split("/")
                        p = temp[0]
                        num = temp[1]
                        dm.post_stop_market_order(symbol, side, p, num, "w_{}".format(int(time.time() * 1000)), reduce_only)
                        time.sleep(3)
                        return redirect('/transaction/bnwh/')
                    else:
                        dm.post_limit_order(symbol, side, price, trade_num, "w_{}".format(int(time.time() * 1000)), reduce_only)
                        time.sleep(3)
                        return redirect('/transaction/bnwh/')
                elif trade_select == 'to':
                    asset = request.POST.get('asset', '')
                    to_direction = request.POST.get('to_direction', '')
                    to_num = request.POST.get('to_num', '')
                    dm.post_transfer(asset, to_num, to_direction)
                    time.sleep(3)
                    return redirect('/transaction/bnwh/')
                elif trade_select == 'bi':
                    symbol = request.POST.get('code_s', '')
                    side = request.POST.get('trade_direction_s', '')
                    trade_num = request.POST.get('trade_num_s', '')
                    dm.post_spot_market(symbol, side, trade_num, "w_{}".format(int(time.time() * 1000)))
                    time.sleep(3)
                    return redirect('/transaction/bnwh/')
                elif trade_select == 'do':
                    symbol = request.POST.get('code', '')
                    client_id = request.POST.get('client_id', '')
                    if symbol == "PID":
                        os.system("kill -9 {}".format(client_id))
                    else:
                        if symbol[-1] != "T":
                            data = dm.delete_dapi_one_order(symbol, client_id, rake_back="")
                        else:
                            dm.delete_order(symbol, client_id, rake_back="")
                    time.sleep(3)
                    return redirect('/transaction/senior/')
                elif trade_select == 'da':
                    symbol = request.POST.get('code', '')
                    if symbol[-1] != "T":
                        dm.delete_dapi_all_order(symbol)
                    else:
                        dm.delete_all_order(symbol)
                    time.sleep(3)
                    return redirect('/transaction/senior/')
                elif trade_select == 'le':
                    symbol = request.POST.get('code', '')
                    leverage = request.POST.get('leverage', '')
                    dm.post_leverage(symbol, leverage)
                    time.sleep(3)
                    return redirect('/transaction/senior/')
                elif trade_select == 'clear':
                    user = key_name.split("_")[0]
                    os.popen("nohup /usr/bin/python3 /root/TradeDirs/freq/{}/{}_stop.py > /dev/null 2>&1 &".format(user, user))
                    time.sleep(30)
                    os.popen("nohup /usr/bin/python3 /root/TradeDirs/freq/{}/{}_start.py > /dev/null 2>&1 &".format(user, user))
                    return redirect('/transaction/senior/')
                elif trade_select == 'bao':
                    symbol = request.POST.get('code', '')
                    side = request.POST.get('trade_direction', '')
                    trade_num = request.POST.get('trade_num', '')
                    if side == "BUY": dm.post_bao_purchase(symbol, trade_num)
                    elif side == "SELL": dm.post_bao_redeem(symbol, trade_num)
                    time.sleep(3)
                    return redirect('/transaction/senior/')
                else:
                    return redirect('/transaction/senior/')
            except Exception as e: pass
        else:
            # position
            try:
                if key_name[:3] == "btc":
                    positions = dm.get_dapi_position()
                else:
                    positions = dm.get_position()
            except: positions = [{"symbol": "error", "positionAmt": 9.9}]
            position = []
            for p in positions:
                if float(p["positionAmt"]) != 0.0:
                    position.append(p)
            time.sleep(0.2)
            # bao pos
            try:
                bao_pos = []
            except:
                bao_pos = []
            # 挂单
            open_orders = []
            try:
                if key_name[:3] == "btc":
                    open_orders = dm.get_dapi_open_orders("BTCUSD_PERP")
                else:
                    open_orders = dm.get_open_orders("")
                time.sleep(0.1)
            except:
                open_orders = []
            # 合约 usdt/bnb
            try:
                balance = dm.get_account().get("assets", [])
                new_balance = [0,0]
                for each in balance:
                    if each["asset"] == "USDT":
                        new_balance[0] = float(each["marginBalance"])
                        new_balance[1] = float(each["positionInitialMargin"])
            except:
                new_balance = [0,0]
            # tl - 5.0
            rate = 10.0
            if key_name == "ll_bian_api":
                for each in position:
                    each["positionAmt"] = round(float(each["positionAmt"]) * rate, 2)
                    each["unRealizedProfit"] = round(float(each["unRealizedProfit"]) * rate, 3)
            time.sleep(0.2)
            return render(request, 'senior.html', {'username': username, 'key_name': key_name, 'position': position, "bao_pos": bao_pos,
                                                   "open_orders": open_orders, "balance": new_balance})
    else:
        return redirect('/transaction/login/')


# 资金曲线
def capitalcurve(request):
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')
        # cap
        key_name = request.COOKIES.get("user", "")
        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='trade')
        cur = conn.cursor()
        #
        sql = "SELECT this_time, balance FROM `key_balance` where user_name=%s ORDER BY this_time;"
        cur.execute(sql, key_name)
        temp = cur.fetchall()
        conn.close()
        result = [[i, round(float(j), 1)] for i, j in temp]
        # tl - 5.0
        rate = 10.0
        if key_name == "ll_bian_api":
            temp_result = []
            for each in result:
                temp_result.append([each[0], round(float(each[1]) * rate, 1)])
            result = temp_result
        return render(request, 'capitalcurve.html',
                      {'username': username, 'key_name': key_name, 'result': result})
    else:
        return redirect('/transaction/login/')


# 高频信息
def freq_info(request):
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')
        key_name = request.COOKIES.get("user", "")

        if request.method == "POST":
            # bn obj
            conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=settings.PWD, db='trade')
            cur = conn.cursor()
            sql = 'SELECT access_key, secret_key, pass_phrase FROM `key_table` where user_name = %s;'
            cur.execute(sql, key_name)
            key_tuple = cur.fetchone()
            conn.close()
            dm = BinanceDMService.BinanceDm(key_tuple[0], key_tuple[1], "https://fapi.binance.com/")
            # type
            kill_type = request.POST.get('kill_type', '')
            if kill_type == 'kill_one':
                # 根据输入id 验证是否属于key ( 撤销订单和仓位 删order-up dn id, 删trade-id )
                kill_id = request.POST.get('kill_id', '')
                sql_list = []
                arg_list = []
                # trade_usdt
                trade_usdt = request.POST.get('trade_usdt', 'no')
                if trade_usdt != "no":
                    sql_list.append("trade_usdt=%s")
                    arg_list.append(trade_usdt)
                # db_num -> strategy
                db_num = request.POST.get('db_num', 'no')
                if db_num != "no":
                    sql_list.append("strategy=%s")
                    arg_list.append(db_num)
                # cal_offset
                cal_offset = request.POST.get('cal_offset', 'no')
                if cal_offset != "no":
                    sql_list.append("cal_offset=%s")
                    arg_list.append(cal_offset)
                # syn_offset
                syn_offset = request.POST.get('syn_offset', 'no')
                if syn_offset != "no":
                    sql_list.append("syn_offset=%s")
                    arg_list.append(syn_offset)
                # 查询
                sql = 'update web_pos set {} where id=%s and user_name=%s;'.format(",".join(sql_list))
                arg_list += [kill_id, key_name]
                conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
                cur = conn.cursor()
                if sql_list != []: cur.execute(sql, arg_list)
                conn.commit()
                conn.close()
                return redirect('/transaction/freq_info/')
            elif kill_type == "insert":
                strategy = request.POST.get('strategy', 'no')
                trade_code = request.POST.get('trade_code', 'no')
                trade_usdt = request.POST.get('trade_usdt', 'no')
                db_num = request.POST.get('db_num', 'no')
                cal_offset = request.POST.get('cal_offset', 'no')
                syn_offset = request.POST.get('syn_offset', 'no')
                sql = 'insert into web_pos (user_name, strategy, trade_code, trade_usdt, db_num, cal_offset, syn_offset) value ' \
                      '(%s, %s, %s, %s, %s, %s, %s);'
                conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
                cur = conn.cursor()
                cur.execute(sql, [key_name, strategy, trade_code, trade_usdt, db_num, cal_offset, syn_offset])
                conn.commit()
                conn.close()
                return redirect('/transaction/freq_info/')
            elif kill_type == "delete":
                kill_id = request.POST.get('kill_id', '')
                sql = "delete from web_pos where id=%s and user_name=%s;"
                conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
                cur = conn.cursor()
                cur.execute(sql, [kill_id, key_name])
                conn.commit()
                conn.close()
                return redirect('/transaction/freq_info/')
            elif kill_type == 'kill_all':
                # 一键停止所有程序 清空所有仓位 删除数据库order(finish or web) 数据库trade(api_name)
                kill_pwd = request.POST.get('syn_offset', 'no')
                sql = 'update web_pos set syn_offset=%s where user_name=%s;'
                conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
                cur = conn.cursor()
                cur.execute(sql, [kill_pwd, key_name])
                conn.commit()
                conn.close()
                return redirect('/transaction/freq_info/')
            elif kill_type == 'freq_s':
                kill_pwd = request.POST.get('syn_offset', 'no')
                this_name = key_name.split("_")[0]
                if kill_pwd == "1":
                    os.popen("nohup /usr/bin/python3 /root/TradeDirs/freq/{}/{}_hfreq.py > /dev/null 2>&1 &".format(this_name, this_name))
                else:
                    os.popen("ps -ef | grep '"+this_name+"_hfreq.py' | awk '{print $2}' | xargs kill -9")
                return redirect('/transaction/ps_aux/')
            elif kill_type == 'kill_freq':
                # 一键停止所有程序 清空所有仓位 删除数据库order(finish or web) 数据库trade(api_name)
                user = key_name.split("_")[0]
                os.popen("nohup /usr/bin/python3 /root/TradeDirs/freq/{}/{}_stop.py > /dev/null 2>&1 &".format(user, user))
                return redirect('/transaction/bnwh/')
            else:
                return redirect('/transaction/freq_info/')
        else:
            sql = 'select id, user_name, strategy, trade_code, trade_usdt, db_num, cal_offset, syn_offset from web_pos where user_name=%s;'
            conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
            cur = conn.cursor()
            cur.execute(sql, key_name)
            freq_data = cur.fetchall()
            conn.close()
            # tl - 5.0
            rate = 10.0
            if key_name == "ll_bian_api":
                temp_data = []
                for each in freq_data:
                    temp_data.append([each[0], each[1], each[2], each[3], float(each[4]) * rate, float(each[5]) * rate, each[6], each[7]])
                freq_data = temp_data
            return render(request, 'freq_info.html', {'username': username, 'key_name': key_name, 'freq_tuple': freq_data})
    else:
        return redirect('/transaction/login/')


# 进程
def ps_aux(request):
    if request.session.get('username', '') != '':
        username = request.session.get('username', '')
        key_name = request.COOKIES.get("user", "")

        if request.method == "POST":
            this_type = request.POST.get('this_type', "")
            if this_type == "ps_aux":
                all_list = ["ws", "hg1", "bl1", "freq", "stop", "email"]
                bind_list = request.POST.getlist('bind', [])
                result = []
                for each in all_list:
                    if each in bind_list:
                        result.append("{}=1".format(each))
                    else:
                        result.append("{}=0".format(each))
                sql = 'update ps_aux set {} where user=%s;'.format(",".join(result))
                conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
                cur = conn.cursor()
                cur.execute(sql, key_name)
                conn.commit()
                conn.close()
                time.sleep(2.5)
                return redirect('/transaction/ps_aux/')
            elif this_type == "web_house":
                freq_num = request.POST.get("freq_num", "no")
                hg1_num = request.POST.get("hg1_num", "no")
                bl1_num = request.POST.get("bl1_num", "no")
                conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
                cur = conn.cursor()
                if freq_num != "no":
                    freq_num = float(freq_num)
                    sql = "update freq_param set trade_num_usd=%s where api_name=%s;"
                    cur.execute(sql, [freq_num, key_name])
                if hg1_num != "no":
                    hg1_num = float(hg1_num)
                    sql = "update web_house set usdt_hg1=%s,sign_hg1=0.0,order_hg1='[]',max_balance=0.0 where user_name=%s;"
                    cur.execute(sql, [hg1_num, key_name])
                if bl1_num != "no":
                    bl1_num = float(bl1_num)
                    sql = "update web_house set usdt_bl1=%s,sign_bl1=0.0,order_bl1='[]',max_balance=0.0 where user_name=%s;"
                    cur.execute(sql, [bl1_num, key_name])
                conn.commit()
                conn.close()
                return redirect('/transaction/ps_aux/')
            elif this_type == "wh_order":
                stop_num = request.POST.get("stop_num", "no")
                bl1_first = request.POST.get("bl1_first", "no")
                hg1_first = request.POST.get("hg1_first", "no")
                conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
                cur = conn.cursor()
                if stop_num != "no":
                    stop_num = float(stop_num)
                    sql = "update web_house set freq_stop=%s, max_balance=0.0 where user_name=%s;"
                    cur.execute(sql, [stop_num, key_name])
                if bl1_first != "no":
                    bl1_first = float(bl1_first)
                    select_sql = "select order_bl1 from web_house where user_name=%s;"
                    cur.execute(select_sql, key_name)
                    temp = cur.fetchone()[0]
                    orders = json.loads(temp)
                    order_temp = orders[0].split("_")
                    order_temp[2] = str(bl1_first)
                    orders[0] = "_".join(order_temp)
                    order_str = json.dumps(orders)
                    sql = "update web_house set order_bl1=%s where user_name=%s;"
                    cur.execute(sql, [order_str, key_name])
                if hg1_first != "no":
                    hg1_first = float(hg1_first)
                    select_sql = "select order_hg1 from web_house where user_name=%s;"
                    cur.execute(select_sql, key_name)
                    temp = cur.fetchone()[0]
                    orders = json.loads(temp)
                    order_temp = orders[0].split("_")
                    order_temp[2] = str(hg1_first)
                    orders[0] = "_".join(order_temp)
                    order_str = json.dumps(orders)
                    sql = "update web_house set order_hg1=%s where user_name=%s;"
                    cur.execute(sql, [order_str, key_name])
                conn.commit()
                conn.close()
                return redirect('/transaction/ps_aux/')
            else:
                return redirect('/transaction/ps_aux/')
        else:
            ps_info = os.popen("ps aux | grep {}_".format(key_name.split("_")[0])).readlines()
            conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
            cur = conn.cursor()
            cur.execute('select ws,hg1,bl1,freq,stop,email from ps_aux where user=%s;', key_name)
            ps_tuple = cur.fetchone()
            cur.execute('select sum(trade_num_usd)/count(trade_num_usd) from freq_param where api_name=%s;', key_name)
            fq_temp = cur.fetchone()[0]
            cur.execute('select freq_stop, max_balance, sign_bl1, usdt_bl1, order_bl1, sign_hg1, usdt_hg1, order_hg1 '
                        'from web_house where user_name=%s;', key_name)
            wh_temp = list(cur.fetchone())
            conn.close()
            if fq_temp != None:
                wh_temp.append(fq_temp)
            else:
                wh_temp.append(0)
            return render(request, 'ps_aux.html', {'username': username, 'key_name': key_name, 'ps_tuple': ps_tuple,
                                                   'web_house': wh_temp, 'ps_info': ps_info})
    else:
        return redirect('/transaction/login/')


# 用户api信息
def api_info(request):
    data = {"msg": "Url Error"}
    pwd = request.GET.get('pwd', '')
    if pwd == "liuwei":
        # 用户
        user = request.GET.get('user', '')
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=settings.PWD, db='trade')
        cur = conn.cursor()
        sql = 'SELECT access_key, secret_key, pass_phrase FROM `key_table` where user_name = %s;'
        cur.execute(sql, user)
        key_tuple = cur.fetchone()
        conn.close()
        # 交易对象，balance
        bm = BinanceDMService.BinanceDm(key_tuple[0], key_tuple[1], "https://fapi.binance.com/")
        # balance: 合约，现货，总资金状态
        balance_list = []
        bf = bm.get_account().get("assets", [])
        time.sleep(0.5)
        for b in bf:
            new_dict = {
                "asset": "{}_F".format(b["asset"]),
                "marginBalance": b["marginBalance"],
            }
            balance_list.append(new_dict)
        bs = bm.get_spot_balances()
        time.sleep(0.5)
        # ##
        symbol_dict = {"ZEC": 0.0, "XRP": 0.0, "LINK": 0.0, "BCH": 0.0, "LTC": 0.0, "ETH": 0.0, "ETC": 0.0}
        res = bm.get_spot_tick_price()
        for each in res:
            if each["symbol"] == "BTCUSDT":
                symbol_dict[each["symbol"].replace("BTC", "")] = 1.0 / float(each["price"])
            elif each["symbol"] in [name + "BTC" for name, price in symbol_dict.items()]:
                symbol_dict[each["symbol"].replace("BTC", "")] = float(each["price"])
        symbol_dict["BTC"] = 1.0
        sum_btc = 0.0
        for b in bs:
            if b["asset"] in [name for name, price in symbol_dict.items()]:
                sum_btc += (float(b["free"]) + float(b["locked"])) * symbol_dict[b["asset"]]
            new_dict = {
                "asset": "{}_S".format(b["asset"]),
                "marginBalance": b["free"],
                "positionInitialMargin": b["locked"],
            }
            balance_list.append(new_dict)
        balance_list.append({"asset": "BTC_A", "marginBalance": sum_btc, "positionInitialMargin": "0"})
        balance_list.append({"asset": "USDT_R", "marginBalance": key_tuple[2]})
        # transfer
        start_time = request.GET.get('start_time', "")
        start_time = "20200101000000" if start_time == "" else start_time
        end_time = request.GET.get('end_time', "")
        end_time = time.strftime("%Y%m%d") + "235959" if end_time == "" else end_time
        transfer_list = []
        res = bm.get_transfer("USDT", str(int(time.mktime(time.strptime(start_time, "%Y%m%d%H%M%S")) * 1000)),
                              str(int(time.mktime(time.strptime(end_time, "%Y%m%d%H%M%S")) * 1000)), "100").get("rows", [])
        time.sleep(0.5)
        for each in res:
            if each["status"] == "CONFIRMED":
                this_type = "S->F" if int(each["type"]) == 1 else "F->S"
                transfer_list.append([time.strftime("%Y%m%d%H%M%S", time.localtime(each["timestamp"] / 1000.0)),
                                      this_type, each["amount"]])
        # curve
        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='trade')
        cur = conn.cursor()
        sql = "SELECT this_time, balance FROM `key_balance` where user_name=%s ORDER BY this_time;"
        cur.execute(sql, user)
        temp = cur.fetchall()
        conn.close()
        curve = [[i, round(float(j), 1)] for i, j in temp]
        # 重构数据
        data = {
            "user": user,
            "balance": balance_list,
            "transfer": transfer_list,
            "curve": curve,
        }
        del bm
    return HttpResponse(str(data), content_type="application/json")


# 对接MT4接口
def mt4_update(request):
    pwd = request.GET.get('pwd', '')
    amount = request.GET.get('amount', '')
    if pwd == "liuwei" and amount != '':
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=settings.PWD, db='freq')
        cur = conn.cursor()
        sql = 'update web_pos set db_num=%s where trade_usdt = "MT4";'
        cur.execute(sql, amount)
        conn.commit()
        conn.close()
        return HttpResponse(str({"msg": "Success"}), content_type="application/json")
    return HttpResponse(str({"msg": "Url Error"}), content_type="application/json")


# 添加用户函数
def add_user(us, access, secret, google="", stime=""):
    try:
        # 判断用户名（首字母，长度）
        if len(us) < 2 or len(us) > 32:
            return {"code": 4001, "msg": "The length of user name should conform to 2-8"}
        us = us.lower()
        user = "{}_bian_api".format(us)
        u = user.split("_")[0]
        # 判断用户名（重复）
        if u in ("freq", "mysql", "sys", "trade", "web"):
            return {"code": 4003, "msg": "The user name already exists"}
        # conn
        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD)
        # trade
        conn.select_db("trade")
        # 判断是否存在
        cur = conn.cursor()
        cur.execute("select user_name from key_table group by user_name;")
        temp = cur.fetchall()
        conn.commit()
        cur.close()
        u_list = [each[0].split("_")[0] for each in temp]
        # 判断用户名（重复）
        if u in u_list:
            # 更新用户
            cur = conn.cursor()
            cur.execute("update key_table set access_key=%s, secret_key=%s where user_name=%s;",
                        [access, secret, user])
            conn.commit()
            cur.close()
            conn.close()
            return {"code": 200, "msg": "success"}
        else:
            # insert
            sql = "INSERT INTO `key_table` (user_name, access_key, secret_key, pass_phrase, stime)" \
                  " VALUE (%s,%s,%s,%s,%s);"
            cur = conn.cursor()
            cur.execute(sql, [user, access, secret, google, stime])
            conn.commit()
            cur.close()
            # 文件
            os.system("cp -r /root/TradeDirs/freq/back /root/TradeDirs/freq/{}".format(u))
            os.system("rename back {} /root/TradeDirs/freq/{}/*.py".format(u, u))
            # freq
            wh_sql = ('insert into web_house (user_name,trade_code,freq_stop,max_balance,'
                      'sign_bl1,usdt_bl1,order_bl1,sign_hg1,usdt_hg1,order_hg1) value '
                      '(%s,"ETHUSDT",1000000,0.0,0.0,0.0,"[]",0.0,0.0,"[]");')
            conn.select_db("freq")
            cur = conn.cursor()
            cur.execute(wh_sql, user)
            wp_sql = 'insert into web_pos (user_name,strategy,trade_code,trade_usdt,db_num,cal_offset,syn_offset) ' \
                     'value (%s,"big","no","250","no","no","0");'
            cur.execute(wp_sql, user)
            conn.commit()
            cur.close()
        # user
        create_sql = 'create database IF NOT EXISTS `{}`;'.format(u)
        cur = conn.cursor()
        cur.execute(create_sql)
        conn.commit()
        cur.close()
        # u
        sql1 = ("""
        CREATE TABLE `ws_orders` (
            `id` int(30) NOT NULL AUTO_INCREMENT,
            `user_name` varchar(100) DEFAULT NULL,
            `eventTime` varchar(100) DEFAULT NULL,
            `symbol` varchar(100) DEFAULT NULL,
            `clientOrderId` varchar(100) DEFAULT NULL,
            `side` varchar(100) DEFAULT NULL,
            `type` varchar(100) DEFAULT NULL,
            `origQty` varchar(100) DEFAULT NULL,
            `avgPrice` varchar(100) DEFAULT NULL,
            `orderStatus` varchar(100) DEFAULT NULL,
            `orderId` varchar(100) DEFAULT NULL,
            `cumulativeFilledQty` varchar(100) DEFAULT NULL,
            `no_repeat` varchar(255) DEFAULT NULL,
            PRIMARY KEY (`id`),
            UNIQUE KEY `no_repeat` (`no_repeat`),
            KEY `index_name` (`clientOrderId`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """)
        sql2 = ("""
        CREATE TABLE `freq_trade` (
            `id` int(20) NOT NULL AUTO_INCREMENT,
            `api_name` varchar(255) DEFAULT NULL,
            `trade_name` varchar(255) DEFAULT NULL,
            `trade_code` varchar(255) DEFAULT NULL,
            `first_price` varchar(255) DEFAULT NULL,
            `trade_arr` varchar(2550) DEFAULT NULL,
            `mid_index` varchar(255) DEFAULT NULL,
            `up_id` varchar(255) DEFAULT NULL,
            `down_id` varchar(255) DEFAULT NULL,
            `last_order` varchar(255) DEFAULT NULL,
            `sum_num` varchar(255) DEFAULT NULL,
            PRIMARY KEY (`id`),
            KEY `index_name` (`trade_code`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """)
        sql3 = ("""
        CREATE TABLE `freq_orders` (
            `id` int(20) NOT NULL AUTO_INCREMENT,
            `api_name` varchar(255) DEFAULT NULL,
            `trade_name` varchar(255) DEFAULT NULL,
            `trade_code` varchar(255) DEFAULT NULL,
            `handle` varchar(255) DEFAULT NULL,
            `side` varchar(255) DEFAULT NULL,
            `price` varchar(255) DEFAULT NULL,
            `quantity` varchar(255) DEFAULT NULL,
            `client_id` varchar(255) DEFAULT NULL,
            `trade_status` varchar(255) DEFAULT NULL,
            `web_status` varchar(255) DEFAULT NULL,
            `finish_status` varchar(255) DEFAULT NULL,
            PRIMARY KEY (`id`),
            KEY `index_name` (`client_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """)
        conn.select_db(u)
        cur = conn.cursor()
        cur.execute(sql1)
        cur.execute(sql2)
        cur.execute(sql3)
        conn.commit()
        cur.close()
        conn.close()
        return {"code": 200, "msg": "success"}
    except: return {"code": 500, "msg": "error"}


# 更新用户函数
def update_status(us, syn_offset, db_num="", trade_usdt=""):
    try:
        # 用户
        us = us.lower()
        user = "{}_bian_api".format(us)
        # conn
        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
        # 功能
        if syn_offset == "0":
            cur = conn.cursor()
            sql = 'update web_pos set syn_offset=%s where user_name=%s;'
            cur.execute(sql, [syn_offset, user])
            conn.commit()
            cur.close()
            info = {"code": 200, "msg": "success"}
        elif syn_offset == "1":
            # 参数必须为指定参数
            if trade_usdt in ("250", "500", "1000", "2500", "5000", "10000"):
                cur = conn.cursor()
                sql = 'update web_pos set syn_offset=%s, strategy=%s, trade_usdt=%s where user_name=%s;'
                cur.execute(sql, [syn_offset, db_num, trade_usdt, user])
                conn.commit()
                cur.close()
                info = {"code": 200, "msg": "success"}
            else:
                info = {"code": 4004, "msg": "Parameter does not match"}
        else:
            info = {"code": 4005, "msg": "Command exception"}
        conn.close()
        return info
    except: return {"code": 500, "msg": "error"}


# 验证
def create_sign(params_dict, secret_key):
    """ 生成 signature 参数 """
    signature = hmac.new(
        bytes(secret_key.encode('utf-8')),
        bytes(urllib.parse.urlencode(params_dict).encode('utf-8')),
        digestmod=hashlib.sha256
    ).hexdigest()
    return signature


# AES 解密后，去掉补足的空格用strip() 去掉
def decrypt(text):
    key = 'bdd-secret-key01'.encode('utf-8')
    cryptor = AES.new(key, AES.MODE_ECB)
    plain_text = cryptor.decrypt(a2b_hex(text.encode('utf-8')))
    d = bytes.decode(plain_text).rstrip('\0')
    return d


# bdd count
def get_count(request):
    if request.GET.get("pwd", "") == "bdd":
        sql = "select count(*) from web_pos where syn_offset = 1;"
        conn = pymysql.connect(host="127.0.0.1", port=3306, user='root', passwd=settings.PWD, db='freq')
        cur = conn.cursor()
        cur.execute(sql)
        temp = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return HttpResponse(temp[0])
    else:
        return HttpResponse("error")


# bdd status
def get_status(request):
    if request.GET.get("pwd", "") == "bdd":
        name = request.GET.get("name", "")
        temp = os.popen("ps -ef|grep " + name + "_freq.py|awk '{print $9}'")
        py_info = temp.read()
        if "/root/TradeDirs/freq/{}/{}_freq.py".format(name, name) in py_info: info = "1"
        else: info = "0"
        return HttpResponse(info)
    else:
        return HttpResponse("error")


# bdd
@csrf_exempt
def bdd(request):
    # 0.1、try
    try:
        # 1.1、判断 Method 请求方式
        if request.method == 'POST':
            #print(request.POST)
            # 2.1、判断 API KEY
            if request.META.get("HTTP_X_MBX_APIKEY", "") == "bdd":
                timestamp = float(request.POST.get("timestamp", 0.0))
                sys_time = time.time() * 1000
                #print(timestamp, sys_time)
                # 3.1、判断 timestamp 时间戳
                if timestamp >= sys_time - 5000 and timestamp <= sys_time + 1000:
                    # 4.1、判断 user 用户
                    user = request.POST.get("user", "")
                    if user != "":
                        # 5.1、判断 signature 数字签名
                        rp = {}
                        for i, j in request.POST.items():
                            if i != "signature": rp[i] = j
                        sys_sign = create_sign(rp, secret_key="bdd-secret-key01")
                        # print(rp, request.POST.get("signature", ""), sys_sign)
                        if request.POST.get("signature", "") == sys_sign:
                            """ 指令模块 START """
                            # 6.1、指令为添加用户
                            cmd = request.POST.get("cmd", "")
                            if cmd == "add_user":
                                access = request.POST.get("access", "")
                                secret = request.POST.get("secret", "")
                                # 6.1.1、判断是否参数存在
                                if access != "" and secret != "":
                                    # access secret 解密
                                    # print(user, access, secret, type(access))
                                    access = decrypt(access)
                                    secret = decrypt(secret)
                                    # print(user, access, secret)
                                    info = add_user(user, access, secret)
                                # 6.1.2、false
                                else: info = {"code": 4612, "msg": "Key cannot be empty"}
                            # 6.2、指令为修改状态
                            elif cmd == "update_status":
                                syn_offset = request.POST.get("syn_offset", "")
                                # 6.2.1、修改为关闭
                                if syn_offset == "0":
                                    info = update_status(user, syn_offset)
                                # 6.2.2、修改为开启
                                elif syn_offset == "1":
                                    risk = request.POST.get("risk", "")
                                    trade_usd = request.POST.get("trade_usd", "")
                                    # 6.2.2.1、判断是否参数存在
                                    if risk != "" and trade_usd != "":
                                        # print(user, risk, trade_usd)
                                        info = update_status(user, syn_offset, risk, trade_usd)
                                    # 6.2.2.1、false
                                    else: info = {"code": 4622, "msg": "Risk and trade_usd cannot be empty"}
                                # 6.2.3、false
                                else: info = {"code": 4623, "msg": "Start stop command error"}
                            # 6.3、false
                            else: info = {"code": 4630, "msg": "Cmd error"}
                            """ 指令模块 END """
                        # 5.2、false
                        else: info = {"code": 4520, "msg": "Digital signature exception"}
                    # 4.2、false
                    else: info = {"code": 4420, "msg": "The user name cannot be empty"}
                # 3.2、false
                else: info = {"code": 4320, "msg": "Timestamp exceeded"}
            # 2.2、false
            else: info = {"code": 4220, "msg": "Api key error"}
        # 1.2、false
        else: info = {"code": 4120, "msg": "Request method error"}
    # 0.2、false
    except: info = {"code": 500, "msg": "error"}
    return HttpResponse(json.dumps(info))
