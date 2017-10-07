import schedule
import time
import datetime
import calendar
import traceback

import pandas as pd
import numpy as np
import logging

from abc import ABCMeta, abstractmethod, abstractproperty
from time import strftime
from datetime import datetime, timedelta
from friartuck.broker import RHBroker
from friartuck.Robinhood import Robinhood
from friartuck.quote_source import GoogleQuoteSource
from friartuck import utc_to_local
from collections import Iterable
from asyncio.tasks import sleep

log = logging.getLogger("friar_tuck")


class FriarContext:
    def __init__(self):
        self.is_market_open = False
        self.account = None
        self.portfolio = None


class Security:
    def __init__(self, symbol=None, is_tradeable=False, security_type=None, security_detail=None):
        self.symbol = symbol
        self.is_tradeable = is_tradeable
        self.security_type = security_type
        self.security_detail = {}  # this the raw hash
        if security_detail:
            self.security_detail = security_detail

    def __str__(self):
        return str(self.__dict__)


class FriarData:
    def __init__(self, friar_tuck_live):
        self.friar_tuck_live = friar_tuck_live

    """
    Params: 
        Security security[1...n]: can be a list
        Int bar_count: Number of quote records to return
        String frequency: 1m|1h|1d
        String field[1...n]: None=All, possible fields ["open","high","low","close","volume","price"] 
    """

    def history(self, security, bar_count=1, frequency="1d", field=None):
        return self.friar_tuck_live.history(security, bar_count, frequency, field)

    """
    Params: 
        Security security[1...n]: can be a list
        String field[1...n]: None=All, possible fields ["open","high","low","close","volume","price"] 
    """

    def current(self, security, field=None):
        return self.friar_tuck_live.current(security, field)

    def can_trade(self, security):
        return self.friar_tuck_live.can_trade(security)


class OrderType:
    def __init__(self, price=None, stop_price=None):
        self.price = price
        self.stop_price = stop_price

    def __str__(self):
        return str(self.__dict__)

    def is_market_order(self):
        if self.price or self.stop_price:
            return False
        return True


class Order:
    def __init__(self, id):
        self.id = id
        """
        Integer: The status of the order.
            0 = Open
            1 = Filled
            2 = Cancelled
            3 = Rejected
            4 = Held
        """
        self.status = None
        self.created = None
        self.stop = None
        self.limit = None
        self.amount = 0
        self.symbol = None
        self.filled = 0
        self.Commission = 0
        self.rejected_reason = None
        self.time_in_force = None

    def __str__(self):
        return str(self.__dict__)


class Position:
    def __init__(self, amount=0, cost_basis=0, last_sale_price=0):
        self.amount = amount
        self.cost_basis = cost_basis
        self.last_sale_price = last_sale_price

    def __str__(self):
        return str(self.__dict__)


class Portfolio:
    def __init__(self):
        self.capital_used = 0
        self.cash = 0
        self.pnl = 0
        self.positions = {}
        self.portfolio_value = 0
        self.positions_value = 0
        self.returns = 0
        self.starting_cash = 0
        self.start_date = None

    def __str__(self):
        return str(self.__dict__)


class Account:
    def __init__(self):
        self.accrued_interest = 0
        self.available_funds = 0
        self.buying_power = 0
        self.cushion = 0
        self.day_trades_remaining = 0
        self.equity_with_loan = 0
        self.excess_liquidity = 0
        self.initial_margin_requirement = 0
        self.leverage = 0
        self.maintenance_margin_requirement = 0
        self.net_leverage = 0
        self.net_liquidation = 0
        self.regt_equity = 0
        self.regt_margin = 0
        self.settled_cash = 0
        self.total_positions_value = 0

    def __str__(self):
        return str(self.__dict__)


