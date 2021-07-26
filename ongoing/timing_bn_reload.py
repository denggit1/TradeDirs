# coding:utf-8

import os, time, logging


# 重启ws
def reload_ws(rate=2.0):
    text = os.popen('ps aux|grep -e "/usr/bin/python3 /root/TradeDirs/"|grep _ws.py').read()
    text_list = text.split("\n")
    new_list = [each.split() for each in text_list][:-1]
    for each in new_list:
        if float(each[2]) >= rate:
            os.popen("kill -9 {}".format(each[1]))
            time.sleep(0.5)
            os.popen("nohup /usr/bin/python3 {} > /dev/null 2>&1 &".format(each[-1]))
            logging.info("重启 {}".format(each[-1]))
            time.sleep(1)
    return None


if __name__ == '__main__':
    # 日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
                        filename="/root/TradeDirs/ongoing/logs/reload.log")
    logging.info("初始化")
    reload_ws(0.0)

