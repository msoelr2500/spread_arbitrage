# -*- coding:utf-8 -*-
import logging
import sys
import json
import time


_MaZhaoYang = 0
_YangRui = 1
_NanHuaQiHuo = 2

_Instruments = {
"IC": ["IC1707", "IC1708"],
"IH": ["IH1707", "IH1708"],
"IF": ["IF1707", "IF1708"]
}

def decode(text):
    return text.decode('gb2312').encode('utf-8')

def get_logger(logger_name, output_file):
    logger = logging.getLogger(logger_name)
    # 指定logger输出格式
    formatter = logging.Formatter('%(asctime)s [%(levelname)-8s]: %(message)s')
    # 文件日志
    file_handler = logging.FileHandler(output_file)
    file_handler.setFormatter(formatter)  # 可以通过setFormatter指定输出格式
    # 控制台日志
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.formatter = formatter  # 也可以直接给formatter赋值
    # 为logger添加的日志处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    # 指定日志的最低输出级别，默认为WARN级别
    logger.setLevel(logging.INFO)
    return logger

def jsonload():
    try:
        with open('jsonfile.json', 'r') as f:
            data = json.load(f)
            return data
    except:
        return {}


class data_window():
    def __init__(self, total_length = 600, second_length = 120):
        self.length = total_length
        self.second_length = second_length
        self.datawindow = []

    def add(self, data):
        if self.datawindow == []:
            self.datawindow.append(data)
        else:
            while len(self.datawindow) > self.length - 1:
                self.datawindow.pop(0)
            self.datawindow.append(data)

    def is_grow(self):
        if len(self.datawindow) <= self.length - 1:
            return 0
        growth_1min = self.datawindow[-1] - self.datawindow[-120]
        growth_5min = self.datawindow[-1] - self.datawindow[0]
        if growth_1min > 0 and growth_5min > 0:
            return 1
        elif growth_1min < 0 and growth_5min < 0:
            return -1
        else:
            return 0

    def clear(self):
        self.datawindow = []

def get_account(account):
    """
    :param account:
        2: 南华期货
        1：杨睿_SimNow
        0：马朝阳_SimNow
        ...
    :return: 
    """
    if account == 2:
        # 南华期货
        brokerID = '1008'
        userID = '90095502'
        password = '222832'
        mdapi_front = 'tcp://115.238.106.253:41213'
        trade_front = 'tcp://115.238.106.253:41205'
    else:
        # simnow
        brokerID = b'9999'
        mdapi_front = b'tcp://180.168.146.187:10010'
        trade_front = b'tcp://180.168.146.187:10000'
        if account == 1:
            userID = b'097138'
            password = b'285135278'
        else:
            userID = b'092120'
            password = b'mzy187623'

    return brokerID, userID, password, mdapi_front, trade_front

if __name__ == '__main__':
    from unittest import TestCase
    