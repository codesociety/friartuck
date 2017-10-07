import argparse
import datetime
import sys

import time

from friartuck.api import FriarTuckLive, Order
import logging
from os import path
import configparser

parser = argparse.ArgumentParser(description='FriarTuck Quant Robinhood Broker Application')

parser.add_argument('--algo_script', action="store", dest="algo_script", help="Algorithm script file")
parser.add_argument('--config_file', action="store", dest="config_file",
                    help="Configuration file which should include credentials")
parser.add_argument('--data_frequency', action="store", dest="data_frequency",
                    help="[1m, 1h, 1d] The frequency of bar data... default is 1h")
# parser.add_argument('--tzone', action="store", dest="tzone",  help="Time_zone")

log = logging.getLogger("friar_tuck")

PATH = path.abspath(path.dirname(__file__))
ROOT = path.dirname(PATH)


def get_config(config_filename):
    friar_config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation(),
        allow_no_value=True,
        delimiters='=',
        inline_comment_prefixes='#'
    )

    local_filename = config_filename.replace('.cfg', '_local.cfg')
    if path.isfile(local_filename):
        config_filename = local_filename

    with open(config_filename, 'r') as file:
        friar_config.read_file(file)

    return friar_config


def get_datetime():
    return friar_tuck.get_datetime()


def lookup_security(symbol):
    return friar_tuck.fetch_and_build_security(symbol)


def get_order(order):
    # Checking to see if the order is the Order object, if yes, use the id
    if isinstance(order, Order):
        return friar_tuck.get_order(order.id)
    return friar_tuck.get_order(order)


def get_open_orders(security=None):
    return friar_tuck.get_open_orders(security)


def cancel_order(order):
    # Checking to see if the order is the Order object, if yes, use the id
    if isinstance(order, Order):
        return friar_tuck.cancel_order(order.id)
    return friar_tuck.cancel_order(order)


def order_shares(security, shares, order_type=None, time_in_force='gfd'):
    return friar_tuck.order_shares(security, shares, order_type, time_in_force)


def order_value(security, amount, order_type=None, time_in_force='gfd'):
    return friar_tuck.order_value(security, amount, order_type, time_in_force)


if __name__ == "__main__":
    # if len(sys.argv) <= 2:
    #   exit("Too less arguments calling script")

    args = parser.parse_args(sys.argv[1:])

    global trading_algo, config
    trading_algo = __import__(args.algo_script)
    config_file = args.config_file
    data_frequency = args.data_frequency
    if not data_frequency:
        data_frequency = "1h"

    CONFIG_FILENAME = path.join(PATH, config_file)

    config = get_config(CONFIG_FILENAME)

    # os.environ['TZ'] = 'US/Eastern'
    # time.tzset()

    if (not config.get('LOGIN', 'username')) or (not config.get('LOGIN', 'password')):
        exit('no login credentials given')

    """Start Shell Setup"""
    global friar_tuck
    friar_tuck = FriarTuckLive(user_name=config.get('LOGIN', 'username'), password=config.get('LOGIN', 'password'),
                               data_frequency=data_frequency)
    trading_algo.friar_tuck = friar_tuck

    trading_algo.lookup_security = lookup_security
    trading_algo.get_order = get_order
    trading_algo.get_open_orders = get_open_orders
    trading_algo.cancel_order = cancel_order
    trading_algo.order_shares = order_shares
    trading_algo.order_value = order_value
    trading_algo.get_datetime = get_datetime

    friar_tuck.set_active_algo(trading_algo)
    friar_tuck.run_engine(block=False)

    while 1:
        # log.info("Alive and well: %s" % datetime.datetime.now())
        time.sleep(60)
    """End Shell Setup"""
