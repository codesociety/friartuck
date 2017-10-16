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

log = logging.getLogger("friar_tuck")


def initialize(context, data):
    # (required) is called when the process starts up
    # Note: within this method "initialize", the parameter "data" should primarily be used to load historical data for initialization, the use of data.current(...) method is best within the handle_data(...) method.
    log.info("hello, I am in initialize...")


def on_market_open(context, data):
    # (optional) is called when the market opens or after a restart of the process during the live market
    # Note: within this method "initialize", the parameter "data" should primarily be used to load historical data for initialization, the use of data.current(...) method is best within the handle_data(...) method.
    log.info("on market open")


def handle_data(context, data):
    # (required) is called at each data interval, currently supported frequencies (1m=every minute, 1h=every hour, 1d=every day at end of session).
    log.info("hello, I am in handle_data")