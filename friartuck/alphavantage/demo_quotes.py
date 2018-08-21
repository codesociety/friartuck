import argparse
import alphavantage
from datetime import datetime, timedelta


def main(symbol, verbose):
    qs = alphavantage.AlphaVantage("OQ321AAF6BXS3HXX")

    last_quote_time = datetime.now()
    if last_quote_time < last_quote_time.replace(hour=8, minute=30):
        last_quote_time = last_quote_time - timedelta(days=1)

    last_quote_time = last_quote_time.replace(hour=8, minute=58, microsecond=0, second=0)

    # symbol = "BOX"
    quote = qs.get_quote_intraday(symbol=symbol, interval="5min", since_last_quote_time=last_quote_time)
    print(quote)

    """
    symbol = "BOX"
    hist_date = datetime(2018, 8, 3)
    quote = iex.get_quote_intraday_by_date(symbol=symbol, minute_series=60, date=hist_date)
    print(quote)
    """
    """
    #symbol = "BOX"
    quote = qs.get_quote_daily(symbol=symbol, bars=30)
    print(quote)
    """
    """
    symbol = "BOX"
    quote = iex.get_quote_intraday_hist_by_bars(symbol=symbol, minute_series=60, bars=15)
    print(quote)
    """

    """
    if not verbose:
        print("%s price: %s" % (symbol, quote["last"]))
    else:
        print("%s quote: %s" % (symbol, quote))
    """


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", type=str,
                        help="display stock quote for a symbol")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    args = parser.parse_args()
    main(args.symbol, args.verbose)
