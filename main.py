# -*- coding:utf-8 -*-
from MyMdApi import *
from MyTdApi import *
from strategy import *
import myutils
import time

account = myutils._YangRui
instrument_type = "IH"
left_position = 0

# 账户：
brokerID, userID, password, mdapi_front, trade_front = myutils.get_account(account=account)

# 日志类
logger = myutils.get_logger("spread_arbitrage", "logs/%s.log" % instrument_type)

# 远月价差行情实例
mdapi1 = my_mdapi(brokerID, userID, password, [myutils._Instruments[instrument_type][0]], logger)
mdapi1.RegisterFront(mdapi_front)
mdapi1.Init()
time.sleep(1)

# 远月价差行情实例
mdapi2 = my_mdapi(brokerID, userID, password, [myutils._Instruments[instrument_type][1]], logger)
mdapi2.RegisterFront(mdapi_front)
mdapi2.Init()
time.sleep(5)
logger.info('=========== 行情实例结束创建 ===========')

# 交易实例
trade = my_tdapi(broker_id=brokerID, investor_id=userID, passwd=password,
                instrumentIDs=myutils._Instruments[instrument_type], mdapi1 = mdapi1,
                mdapi2 = mdapi2, logger=logger, left_position=left_position)
trade.Create(pszFlowPath = 'TdFile/')
trade.SubscribePrivateTopic(ApiStruct.TERT_RESTART)
trade.SubscribePublicTopic(ApiStruct.TERT_RESTART)
trade.RegisterFront(trade_front)
trade.Init()
time.sleep(5)

# 策略实例
logger.info('============== 策略开始！ =============')
strategy = spread_arbitrage(mdapi1, mdapi2, trade, logger)
strategy.begin()


try:
    while 1:
        time.sleep(1)
except KeyboardInterrupt:
    pass
