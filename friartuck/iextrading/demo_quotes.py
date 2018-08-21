import argparse
from datetime import datetime

import iextrading


def main(symbol, verbose):
    iex = iextrading.IEXTrading()

    """
    last_quote_time = datetime.now().replace(hour=13, minute=58, microsecond=0, second=0)+timedelta(minutes=1)
    symbol = "BOX"
    # quote = iex.get_quote_intraday(symbol=symbol, minute_series=5, last_quote_time=last_quote_time)
    print(quote)
    """
    """
    symbol = "BOX"
    hist_date = datetime(2018, 8, 3)
    quote = iex.get_quote_intraday_by_date(symbol=symbol, minute_series=60, date=hist_date)
    print(quote)
    """
    """
    symbol = "BOX"
    quote = iex.get_quote_daily(symbol=symbol, bars=30)
    print(quote)
    """

    symbol = "BOX"
    quote = iex.get_quote_intraday_hist_by_bars(symbol=symbol, minute_series=5, bars=15)
    print(quote)

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
