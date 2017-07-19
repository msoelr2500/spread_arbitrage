# -*- coding:utf-8 -*-
import sys
sys.path.append('../')
from MyMdApi import *
import unittest
import myutils


class TestMdApi(unittest.TestCase):

    def setUp(self):
        instrument_type = "IH"
        brokerID, userID, password, mdapi_front, trade_front = myutils.get_account(0)
        logger = myutils.get_logger("spread_arbitrage", "logs/%s.log" % "MdApi_test")
        self._mdapi1 = my_mdapi(brokerID, userID, password, [myutils._Instruments[instrument_type][0]], logger)
        mdapi1.RegisterFront(mdapi_front)
        mdapi1.Init()
        time.sleep(1)

    def test_OnRtnDepthMarketData(self):

        self.assertIsInstance(self._mdapi1.depth_info.AskPrice1, float)


