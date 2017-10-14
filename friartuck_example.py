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
from friartuck.api import FriarTuckLive, OrderType
import logging
log = logging.getLogger("friar_tuck")

def initialize(context):
    log.info("hello, I am in initialize")
    context.aapl = friarTuck.lookup_security("AAPL")
    context.wtw = friarTuck.lookup_security("WTW")
    log.info(context.account)
    log.info(context.portfolio)
    log.info("pnl(%s)" % context.portfolio.pnl)
    for sec in context.portfolio.positions:
        log.info("symbol(%s) pos(%s) " % (sec.symbol, context.portfolio.positions[sec]))
    
def handle_data(context, data):
    log.info("hello, I am in handle_data")
    
    current_quote = data.current(context.aapl, field=['close', 'open'])
    log.debug(current_quote)
    current_quote = data.current(context.wtw, field='close')
    log.debug(current_quote)
    
    current_quote = friarTuck.current([context.aapl, context.wtw], field='close')
    log.debug(current_quote)

"""Start Shell Setup"""
friarTuck = FriarTuckLive(user_name="clivens.laguerre@gmail.com", password="Abs0lut3ly")
class AlgoShell:
    def initialize(self, context):
        initialize(context)
    def handle_data(self, context, data):
        handle_data(context, data)
my_algo = AlgoShell()
friarTuck.active_algo = my_algo
#friarTuck.run_engine(block=True)
"""End Shell Setup"""


sec2 = friarTuck.fetch_and_build_security("GRPN")
log.debug(sec2)
current_data = friarTuck._current(sec2, field=['close','price','high'])
log.debug(current_data['high'])

"""order_id = friarTuck.order(sec2, 1, order_type=OrderType(stop_price=6.40), time_in_force='gtc')
log.info("order_id=%s" % order_id)

#order_id="c853b2b2-a60a-4358-96be-65a8a2d17bf2"
order = friarTuck.get_order(order_id)
log.info("order=%s" % order)

open_orders = friarTuck.get_open_orders(sec2)
log.info("FIT open_orders=%s" % open_orders)

open_orders = friarTuck.get_open_orders()
log.info("ALL open_orders=%s" % open_orders)

friarTuck.cancel_order(order_id)
"""
#friarTuck.__load_market_info()
#friarTuck.__load_profile_info()
#log.info(friarTuck.context.account)
"""
sec = friarTuck.lookup_security("AAPL")
log.debug(sec)
sec2 = friarTuck.lookup_security("WTW")
log.debug(sec2)

history_data = friarTuck.history(sec, bar_count=400, frequency="1h", field=['close','open'])
#log.debug(history_data)

current_quote = friarTuck.current(sec, field=['close','open'])
log.debug(current_quote)
current_quote = friarTuck.current(sec, field='close')
log.debug(current_quote)

current_quote = friarTuck.current([sec,sec2], field='close')
log.debug(current_quote)
"""
