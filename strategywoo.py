
from zipline.pipeline import (Pipeline)
from zipline.pipeline.factors import (AverageDollarVolume, AnnualizedVolatility)
from pylivetrader.api import (attach_pipeline, pipeline_output)
#import iexfinance as iex
import numpy as np  # needed for NaN handling
#import math  # ceil and floor are useful for rounding
import pandas as pd

def initialize(context):
    pipe = Pipeline()
    volatility = AnnualizedVolatility(window_length=30)
    #pipe.set_screen(QTradableStocksUS())
    pipe.add(volatility,'VOL')
    attach_pipeline(pipe, 'pipe')
    schedule_function(flush_portfolio, date_rules.every_day(), time_rules.market_close())
    
    #set_slippage(slippage.FixedSlippage(spread=0))
    #set_commission(commission.PerShare(cost=0.000, min_trade_cost=0.00)) # 0.0003 and 0.00 is about the most we can pay right now for this.

    schedule_function(test_waters_beginning, date_rules.every_day(), time_rules.market_open(minutes=1))
    schedule_function(flush_orders, date_rules.every_day(), time_rules.market_open(minutes=2))
    schedule_function(order_list, date_rules.every_day(), time_rules.market_open(minutes=(3)))
    schedule_function(trade_market, date_rules.every_day(), time_rules.market_open(minutes=3))
    schedule_function(flush_orders, date_rules.every_day(), time_rules.market_open(minutes=7))
    schedule_function(flush_portfolio, date_rules.every_day(), time_rules.market_open(minutes=7))
    
    for i in range(7, 360, 6):
            schedule_function(test_waters_beginning, date_rules.every_day(), time_rules.market_open(minutes=i))
            schedule_function(flush_orders, date_rules.every_day(), time_rules.market_open(minutes=(i+1)))
            schedule_function(order_list, date_rules.every_day(), time_rules.market_open(minutes=(i+2)))
            schedule_function(trade_market, date_rules.every_day(), time_rules.market_open(minutes=i+2))
            schedule_function(flush_orders, date_rules.every_day(), time_rules.market_open(minutes=(i+6)))
            schedule_function(flush_portfolio, date_rules.every_day(), time_rules.market_open(minutes=(i+6)))

    schedule_function(flush_portfolio, date_rules.every_day(), time_rules.market_close(minutes=1))
    
        # API functions
def initialize_api(context):
    context.incr = 0
    context.sale_price = None
    set_slippage(FixedSlippage(spread=0))
    set_commission(commission.PerShare(cost=0.000, min_trade_cost=0.00)) # 0.0003 and 0.00 is about the most we can pay right now for this.

def before_trading_start(context, data):
    context.output = pipeline_output('pipe').nlargest(20, 'VOL')
    context.position_values = 1.0

def limit_order_price(price, up):
    delta=0.0005
    min_delta = 0.01
    if delta * price < min_delta:
        if up:
            return price + min_delta
        else:
            return price - min_delta
    else:
        if up:
            return float(int(price * (1.0 + delta) * 100))/100.0 # round to penny
        else:
            return float(int(price * (1.0 - delta) * 100))/100.0
        
    
def test_waters_beginning(context,data):
    context.currprice = data.current(context.output.index, 'price')
    
    context.order_list = []
    
    value = 10000/len(context.currprice)
    
    for stock in context.currprice.items():
        try:
            order_target(stock[0], value, style = LimitOrder(limit_order_price(stock[1], False)))
            order_target(stock[0], -value, style = LimitOrder(limit_order_price(stock[1], True)))
        except:            
            pass        

def test_waters(context,data):
    context.currprice = data.current(context.output.index,'price')
    
    value = 10000/len(context.currprice)
    
    for stock in context.currprice.items():
        if stock in context.order_list:
            try:
                order_target_value(stock[0], value, style = LimitOrder(limit_order_price(stock[1], False)))
                order_target_value(stock[0], -value, style = LimitOrder(limit_order_price(stock[1], True)))
            except:            
                pass
        
    for stock in context.currprice.items():
        if stock not in context.order_list:
            try:
                order_target_value(stock[0], value, style = LimitOrder(stock[1] - stock[1] * 0.05))
                order_target_value(stock[0], -value, style = LimitOrder(stock[1] + stock[1] * 0.05))
            except:            
                pass
            
    context.order_list = []
        
def order_list(context,data):   
    for stock, orders in get_open_orders().items():  
        for order in orders:
            cancel_order(order) 
            
    for stock in context.currprice.items():
        if stock[0] in context.portfolio.positions:
                context.order_list.append(stock)
       
    
def trade_market(context,data):
    order_list = context.order_list
    
    number = len(order_list)
    number_2 = len(context.currprice)
    
    loose = number_2 - number
        
    for stock in order_list:
        try:
            order_target_percent(stock[0], 0.75/float(number), \
                                 style=StopLimitOrder(limit_order_price(stock[1], False), \
                                                      stock[1] * 0.99))
            order_target_percent(stock[0], -0.75/float(number), \
                                 style=StopLimitOrder(limit_order_price(stock[1], True), \
                                                      stock[1] * 1.01))
        except:
            pass
            
    for stock in context.currprice.items():
        if stock not in order_list:
            try:
                order_target_percent(stock[0], 0.25/float(loose), \
                                     style = StopLimitOrder(stock[1] - stock[1]*0.05, \
                                                            stock[1] - stock[1]*0.10))
                order_target_percent(stock[0], -0.25/float(loose), \
                                     style = StopLimitOrder(stock[1] + stock[1]*0.05, \
                                                            stock[1] + stock[1]*0.10))
            except:
                pass
    
def flush_orders(context,data):
    for stock, orders in get_open_orders().items():  
        for order in orders:
            cancel_order(order)        
 
def flush_portfolio(context,data):
    for stock in context.portfolio.positions:
        order_target_percent(stock, 0)
