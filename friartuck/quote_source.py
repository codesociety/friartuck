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

import logging
import time

import urllib.request
from abc import abstractmethod
from datetime import datetime
import pandas as pd
import numpy as np
from friartuck.iextrading import iextrading
from friartuck.alphavantage import alphavantage


log = logging.getLogger("friar_tuck")


class QuoteSourceAbstract:
    @abstractmethod
    def fetch_quotes(self, symbol, bar_count=10, frequency='1m'):
        pass

    def fetch_intraday_quotes(self, symbol, since_last_quote_time=None, frequency='1m', field=None):
        pass


class FriarTuckQuoteSource(QuoteSourceAbstract):
    allowed_history_frequency = {'1m': 1, '5m': 5, '15m': 15, '1h': 60, '1d': 1}

    def __init__(self, config):
        self.config = config
        self.alpha = alphavantage.AlphaVantage(config.get('ALPHA_VANTAGE', 'apikey'))
        self.iex = iextrading.IEXTrading()

    def fetch_intraday_quotes(self, symbol, since_last_quote_time=None, frequency='1m', field=None):
        if frequency not in ['1m', '5m', '15m', '1h']:
            log.warning("frequency used (%s) is not allowed, the allowable list includes (%s)" % (frequency, self.allowed_history_frequency))
            return None

        interval = "%smin" % self.allowed_history_frequency[frequency]
        if isinstance(symbol, str):
            bars = self.alpha.get_quote_intraday(symbol=symbol, interval=interval, since_last_quote_time=since_last_quote_time)
            ctr = 0
            log.info("connected:%s" % bars.iloc[0]['connected'])
            while len(bars) <= 1 and np.isnan(float(bars.iloc[0]['close'])) and not bars.iloc[0]['connected']:
                log.info("got no quote (%s), trying again(%s)" % (bars, ctr))
                if ctr >= 7:
                    break
                time.sleep(10)
                bars = self.alpha.get_quote_intraday(symbol=symbol, interval=interval, since_last_quote_time=since_last_quote_time)
                ctr = ctr+1
            if field:
                bars = bars[field]

            return bars

        symbol_bars = {}
        for sym in symbol:
            bars = self.alpha.get_quote_intraday(symbol=sym, interval=interval, since_last_quote_time=since_last_quote_time)
            ctr = 0
            log.info("connected:%s" % bars.iloc[0]['connected'])
            while len(bars) <= 1 and np.isnan(float(bars.iloc[0]['close'])) and not bars.iloc[0]['connected'] and 'yes' == self.config.get('ALPHA_VANTAGE', 'wait_for_connection'):
                log.info("got no quote (%s), trying again(%s)" % (bars, ctr))
                if ctr >= 7:
                    break
                time.sleep(10)
                bars = self.alpha.get_quote_intraday(symbol=sym, interval=interval, since_last_quote_time=since_last_quote_time)
                ctr = ctr+1

            if field:
                bars = bars[field]

            symbol_bars[sym] = bars

        return symbol_bars

    def fetch_quotes(self, symbol, bar_count=1, frequency='1m', field=None, market_open=True, since_last_quote_time=None):
        # market_open = True
        if frequency not in self.allowed_history_frequency:
            log.warning("frequency used (%s) is not allowed, the allowable list includes (%s)" % (frequency, self.allowed_history_frequency))
            return None

        if isinstance(symbol, str):
            return self._fetch_quotes_by_sym(symbol=symbol, bar_count=bar_count, frequency=frequency, field=field, market_open=market_open, since_last_quote_time=since_last_quote_time)

        symbol_bars = {}
        for sym in symbol:
            symbol_bars[sym] = self._fetch_quotes_by_sym(symbol=sym, bar_count=bar_count, frequency=frequency, field=field, market_open=market_open, since_last_quote_time=since_last_quote_time)

        return symbol_bars

    def _fetch_quotes_by_sym(self, symbol, bar_count=1, frequency='1m', field=None, market_open=True, since_last_quote_time=None):
        if frequency not in self.allowed_history_frequency:
            log.warning("frequency used (%s) is not allowed, the allowable list includes (%s)" % (frequency, self.allowed_history_frequency))
            return None

        if not isinstance(symbol, str):
            log.warning("only for str symbol (%s)" % symbol)
            return None

        if frequency in ['1m', '5m', '15m', '1h']:
            bars = None
            before_date = None
            if market_open:
                bars = self.fetch_intraday_quotes(symbol=symbol, frequency=frequency, field=None, since_last_quote_time=since_last_quote_time)
                # log.info("intra_bars:"+len(bars))

                if len(bars) > 0 and not np.isnan(float(bars.iloc[0]['close'])):
                    before_date = bars.iloc[-1]['date']

                if len(bars) > 0 and np.isnan(float(bars.iloc[0]['close'])):
                    bars = bars.drop([bars.index[0]])

            # log.info(bars)
            if bars is None or len(bars) < bar_count:
                new_bars = self.iex.get_quote_intraday_hist_by_bars(symbol=symbol, minute_series=self.allowed_history_frequency[frequency], bars=bar_count, before_date=before_date)
                if bars is None:
                    bars = new_bars
                else:
                    bars = new_bars.append(bars)

            bars.sort_index(inplace=True)
            if field:
                bars = bars[field]

            return bars

        bars = self.iex.get_quote_daily(symbol=symbol, bars=bar_count)
        if field:
            bars = bars[field]

        return bars
