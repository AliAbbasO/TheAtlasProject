import config
from polygon import ReferenceClient, StocksClient
import requests
import logging
from benzinga import news_data

BENZINGA_NEWS = news_data.News(config.benzinga_key)

POLYGON_REFERENCE_CLIENT = ReferenceClient(config.polygon_key)
POLYGON_STOCKS_CLIENT = StocksClient(config.polygon_key)


class CATEGORIES:
    FDA_APPROVAL = 'FDA Drug Approval'
    FDA_REJECTION = 'FDA Drug Rejection'
    CLINICAL_TRIAL = 'Clinical Trial Result'
    MERGER_ACQUISITION = 'Merger/Acquisition'
    LEGAL = 'Legal'   # Just to stop GPT from using the main categories
    STAFF_UPDATE = 'Staff Update'   # Just to stop GPT from using the main categories
    OTHER = 'Other'
    ALL = [
        FDA_APPROVAL, FDA_REJECTION, CLINICAL_TRIAL, MERGER_ACQUISITION, LEGAL, STAFF_UPDATE, OTHER
    ]
    PROD = [
        FDA_APPROVAL, FDA_REJECTION, CLINICAL_TRIAL, MERGER_ACQUISITION
    ]


# ---Important Constants---

# At least one of these keywords must be in the article headline for us to even process it. Case-insensitive
HEADLINE_KEYWORDS = [
    'fda authorization', 'fda approves', 'fda approval',    # FDA Drug Approval
    'complete response letter',    # FDA Drug Rejection
    'phase', 'clinical trial', 'trial results', 'study'    # Clinical Trial
    'acquisition', 'acquire', 'merge', 'combine', 'combination', 'sell', 'join',    # Merger/Acquisition
    # 'stock split',    # Stock Split

    # 'a'    # For testing (to match all headlines)
]
LAX_HEADLINE_KEYWORDS = [  # Matches all possible alerts - not currently in use
    'fda authorization', 'approves', 'approval',    # FDA Drug Approval
    'complete response letter',    # FDA Drug Rejection
    'phase', 'clinical trial', 'trial results', 'study'    # Clinical Trial
    'acquisition', 'acquire', 'merge', 'combine', 'combination', 'sell', 'join',    # Merger/Acquisition
    # 'stock split',    # Stock Split

    # 'a'    # For testing (to match all headlines)
]

ANTI_KEYWORDS = {
    CATEGORIES.FDA_APPROVAL: [
        'initiate', 'initiation', 'phase 1', 'phase 2', 'clinical trial', 'clinical hold', 'clearance',
        'phase'
    ],
    CATEGORIES.FDA_REJECTION: [

    ],
    CATEGORIES.CLINICAL_TRIAL: [
        'enroll', 'initiate', 'initiation', 'initial', 'authorization', 'expand', 'to conduct', 'first patient',
        'first subject', 'last patient', 'last subject', 'starts phase', 'starts study', 'clearance',
        'pre-clinical', 'preclinical', 'readout', 'interim', 'update',
        'resumption', 'resume', 'launch', 'ongoing', 'dose',
        'preliminary', 'completion of dosing', 'completes production', 'trial design', 'completion of dose',
        'completes dosing', 'proceed', 'register', 'prepare', 'progress', 'continue'
    ],
    CATEGORIES.MERGER_ACQUISITION: [
        'joint venture', 'term sheet', 'asset', 'property', 'portfolio', 'extension', 'extend', 'deadline',
        'vote', 'terminate'
    ],
}

# Main prompt given to GPT to generate a summary and category
GPT_PROMPT = f"You are given press releases and you must respond with a category from this list ({', '.join(CATEGORIES.ALL)}) and a summary of the press release that is somewhat short and contains market related info. Keep the summary under 5 sentences."

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
