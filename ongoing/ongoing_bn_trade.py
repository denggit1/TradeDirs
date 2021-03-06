# coding:utf-8

import os
import time
import pymysql
import logging


class UpdateHouse(object):
    def __init__(self):
        self.pwd = 'Mysql_123'
        self.conn_freq = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db="freq")
        self.all_dict = {}
        # 日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
                            filename="/root/TradeDirs/ongoing/logs/trade.log")
        self.logger = logging.getLogger()

    def run_conn_freq(self):
        try:
            self.conn_freq.ping()
            status = True
        except:
            status = False
        # 无法ping通时重连直到重连成功
        while status == False:
            try:
                self.conn_freq = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=self.pwd, db="freq")
                status = True
            except:
                status = False
            time.sleep(1)

    def get_all_info(self):
        self.run_conn_freq()
        cur = self.conn_freq.cursor()
        cur.execute("select user_name, syn_offset from web_pos;")
        temp_list = cur.fetchall()
        self.conn_freq.commit()
        cur.close()
        all_dict = {}
        for info in temp_list:
            name, offset = info
            user = name.split("_")[0]
            all_dict[user] = offset
        return all_dict

    def get_name_status(self, name):
        temp = os.popen("ps -ef|grep " + name + "_freq.py|awk '{print $9}'")
        py_info = temp.read()
        if "/root/TradeDirs/freq/{}/{}_freq.py".format(name, name) in py_info: info = "1"
        else: info = "0"
        return info

    def run(self):
        # 获取所有的dict
        all_dict = self.get_all_info()
        if all_dict != self.all_dict:
            self.logger.info("{} 更替".format("dict"))
            for name, value in all_dict.items():
                status = self.get_name_status(name)
                # print(name, value, status)
                # 执行开启或关闭
                if status != value:
                    if value == "1":
                        os.popen(
                            "nohup /usr/bin/python3 /root/TradeDirs/freq/{}/{}_start.py "
                            "> /dev/null 2>&1 &".format(name, name))
                        self.logger.info("{} 运行".format(name))
                    elif value == "0":
                        os.popen(
                            "nohup /usr/bin/python3 /root/TradeDirs/freq/{}/{}_stop.py "
                            "> /dev/null 2>&1 &".format(name, name))
                        self.logger.info("{} 停止".format(name))
                time.sleep(0.1)
            self.all_dict = all_dict
        return None

    def start(self):
        self.logger.info("初始化")
        while True:
            try: self.run()
            except Exception as e: print(e)
            time.sleep(1)


if __name__ == '__main__':
    uh = UpdateHouse()
    uh.start()

