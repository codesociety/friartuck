import logging
import sys
import calendar
from datetime import datetime, timedelta

log = logging.getLogger("friar_tuck")

formatter = logging.Formatter('%(asctime)s:%(levelname)s - %(module)s:%(lineno)d - %(message)s')
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)

log.addHandler(handler)
log.setLevel(logging.DEBUG)


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)    