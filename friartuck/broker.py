#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from friartuck.Robinhood import Robinhood

class RHBroker():
    
    def __init__(self, rh_session):
        self.symbol=[]
        self.subscription_symbol={}
        self.positions = {}
        self.portfolio = {}
        self.orders = {}
        #Bars is not going to be accurate since the prices are not live... for RH the most frequency is every 5 minutes and it seems to be 5 minutes behind. but at least price/last price will be accurate on the call interval
        self.bars = {}
        self.time_skew = None
        
        self.rh_session = rh_session
        
    def execute(self):
        pass
    
    def subscribe_to_market_data(self, symbol):
        if symbol in self.subscription_symbol:
            # Already subscribed to market data
            return
        
        self.subscription_symbol.append(symbol)
    
    def positions(self):
        pass

    def portfolio(self):
        pass

    def account(self):
        pass

    def time_skew(self):
        return self.time_skew

    def order(self, asset, amount, limit_price, stop_price, style):
        pass

    def get_open_orders(self, asset):
        pass

    def get_order(self, order_id):
        pass

    def cancel_order(self, order_param):
        pass

    def get_spot_value(self, assets, field, dt, data_frequency):
        pass