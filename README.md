<!-- [![Image caption](/project.logo.jpg)](#) -->

# PROJECT
**[INSTALL][i] | [USAGE][u] | [API][a] | [CREDITS][c] | [CONTRIBUTE][cpl] | [LICENSE][cpl] | [SUPPORT][ps]**

[d]: #project

**KISS** - Keep it simple, stupid!

Algorithm script file (**algo_template.py**) ...
```
import logging
log = logging.getLogger("friar_tuck")
    
def initialize(context):
    # (required) is called when the process starts up 
    log.info("hello, I am in initialize...")
    
def on_market_open(context, data):
    # (optional) is called when the market opens or after a restart of the process during the live market
    log.info("on market open")
    
def handle_data(context, data):
    # (required) is called at each data interval, currently supported frequencies (1m=every minute, 1h=every hour, 1d=every day at end of session).
    log.info("hello, I am in handle_data")
```
Config file (**rh_config.cfg**) ...
```
[LOGIN]
    username = <robinhood username>
    password = <robinhood password>
```
Run FriarTuck - **Live**
```
python friar_tuck_run.py --algo_script algo_template --config_file rh_config.cfg --data_frequency 1h
```
## FRIAR TUCK SUMMARY
Drive for this project: Build an algorithm on Quantopian, was satisfied with the results, the day I was ready to run live I found out that Quantopian was discontinuing live trading... Bummer!!! Quantopian was my only hope for trading algorithmic on Robinhood and thought all hopes were gone. Than I came across the unofficial api for Robinhood (https://github.com/Jamonek/Robinhood), regained some hopes again... Spent sometime leveraging the Jamonek's Python implementation of the API to build a framework similar to Quantopian. Since Quantopian is keeping their framework for backtesting; my aim for this framework is to keep it was close to Quantopian as possible, this way I can backtest on Quantopian and run live using this framework.
    
    Using the following projects/data (Respect!):
        # As a broker to Robinhood
        https://github.com/Jamonek/Robinhood
        
        # Quantopian (runs on Zipline)
        https://www.quantopian.com/
        
        # Google's Undocumented Finance API For quotes(ohlcv) (frequencies 1m, 1h, 1d)
        finance.google.com/finance/
        # Google informatin on delays for quotes(most are realtime)
        https://www.google.com/intl/en/googlefinance/disclaimer/
      
 
## GETTING STARTED
[gt]: #getting-started 'Getting started guide'
### REQUIREMENTS

* ROBINHOOD Trading Account
* An environment to run FriarTuck (All my testing so far has been on Windows)
* Python (built this using version 3.4)

### INSTALLATION
[i]: #installation 'Installation guide'

```
pip install -r requirements.txt
```

## USAGE
[u]: #usage 'Product usage'
***Load Contracts***
```
    context.aapl = lookup_security("AAPL")
    context.wtw = lookup_security("WTW")
    context.fit = lookup_security("FIT")
    ...
    # Get active trading account details
    my_account = context.account
    log.info(my_account)
    ...
    # Get active portfolio details
    my_portfolio = context.portfolio
    log.info(my_portfolio)
    ...
    # Iterate through all open positions
    for security in context.portfolio.positions:
        log.info("symbol(%s) pos(%s) " % (security.symbol, context.portfolio.positions[security]))
    ...
```
***Using "data" object for current data from "handle_data(context, data)"***
```
    # Get current data (all fields [open, high, low, close, volume, price])
    current_quote = data.current(context.aapl)
    log.debug(current_quote)
    ...
    # Get current data (specific fields)
    current_quote = data.current(context.aapl, field=['close', 'open'])
    log.debug(current_quote)
    ...
    # Get field(s) for more than 1 securities
    current_quote = data.current([context.aapl, context.wtw], field='close')
    log.debug(current_quote)
    
```
***Using "data" object for historical-data from "handle_data(context, data) and on_market_open(context, data)"***
```
    hist_quotes = data.history([context.aapl, context.wtw], frequency='1m', bar_count=10, field='close')
    log.debug(hist_quotes)

    log.debug(context.fit)
    current_data = data.current(context.fit, field=['close', 'price'])
    log.debug(current_data)
    
```
***Sample code using pandas to load contracts from external file***
```
    import pandas as pd
    ...
    context.assets = []
    context.symbol_metadata = {}
    dataset = pd.read_csv("https://dl.dropboxusercontent.com/s/cg8qzffg7yfyzk6/my_universe.csv?dl=0")
    for (index, series) in dataset.iterrows():
        asset = lookup_security(series["symbol"])
        context.symbol_metadata[asset] = series
        context.assets.append(asset)
    log.debug("symbol_metadata (%s)" % context.symbol_metadata)
```
***Ordering using Friar Tuck***
```
    ...
    # Ordering using monetary value; this will use last trade price to calculate number of shares to order
    # for buy
    cash = 1000
    # or for sell
    cash = -1000 
    context.aapl_order_id = order_value(context.aapl, cash, order_type=OrderType(stop_price=158.60), time_in_force='gtc')
        
    ...
    # Ordering a set number of shares
    # for buy
    shares = 120
    # or for sell
    shares = -120
    context.aapl_order_id = order_shares(context.aapl, shares, order_type=OrderType(stop_price=158.60), time_in_force='gtc')
    
    ...
    # retrieve order object
    order = get_order(context.aapl_order_id)
    log.info("order=%s" % order)
    
    ...
    # Retrieve all open orders
    open_orders = get_open_orders()
    for stock_symbol in open_orders:
        log.info("open_order=%s" % open_orders[stock_symbol])
    
    ...
    # Retrieve all open orders by security
    open_orders = get_open_orders(context.aapl.symbol)
    for open_order in open_orders:
        log.info("AAPL open_order=%s" % open_order)
    
    ...
    # Cancel an order
    cancel_order(context.aapl_order_id)
```

## API
[a]: #api 'Module\'s API description'

#### WARNING!: This api is subject to change! Make sure you know what you're doing!
***Much of this API is the same of similar to [Quantopian](https://www.quantopian.com)***

    Context Object:
        is_market_open (boolean): Indicates if the stock market is open or not.
        account (Account Object): Contains the details about the trading account.
        portfolio (Portfolio Object): holds portfolio details including positions.
        
    Security Object: Used when interacting with the broker.
        symbol (string): Stock symbol
        is_tradeable (boolean): Indicates if the security is tradeable
        security_type (String): The security type
        security_detail (json object): The actual security details from Robinhood
        
    OrderType Object: Use to determine the type of order (limit, stop, stop-limit)
        price (float): Use to determine a limit order
        stop_price (float): Use to determine a stop order
        
        Note: both fields can be set from the constructor (price=my_limit_price, stop_price=my_stop_price)... 
        If both fields are obmitted then its a market order, however, 
        please note that though it's a market order to you but robinhood always uses a limit order
        
    Order Object: This represents an order on the market
        id (string): this is the unique identifier of the order
        status (integer): The status of the order
            0 = Open (Robinhood confirmed/partially_filled)
            1 = Filled
            2 = Cancelled
            3 = Rejected
            4 = Unconfirmed (Robinhood queued/unconfirmed)
            5 = Failed
        created (datetime): the date and time the order was created
        stop (float): Stop price
        limit (float): Limit price
        amount (int): Shares ordered
        symbol (string): Stock symbol
        filled (boolean): Indicates if the entire order is filled
        commission (float): commissione charged
        rejected_reason (string): if the order was rejected, this will be the reason
        time_in_force (string): (Robinhood [gfd|gtc])
        
    Portfolio Object:
        capital_used (float): net capital at play (Total cost of shorts) minus (Total cost of longs)
        cash (float): total cash at hand available for trading
        pnl (float): net profit_loss (unrealized_pl + unsettled_funds)
        positions (dict): key=Security object, value=Position object
        portfolio_value (float): total value of the portfolio (cash + market-value)
        positions_value (float): market-value (Robinhood)
        returns (float): total returns since starting the FriarTuck process ((portfolio_value - starting_cash) / starting_cash)
        starting_cash (float): total available cash at the start of the FriarTuck process
        start_date (datetime): The date and time the FriarTuck process started
        
    Position Object: (context->portfolio->positions)
        amount (int): The number of shares
        cost_basis (float): The average price of the position.
        last_sale_price (float): The more recent quote trade price for the security.
        
    Account Object: These fields are from Quantopian, I attempt to map them with fields from and calcs from Robinhood
        accrued_interest (float): This will always be with Robinhood(could not find a matching field) 0
        available_funds (float): cash available for trading
        buying_power (float): Robinhood buying power
        cushion (float): cash / portfolio_value
        day_trades_remaining (int): Infinity (could not identify a Robinhood field to match)
        equity_with_loan (float): portfolio_value
        excess_liquidity (float): available cash
        initial_margin_requirement (float): 0 (could not identify a Robinhood field to match)
        leverage (float): current leverage = (long_position_value + short_position_value) / portfolio_value
        maintenance_margin_requirement (float): 0 (could not identify a Robinhood field to match)
        net_leverage (float): market_value / portfolio_value
        net_liquidation (float): portfolio_value
        regt_equity (float): available cash
        regt_margin (float): Infinity (could not identify a Robinhood field to match)
        settled_cash (float): cash
        total_positions_value (float): market_value
        
    

## CREDITS/CONTACT AUTHOR
[c]: #creditscontact-author 'Credits & author\'s contacts info '
You can follow me on [twitter](https://twitter.com/ClivensLaguerre).

## ACKNOWLEDGMENTS
[acc]: acknowledgments

I want to praise the efforts of the people/projects that have inspired me while <br>
I've been working on this project by briefly mention below their names and projects: <br>

- @Quantopian [here](https://www.quantopian.com)
- @Jamonek / Robinhood [github](https://github.com/Jamonek/Robinhood).
- Github guides for their precious [documenting your project](https://guides.github.com/features/wikis/#creating-a-readme) article concerning readme creation
## LICENSE
[cpl]:#contribution--license 'Contribution guide & license info'

Check out <a href='/LICENSE'>license</a> for more details.

## PRODUCTION STATUS & SUPPORT
[ps]: #production-status--support 'Production use disclaimer & support info'

This project is currently in the very alpha phase, its changing all the time; production readiness is fully determined by you.
I can not guarantee that this project has no bugs, I do try to minimize them but don't have the time or the resources eliminate them. 
I am testing this project live as I am using it for my own use, 
however, I am afraid that my testing is and will be bias since I'll somehow shape it to solve only my problems.
To broaden this up, it would be nice to expand this project to solve other quant issues as well.
Looking for volunteers to test and to develop this project for others to use.
Use of this product is entirely AT YOUR OWN RISK; I do not and can not guarantee any part of this code.  

If you want to **help** me please follow [here][c].

Go back to the **[project description][d]**

Copyright © 2017 Code Society
