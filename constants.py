import config
from polygon import ReferenceClient, StocksClient
import requests
import logging
from benzinga import news_data

BENZINGA_NEWS = news_data.News(config.benzinga_key)

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

    # 'a'    # For testing (to match all headlines)
]

ANTI_CLINICAL_TRIAL_KEYWORDS = [
    'enroll', 'initiate', 'initiation', 'initial', 'authorization', 'expand', 'to conduct', 'first patient',
    'first subject', 'last patient', 'last subject', 'starts phase', 'starts study'
    'pre-clinical', 'readouts', 'interim analysis', 'interim data analysis', 'update',
]

# Main prompt given to GPT to generate a summary and category
GPT_PROMPT = f"You are given press releases and you must respond with a category from this list ({', '.join(ALERT_CATEGORIES)}, Other) and a summary of the press release that is somewhat short and contains market related info. Keep the summary under 5 sentences.\nBy default, all press releases should be categorized as other, unless the press release matches perfectly with one of the categories. Any announcements RELATING to an approval, rejection, merger, etc should be classified as \"Other\". Only very obvious announcements OF these categories should be categorized as such."

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
