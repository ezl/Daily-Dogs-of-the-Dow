import numpy as np
import csv
import urllib2
from datetime import datetime, date, timedelta
from matplotlib import pyplot

DOW_COMPONENTS = (
    ("AA", "Alcoa Inc. Common Stock"),
    ("AXP", "American Express Company Common"),
    ("BA", "Boeing Company (The) Common Sto"),
    ("BAC", "Bank of America Corporation Com"),
    ("CAT", "Caterpillar, Inc. Common Stock"),
    ("CSCO", "Cisco Systems, Inc"),
    ("CVX", "Chevron Corporation Common Stoc"),
    ("DD", "E.I. du Pont de Nemours and Com"),
    ("DIS", "Walt Disney Company (The) Commo"),
    ("GE", "General Electric Company Common"),
    ("HD", "Home Depot, Inc. (The) Common S"),
    ("HPQ", "Hewlett-Packard Company Common"),
    ("IBM", "International Business Machines"),
    ("INTC", "Intel Corporation"),
    ("JNJ", "Johnson & Johnson Common Stock"),
    ("JPM", "JP Morgan Chase & Co. Common St"),
    ("KFT", "Kraft Foods Inc. Common Stock"),
    ("KO", "Coca-Cola Company (The) Common"),
    ("MCD", "McDonald's Corporation Common S"),
    ("MMM", "3M Company Common Stoc"),
    ("MRK", "Merck & Company, Inc. Common St"),
    ("MSFT", "Microsoft Corporation"),
    ("PFE", "Pfizer, Inc. Common Stock"),
    ("PG", "Procter & Gamble Company (The"),
    ("T", "AT&T Inc"),
    ("TRV", "The Travelers Companies, Inc. C"),
    ("UTX", "United Technologies Corporation"),
    ("VZ", "Verizon Communications Inc. Com"),
    ("WMT", "Wal-Mart Stores, Inc. Common St"),
    ("XOM", "Exxon Mobil Corporation Common"),
)

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

if __name__ == "__main__":
    # Init
    END_DATE = date.today()
    START_DATE = END_DATE - timedelta(days=8 * 365)
    DOW_SYMBOLS = [c[0] for c in DOW_COMPONENTS]
    NUM_LONGS = 10
    NUM_SHORTS = 10
    DAILY_RISK_CAPITAL = 100. # per symbol we trade.

    # Get the raw data
    data = dict()
    for symbol in DOW_SYMBOLS:
        print("Retrieving data for: %s" % symbol)
        # we need to extra days of returns for the backtest, so start 2 days early
        data[symbol] = get_yahoo_csv(symbol=symbol,
                                     start_date=START_DATE - timedelta(days=2),
                                     end_date=END_DATE,
                                     interval='w')

    # Make it usable
    prices = np.array( [ [np.float(i['Adj Close']) for i in data[symbol]]
                          for symbol in DOW_SYMBOLS
                       ]
                     )
    dprices = np.hstack( (np.zeros((prices.shape[0], 1)),
                          np.diff(prices, axis=1))
                       )
    returns = np.hstack( (np.zeros((prices.shape[0], 1)),
                          np.diff(np.log(prices), axis=1))
                       )

    # Just for clarity, truncate to only trade dates
    prices = prices[:, 2:]
    dprices = dprices[:, 2:]
    previous_returns = returns[:, 1:-1]
    tdates = np.array( [ [datetime.strptime(i['Date'], '%Y-%m-%d').date() for i in data[symbol]]
                          for symbol in DOW_SYMBOLS
                       ]
                     )[:, 2:] # took too many days before remove them now.

    # Sanity check, also make sure data isn't missing days for some names
    assert prices.shape == dprices.shape == previous_returns.shape == tdates.shape

    # The "backtest"

    # In our version of dogs of the dow, we'll take the 10 worst performers every day and buy them for one day.
    low_threshold = previous_returns[previous_returns.argsort(axis=0)[NUM_LONGS - 1]].diagonal()
    buys = previous_returns <= low_threshold

    # If you want a beta neutral dogs of the dow, apply the same principal in reverse
    high_threshold = previous_returns[previous_returns.argsort(axis=0)[previous_returns.shape[0] - NUM_SHORTS - 1]].diagonal()
    sales = previous_returns > high_threshold

    # Just do an equal notional allocation in each asset
    long_or_short = (buys * 1) - (sales * 1)
    position = DAILY_RISK_CAPITAL / prices * (long_or_short)
    pnl = position * dprices
    portfolio_pnl = pnl.sum(axis=0)

    # roc == "Return on Capital"
    roc = portfolio_pnl / abs(long_or_short).sum() * DAILY_RISK_CAPITAL
    bankroll = 5

    pyplot.plot(tdates[0], np.cumsum(portfolio_pnl))
    pyplot.title("Investing %s per trade, independent of bankroll" % DAILY_RISK_CAPITAL)

    pyplot.figure()
    pyplot.plot(tdates[0], np.cumprod(np.exp(roc)))
    pyplot.title("Scale investment to bankroll size to become a billionaire")

    pyplot.show()
