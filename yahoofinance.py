import csv
import urllib2
from datetime import date

YAHOO_FINANCE_CSV_URL = """http://ichart.finance.yahoo.com/table.csv?s=%(symbol)s&a=%(start_month)s&b=%(start_day)s&c=%(start_year)s&d=%(end_month)s&e=%(end_day)s&f=%(end_year)s&g=%(interval)s&ignore=.csv"""

def get_yahoo_csv(symbol, start_date=None, end_date=date.today(), interval="d"):
    """Get Yahoo CSV data.

       Args:
           symbol: the stock ticker symbol
           start_date: python date object
           end_date: python date object
           interval: 'd' == daily
                     'w' == weekly
                     'm' == monthly

       Returns a list of dicts containing keys:
           'Adj Close', 'Close', 'Date', 'High', 'Low', 'Open', 'Volume'

        ** Hint: you should be using Adj Close, unless you know what you're doing.
    """
    # if a start date isn't specified, just use the entire history.
    if not start_date:
        start_date = date(1900, 1, 1)

    # construct this parameter dict for Yahoo CSV request
    args = dict(symbol=symbol,
                start_month=start_date.month - 1, # Yahoo finance is stupid. have to correct the months.
                start_day=start_date.day,
                start_year=start_date.year,
                end_month=end_date.month - 1, # Yahoo finance is stupid. have to correct the months.
                end_day=end_date.day,
                end_year=end_date.year,
                interval=interval,
    )
    url = YAHOO_FINANCE_CSV_URL % args
    # reverse this sucker so they're cronological by index
    return [l for l in csv.DictReader(urllib2.urlopen(url))][::-1]
