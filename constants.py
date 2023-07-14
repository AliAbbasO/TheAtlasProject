import config
from polygon import ReferenceClient, StocksClient
import requests
import logging

POLYGON_REFERENCE_CLIENT = ReferenceClient(config.polygon_key)
POLYGON_STOCKS_CLIENT = StocksClient(config.polygon_key)

# ---Important Constants---
ALERT_CATEGORIES = [
    'FDA Drug Approval', 'FDA Drug Rejection', 'Clinical Trial Result', 'Merger/Acquisition'
]

# At least one of these keywords must be in the article headline for us to even process it. Case-insensitive
HEADLINE_KEYWORDS = [
    'fda authorization', 'approves', 'approval',    # FDA Drug Approval
    'complete response letter',    # FDA Drug Rejection
    'phase', 'clinical trial', 'trial results', 'study'    # Clinical Trial
    'acquisition', 'acquire', 'merge', 'combine', 'combination', 'sell', 'join',    # Merger/Acquisition
    # 'stock split',    # Stock Split

]

# ---Logging---
# log.log will contain everything logged (above the logging level) in the most recent run of the program
logging.basicConfig(level=logging.INFO, filename="log.log", filemode='w',
                    format='%(asctime)s %(levelname)s: %(message)s')

# Info logging to info.log
INFO_LOGGER = logging.getLogger('INFO_LOGGER')

handler = logging.FileHandler('info.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)

INFO_LOGGER.addHandler(handler)

# ---Polygon Stock List---
STOCK_LIST = []

# Exchanges we need to cover: XNAS XNYS XASE (NYSE and NASDAQ)
for exch in ('XNAS', 'XNYS', 'XASE'):
    poly_tickers = POLYGON_REFERENCE_CLIENT.get_tickers(market='stocks', exchange=exch, symbol_type='CS', limit=1000)
    next_url = poly_tickers.get('next_url', '')
    stock_list = poly_tickers['results']
    while next_url:
        poly_tickers = requests.get(next_url + f'&apiKey={config.polygon_key}').json()
        next_url = poly_tickers.get('next_url', '')
        stock_list += poly_tickers['results']

    STOCK_LIST += stock_list

    # print(exch)
    # print(len(STOCK_LIST))

TICKER_LIST = [stock['ticker'] for stock in STOCK_LIST]

# print(TICKER_LIST)
