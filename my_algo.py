import logging
import pandas as pd

from friartuck.api import OrderType

log = logging.getLogger("friar_tuck")


def initialize(context):
    log.info("hello, I am in initialize...")

    context.assets = []
    context.symbol_metadata = {}
    dataset = pd.read_csv("https://dl.dropboxusercontent.com/s/cg8qzffg7yfyzk6/live_universe.csv?dl=0")
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
    log.info(context.account)
    log.info(context.portfolio)
    log.info("pnl(%s)" % context.portfolio.pnl)
    for sec in context.portfolio.positions:
        log.info("symbol(%s) pos(%s) " % (sec.symbol, context.portfolio.positions[sec]))


def before_trading_start(context, data):
    log.info("before trading starts")
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

    """    
    order_id = order_for_robinhood(context=context, security=context.fit, weight=1.0, order_type=OrderType(stop_price=6.56))
    order = get_order(order_id)
    log.info("order=%s" % order)
    """

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