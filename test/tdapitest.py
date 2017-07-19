# -*- coding:utf-8 -*-
import sys
from ctp.futures import ApiStruct
import unittest
sys.path.append('../')
from MyTdApi import my_tdapi
from  MyMdApi import my_mdapi
from myutils import get_logger, _Instruments, get_account
import time


class TestTdApi(unittest.TestCase):

    def setUp(self):
        instrument_type = "IH"
        brokerID, userID, password, mdapi_front, trade_front = get_account(0)
        logger = get_logger("spread_arbitrage", "%s.log" % "mytdapi_test")

        mdapi1 = my_mdapi(brokerID, userID, password, [_Instruments[instrument_type][0]], logger)
        mdapi1.RegisterFront(mdapi_front)
        mdapi1.Init()
        time.sleep(1)
        mdapi2 = my_mdapi(brokerID, userID, password, [_Instruments[instrument_type][1]], logger)
        mdapi2.RegisterFront(mdapi_front)
        mdapi2.Init()
        time.sleep(5)
        logger.info('=========== 行情实例结束创建 ===========')

        self.trade = my_tdapi(broker_id=brokerID, investor_id=userID, passwd=password,
                         instrumentIDs=_Instruments[instrument_type], mdapi1=mdapi1,
                         mdapi2=mdapi2, logger=logger, left_position=0)
        self.trade.Create(pszFlowPath='TdFile/')
        self.trade.SubscribePrivateTopic(ApiStruct.TERT_RESTART)
        self.trade.SubscribePublicTopic(ApiStruct.TERT_RESTART)
        self.trade.RegisterFront(trade_front)
        self.trade.Init()
        time.sleep(5)


    def test_order_when_closed(self):
        def order_test(growth, order_type):
            self.trade.forward_growth = growth
            self.trade.order(order_type)

        # 确定趋势参数是否正确
        order_test(0, 0)
        self.assertFalse(self.trade.real_trade_flag)

        order_test(1, 0)
        self.assertFalse(self.trade.real_trade_flag)

        order_test(-1, 0)
        self.assertTrue(self.trade.real_trade_flag)

        order_test(0, 1)
        self.assertFalse(self.trade.real_trade_flag)

        order_test(-1, 1)
        self.assertFalse(self.trade.real_trade_flag)

        order_test(1, 1)
        self.assertTrue(self.trade.real_trade_flag)

        order_test(0, 2)
        self.assertFalse(self.trade.real_trade_flag)

        order_test(1, 2)
        self.assertFalse(self.trade.real_trade_flag)

        order_test(-1, 2)
        self.assertTrue(self.trade.real_trade_flag)

        order_test(0, 3)
        self.assertFalse(self.trade.real_trade_flag)

        order_test(-1, 3)
        self.assertFalse(self.trade.real_trade_flag)

        order_test(1, 3)
        self.assertTrue(self.trade.real_trade_flag)

if __name__ == '__main__':
    unittest.main()