import json
from datetime import timedelta, datetime
import pandas as pd
import urllib.request


class AlphaVantage(object):
    def __init__(self, apikey):
        self.apikey = apikey
        pass

    def get_quote_daily(self, symbol, bars=22):

        output_size = "compact"
        if bars > 100:
            output_size = 'full'

        url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=%s&datatype=json&outputsize=%s&apikey=%s" % (symbol.lower(), output_size, self.apikey)

        print(url)
        quote_bars = None
        with urllib.request.urlopen(url) as response:
            content = response.read()

        # resp, content = self.client.request(url, "GET")
        # print(content)
        data = json.loads(content.decode('utf-8'))
        # print(data)
        if "Time Series (Daily)" in data:
            quotes = data["Time Series (Daily)"]

            # print(quotes)
            print(len(quotes))

            for date_str in quotes:
                quote_data = quotes[date_str]
                quote_date = datetime.strptime(date_str, "%Y-%m-%d")
                bar = pd.DataFrame(index=pd.DatetimeIndex([quote_date]),
                                   data={'price': float(quote_data['4. close']),
                                         'open': float(quote_data['1. open']),
                                         'high': float(quote_data['2. high']),
                                         'low': float(quote_data['3. low']),
                                         'close': float(quote_data['4. close']),
                                         'volume': int(quote_data['5. volume']),
                                         'date': quote_date})

                # print(close)
                if quote_bars is None:
                    quote_bars = bar
                else:
                    quote_bars = bar.append(quote_bars)

        if quote_bars is None:
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

        # print(bars)
        quote_bars.sort_index(inplace=True)
        return quote_bars.tail(bars)

    def get_quote_intraday(self, symbol, since_last_quote_time, interval='5min'):
        if not since_last_quote_time:
            since_last_quote_time = datetime.now().replace(hour=8, minute=25, second=0, microsecond=0)

        output_size = "compact"
        if interval == '1min':
            start_time = since_last_quote_time
            end_time = start_time.replace(hour=15, minute=0, second=0, microsecond=0)

            now_time = datetime.now().replace(second=0, microsecond=0)
            if now_time < end_time:
                end_time = now_time

            diff = (end_time - start_time).seconds / 60

            print("diff: %s, start(%s) end(%s)" % (diff, start_time, end_time))
            if diff > 100:
                output_size = 'full'

        url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=%s&datatype=json&outputsize=%s&interval=%s&apikey=%s" % (symbol.lower(), output_size, interval, self.apikey)

        print(url)
        quote_bars = None
        with urllib.request.urlopen(url) as response:
            content = response.read()

        # resp, content = self.client.request(url, "GET")
        # print(content)
        data = json.loads(content.decode('utf-8'))
        # print(data)
        connected = False
        # quote_dates = []
        time_series_key = "Time Series (%s)" % interval
        if time_series_key in data:
            quotes = data[time_series_key]

            # print(quotes)
            print("since_last_quote_time(%s), returned length(%s)" % (since_last_quote_time, len(quotes)))
            if len(quotes) > 0:
                connected = True

            for date_str in quotes:
                quote_data = quotes[date_str]
                minute_adjust = 0
                if interval != "1min":
                    minute_adjust = int(interval.replace("min", ""))

                quote_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:00") - timedelta(hours=1, minutes=minute_adjust)

                # quote_dates.append(quote_date.strftime("%Y-%m-%d %H:%M:00"))
                if since_last_quote_time >= quote_date:
                    continue

                bar = pd.DataFrame(index=pd.DatetimeIndex([quote_date]), columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date', 'connected'],
                                   data={'price': float(quote_data['4. close']),
                                         'open': float(quote_data['1. open']),
                                         'high': float(quote_data['2. high']),
                                         'low': float(quote_data['3. low']),
                                         'close': float(quote_data['4. close']),
                                         'volume': int(quote_data['5. volume']),
                                         'date': quote_date,
                                         'connected': connected})

                # print(close)
                if quote_bars is None:
                    quote_bars = bar
                else:
                    quote_bars = bar.append(quote_bars)

        # print("quote_dates %s" % quote_dates)
        if quote_bars is None:
            # log.warn("Unexpected, could not retrieve quote for security (%s) " % symbol)
            # bars = pd.DataFrame(index=[6], columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date'])
            quote_date = datetime.now()
            quote_date = quote_date.replace(second=0, microsecond=0)
            quote_bars = pd.DataFrame(index=pd.DatetimeIndex([quote_date]), columns=['price', 'open', 'high', 'low', 'close', 'volume', 'date', 'connected'],
                                      data={'price': float("nan"),
                                            'open': float("nan"),
                                            'high': float("nan"),
                                            'low': float("nan"),
                                            'close': float("nan"),
                                            'volume': int(0),
                                            'date': quote_date,
                                            'connected': connected})

        # print(bars)
        quote_bars.sort_index(inplace=True)
        return quote_bars


def is_valid_value(value, default):
    if value != -1:
        return value
    return default
