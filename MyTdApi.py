# -*- coding:utf-8 -*-
from ctp.futures import ApiStruct, TraderApi
import myutils
import time

class my_tdapi(TraderApi):

    def __init__(self, broker_id,
                 investor_id, passwd, instrumentIDs, mdapi1, mdapi2, logger, left_position = 0):
        self.logger = logger                            # 日志器
        self.logger.info( '=========== 交易实例开始创建 ===========')
        self.broker_id = broker_id                      # 券商代码
        self.investor_id = investor_id                  # 用户代码
        self.passwd = passwd                            # 密码
        self.instruimentIDs =  instrumentIDs            # 合约品种
        self.mdapi1 = mdapi1                            # 近月行情
        self.mdapi2 = mdapi2                            # 远月行情
        if left_position == 0:                          # 存储当前持仓，true表示直接开仓，False表示先平后开，数字为对应价差组合数
            self.position = {"short": 0, "long": 0, "situation": True}
        else:
            self.position = {"short": left_position, "long": left_position, "situation": False}
        time.sleep(0.5)
        self.initial()

    def initial(self):
        """
        每次实例创建时需要初始化的变量（一般不改变）
        :return: 
        """
        self.logger.info("行情价格初始化中...")
        if self.broker_id == '9999':
            self.max_trade_time = 2                     # 最大套利次数，一次套利包括了四次交易，必须是偶数，simNow只支持IH2次
        else:
            self.max_trade_time = 4                     # 最大套利次数，一次套利包括了四次交易，必须是偶数，南华期货最多4次
        self.request_id = 0
        self.count = {'long':0, 'short':0}              # 开仓计数器，确保每天正向反向套利均发生两次
        self.order_follow_point = 1.0                   # 追单价差
        self.max_diff = {'long': 100.0, 'short': 0.0}   # 存储多头价差最小值，空头价差最大值
        self.ask_price_dict = {}                        # 卖价信息
        self.bid_price_dict = {}                        # 买价信息
        self.forward_growth = 0                         # 存储近月前几分钟K线涨跌情况（stragety中进行修改）
        self.price_update()

    def price_update(self):
        """
        每次跳价时需要 重新 初始化的变量
        """
        self.order_status_dict = {}                     # 存储每个合约品种与价格对应的成交状态
        self.real_trade_flag = False                    # 识别一次价差交易是否完整发生
        json_dict = myutils.jsonload()                  # 读取json文件中的阈值数据，如果出错，则沿用上一次，第一次读取不能错
        if json_dict != {}:
            self.threshold = json_dict[self.instruimentIDs[0][:2]]
        # 字典存储价格
        self.ask_price_dict[self.mdapi1.depth_info.InstrumentID] = self.mdapi1.depth_info.AskPrice1
        self.ask_price_dict[self.mdapi2.depth_info.InstrumentID] = self.mdapi2.depth_info.AskPrice1
        self.bid_price_dict[self.mdapi1.depth_info.InstrumentID] = self.mdapi1.depth_info.BidPrice1
        self.bid_price_dict[self.mdapi2.depth_info.InstrumentID] = self.mdapi2.depth_info.BidPrice1

    def wait(self, instrument, price):
        """
        确定报单返回成交或撤单其中之一
        :param instrument:  合约代码
        :param price:       交易价格
        """
        self.logger.info('等待服务器返回报单成交信息...')
        while (instrument, price) not in self.order_status_dict:            # 确定服务器返回了保单信息
            time.sleep(0.01)
        while True:
            if self.order_status_dict[(instrument, price)] in ['0', '5']:   # 确定服务器返回了成交(0)或是撤单(5)信息
                break
            time.sleep(0.01)

    def OnRspError(self, info, RequestId, IsLast):
        self.logger.error(myutils.decode(info.ErrorMsg))
        self.isErrorRspInfo(info)

    def isErrorRspInfo(self, info):
        if info.ErrorID != 0:
            self.logger.info("ErrorID= %s, ErrorMsg= %s", info.ErrorID, info.ErrorMsg)
        return info.ErrorID != 0

    def OnFrontDisConnected(self, reason):
        self.logger.info("onFrontDisConnected: %s", reason)

    def OnFrontConnected(self):
        self.logger.info('交易前置机连接成功!')
        self.logger.info('用户登录中... ...')
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    def user_login(self, broker_id, investor_id, passwd):
        req = ApiStruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)
        self.request_id += 1
        self.ReqUserLogin(req, self.request_id)

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        self.logger.info('用户登录成功!')
        self.logger.info('请求确认投资者结算结果...')
        #self.request_id += 1
        #self.ReqQrySettlementInfo(ApiStruct.QrySettlementInfo(self.broker_id, self.investor_id), self.request_id)
        #time.sleep(1)

        self.logger.info('开始账户查询:')
        self.request_id += 1
        self.ReqQryTradingAccount(ApiStruct.QryTradingAccount(self.broker_id, self.investor_id), self.request_id)
        time.sleep(1)

        self.request_id += 1
        self.ReqSettlementInfoConfirm(ApiStruct.SettlementInfoConfirm(self.broker_id, self.investor_id), self.request_id)
        time.sleep(1)

    def OnRspQrySettlementInfo(self, pSettlementInfo, pRspInfo, nRequestID, bIsLast):
        try:
            print myutils.decode(pSettlementInfo.Content)
        except:
            if pSettlementInfo == None:
                pass
            else:
                print pSettlementInfo.Content

    def OnRspSettlementInfoConfirm(self, pSettlementInfoConfirm, pRspInfo, nRequestID, bIsLast):
        self.logger.info('投资者结算结果确认完毕!')
        self.logger.info('\t确认日期: %s', pSettlementInfoConfirm.ConfirmDate)
        self.logger.info('\t确认时间: %s', pSettlementInfoConfirm.ConfirmTime)
        self.request_id += 1

        self.logger.info('开始持仓查询:')
        self.ReqQryInvestorPosition(
            ApiStruct.QryInvestorPosition(self.broker_id, self.investor_id, self.instruimentIDs[0]), self.request_id)
        time.sleep(1)

        self.request_id += 1
        self.ReqQryInvestorPosition(
            ApiStruct.QryInvestorPosition(self.broker_id, self.investor_id, self.instruimentIDs[1]), self.request_id)
        time.sleep(1)

    def OnRspQryInvestorPosition(self, pInvestorPosition, pRspInfo, nRequestID, bIsLast):
        self.logger.info('持仓查询结果:')
        self.logger.info('\t合约代码: %s', pInvestorPosition.InstrumentID)
        self.logger.info('\t持仓日期: %s', pInvestorPosition.PositionDate)
        self.logger.info('\t今日持仓: %s', pInvestorPosition.Position)
        self.logger.info('\t开仓量: %s, 开仓金额: %s' % (pInvestorPosition.OpenVolume, pInvestorPosition.OpenAmount))
        self.logger.info('\t平仓量: %s, 平仓金额: %s' % (pInvestorPosition.CloseVolume, pInvestorPosition.CloseAmount))
        self.logger.info('\t占用保证金: %s', pInvestorPosition.UseMargin)
        self.logger.info('持仓查询结束。')

    def OnRspQryTradingAccount(self, pTradingAccount, pRspInfo, nRequestID, bIsLast):
        self.logger.info('账户查询结果：')
        self.logger.info('利息收入：%s', pTradingAccount.Interest)
        self.logger.info('冻结的保证金：%s', pTradingAccount.FrozenMargin)
        self.logger.info('冻结的资金： %s', pTradingAccount.FrozenCash)
        self.logger.info('前保证金总额： %s', pTradingAccount.CurrMargin)
        self.logger.info('手续费： %s', pTradingAccount.Commission)
        self.logger.info('平仓盈亏： %s', pTradingAccount.CloseProfit)
        self.logger.info('持仓盈亏： %s', pTradingAccount.PositionProfit)
        self.logger.info('可用资金： %s', pTradingAccount.Available)
        self.available_capital = pTradingAccount.Available
        self.logger.info('可用资金： %s', pTradingAccount.Available)
        self.logger.info('账户查询结束。')

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        # 报单报错(无法提交）后返回
        self.logger.info("报单错误！无法提交")
        self.logger.info("报错内容： %s", myutils.decode(pRspInfo.ErrorMsg))

    def OnRtnOrder(self, pOrder):
        # 报单提交（可提交，但是有错）后返回
        self.order_status_dict[(pOrder.InstrumentID, pOrder.LimitPrice)] = pOrder.OrderStatus

        self.logger.info('-------------------------------------')
        self.logger.info('合约代码: %s', pOrder.InstrumentID)
        self.logger.info('价格: %s', pOrder.LimitPrice)
        self.logger.info('买卖方向: %s', pOrder.Direction)
        self.logger.info('数量: %s', pOrder.VolumeTotalOriginal)
        self.logger.info('报单提交状态: %s', pOrder.OrderSubmitStatus)
        """
        OSS_InsertSubmitted = '0' #已经提交
        OSS_CancelSubmitted = '1' #撤单已经提交
        OSS_ModifySubmitted = '2' #修改已经提交
        OSS_Accepted = '3' #已经接受
        OSS_InsertRejected = '4' #报单已经被拒绝
        OSS_CancelRejected = '5' #撤单已经被拒绝
        """
        self.logger.info('报单状态: %s', pOrder.OrderStatus)
        """
        OST_AllTraded = '0' #全部成交
        OST_PartTradedQueueing = '1' #部分成交还在队列中
        OST_PartTradedNotQueueing = '2' #部分成交不在队列中
        OST_NoTradeQueueing = '3' #未成交还在队列中
        OST_NoTradeNotQueueing = '4' #未成交不在队列中
        OST_Canceled = '5' #撤单
        """
        self.logger.info('报单日期: %s', pOrder.InsertDate)
        self.logger.info('委托时间: %s', pOrder.InsertTime)
        self.logger.info('状态信息: %s', myutils.decode(pOrder.StatusMsg))
        self.logger.info('报单价格条件: %s', pOrder.OrderPriceType)

    def OnRtnTrade(self, pTrade):
        # 交易成功后返回
        self.logger.info('-------------------------------------')
        self.logger.info("交易确认：----------------------------")
        self.logger.info('\t 合约代码: %s', pTrade.InstrumentID)
        self.logger.info('\t 买卖方向: %s', pTrade.Direction)
        self.logger.info('\t 开平标志: %s', pTrade.OffsetFlag)
        self.logger.info('\t 价格: %s', pTrade.Price)
        self.logger.info('\t 数量: %s', pTrade.Volume)
        self.logger.info('\t 成交时期: %s', pTrade.TradeDate)
        self.logger.info('\t 成交时间: %s', pTrade.TradeTime)

    def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
        self.logger.info("报单失败!: %s", pInputOrder, pRspInfo)

    def ReqOrderInsert2(self, InstrumentID, LimitPrice, Volumes, Direction = ApiStruct.D_Buy,
                       TimeCondition = ApiStruct.TC_IOC, CombOffsetFlag = ApiStruct.OF_Open, OrderPriceType = '2'):
        """
        OrderPriceType: #报单价格条件, char
            OPT_AnyPrice = '1' #任意价
            OPT_LimitPrice = '2' #限价
            OPT_BestPrice = '3' #最优价
            OPT_LastPrice = '4' #最新价
        Direction:
            D_Buy = '0' #买
            D_Sell = '1' #卖
        TimeCondition: #有效期类型, char
            TC_IOC = '1' #立即完成，否则撤销
            TC_GFS = '2' #本节有效
            TC_GFD = '3' #当日有效
            TC_GTD = '4' #指定日期前有效
            TC_GTC = '5' #撤销前有效
            TC_GFA = '6' #集合竞价有效
        CombOffsetFlag：
            OF_Open = '0' #开仓
            OF_Close = '1' #平仓
            OF_ForceClose = '2' #强平
            OF_CloseToday = '3' #平今
            OF_CloseYesterday = '4' #平昨
            OF_ForceOff = '5' #强减
            OF_LocalForceClose = '6' #本地强平
        VolumeCondition: #成交量类型, char
            VC_AV = '1' #任何数量
            VC_MV = '2' #最小数量
            VC_CV = '3' #全部数量
        ContingentCondition： #触发条件, char
            CC_Immediately = '1' #立即
            CC_Touch = '2' #止损
            CC_TouchProfit = '3' #止赢
            CC_ParkedOrder = '4' #预埋单
        ForceCloseReason：    #强平原因, char
            FCC_NotForceClose = '0' #非强平
            FCC_LackDeposit = '1' #资金不足
            FCC_ClientOverPositionLimit = '2' #客户超仓
            FCC_MemberOverPositionLimit = '3' #会员超仓
            FCC_NotMultiple = '4' #持仓非整数倍
            FCC_Violation = '5' #违规
            FCC_Other = '6' #其它
            FCC_PersonDeliv = '7' #自然人临近交割
        """
        self.request_id += 1
        self.ReqOrderInsert(ApiStruct.InputOrder(
            BrokerID=self.broker_id,
            InvestorID=self.investor_id,
            InstrumentID=InstrumentID,
            OrderRef='',
            UserID='',
            OrderPriceType=OrderPriceType,
            Direction=Direction,
            CombOffsetFlag=CombOffsetFlag,
            LimitPrice=LimitPrice,
            CombHedgeFlag='1',
            VolumeTotalOriginal=Volumes,
            TimeCondition=TimeCondition,
            GTDDate='',
            VolumeCondition='1',
            MinVolume=0,
            ContingentCondition='1',
            StopPrice=0.0,
            ForceCloseReason='0',
            # IsAutoSuspend=0,
            # BusinessUnit='',
            # RequestID=0,
            # UserForceClose=0,
            # IsSwapOrder=0
        ), self.request_id)
        self.wait(InstrumentID, LimitPrice)

    def get_order_parameter(self, order_type):
        """
        返回下单参数
        :param order_type:
            0: order_long, buy current sell forward
            1: order_short, sell current buy forward
            2: offset_long
            3: offset_short
        :return:
        """
        if order_type == 0:
            param = [(self.instruimentIDs[1], self.bid_price_dict[self.instruimentIDs[1]], ApiStruct.D_Sell,
                      ApiStruct.OF_Open),
                     (self.instruimentIDs[0], self.ask_price_dict[self.instruimentIDs[0]], ApiStruct.D_Buy,
                      ApiStruct.OF_Open),
                     self.forward_growth == -1]             # 做多近月时近月必须跌，否则无法追单
        elif order_type == 1:
            param = [(self.instruimentIDs[1], self.ask_price_dict[self.instruimentIDs[1]], ApiStruct.D_Buy,
                      ApiStruct.OF_Open),
                     (self.instruimentIDs[0], self.bid_price_dict[self.instruimentIDs[0]], ApiStruct.D_Sell,
                      ApiStruct.OF_Open),
                     self.forward_growth == 1]              # 做空近月时近月必须涨，否则无法追单
        elif order_type == 2:
            param = [(self.instruimentIDs[1], self.bid_price_dict[self.instruimentIDs[1]], ApiStruct.D_Sell,
                      ApiStruct.OF_Close),
                     (self.instruimentIDs[0], self.ask_price_dict[self.instruimentIDs[0]], ApiStruct.D_Buy,
                      ApiStruct.OF_Close),
                     self.forward_growth == -1]
        elif order_type == 3:
            param = [(self.instruimentIDs[1], self.ask_price_dict[self.instruimentIDs[1]], ApiStruct.D_Buy,
                      ApiStruct.OF_Close),
                     (self.instruimentIDs[0], self.bid_price_dict[self.instruimentIDs[0]], ApiStruct.D_Sell,
                      ApiStruct.OF_Close),
                     self.forward_growth == 1]
        else:
            raise Exception("Wrong Order Type")
        return param

    def get_follow_price(self, order_type, follow_price, ratio = 1):
        """
        根据下单类型返回**近月**追单价格
        :param order_type:      下单类型
        :param follow_price:    当前价格  
        :param ratio:           追单乘子
        :return:                追单价格
        """
        if order_type == 0 or order_type == 2:      # 做多近月时，出更高的买价去追单
            follow_price = follow_price + self.order_follow_point * ratio
        else:                                       # 做空近月时，出更低的卖价去追单
            follow_price = follow_price - self.order_follow_point * ratio
        return  follow_price

    def order_output(self, order_type, param, follow_price):
        """
        下单输出
        :param order_type:      下单类型 
        :param param:           下单参数
        :param follow_price:    追单价格
        """
        if order_type == 0:
            self.position['long'] += 1
            outputtext = " (开仓)买入:%s(%.2f), 卖出:%s(%.2f), 价差:%.2f"
        elif order_type == 1:
            self.position['short'] += 1
            outputtext = " (开仓)卖出:%s(%.2f), 买入:%s(%.2f), 价差:%.2f"
        elif order_type == 2:
            self.position['long'] -= 1
            outputtext = " (平仓)买入:%s(%.2f), 卖出:%s(%.2f), 价差:%.2f"
        else:
            self.position['short'] -= 1
            outputtext = " (平仓)卖出:%s(%.2f), 买入:%s(%.2f), 价差:%.2f"

        output_text = outputtext % (
            param[1][0],
            follow_price,
            param[0][0],
            param[0][1],
            follow_price - param[0][1]
        )
        self.logger.warning(output_text)

    def order(self, order_type):
        """
        下单
        :param order_type:  下单类型 
        """
        param = self.get_order_parameter(order_type)
        if param[2]:        # 确定近月的趋势
            self.ReqOrderInsert2(param[0][0], param[0][1], 1, param[0][2], ApiStruct.TC_IOC, param[0][3])
            if self.order_status_dict[(param[0][0], param[0][1])] == '5':
                self.logger.warning('远期未成交，已撤单。')
            else:
                follow_price = param[1][1]
                self.ReqOrderInsert2(param[1][0], follow_price, 1, param[1][2], ApiStruct.TC_IOC, param[1][3])
                if self.order_status_dict[(param[1][0], follow_price)] == '0':
                    self.real_trade_flag = True
                    self.logger.warning("近月直接成交！")
                else:
                    follow_price = self.get_follow_price(order_type, follow_price, 1)       # 1倍追单
                    self.ReqOrderInsert2(param[1][0], follow_price, 1, param[1][2], ApiStruct.TC_IOC, param[1][3])
                    if self.order_status_dict[(param[1][0], follow_price)] == '0':
                        self.logger.warning("近月一次追单成交！")
                        self.real_trade_flag = True
                    else:
                        follow_price = self.get_follow_price(order_type, follow_price, 10)  # 10倍追单
                        self.ReqOrderInsert2(param[1][0], follow_price, 1, param[1][2], ApiStruct.TC_IOC, param[1][3])
                        if self.order_status_dict[(param[1][0], follow_price)] == '0':
                            self.logger.warning("近月二次追单成交！")
                            self.real_trade_flag = True
                        else:
                            self.logger.warning("近月无法成交！")

            if self.real_trade_flag:
                self.order_output(order_type, param, follow_price)
        else:
            if order_type == 0 or order_type == 2:
                self.logger.info('近月非下降趋势，放弃该信号点。')
            else:
                self.logger.info('近月非上升趋势，放弃该信号点。')

    def have_enough_money(self):
        """
        每次套利第一次开仓前判断资金是否充足，以近月最新价的四倍（4次套利）作为所需资金
        """
        self.request_id += 1
        self.available_capital = 0.0
        self.ReqQryTradingAccount(ApiStruct.QryTradingAccount(BrokerID = self.broker_id,
                                                  InvestorID = self.investor_id), self.request_id)
        while self.available_capital == 0.0:
            print self.available_capital
            time.sleep(0.01)
        if self.instruimentIDs[0][:2] == "IC":
            need_capital = self.mdapi1.depth_info.LastPrice * 4 * 200 * 0.3
        else:
            need_capital = self.mdapi1.depth_info.LastPrice * 4 * 300 * 0.2

        if self.available_capital > (need_capital + 100000.0):
            return True
        else:
            return False


