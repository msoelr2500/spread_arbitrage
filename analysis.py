# -*- coding:utf-8 -*-

from WindPy import *
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt

def wind_to_df(wind_data):
    # wind导出的数据转为数据框
    df = pd.DataFrame(wind_data.Data).T
    df.index = wind_data.Times
    df.columns = wind_data.Fields
    return df

time_window = {
    "today": datetime.timedelta(0),
    "1day": datetime.timedelta(1),
    "2day": datetime.timedelta(2),
    "3day": datetime.timedelta(3),
    "7day": datetime.timedelta(10)
}

def data_extract(ic00, ic01):
    w.start()
    today = datetime.datetime.today()
    start_time = datetime.datetime(today.year, today.month, today.day, 9, 30, 0)
    start_time = start_time - datetime.timedelta(10)
    ic00_df = wind_to_df(w.wst(ic00, "bid1,ask1",str(start_time), today.strftime("%Y-%m-%d %H:%M:%S"), ""))
    ic01_df = wind_to_df(w.wst(ic01, "bid1,ask1", str(start_time), today.strftime("%Y-%m-%d %H:%M:%S"), ""))
    ic00_df.columns = ['ic00_bid1', 'ic00_ask1']
    ic01_df.columns = ['ic01_bid1', 'ic01_ask1']
    df_all = pd.merge(ic00_df, ic01_df, left_index=True, right_index=True)
    df_all["long_diff"] = df_all['ic00_ask1'] - df_all['ic01_bid1']
    df_all['short_diff'] = df_all['ic00_bid1'] - df_all['ic01_ask1']
    return df_all


def statistic_analysis(ic00, ic01):
    time_window_list = [0,1,2,3,5,7]
    df_all = data_extract(ic00, ic01)
    df_all['date'] = map(lambda x: x.date(), df_all.index)
    date_set = list(set([i.date() for i in df_all.index]))
    date_set = sorted(date_set, reverse=True)
    fig = plt.figure()
    ax1 = fig.add_subplot(321)
    ax2 = fig.add_subplot(322)
    ax3 = fig.add_subplot(323)
    ax4 = fig.add_subplot(324)
    ax5 = fig.add_subplot(325)
    ax6 = fig.add_subplot(326)
    ax_list = [ax1, ax2, ax3, ax4, ax5, ax6]
    for i, time_window in enumerate(time_window_list):
        select_date = date_set[:time_window+1]
        df_all['is_selected'] = map(lambda x: True if x in select_date else False, df_all['date'])
        temp = df_all.loc[df_all['is_selected'], :]
        temp.index = range(temp.shape[0])
        temp.to_csv("%s.csv" % time_window)
        print "-----------------------------  %s天 -----------------------------" % time_window
        print """long_diff:
\t Mean: %.2f \t Std: %.4f
\t Quantile: 1%%: %.2f,  2%%: %.2f,  5%%: %.2f, 10%%: %.2f
short_diff:
\t Mean: %.2f \t Std: %.4f
\t Quantile:99%%: %.2f, 98%%: %.2f, 95%%: %.2f, 90%%: %.2f""" % (np.mean(temp['long_diff']), np.std(temp['long_diff']), np.percentile(temp['long_diff'], 1),
               np.percentile(temp['long_diff'], 2), np.percentile(temp['long_diff'], 5),
               np.percentile(temp['long_diff'], 10),
               np.mean(temp['short_diff']), np.std(temp['short_diff']), np.percentile(temp['short_diff'], 99),
               np.percentile(temp['short_diff'], 98), np.percentile(temp['short_diff'], 95),
               np.percentile(temp['short_diff'], 90)
               )
        # print "----------------------------------------------------------------"
        temp[['long_diff', 'short_diff']].plot(ax = ax_list[i])
    plt.show()

ic00 = "IF1707.CFE"
ic01 = "IF1708.CFE"
statistic_analysis(ic00, ic01)
