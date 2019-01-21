import json
from datetime import timedelta, datetime
import calendar
import pandas as pd
import urllib.request
from tinydb import TinyDB, Query


class IEXTrading(object):
    def __init__(self):
        pass

    def get_earnings_today(self):
        url = "https://api.iextrading.com/1.0/stock/market/today-earnings"

        print(url)
        with urllib.request.urlopen(url) as response:
            content = response.read()

        # resp, content = self.client.request(url, "GET")
        # print(content)
        data = json.loads(content.decode('utf-8'))

        return data

    def get_quote_daily(self, symbol, bars=22, before_date=None):
        if before_date:
            delta = (datetime.now().date() - before_date)
            day_diff = delta.days
            if day_diff > 0:
                bars = bars+day_diff

        if bars <= 20:
            query_length = '1m'
        elif bars <= 60:
            query_length = '3m'
        elif bars <= 120:
            query_length = '6m'
        elif bars <= 240:
            query_length = '1y'
        elif bars <= 480:
            query_length = '2y'
        else:
            query_length = '5y'

        # url = "https://api.iextrading.com/1.0/stock/%s/chart/%s?chartLast=%s" % (symbol.lower(), query_length, bars)
        url = "https://api.iextrading.com/1.0/stock/%s/chart/%s" % (symbol.lower(), query_length)

        print(url)
        bars_df = None
        with urllib.request.urlopen(url) as response:
            content = response.read()

        # resp, content = self.client.request(url, "GET")
        # print(content)
        data = json.loads(content.decode('utf-8'))
        quotes = data

        # print(quotes)
        print(len(quotes))

        for quote_data in quotes:
            quote_date = datetime.strptime(quote_data['date'], "%Y-%m-%d")

            if before_date and quote_date.date() >= before_date:
                break

            bar = pd.DataFrame(index=pd.DatetimeIndex([quote_date]),
                               data={'price': quote_data['close'],
                                     'open': quote_data['open'],
                                     'high': float(quote_data['high']),
                                     'low': float(quote_data['low']),
                                     'close': quote_data['close'],
                                     'volume': int(quote_data['volume']),
                                     'date': quote_date})

            # print(close)
            if bars_df is None:
                bars_df = bar
            else:
                bars_df = bars_df.append(bar)

        if bars_df is None:
            # log.warn("Unexpected, could not retrieve quote for security (%s) " % symbol)
            # bars = pd.DataFrame(index=[6], columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date'])
            quote_date = datetime.now()
            quote_date = quote_date.replace(second=0, microsecond=0)
            bars = pd.DataFrame(index=pd.DatetimeIndex([quote_date]), columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date'],
                                data={'price': float("nan"),
                                      'open': float("nan"),
                                      'high': float("nan"),
                                      'low': float("nan"),
                                      'close': float("nan"),
                                      'volume': int(0),
                                      'date': quote_date})
        return bars_df.tail(bars)

    def get_quote_daily_old(self, symbol, bars=22):

        if bars <= 20:
            query_length = '1m'
        elif bars <= 60:
            query_length = '3m'
        elif bars <= 120:
            query_length = '6m'
        elif bars <= 240:
            query_length = '1y'
        elif bars <= 480:
            query_length = '2y'
        else:
            query_length = '5y'

        url = "https://api.iextrading.com/1.0/stock/%s/chart/%s?chartLast=%s" % (symbol.lower(), query_length, bars)

        print(url)
        bars = None
        with urllib.request.urlopen(url) as response:
            content = response.read()

        # resp, content = self.client.request(url, "GET")
        # print(content)
        data = json.loads(content.decode('utf-8'))
        quotes = data

        # print(quotes)
        print(len(quotes))

        for quote_data in quotes:
            quote_date = datetime.strptime(quote_data['date'], "%Y-%m-%d")
            bar = pd.DataFrame(index=pd.DatetimeIndex([quote_date]),
                               data={'price': quote_data['close'],
                                     'open': quote_data['open'],
                                     'high': float(quote_data['high']),
                                     'low': float(quote_data['low']),
                                     'close': quote_data['close'],
                                     'volume': int(quote_data['volume']),
                                     'date': quote_date})

            # print(close)
            if bars is None:
                bars = bar
            else:
                bars = bars.append(bar)

        if bars is None:
            # log.warn("Unexpected, could not retrieve quote for security (%s) " % symbol)
            # bars = pd.DataFrame(index=[6], columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date'])
            quote_date = datetime.now()
            quote_date = quote_date.replace(second=0, microsecond=0)
            bars = pd.DataFrame(index=pd.DatetimeIndex([quote_date]), columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date'],
                                data={'price': float("nan"),
                                      'open': float("nan"),
                                      'high': float("nan"),
                                      'low': float("nan"),
                                      'close': float("nan"),
                                      'volume': int(0),
                                      'date': quote_date})
        return bars

    def get_quote_intraday(self, symbol, minute_series, last_quote_time):
        if not last_quote_time:
            last_quote_time = datetime.now().replace(hour=8, minute=30, second=0, microsecond=0)

        start_time = last_quote_time

        end_time = last_quote_time.replace(hour=15, minute=0, second=0, microsecond=0)

        diff = (end_time - start_time).seconds / 60

        print("diff: %s" % diff)

        url = "https://api.iextrading.com/1.0/stock/%s/chart/1d?" \
              "chartLast=%s" % (symbol.lower(), diff)

        print(url)
        with urllib.request.urlopen(url) as response:
            content = response.read()

        # resp, content = self.client.request(url, "GET")
        # print(content)
        data = json.loads(content.decode('utf-8'))
        quotes = data

        # print(quotes)
        print(len(quotes))

        return self.summarize_quote(quotes, minute_series)

    def _get_quote_intraday_by_date(self, symbol, date):
        db = TinyDB('data/iex_db_%s.json' % symbol)
        quote_query = Query()
        datestr = date.strftime("%Y%m%d")
        quotes = db.search(quote_query.date == datestr)
        if quotes and len(quotes) > 0:
            print("from db: %s" % len(quotes))
            return quotes

        url = "https://api.iextrading.com/1.0/stock/%s/chart/date/%s" % (symbol.lower(), datestr)

        print(url)
        with urllib.request.urlopen(url) as response:
            content = response.read()

        # resp, content = self.client.request(url, "GET")
        # print(content)
        data = json.loads(content.decode('utf-8'))
        quotes = data

        # print(quotes)
        print(len(quotes))
        if len(quotes) > 0:
            current_datetime = datetime.now()
            if date < current_datetime.date() or current_datetime > current_datetime.replace(hour=16, minute=0, second=0, microsecond=0):
                print("storing quotes:")
                db.insert_multiple(quotes)

        return quotes

    def get_quote_intraday_hist_by_date(self, symbol, minute_series, date):
        quote_bars = None

        quotes = self._get_quote_intraday_by_date(symbol, date)
        if len(quotes) > 0:
            quote_bars = summarize_quote(quotes, minute_series)

        if quote_bars is None:
            quote_date = datetime.now()
            quote_date = quote_date.replace(second=0, microsecond=0)
            quote_bars = pd.DataFrame(index=pd.DatetimeIndex([quote_date]), columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date'],
                                      data={'price': float("nan"),
                                            'open': float("nan"),
                                            'high': float("nan"),
                                            'low': float("nan"),
                                            'close': float("nan"),
                                            'volume': int(0),
                                            'date': quote_date})

        return quote_bars

    def get_quote_intraday_hist_by_bars(self, symbol, minute_series, bars=1, before_date=None):
        if before_date:
            date = before_date
        else:
            date = datetime.now()
        # if date.hour < 15:
        #    # if intra-day, start with previous
        #    date = date - timedelta(days=1)

        date_ctr = 0
        quote_bars = None
        while date_ctr < 35 and (quote_bars is None or len(quote_bars) < bars):
            while date.weekday() in [5, 6] or (before_date and date >= before_date):
                date = date - timedelta(days=1)

            quotes = self._get_quote_intraday_by_date(symbol, date.date())
            date_ctr = date_ctr+1
            date = date - timedelta(days=1)

            if len(quotes) == 0:
                continue

            my_bars = summarize_quote(quotes, minute_series)
            if quote_bars is None:
                quote_bars = my_bars
            else:
                quote_bars = pd.concat([my_bars, quote_bars])

        if quote_bars is None:
            quote_date = datetime.now()
            quote_date = quote_date.replace(second=0, microsecond=0)
            quote_bars = pd.DataFrame(index=pd.DatetimeIndex([quote_date]), columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date'],
                                      data={'price': float("nan"),
                                            'open': float("nan"),
                                            'high': float("nan"),
                                            'low': float("nan"),
                                            'close': float("nan"),
                                            'volume': int(0),
                                            'date': quote_date})

        return quote_bars.tail(bars)


