import logging
import time
# import utcfromtimestamp

import urllib.request
# from urllib.request import urlopen  # the lib that handles the url stuff
from abc import ABCMeta, abstractmethod, abstractproperty
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from friartuck import utc_to_local

log = logging.getLogger("friar_tuck")
class QuoteSourceAbstract:
    @abstractmethod
    def fetch_quotes(self, bar_count=10, frequency='1m'):
        pass
    
class GoogleQuoteSource(QuoteSourceAbstract):
    allowed_history_frequency = {'1m':'1minute', '1h':'1hour', '1d':'day'}
    def __init__(self):
        pass
        
    def fetch_quotes(self, symbol, bar_count=1, frequency='1m', field=None):
        if frequency not in self.allowed_history_frequency:
            log.warn("frequency used (%s) is not allowed, the allowable list includes (%s)" % (frequency, self.allowed_history_frequency))
            return [];
        
        interval = 60
        period_factor = bar_count
        period = 'm'
        if frequency != "1m" or period_factor > 50:
            period = 'd'
            if frequency == "1m":
                period_factor = int(np.ceil([bar_count / 390])[0])
            elif frequency == "1h":
                if period_factor > 350:
                    period = 'Y'
                    period_factor = int(np.ceil([bar_count / 1760])[0])
                else:
                    interval = 3600
                    period_factor = int(np.ceil([bar_count / 7])[0])
            elif frequency == "1d":
                period = 'Y'
                interval = 86400
                period_factor = int(np.ceil([bar_count / 252])[0])
    
        if isinstance(symbol, str):
            quotes = self._load_quotes(symbol, frequency, interval, period_factor, period, bar_count, field);
            if quotes is None:
                quote_date = datetime.now()
                quote_date = quote_date.replace(second=0, microsecond=0)
                quotes = pd.DataFrame(index=pd.DatetimeIndex([quote_date]),
                                                    data={'price': float("nan"),
                                                          'open': float("nan"),
                                                          'high': float("nan"),
                                                          'low': float("nan"),
                                                          'close': float("nan"),
                                                          'volume': int(0)})
            return {symbol: quotes}
        
        symbol_bars = {}
        for sym in symbol:
            quotes = self._load_quotes(sym, frequency, interval, period_factor, period, bar_count, field)
            # if quotes is None:
                # Since we gotten nothing, lets wait 3 secs and try again
                # time.sleep(5)
             #   quotes = self._load_quotes(sym, frequency, interval, period_factor, period, bar_count, field, wait_time=5)
            
            if quotes is not None:
                symbol_bars[sym] = quotes
            else:
                quote_date = datetime.now()
                quote_date = quote_date.replace(second=0, microsecond=0)
                symbol_bars[sym] = pd.DataFrame(index=pd.DatetimeIndex([quote_date]),
                                                    data={'price': float("nan"),
                                                          'open': float("nan"),
                                                          'high': float("nan"),
                                                          'low': float("nan"),
                                                          'close': float("nan"),
                                                          'volume': int(0)})
        
        return symbol_bars
    
    def _load_quotes(self, symbol, frequency, interval, period_factor, period, bar_count, field, wait_time=None):
        target_url = "https://finance.google.com/finance/getprices?i=" + str(interval) + "&p=" + str(period_factor) + period + "&f=d,o,h,l,c,v&q=" + symbol
        log.debug(target_url)
        # data = urlopen(target_url, timeout=10)  # it's a file like object and works just like a file
        bars = None
        unix_date = None
        req = urllib.request.Request(target_url)
        with urllib.request.urlopen(req) as response:
            if wait_time:
                log.debug("About to sleep")
                time.sleep(wait_time)
            # data = response.decode()         
            # res = requests.get(target_url)
            # res.raise_for_status()  #will throw without auth
            # data = res.text()                
            for line in response:  # files are iterable
                line = line.decode("utf-8").strip()
                # print (line)
                if not unix_date and not line.startswith("a"):
                    continue
                
                offset = 0
                (date, close, high, low, open, volume) = line.split(',')
                if date.startswith("a"):
                    unix_date = int(date.replace("a", ""))
                    offset = 0
                else:
                    offset = int(date)
                
                quote_date = datetime.utcfromtimestamp(unix_date + (offset * interval))
                if frequency == "1m" or frequency == "1h":
                    quote_date = utc_to_local(quote_date)
                         
                bar = pd.DataFrame(index=pd.DatetimeIndex([quote_date]),
                                       data={'price': float(close),
                                             'open': float(open),
                                             'high': float(high),
                                             'low': float(low),
                                             'close': float(close),
                                             'volume': int(volume)})
                # print(close)
                if bars is None:
                    bars = bar
                else:
                    bars = bars.append(bar)
        
        if bars is None:
            log.warn("Unexpected, could not retrieve quote for security (%s) " % symbol)
            return None
        
        bars = bars.tail(bar_count)
        if field:
            bars = bars[field]
            
        return bars  
