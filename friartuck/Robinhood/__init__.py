import six

if six.PY3:
    from friartuck.Robinhood.Robinhood import Robinhood
else:
    from Robinhood import Robinhood
    import exceptions as RH_exception
