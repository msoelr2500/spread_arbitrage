# -*- coding:utf-8 -*-
import time
import datetime
import myutils

class strategy():
    def __init__(self, mdapi1, mdapi2, trade, logger):
        self.mdapi1 = mdapi1
        self.mdapi2 = mdapi2
        self.tradeapi = trade
        self.logger = logger

    def Close(self):
        pass


class spread_arbitrage(strategy):

    def get_diff(self):
        """
        计算多头与空头价差
        :return:    (空头价差, 空头价差)
        """
        long_diff = self.tradeapi.ask_price_dict[self.tradeapi.instruimentIDs[0]] \
                    - self.tradeapi.bid_price_dict[self.tradeapi.instruimentIDs[1]]

        short_diff = self.tradeapi.bid_price_dict[self.tradeapi.instruimentIDs[0]] \
                    - self.tradeapi.ask_price_dict[self.tradeapi.instruimentIDs[1]]
        return long_diff, short_diff

    def max_price_update(self, long_diff, short_diff):
        """
        计算当前最小与最大价差
        :param long_diff:   多头价差
        :param short_diff:  空头价差
        """
        if long_diff < self.tradeapi.max_diff['long']:
            self.tradeapi.max_diff['long'] = long_diff
        if short_diff > self.tradeapi.max_diff['short']:
            self.tradeapi.max_diff['short'] = short_diff

    def offset(self, long_diff, short_diff):
        """
        平仓
        """
        if not self.tradeapi.position['situation']:                                                 # 如果上一期有仓位未平

            if long_diff <= self.tradeapi.threshold[0] and self.tradeapi.position['long'] > 0:      # 遇到多头平仓机会直接平多
                self.tradeapi.order(2)

            elif short_diff >= self.tradeapi.threshold[1] and self.tradeapi.position['short'] > 0:  # 遇到空头平仓机会直接平空
                self.tradeapi.order(3)

            if self.tradeapi.position['long'] == self.tradeapi.position['short'] == 0:              # 仓位平完后返回空仓状态
                self.tradeapi.position['situation'] = True

    def get_final_threshold(self, now_time):
        """
        两点半以后如果还未锁仓，根据开仓价格动态调整阈值，2点30时刚好赚预期的点数，3点时刚好赚0点
        :param now_time:    当前时间
        :return:            新的阈值
        """
        earn_point = self.tradeapi.threshold[1] - self.tradeapi.threshold[0]
        remaining_minute = 60 - now_time.minute
        return earn_point / 30.0 * remaining_minute

    def open_order(self, long_diff, short_diff):
        """
        开仓下单
        :param long_diff:    当前多头价差
        :param short_diff:   当前空头价差
        :return: 
        """
        if self.tradeapi.position['situation']: # 当标记为True时，意味着仓位已经平完

            if self.tradeapi.position['long'] == self.tradeapi.position['short']:   # 当多头与空头组合当前仓位相同时，进行开仓
                if long_diff <= self.tradeapi.threshold[0] and self.tradeapi.position['long'] < self.tradeapi.max_trade_time \
                        and self.tradeapi.count['long'] < (self.tradeapi.max_trade_time / 2):
                    self.tradeapi.order(0)
                    self.reference_diff = long_diff
                    if self.tradeapi.real_trade_flag:
                        self.tradeapi.count['long'] += 1                            # 记录开仓次数的计数器+1s
                elif short_diff >= self.tradeapi.threshold[1] and self.tradeapi.position['short'] < self.tradeapi.max_trade_time \
                        and self.tradeapi.count['short'] < (self.tradeapi.max_trade_time / 2):
                    self.tradeapi.order(1)
                    self.reference_diff = short_diff
                    if self.tradeapi.real_trade_flag:
                        self.tradeapi.count['short'] += 1


            else:
                if self.tradeapi.position['long'] > self.tradeapi.position['short']:
                    if short_diff >= self.tradeapi.threshold[1]:
                        self.tradeapi.order(1)
                    elif long_diff <= self.reference_diff - 3:  # 止损
                        self.logger.warning("空头止损！")
                        self.tradeapi.order(1)
                elif self.tradeapi.position['short'] > self.tradeapi.position['long']:
                    if long_diff <= self.tradeapi.threshold[0]:
                        self.tradeapi.order(0)
                    elif short_diff >= self.reference_diff + 3:  # 止损
                        self.logger.warning("空头止损！")
                        self.tradeapi.order(0)

            now_time = datetime.datetime.today()
            if now_time.time() > datetime.time(14, 30, 0, 0):                       # 到两点半后还未锁仓，则特殊处理
                if self.tradeapi.position['long'] > self.tradeapi.position['short']:
                    # 逐渐降低收益，完成锁仓
                    if short_diff - self.reference_diff >= self.get_final_threshold(now_time):
                        self.tradeapi.order(1)
                    # 强行锁仓，关闭风险敞口
                    elif now_time.time() > datetime.time(14, 57, 0, 0):
                        self.tradeapi.forward_growth = 1.0  # 强行锁仓不看近月涨跌
                        self.tradeapi.order(1)

                elif self.tradeapi.position['long'] < self.tradeapi.position['short']:
                    if -long_diff + self.reference_diff >= self.get_final_threshold(now_time):
                        self.tradeapi.order(0)
                    elif now_time.time() > datetime.time(14, 57, 0, 0):
                        self.tradeapi.forward_growth = -1.0
                        self.tradeapi.order(0)

                if self.tradeapi.position['long'] == self.tradeapi.position['short']:
                    self.tradeapi.position['situation'] = False
                    self.break_flag = True

            elif self.tradeapi.position['long'] == self.tradeapi.position['short'] == self.tradeapi.max_trade_time:
                self.tradeapi.position['situation'] = False
                self.break_flag = True

    def begin(self):
        dw = myutils.data_window(100, 50)
        self.break_flag = False
        self.reference_price = None
        while True:
            if self.tradeapi.real_trade_flag:
                time.sleep(2)

            if self.mdapi1.tick_change or self.mdapi2.tick_change:
                self.tradeapi.price_update()
                dw.add(self.mdapi1.depth_info.LastPrice)
                self.tradeapi.forward_growth = dw.is_grow()
                long_diff, short_diff = self.get_diff()
                self.max_price_update(long_diff, short_diff)

                self.logger.info("%.2f(%.2f, %.2f), %.2f(%.2f, %.2f), %s" % (
                            long_diff, self.tradeapi.max_diff['long'], self.tradeapi.threshold[0], short_diff,
                            self.tradeapi.max_diff['short'], self.tradeapi.threshold[1],self.tradeapi.forward_growth))

                # 首先平仓
                self.offset(long_diff, short_diff)

                # 然后开仓
                self.open_order(long_diff, short_diff)

                if self.break_flag:
                    break

            self.mdapi1.tick_change = False
            self.mdapi2.tick_change = False
        time.sleep(4)
        self.logger.info('多头价差头寸： %s, 空头价差头寸：%s' % (self.tradeapi.position['long'], self.tradeapi.position['short']))
        self.logger.info('============== 策略结束！ =============')