if __name__ == '__main__':
    import myutils
    from  MyMdApi import *

    instrument_type = "IH"
    brokerID, userID, password, mdapi_front, trade_front = myutils.get_account(0)
    logger = myutils.get_logger("spread_arbitrage", "%s.log" % instrument_type)

    mdapi1 = my_mdapi(brokerID, userID, password, [myutils._Instruments[instrument_type][0]], logger)
    mdapi1.RegisterFront(mdapi_front)
    mdapi1.Init()
    time.sleep(1)
    mdapi2 = my_mdapi(brokerID, userID, password, [myutils._Instruments[instrument_type][1]], logger)
    mdapi2.RegisterFront(mdapi_front)
    mdapi2.Init()
    time.sleep(5)
    logger.info('=========== 行情实例结束创建 ===========')
    trade = my_tdapi(broker_id=brokerID, investor_id=userID, passwd=password,
                     instrumentIDs=myutils._Instruments[instrument_type], mdapi1=mdapi1,
                     mdapi2=mdapi2, logger=logger, left_position=0)
    trade.Create(pszFlowPath='TdFile/')
    trade.SubscribePrivateTopic(ApiStruct.TERT_RESTART)
    trade.SubscribePublicTopic(ApiStruct.TERT_RESTART)
    trade.RegisterFront(trade_front)
    trade.Init()
    time.sleep(5)
    time1 = time.time()
    print trade.have_enough_money()
    print time.time() - time1
    trade.Join()
    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


















