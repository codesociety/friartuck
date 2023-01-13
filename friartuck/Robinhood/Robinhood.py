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
"""Robinhood.py: a collection of utilities for working with Robinhood's Private API"""
import getpass
import logging
import warnings
from enum import Enum

import requests
import six
from six.moves.urllib.parse import unquote
from six.moves.urllib.request import getproxies
from six.moves import input
from . import exceptions as RH_exception
from _datetime import datetime

class Bounds(Enum):
    """enum for bounds in `historicals` endpoint"""
    REGULAR = 'regular'
    EXTENDED = 'extended'


class Transaction(Enum):
    """enum for buy/sell orders"""
    BUY = 'buy'
    SELL = 'sell'


class Robinhood:
    """wrapper class for fetching/parsing Robinhood endpoints"""
    endpoints = {
        "login": "https://api.robinhood.com/api-token-auth/",
        "logout": "https://api.robinhood.com/api-token-logout/",
        "investment_profile": "https://api.robinhood.com/user/investment_profile/",
        "accounts": "https://api.robinhood.com/accounts/",
        "ach_iav_auth": "https://api.robinhood.com/ach/iav/auth/",
        "ach_relationships": "https://api.robinhood.com/ach/relationships/",
        "ach_transfers": "https://api.robinhood.com/ach/transfers/",
        "applications": "https://api.robinhood.com/applications/",
        "dividends": "https://api.robinhood.com/dividends/",
        "edocuments": "https://api.robinhood.com/documents/",
        "instruments": "https://api.robinhood.com/instruments/",
        "margin_upgrades": "https://api.robinhood.com/margin/upgrades/",
        "markets": "https://api.robinhood.com/markets/",
        "market_info": "https://api.robinhood.com/markets/ARCX/hours/",
        "notifications": "https://api.robinhood.com/notifications/",
        "orders": "https://api.robinhood.com/orders/",
        "password_reset": "https://api.robinhood.com/password_reset/request/",
        "portfolios": "https://api.robinhood.com/portfolios/",
        "positions": "https://api.robinhood.com/positions/",
        "quotes": "https://api.robinhood.com/quotes/",
        "historicals": "https://api.robinhood.com/quotes/historicals/",
        "document_requests": "https://api.robinhood.com/upload/document_requests/",
        "user": "https://api.robinhood.com/user/",
        "watchlists": "https://api.robinhood.com/watchlists/",
        "news": "https://api.robinhood.com/midlands/news/",
        "fundamentals": "https://api.robinhood.com/fundamentals/",
    }

    session = None

    username = None

    password = None

    headers = None

    auth_token = None

    logger = logging.getLogger('Robinhood')
    logger.addHandler(logging.NullHandler())

    ##############################
    #Logging in and initializing
    ##############################

    def __init__(self):
        self.session = requests.session()
        self.session.proxies = getproxies()
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en;q=1, fr;q=0.9, de;q=0.8, ja;q=0.7, nl;q=0.6, it;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "X-Robinhood-API-Version": "1.0.0",
            "Connection": "keep-alive",
            "User-Agent": "Robinhood/823 (iPhone; iOS 7.1.2; Scale/2.00)"
        }
        self.session.headers = self.headers

    def login_prompt(self): #pragma: no cover
        """Prompts user for username and password and calls login()."""
        username = input("Username: ")
        password = getpass.getpass()
        return self.login(username=username, password=password)

    def login(
            self,
            username,
            password,
            mfa_code=None
        ):
        """save and test login info for Robinhood accounts

            Args:
        username (str): username
        password (str): password

        Returns:
            (bool): received valid auth token

        """

        self.username = username
        self.password = password
        payload = {
            'client_id': 'c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS',
            'expires_in': 86400,
            'grant_type': 'password',
            'password': self.password,
            'scope': 'internal',
            'username': self.username
        }

        if mfa_code:
            payload['mfa_code'] = mfa_code

        try:
            res = self.session.post('https://api.robinhood.com/oauth2/token/', data=payload, timeout=15)
            res.raise_for_status()
            data = res.json()
            print(data)
        except requests.exceptions.HTTPError:
            raise RH_exception.LoginFailed()

        if 'mfa_required' in data.keys():           # pragma: no cover
            raise RH_exception.TwoFactorRequired()  # requires a second call to enable 2FA

        if 'access_token' in data.keys():
            self.oauth_token = data['access_token']
            self.headers['Authorization'] = 'Bearer ' + self.oauth_token
            return True

        return False
    
    def loginOld(
            self,
            username,
            password,
            mfa_code=None
        ):
        """save and test login info for Robinhood accounts

        Args:
            username (str): username
            password (str): password

        Returns:
            (bool): received valid auth token

        """
        self.username = username
        self.password = password
        payload = {
            'password': self.password,
            'username': self.username
        }

        if mfa_code:
            payload['mfa_code'] = mfa_code

        try:
            res = self.session.post(
                self.endpoints['login'],
                data=payload
            )
            res.raise_for_status()
            data = res.json()
        except requests.exceptions.HTTPError as err_msg:
            print(err_msg)
            warnings.warn('Failed to log out ' + repr(err_msg))
            raise RH_exception.LoginFailed()

        if 'mfa_required' in data.keys():           #pragma: no cover
            raise RH_exception.TwoFactorRequired()  #requires a second call to enable 2FA

        if 'token' in data.keys():
            self.auth_token = data['token']
            self.headers['Authorization'] = 'Token ' + self.auth_token
            return True

        return False

    def logout(self):
        """logout from Robinhood

        Returns:
            (:obj:`requests.request`) result from logout endpoint

        """
        try:
            req = self.session.post(self.endpoints['logout'])
            req.raise_for_status()
        except requests.exceptions.HTTPError as err_msg:
            warnings.warn('Failed to log out ' + repr(err_msg))

        self.headers['Authorization'] = None
        self.auth_token = None

        return req

    ##############################
    #GET DATA
    ##############################

    def get_url_content_json(self, url):
        """fetch url content"""
        res = self.session.get(url)
        res.raise_for_status()  #will throw without auth
        data = res.json()
        return data

    def post_url_content_json(self, url):
        """fetch url content"""
        res = self.session.post(url)
        res.raise_for_status()  #will throw without auth
        data = res.json()
        return data

    def investment_profile(self):
        """fetch investment_profile"""
        res = self.session.get(self.endpoints['investment_profile'])
        res.raise_for_status()  #will throw without auth
        data = res.json()
        return data

    def instruments(self, symbol):
        ''' Generates an instrument object. Currently this is only used for 
        placing orders, and generating and using the instrument object are handled
        for you, so you can ignore this method'''
        res = self.session.get(self.endpoints['instruments'], params={'query':symbol.upper()})
        print(self.endpoints['instruments'])
        if res.status_code == 200:
            return res.json()['results']
        else:
            print(res.content)
            raise Exception("Could not generate instrument object: %s " % res.headers)

    def market_info(self):
        """fetch market info using one of the prominent exchanges

        Args:

        Returns:
            (:obj:`dict`): JSON contents from `quotes` endpoint

        """
        current_date_str  = datetime.now().strftime("%Y-%m-%d")
        url = str(self.endpoints['market_info']) + current_date_str + "/"
        try:
            req = requests.get(url)
            req.raise_for_status()
            data = req.json()
        except requests.exceptions.HTTPError:
            raise NameError('Invalid Query: ' + stock) #TODO: custom exception

        return data

    def quote_data(self, stock=''):
        """fetch stock quote

        Args:
            stock (str): stock ticker, prompt if blank

        Returns:
            (:obj:`dict`): JSON contents from `quotes` endpoint

        """
        url = None
        if stock.find(',') == -1:
            url = str(self.endpoints['quotes']) + str(stock) + "/"
        else:
            url = str(self.endpoints['quotes']) + "?symbols=" + str(stock)
        #Check for validity of symbol
        try:
            res = self.session.get(url)
            res.raise_for_status()  # auth required
            data = res.json()
        except requests.exceptions.HTTPError:
            raise NameError('Invalid Symbol: ' + stock) #TODO: custom exception

        return data

    # We will keep for compatibility until next major release
    def quotes_data(self, stocks):
        """Fetch quote for multiple stocks, in one single Robinhood API call

        Args:
            stocks (list<str>): stock tickers

        Returns:
            (:obj:`list` of :obj:`dict`): List of JSON contents from `quotes` endpoint, in the
            same order of input args. If any ticker is invalid, a None will occur at that position.
        """
        url = str(self.endpoints['quotes']) + "?symbols=" + ",".join(stocks)
        try:
            req = requests.get(url)
            req.raise_for_status()
            data = req.json()
        except requests.exceptions.HTTPError:
            raise NameError('Invalid Symbols: ' + ",".join(stocks)) #TODO: custom exception

        return data["results"]

    def get_quote_list(self, stock='', key=''):
        """Returns multiple stock info and keys from quote_data (prompt if blank)

        Args:
            stock (str): stock ticker (or tickers separated by a comma)
            , prompt if blank
            key (str): key attributes that the function should return

        Returns:
            (:obj:`list`): Returns values from each stock or empty list
                           if none of the stocks were valid

        """
        #Creates a tuple containing the information we want to retrieve
        def append_stock(stock):
            keys = key.split(',')
            myStr = ''
            for item in keys:
                myStr += str(stock[item]) + ","
            return (myStr.split(','))
        #Prompt for stock if not entered
        if not stock:   #pragma: no cover
            stock = input("Symbol: ")
        data = self.quote_data(stock)
        res = []
        # Handles the case of multple tickers
        if stock.find(',') != -1:
            for stock in data['results']:
                if stock == None:
                    continue
                res.append(append_stock(stock))
        else:
            res.append(append_stock(data))
        return res

    def get_quote(self, stock=''):
        """wrapper for quote_data"""
        data = self.quote_data(stock)
        return data["symbol"]

    def get_historical_quotes(
            self,
            stock,
            interval,
            span,
            bounds=Bounds.REGULAR
        ):
        """fetch historical data for stock

        Note: valid interval/span configs
            interval = 5minute | 10minute + span = day, week
            interval = day + span = year
            interval = week
            TODO: NEEDS TESTS

        Args:
            stock (str): stock ticker
            interval (str): resolution of data
            span (str): length of data
            bounds (:enum:`Bounds`, optional): 'extended' or 'regular' trading hours

        Returns:
            (:obj:`dict`) values returned from `historicals` endpoint

        """
        if isinstance(bounds, str): #recast to Enum
            bounds = Bounds(bounds)

        symbols = stock
        if isinstance(symbols, list):
            symbols = ','.join(stock).upper()
            
        params = {
            'symbols': symbols,
            'interval': interval,
            'span': span,
            'bounds': bounds.name.lower()
        }
        res = self.session.get(
            self.endpoints['historicals'],
            params=params
        )
        return res.json()

    def get_news(self, stock):
        """fetch news endpoint
        Args:
            stock (str): stock ticker

        Returns:
            (:obj:`dict`) values returned from `news` endpoint

        """
        return self.session.get(self.endpoints['news']+stock.upper()+"/").json()

    def print_quote(self, stock=''):    #pragma: no cover
        """print quote information
        Args:
            stock (str): ticker to fetch

        Returns:
            None

        """
        data = self.get_quote_list(stock,'symbol,last_trade_price')
        for item in data:
            quote_str = item[0] + ": $" + item[1]
            print(quote_str)
            self.logger.info(quote_str)

    def print_quotes(self, stocks): #pragma: no cover
        """print a collection of stocks

        Args:
            stocks (:obj:`list`): list of stocks to pirnt

        Returns:
            None

        """
        for stock in stocks:
            self.print_quote(stock)

    def ask_price(self, stock=''):
        """get asking price for a stock

        Note:
            queries `quote` endpoint, dict wrapper

        Args:
            stock (str): stock ticker

        Returns:
            (float): ask price

        """
        return self.get_quote_list(stock,'ask_price')

    def ask_size(self, stock=''):
        """get ask size for a stock

        Note:
            queries `quote` endpoint, dict wrapper

        Args:
            stock (str): stock ticker

        Returns:
            (int): ask size

        """
        return self.get_quote_list(stock,'ask_size')

    def bid_price(self, stock=''):
        """get bid price for a stock

        Note:
            queries `quote` endpoint, dict wrapper

        Args:
            stock (str): stock ticker

        Returns:
            (float): bid price

        """
        return self.get_quote_list(stock,'bid_price')

    def bid_size(self, stock=''):
        """get bid size for a stock

        Note:
            queries `quote` endpoint, dict wrapper

        Args:
            stock (str): stock ticker

        Returns:
            (int): bid size

        """
        return self.get_quote_list(stock,'bid_size')

    def last_trade_price(self, stock=''):
        """get last trade price for a stock

        Note:
            queries `quote` endpoint, dict wrapper

        Args:
            stock (str): stock ticker

        Returns:
            (float): last trade price

        """
        return self.get_quote_list(stock,'last_trade_price')

    def previous_close(self, stock=''):
        """get previous closing price for a stock

        Note:
            queries `quote` endpoint, dict wrapper

        Args:
            stock (str): stock ticker

        Returns:
            (float): previous closing price

        """
        return self.get_quote_list(stock,'previous_close')

    def previous_close_date(self, stock=''):
        """get previous closing date for a stock

        Note:
            queries `quote` endpoint, dict wrapper

        Args:
            stock (str): stock ticker

        Returns:
            (str): previous close date

        """
        return self.get_quote_list(stock,'previous_close_date')

    def adjusted_previous_close(self, stock=''):
        """get adjusted previous closing price for a stock

        Note:
            queries `quote` endpoint, dict wrapper

        Args:
            stock (str): stock ticker

        Returns:
            (float): adjusted previous closing price

        """
        return self.get_quote_list(stock,'adjusted_previous_close')

    def symbol(self, stock=''):
        """get symbol for a stock

        Note:
            queries `quote` endpoint, dict wrapper

        Args:
            stock (str): stock ticker

        Returns:
            (str): stock symbol

        """
        return self.get_quote_list(stock,'symbol')

    def last_updated_at(self, stock=''):
        """get last update datetime

        Note:
            queries `quote` endpoint, dict wrapper

        Args:
            stock (str): stock ticker

        Returns:
            (str): last update datetime

        """
        return self.get_quote_list(stock,'last_updated_at')
        #TODO: recast to datetime object?

    def get_account(self):
        """fetch account information

        Returns:
            (:obj:`dict`): `accounts` endpoint payload

        """
        res = self.session.get(self.endpoints['accounts'])
        res.raise_for_status()  #auth required
        res = res.json()
        return res['results'][0]

    def get_url(self, url):
        """flat wrapper for fetching URL directly"""
        return self.session.get(url).json()

    ##############################
    #GET FUNDAMENTALS
    ##############################

    def get_fundamentals(self, stock=''):
        """find stock fundamentals data

        Args:
            (str): stock ticker

        Returns:
            (:obj:`dict`): contents of `fundamentals` endpoint

        """
        try:
            return self.session.get(self.endpoints['fundamentals']+stock.upper()+"/").json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise RobinhoodException("Invalid stock ticker")
            else:
                raise e


    def fundamentals(self, stock=''):
        """wrapper for get_fundamentlals function"""
        return self.get_fundamentals(stock)

    ##############################
    # PORTFOLIOS DATA
    ##############################

    def portfolios(self):
        """Returns the user's portfolio data."""
        req = self.session.get(self.endpoints['portfolios'])
        req.raise_for_status()
        return req.json()['results'][0]

    def adjusted_equity_previous_close(self):
        """wrapper for portfolios

        get `adjusted_equity_previous_close` value

        """
        return float(self.portfolios()['adjusted_equity_previous_close'])

    def equity(self):
        """wrapper for portfolios

        get `equity` value

        """
        return float(self.portfolios()['equity'])

    def equity_previous_close(self):
        """wrapper for portfolios

        get `equity_previous_close` value

        """
        return float(self.portfolios()['equity_previous_close'])

    def excess_margin(self):
        """wrapper for portfolios

        get `excess_margin` value

        """
        return float(self.portfolios()['excess_margin'])

    def extended_hours_equity(self):
        """wrapper for portfolios

        get `extended_hours_equity` value

        """
        try:
            return float(self.portfolios()['extended_hours_equity'])
        except TypeError:
            return None

    def extended_hours_market_value(self):
        """wrapper for portfolios

        get `extended_hours_market_value` value

        """
        try:
            return float(self.portfolios()['extended_hours_market_value'])
        except TypeError:
            return None

    def last_core_equity(self):
        """wrapper for portfolios

        get `last_core_equity` value

        """
        return float(self.portfolios()['last_core_equity'])

    def last_core_market_value(self):
        """wrapper for portfolios

        get `last_core_market_value` value

        """
        return float(self.portfolios()['last_core_market_value'])

    def market_value(self):
        """wrapper for portfolios

        get `market_value` value

        """
        return float(self.portfolios()['market_value'])

    def order_history(self):
        """wrapper for portfolios

        get orders from account

        """
        return self.session.get(self.endpoints['orders']).json()

    def dividends(self):
        """wrapper for portfolios

        get dividends from account

        """
        return self.session.get(self.endpoints['dividends']).json()

    ##############################
    # POSITIONS DATA
    ##############################

    def positions(self):
        """Returns the user's positions data."""
        return self.session.get(self.endpoints['positions']).json()

    def securities_owned(self):
        """
        Returns a list of symbols of securities of which there are more
        than zero shares in user's portfolio.
        """
        return self.session.get(self.endpoints['positions']+'?nonzero=true').json()

    ##############################
    #PLACE ORDER
    ##############################

    def place_order(
            self,
            instrument,
            quantity=1,
            price=None,
            stop_price=None,
            transaction = None,
            trigger='immediate',
            order='market',
            time_in_force = 'gfd'
        ):
        """place an order with Robinhood

        Notes:
            OMFG TEST THIS PLEASE!

            Just realized this won't work since if type is LIMIT you need to use "price" and if
            a STOP you need to use "stop_price".  Oops.
            Reference: https://github.com/sanko/Robinhood/blob/master/Order.md#place-an-order

        Args:
            instrument (dict): the RH URL and symbol in dict for the instrument to be traded
            quantity (int): quantity of stocks in order
            price (float): limit price for order
            stop_price (float): stop price for order
            transaction (:enum:`Transaction`): BUY or SELL enum
            trigger (:enum:`Trigger`): IMMEDIATE or STOP enum
            order (:enum:`Order`): MARKET or LIMIT
            time_in_force (:enum:`TIME_IN_FORCE`): GFD or GTC (day or until cancelled)

        Returns:
            (:obj:`requests.request`): result from `orders` put command

        """
        if isinstance(transaction, str):
            transaction = Transaction(transaction)

        if transaction == Transaction.BUY and not price:
            bid_price = self.quote_data(instrument['symbol'])['bid_price'];
            price = bid_price

        # if not price:
        #    if transaction == Transaction.BUY:
        #        price = self.quote_data(instrument['symbol'])['bid_price']
        #    else:
        #        price = self.quote_data(instrument['symbol'])['ask_price']
                
        payload = {
            'account': self.get_account()['url'],
            'instrument': unquote(instrument['url']),
            'quantity': quantity,
            'side': transaction.name.lower(),
            'symbol': instrument['symbol'],
            'time_in_force': time_in_force.lower(),
            'trigger': trigger,
            'type': order.lower()
        }
        if price:
            payload['price'] = float(price)
        if stop_price:
            payload['stop_price'] = float(stop_price)
            
        # data = 'account=%s&instrument=%s&price=%f&quantity=%d&side=%s&symbol=%s#&time_in_force=gfd&trigger=immediate&type=market' % (
        #    self.get_account()['url'],
        #    urllib.parse.unquote(instrument['url']),
        #    float(bid_price),
        #    quantity,
        #    transaction,
        #    instrument['symbol']
        #)
        res = self.session.post(
            self.endpoints['orders'],
            data=payload
        )
        print(payload)
        print(res.json())
        res.raise_for_status()
        return res.json()

    def place_buy_order(
            self,
            instrument,
            quantity,
            bid_price=0.0
    ):
        """wrapper for placing buy orders

        Args:
            instrument (dict): the RH URL and symbol in dict for the instrument to be traded
            quantity (int): quantity of stocks in order
            bid_price (float): price for order

        Returns:
            (:obj:`requests.request`): result from `orders` put command

        """
        transaction = Transaction.BUY
        return self.place_order(instrument, quantity, bid_price, transaction)

    def place_sell_order(
            self,
            instrument,
            quantity,
            bid_price=0.0
    ):
        """wrapper for placing sell orders

        Args:
            instrument (dict): the RH URL and symbol in dict for the instrument to be traded
            quantity (int): quantity of stocks in order
            bid_price (float): price for order

        Returns:
            (:obj:`requests.request`): result from `orders` put command

        """
        transaction = Transaction.SELL
        return self.place_order(instrument, quantity, bid_price, transaction)