def summarize_quote(quotes, minute_series):
    if minute_series not in [1, 5, 15, 30, 60]:
        quote_date = datetime.now()
        quote_date = quote_date.replace(second=0, microsecond=0)
        return pd.DataFrame(index=pd.DatetimeIndex([quote_date]), columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date'],
                            data={'price': float("nan"),
                                  'open': float("nan"),
                                  'high': float("nan"),
                                  'low': float("nan"),
                                  'close': float("nan"),
                                  'volume': int(0),
                                  'date': quote_date})

    bars = None
    active_quote = None
    for quote_data in quotes:
        if "date" not in quote_data or ("close" not in quote_data and "marketClose" not in quote_data):
            # quote_data['date'] = datetime.now().strftime("%Y%m%d")
            continue

        quote_date = datetime.strptime("%sT%s" % (quote_data['date'], quote_data['minute']), "%Y%m%dT%H:%M") - timedelta(hours=1)
        # print(quote_date)
        if quote_date.time() > quote_date.time().replace(hour=15, minute=0, second=0, microsecond=0):
            continue

        if not active_quote or ((minute_series in [1, 5, 15, 30] and quote_date.minute % minute_series == 0) or (minute_series in [60] and quote_date.hour != active_quote['date'].hour)):
            if active_quote and active_quote['close'] != -1:
                bar = pd.DataFrame(index=pd.DatetimeIndex([active_quote['date']]),
                                   data=active_quote)

                # print(close)
                if bars is None:
                    bars = bar
                else:
                    bars = bars.append(bar)

            # print(quote_data)
            # active_quote = None

            market_open = -1
            market_close = -1
            if "marketClose" in quote_data and quote_data['marketClose']:
                market_close = is_valid_value(float(quote_data['marketClose']), float(get_field_value('close', quote_data, -1)))
            if "marketOpen" in quote_data and quote_data['marketOpen']:
                market_open = is_valid_value(float(quote_data['marketOpen']), float(get_field_value('open', quote_data, -1)))

            active_quote = {'price': market_close,
                            'open': market_open,
                            'high': is_valid_value(float(get_field_value('marketHigh', quote_data, -1)), float(quote_data['high'])),
                            'low': is_valid_value(float(get_field_value('marketLow', quote_data, -1)), float(quote_data['low'])),
                            'close': market_close,
                            'volume': is_valid_value(int(get_field_value('marketVolume', quote_data, -1)), int(quote_data['volume'])),
                            'date': quote_date}

        else:
            if "marketClose" in quote_data:
                if active_quote['open'] == -1:
                    active_quote['open'] = is_valid_value(float(get_field_value('marketOpen', quote_data, -1)), float(get_field_value('open', quote_data, -1)))

                active_quote['price'] = is_valid_value(float(get_field_value('marketClose', quote_data, -1)), float(get_field_value('close', quote_data, -1)))
                active_quote['close'] = is_valid_value(float(get_field_value('marketClose', quote_data, -1)), float(get_field_value('close', quote_data, -1)))
                active_quote['volume'] = active_quote['volume']+is_valid_value(int(quote_data['marketVolume']), int(quote_data['volume']))
                if active_quote['high'] == -1 or active_quote['high'] < is_valid_value(float(get_field_value('marketHigh', quote_data, -1)), float(quote_data['high'])):
                    active_quote['high'] = is_valid_value(float(get_field_value('marketHigh', quote_data, -1)), float(quote_data['high']))
                if active_quote['low'] == -1 or active_quote['low'] > is_valid_value(float(get_field_value('marketLow', quote_data, -1)), float(quote_data['low'])):
                    active_quote['low'] = is_valid_value(float(get_field_value('marketLow', quote_data, -1)), float(quote_data['low']))

    if active_quote and active_quote['close'] != -1:
        bar = pd.DataFrame(index=pd.DatetimeIndex([active_quote['date']]),
                           data=active_quote)
        # print(close)
        if bars is None:
            bars = bar
        else:
            bars = bars.append(bar)

    if bars is None:
        quote_date = datetime.now()
        quote_date = quote_date.replace(second=0, microsecond=0)
        bars = pd.DataFrame(index=pd.DatetimeIndex([quote_date]), columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date'],
                            data={'price': float("nan"),
                                  'open': float("nan"),
                                  'high': float("nan"),
                                  'low': float("nan"),
                                  'close': float("nan"),
                                  'volume': int(0),
                                  'date': quote_date})

    return bars


def is_valid_value(value, default):
    if value != -1:
        return value
    return default


def get_field_value(field, map_data, default):
    if field in map_data and map_data[field] and map_data[field] != 'null':
        return map_data[field]

    return default
