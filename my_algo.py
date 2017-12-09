"""
MIT License

Copyright (c) 2017 Code Society

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from datetime import datetime, timedelta
import logging
import pandas as pd

from friartuck.api import OrderType

log = logging.getLogger("friar_tuck")


def initialize(context, data):
    log.info("hello, I am in initialize...")

    context.assets = []
    context.symbol_metadata = {}
    dataset = pd.read_csv("https://dl.dropboxusercontent.com/s/vz8cudbw6t9i04e/my_universe.csv?dl=0")
    for (index, series) in dataset.iterrows():
        asset = lookup_security(series["symbol"])
        context.symbol_metadata[asset] = series
        context.assets.append(asset)

    log.debug("symbol_metadata (%s)" % context.symbol_metadata)

    # timestamp of current handle_data event in environment timezone
    date = get_datetime()
    log.info("datetime: %s" % date)
    context.aapl = lookup_security("AAPL")
    context.wtw = lookup_security("WTW")
    context.fit = lookup_security("FIT")
    context.gevo = lookup_security("GEVO")
    context.czr = lookup_security("CZR")
    log.info(context.account)
    log.info(context.portfolio)
    log.info("pnl(%s)" % context.portfolio.pnl)
    for sec in context.portfolio.positions:
        log.info("symbol(%s) pos(%s) " % (sec.symbol, context.portfolio.positions[sec]))

    hist_quotes = data.history([context.aapl, context.wtw], frequency='15m', bar_count=1400, field=['open', 'close'])
    log.debug(hist_quotes)

    # fifteenMinInSecs = (15*60)
    now = datetime.now()
    multiples = int(now.minute/15)
    diff = now.minute-(multiples*15)
    next_trig = now + timedelta(minutes=(15-diff))

    log.info("next trigger:%s, mult:%s, diff:%s" % (next_trig, multiples, diff))
    # order_id = order_shares(security=context.czr, shares=1, order_type=OrderType(stop_price=15.51), time_in_force='gtc')
    # order_id = order_for_robinhood(context=context, security=context.fit, weight=1.0, order_type=OrderType(stop_price=6.56))
    # order_id = order_for_robinhood(context=context, security=context.gevo, weight=1.0, order_type=OrderType(stop_price=0.50))
    # order_id = order_shares(context.gevo, -1, order_type=OrderType(stop_price=0.50), time_in_force='gtc')
    # order_id = order_shares(context.fit, 1, order_type=OrderType(stop_price=6.04), time_in_force='gtc')
    # order = get_order(order_id)
    # log.info("order=%s" % order)

    # open_orders = get_open_orders()
    """
    last_orders_by_side = get_last_filled_orders_by_side(context.gevo)
    log.info("last_buy: %s" % last_orders_by_side["buy"])
    log.info("last_sell: %s" % last_orders_by_side["sell"])

    current_quote = data.current(context.aapl, field=['bid_price', 'ask_price'])
    log.info(current_quote)
    bid_price = data.current(context.aapl, field='bid_price')
    log.info("bid_price=(%s)" % bid_price)
    ask_price = data.current(context.aapl, field='ask_price')
    log.info("ask_price=(%s)" % ask_price)

    price = 13.18
    log.info("CZR price_convert_up_by_tick_size price(%s) converted (%s)" % (price, context.czr.price_convert_up_by_tick_size(price)))
    log.info("CZR price_convert_down_by_tick_size price(%s) converted (%s)" % (price, context.czr.price_convert_down_by_tick_size(price)))
    price = 162.76
    log.info("AAPL price_convert_up_by_tick_size price(%s) converted (%s)" % (price, context.aapl.price_convert_up_by_tick_size(price)))
    log.info("AAPL price_convert_down_by_tick_size price(%s) converted (%s)" % (price, context.aapl.price_convert_down_by_tick_size(price)))
    """

def on_market_open(context, data):
    log.info("on market open")
    pass


def handle_data(context, data):
    log.info("hello, I am in handle_data")

    current_quote = data.current(context.aapl, field=['close', 'open'])
    log.debug(current_quote)
    current_quote = data.current(context.wtw, field='close')
    log.debug(current_quote)

    current_quote = data.current([context.aapl, context.wtw], field='close')
    log.debug(current_quote)

    hist_quotes = data.history([context.aapl, context.wtw], frequency='1m', bar_count=10, field='close')
    log.debug(hist_quotes)

    log.debug(context.fit)
    current_data = data.current(context.fit, field=['close', 'price'])
    log.debug(current_data)

    #order_id = order_for_robinhood(context=context, security=context.fit, weight=1.0, order_type=OrderType(stop_price=6.56))
    #order = get_order(order_id)
    #log.info("order=%s" % order)

    """
    open_orders = get_open_orders(sec2)
    log.info("FIT open_orders=%s" % open_orders)
    
    open_orders = get_open_orders()
    log.info("ALL open_orders=%s" % open_orders)
    
    cancel_order(order_id)
    """


def order_for_robinhood(context, security, weight, order_type=None):
    """
    This is a custom order method for this particular algorithm and
    places orders based on:
    (1) How much of each position in context.assets we currently hold
    (2) How much cash we currently hold

    This means that if you have existing positions (e.g. AAPL),
    your positions in that security will not be taken into
    account when calculating order amounts.

    The portfolio value that we'll be ordering on is labeled
    `valid_portfolio_value`.

    If you'd like to use a Stop/Limit/Stop-Limit Order please follow the
    following format:
    STOP - order_type = OrderType(stop_price=y)
    LIMIT - order_type = OrderType(limit_price=x)
    STOPLIMIT - order_type = OrderType(limit_price=x, stop_price=y)
    """
    # We use .95 as the cash because all market orders are converted into
    # limit orders with a 5% buffer. So any market order placed through
    # Robinhood is submitted as a limit order with (last_traded_price * 1.05)
    valid_portfolio_value = context.portfolio.cash * .95

    # Calculate the percent of each security that we want to hold
    percent_to_order = weight - get_percent_held(context, security, valid_portfolio_value)

    # If within 1% of target weight, ignore.
    if abs(percent_to_order) < .01:
        log.info("Can't Make Order - Percent (%s) to order is less than 0.01 " % percent_to_order)
        return

    # Calculate the dollar value to order for this security
    value_to_order = percent_to_order * valid_portfolio_value
    if order_type:
        return order_value(security, value_to_order, order_type=order_type, time_in_force='gtc')
    else:
        return order_value(security, value_to_order, time_in_force='gtc')


def get_percent_held(context, security, portfolio_value):
    """
    This calculates the percentage of each security that we currently
    hold in the portfolio.
    """
    if security in context.portfolio.positions:
        position = context.portfolio.positions[security]
        value_held = position.last_sale_price * position.amount
        percent_held = value_held / float(portfolio_value)
        return percent_held
    else:
        # If we don't hold any positions, return 0%
        return 0.0