class FriarTuckLive:
    broker = None
    context = None
    active_algo = None
    _active_datetime = None
    is_market_open = False
    # Protection from abuse
    _fetched_securities_cache = {}
    _next_data_reloadable_time = datetime.now()
    _initialized = False
    _market_closed_lastupdate = False
    _starting_cash = None
    _current_security_bars = {}
    _security_last_known_price = {}
    _order_status_map = {"queued": 0, "unconfirmed": 0, "confirmed": 0, "partially_filled": 0, "filled": 1, "cancelled": 2, "rejected": 3, "failed": 3}

    def __init__(self, user_name, password, data_frequency="1h", log_file=None):
        if not self._initialized:
            self._data_frequency = data_frequency
            self._active_datetime = datetime.now()
            # self._active_datetime = temp_datetime.replace(second=0, microsecond=0)
            # self.long_only=False
            self.quote_source = GoogleQuoteSource()
            self.context = FriarContext()
            self.rh_session = Robinhood();
            self.rh_session.login(username=user_name, password=password)
            self.broker = RHBroker(self.rh_session)
            self.friar_data = FriarData(self)

    def set_active_algo(self, active_algo):
        self._current_security_bars = {}
        self._load_all_data()
        self.active_algo = active_algo
        self.active_algo.initialize(self.context)

    def get_datetime(self):
        return self._active_datetime

    # block=True means the thread will not return,
    # if false it will return and the caller will need to keep the program from exiting, thus killing the engine
    def run_engine(self, block=True):
        if not self._initialized:
            self._time_interval_processor()
            self._initialized = True
            # self.active_algo.initialize(self.context)

            if block:
                while 1:
                    schedule.run_pending()
                    time.sleep(1)

                    # def lookup_security(self, symbol):
                    #   return self._fetch_and_build_security(symbol)

    def history(self, security, bar_count=1, frequency="1d", field=None):
        symbol_map = security_to_symbol_map(security)
        quotes = self.quote_source.fetch_quotes(symbol=symbol_map.keys(), bar_count=bar_count, frequency=frequency, field=field)

        if not isinstance(security, Iterable):
            return quotes[security.symbol]

        sec_quotes = {}
        for sym in quotes:
            sec_quotes[symbol_map[sym]] = quotes[sym]

        return sec_quotes

    def can_trade(self, security):
        return security.is_tradeable

    def current(self, security, field):
        now_secs = datetime.now().second
        if now_secs < 10:
            # we need to wait 10 seconds after the minute to load current data... this is so the source can be ready.
            time.sleep(10 - now_secs)

        if not isinstance(security, Iterable):
            if security not in self._current_security_bars:
                security_bars = self.history(security, bar_count=1, frequency=self._data_frequency, field=None)
                self._current_security_bars[security] = security_bars

            # print("price %s " % self._current_security_bars[security].iloc[-1]["price"])
            if self._current_security_bars[security] is not None and (not self._current_security_bars[security].empty or self._current_security_bars[security].iloc[-1]["price"] == float["nan"]):
                last_price_list = self.rh_session.get_quote_list(security.symbol, 'symbol,last_trade_price')
                if last_price_list and len(last_price_list) > 0:
                    if security in self._current_security_bars:
                        self._current_security_bars[security]["price"] = float(last_price_list[0][1])

            if not field:
                return self._current_security_bars[security].iloc[-1]
            return self._current_security_bars[security].iloc[-1][field]

        else:
            symbol_list_map = {}
            return_bars = {}
            for sec in security:
                symbol_list_map[sec.symbol] = sec
                if sec not in self._current_security_bars:
                    security_bars = self.history(sec, bar_count=1, frequency=self._data_frequency, field=None)
                    self._current_security_bars[sec] = security_bars[sec]

                if self._current_security_bars[sec] is not None and (not self._current_security_bars[sec].empty or self._current_security_bars[sec].iloc[-1]["price"] == float["nan"]):
                    last_price_list = self.rh_session.get_quote_list(sec.symbol, 'symbol,last_trade_price')
                    if last_price_list and len(last_price_list) > 0:
                        if sec in self._current_security_bars:
                            self._current_security_bars[sec]["price"] = float(last_price_list[0][1])

                if not field:
                    return_bars[sec] = self._current_security_bars[sec].iloc[-1]
                return_bars[sec] = self._current_security_bars[sec].iloc[-1][field]
            return return_bars

    def get_order(self, id):
        url = self.rh_session.endpoints['orders'] + id + "/"
        order_data = self.rh_session.get_url_content_json(url)

        return self._build_order_object(order_data, symbol=None)

    def get_open_orders(self, security=None):
        open_orders = {}
        order_data = self.rh_session.order_history()
        if order_data and "results" in order_data:
            for result in order_data["results"]:
                status = self._order_status_map[result["state"]]
                if status != 0:
                    # not open order
                    continue
                instrument = self.rh_session.get_url_content_json(result["instrument"])
                symbol = instrument["symbol"]
                if security and security.symbol != symbol:
                    # not for the the security desired
                    continue

                order = self._build_order_object(result, symbol)

                if symbol not in open_orders:
                    open_orders[symbol] = []

                open_orders[symbol].append(order)

        if security:
            if security.symbol in open_orders:
                return open_orders[security.symbol]
            return []

        return open_orders

    def cancel_order(self, order_id):
        url = self.rh_session.endpoints['orders'] + order_id + "/"
        order_data = self.rh_session.get_url_content_json(url)

        if order_data and "cancel" in order_data and order_data["cancel"]:
            self.rh_session.post_url_content_json(order_data["cancel"])

    def order_value(self, security, amount, order_type=None, time_in_force='gfd'):
        if order_type and order_type.stop_price:
            price = order_type.stop_price
        else:
            price = self.current(security, "price")

        shares = int(amount / price)

        return self.order_shares(security, shares, order_type, time_in_force)

    def order_shares(self, security, shares, order_type=None, time_in_force='gfd'):
        if not order_type:
            # Since an order type was not passed lets use MarketOrder
            order_type = OrderType()

        trigger = 'immediate'
        if order_type.stop_price:
            trigger = "stop"

        tran_type = 'market'
        if order_type.price:
            tran_type = "limit"

        transaction = "buy"
        if shares < 0:
            transaction = "sell"

        order_data = self.rh_session.place_order(security.security_detail, quantity=np.abs([shares])[0],
                                                 price=order_type.price, stop_price=order_type.stop_price,
                                                 transaction=transaction, trigger=trigger, order=tran_type,
                                                 time_in_force=time_in_force)

        if order_data and "reject_reason" in order_data and order_data["reject_reason"]:
            log.warning("Appears the order was rejected: %s" % order_data["reject_reason"])

        if order_data:
            return order_data['id']

        return None

    # def _set_long_only(self):
    #    self.long_only=True

    def _build_order_object(self, result, symbol=None):
        status = self._order_status_map[result["state"]]

        if not symbol:
            instrument = self.rh_session.get_url_content_json(result["instrument"])
            symbol = instrument["symbol"]

        order = Order(result["id"])
        order.status = status
        order.created = utc_to_local(datetime.strptime(result["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"))

        order.stop = None
        order.limit = None
        if result["trigger"] == "stop":
            order.stop = float(result["stop_price"])

        if result["type"] == "limit":
            order.limit = float(result["price"])

        order.amount = int(float(result["quantity"]))
        order.symbol = symbol
        order.filled = int(float(result["cumulative_quantity"]))
        order.Commission = float(result["fees"])
        order.rejected_reason = result["reject_reason"]
        order.time_in_force = result["time_in_force"]

        return order

    def fetch_and_build_security(self, symbol, sec_detail=None):
        if symbol in self._fetched_securities_cache:
            return self._fetched_securities_cache[symbol]

        if not sec_detail:
            sec_details = self.rh_session.instruments(symbol)
            if sec_details and len(sec_details) > 0:
                sec_detail = sec_details[0]

        if not sec_detail:
            return None

        # sec_detail = sec_details[0]
        symbol = sec_detail['symbol']
        is_tradeable = sec_detail['tradeable']
        type = sec_detail['type']

        sec = Security(symbol, is_tradeable, type, sec_detail)
        self._fetched_securities_cache[symbol] = sec
        return sec

    def _time_interval_processor(self):
        log.debug("In time interval processor")
        temp_datetime = datetime.now()
        self._active_datetime = temp_datetime.replace(second=0, microsecond=0)

        market_open_temp = self.is_market_open
        self._current_security_bars = {}
        if not self._load_all_data():
            # Load Data Failed... we can't go further until we get fresh data... bad things can happend if algo operate with stale data.
            # Set reload data again in 1 minute.
            log.debug("Data retrieval was adnormal we'll check again next minute to try again ")
            _set_trigger_timer(minute_interval=1, callback_function=self._time_interval_processor)
            return schedule.CancelJob

        # update context status
        self.context.is_market_open = self.is_market_open
        self.active_algo.handle_data(self.context, self.friar_data)
        if (not self._initialized or not market_open_temp) and self.is_market_open:
            # if market was not open and is now open... initialize algo
            try:
                if hasattr(self.active_algo, 'before_trading_start'):
                    self.active_algo.before_trading_start(self.context, self.friar_data)

                    # self.active_algo.handle_data(self.context, self.friar_data)
            except Exception as inst:
                log.error("Error occurred while invoking initialize: %s " % inst)
                traceback.print_exc()

        minutes_after_open_time = self.market_opens_at + timedelta(minutes=1)  # Adding one more call
        if market_open_temp and not self.is_market_open:
            # If market used to be open and at this update is now closed, we want to call handle_data one more time
            self._market_closed_lastupdate = True  # we want the algo to be called one more time.

        current_time = datetime.now()
        try:
            if (self.is_market_open and current_time >= minutes_after_open_time) or self._market_closed_lastupdate:  # current_time < minutes_after_close_time:
                self.active_algo.handle_data(self.context, self.friar_data)

                if self._market_closed_lastupdate:
                    self._market_closed_lastupdate = False
        except Exception as e:
            log.error("Error occurred while invoking handle_data: %s " % e)
            traceback.print_exc()

        if self._data_frequency == "1d":
            direct_time = self.market_closes_at
            if datetime.now() >= direct_time:
                market_info = self.rh_session.get_url_content_json(self.market_info["next_open_hours"])
                direct_time = utc_to_local(datetime.strptime(market_info["closes_at"], "%Y-%m-%dT%H:%M:%SZ"))

            direct_time = direct_time + timedelta(minutes=5)  # wait 5 minutes after market closes
        elif self._data_frequency == "1h":
            if not self.is_market_open and datetime.now() < self.market_opens_at:
                direct_time = self.market_opens_at
            elif not self.is_market_open and datetime.now() > self.market_closes_at:
                market_info = self.rh_session.get_url_content_json(self.market_info["next_open_hours"])
                direct_time = utc_to_local(datetime.strptime(market_info["opens_at"], "%Y-%m-%dT%H:%M:%SZ"))
            else:
                direct_time = datetime.now() + timedelta(hours=1)  # update every hour
                direct_time = direct_time.replace(minute=0, second=0, microsecond=0)
        else:
            direct_time = datetime.now() + timedelta(minutes=1)  # update every minute
            direct_time = direct_time.replace(second=0, microsecond=0)

        # log.debug("Interval Processing Done - Next Trigger %s" % direct_time)

        _set_trigger_timer(callback_function=self._time_interval_processor, direct_time=direct_time)
        return schedule.CancelJob

    def _load_all_data(self):
        current_time = datetime.now()
        if self._next_data_reloadable_time > current_time:
            return True

        try:
            self.__load_market_info()
        except Exception as e:
            log.error("Error occurred while loading market info: %s " % e)
            traceback.print_exc()
            if not self.market_opens_at or not self.market_closes_at:
                return False

        try:
            self.__load_profile_info()
        except Exception as e:
            log.error("Error occurred while loading profile info: %s " % e)
            traceback.print_exc()
            return False

        after_close_time = self.market_closes_at + timedelta(minutes=60)  # 1 hour after close
        before_open_time = self.market_opens_at - timedelta(minutes=120)  # 2hours before open

        if current_time > after_close_time or current_time < before_open_time:
            # we are in after hours, we don't want to tax the rh server, lets load less frequently
            self._next_data_reloadable_time = datetime.now() + timedelta(
                hours=1)  # Can't reload more than once within 1 hour
            self._next_data_reloadable_time = self._next_data_reloadable_time.replace(minute=0, second=0, microsecond=0)
        else:
            self._next_data_reloadable_time = datetime.now() + timedelta(
                seconds=10)  # Can't reload more than once within 10 seconds

        return True

    def __load_market_info(self):
        market_info = self.rh_session.market_info()
        if "opens_at" not in market_info or not market_info["opens_at"] or "closes_at" not in market_info or not market_info["closes_at"]:
            market_info = self.rh_session.get_url_content_json(market_info["next_open_hours"])

        self.market_info = market_info
        self.market_opens_at = utc_to_local(datetime.strptime(market_info["opens_at"], "%Y-%m-%dT%H:%M:%SZ"))
        self.market_closes_at = utc_to_local(datetime.strptime(market_info["closes_at"], "%Y-%m-%dT%H:%M:%SZ"))

        current_time = datetime.now()
        if (current_time >= self.market_opens_at) and (current_time < self.market_closes_at):
            self.is_market_open = True
        else:
            self.is_market_open = False

        log.debug("market opens_at=%s, closes_at=%s, now=%s, is_market_open=%s" % (self.market_opens_at, self.market_closes_at, current_time, self.is_market_open))

    def __load_profile_info(self):
        pos_infos = self.rh_session.positions()
        port_info = self.rh_session.portfolios()
        acct_info = self.rh_session.get_account()

        market_value = float(port_info["market_value"])
        cash = float(acct_info["cash"])
        portfolio_value = market_value + cash
        unsettled_funds = float(acct_info["unsettled_funds"])

        if not self._starting_cash:
            self._starting_cash = portfolio_value

        returns = 0
        if self._starting_cash and self._starting_cash > 0:
            returns = (portfolio_value - self._starting_cash) / self._starting_cash
        long_position_value = 0
        short_position_value = 0
        unrealized_pl = 0
        positions = {}
        if pos_infos and pos_infos["results"]:
            for result in pos_infos["results"]:
                amount = int(float(result["quantity"]))
                if amount == 0:
                    continue

                instrument = self.rh_session.get_url_content_json(result["instrument"])
                symbol = instrument["symbol"]
                security = self.fetch_and_build_security(symbol, sec_detail=instrument)
                last_price = self.current(security, field="price")
                if not last_price:
                    # Lets try again
                    last_price = self.current(security, field="price")

                if not last_price and security in self._security_last_known_price:
                    last_price = self._security_last_known_price[security]

                self._security_last_known_price[security] = last_price

                cost_basis = float(result["average_buy_price"])
                positions[security] = Position(amount, cost_basis, last_price)

                # position_value = position_value+(cost_basis*amount)
                if amount > 0:
                    unrealized_pl = unrealized_pl + ((last_price * amount) - (cost_basis * amount))
                    long_position_value = long_position_value + (cost_basis * amount)
                else:
                    unrealized_pl = unrealized_pl + ((cost_basis * np.abs([amount])) - (last_price * np.abs([amount])))
                    short_position_value = long_position_value + (cost_basis * np.abs([amount]))

        pnl = unrealized_pl + unsettled_funds
        leverage = 0
        net_leverage = 0
        if portfolio_value > 0:
            leverage = (long_position_value + short_position_value) / portfolio_value
            net_leverage = market_value / portfolio_value

        portfolio = Portfolio()
        portfolio.capital_used = portfolio_value - market_value
        portfolio.cash = cash
        portfolio.pnl = pnl
        portfolio.positions = positions
        portfolio.portfolio_value = portfolio_value
        portfolio.positions_value = market_value
        portfolio.returns = returns
        portfolio.starting_cash = self._starting_cash
        portfolio.start_date = None

        self.context.portfolio = portfolio

        account = Account()
        # account.accrued_interest=acct_info
        account.available_funds = cash
        account.buying_power = float(acct_info["buying_power"])
        account.cushion = cash / portfolio_value
        account.day_trades_remaining = float("inf")
        account.equity_with_loan = portfolio_value
        account.excess_liquidity = cash
        account.initial_margin_requirement = 0
        account.leverage = leverage
        account.maintenance_margin_requirement = 0
        account.net_leverage = net_leverage
        account.net_liquidation = portfolio_value
        account.regt_equity = cash
        account.regt_margin = float("inf")
        account.settled_cash = cash
        account.total_positions_value = market_value

        self.context.account = account


def _set_trigger_timer(callback_function, minute_interval=None, direct_time=None):
    log.debug("setting trigger direct_time=%s, minute_interval= %s " % (direct_time, minute_interval))
    if not minute_interval and not direct_time:
        log.error("Bad trigger timer request... one of the following is required (minute_interval, direct_time)")
        return

    if direct_time:
        dt = direct_time
    else:
        dt = datetime.now() + timedelta(minutes=minute_interval)  # update every minute
        dt = dt.replace(second=0, microsecond=0)

    str_time = dt.strftime("%H:%M")
    schedule.every().day.at(str_time).do(callback_function)


def security_to_symbol_map(security):
    if not isinstance(security, list):
        return {security.symbol: security}

    symbols = {}
    for sec in security:
        symbols[sec.symbol] = sec

    return symbols
