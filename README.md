# 股指期货跨期价差套利

## 策略思想

根据股指期货跨期价差的长期平稳性进行日内套利

## 策略要点
- 阈值判断：根据分位数进行判断
- 追单
	- 首先根据近月合约涨跌确定是否交易，如果需要买入近月合约，则近月合约必须是跌的
	- 优先成交远月合约，不成则交易取消，成交则报单近月合约
	- 近月合约成交则交易结束，不成交则加滑点市价追单
- 限仓应对：每天平16手开16手，使利润最大化

## 接口

本策略调用Lovelylain的PyCTP接口，[https://github.com/lovelylain/pyctp](https://github.com/lovelylain/pyctp)
编译环境：Ubuntu17.04 x64, Anaconda

## 文件说明

- </a>**main.py** ： 主文件，修改其中参数并运行</a>
- **MyMdApi.py**： 行情接口文件，重写CTP接口中的函数
- **TdMdApi.py**： 交易接口文件
- **myutils.py**： 工具类，包括登陆参数，账户参数，合约代码参数，以及会在交易中用到的一些工具
- **strategy.py**： 策略类，包括一个策略的基类，以及当前策略的派生类
- **analysis.py**： 分析并获取当前股指期货分位数，需要在windows下且安装Wind的python接口时才能运行
- **jsonfile.json**： 存储阈值参数的序列化文件
- *ctpapi*文件夹： 本来是存放VNPY接口的，暂时用不到
- *logs*文件夹： 存放各个品种的日志
- *MdFile*文件夹： 存储行情数据
- *TdFile*文件夹： 存储交易数据
- *test*文件夹： 单元测试代码

## 如何运行
修改main.py中的三个参数
```python
account = myutils._NanHuaQiHuo
instrument_type = "IH"
left_position = 4
```
- **acount** 为登陆账户，目前提供如下三个账户：
	- SimNow_杨睿的账户：myutils._YangRui
	- SimNow_马朝阳的账户：myutils._MaZhaoYang
	- 南华期货账户：myutils._NanHuaQiHuo
- **instrument_type** 为合约品种，目前有"IH","IF","IC"
- **left_position** 为昨日遗留仓位，如果合约开满16手为4，一次套利为1

## Update List


## ToDo List
1. 止损条件设置
2. 设置可更改的、判断近期涨跌的时间窗体，当前时1分钟和2分钟线
3. 到期自动换仓，可能要加上判断流动性，按流动性高的先报单的逻辑
4. 近期涨跌判断条件该不该加，不加的化会怎么样
