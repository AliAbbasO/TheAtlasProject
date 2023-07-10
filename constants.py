import config
from polygon import ReferenceClient, StocksClient
import requests

POLYGON_REFERENCE_CLIENT = ReferenceClient(config.polygon_key)
POLYGON_STOCKS_CLIENT = StocksClient(config.polygon_key)

# STOCK_LIST = [{'ticker': 'FNKO', 'name': 'FUNKO, INC.', 'market': 'stocks', 'locale': 'us', 'primary_exchange': 'XNYS', 'type': 'CS', 'active': True, 'currency_name': 'usd', 'cik': '0001090872', 'composite_figi': 'BBG000C2V3D6', 'share_class_figi': 'BBG001SCTQY4', 'last_updated_utc': '2023-06-27T00:00:00Z'}, {'ticker': 'A', 'name': 'Agilent Technologies Inc.', 'market': 'stocks', 'locale': 'us', 'primary_exchange': 'XNYS', 'type': 'CS', 'active': True, 'currency_name': 'usd', 'cik': '0001090872', 'composite_figi': 'BBG000C2V3D6', 'share_class_figi': 'BBG001SCTQY4', 'last_updated_utc': '2023-06-27T00:00:00Z'}, {'ticker': 'AA', 'name': 'Alcoa Corporation', 'market': 'stocks', 'locale': 'us', 'primary_exchange': 'XNYS', 'type': 'CS', 'active': True, 'currency_name': 'usd', 'cik': '0001675149', 'composite_figi': 'BBG00B3T3HD3', 'share_class_figi': 'BBG00B3T3HF1', 'last_updated_utc': '2023-06-27T00:00:00Z'}, {'ticker': 'AAA', 'name': 'AXS First Priority CLO Bond ETF', 'market': 'stocks', 'locale': 'us', 'primary_exchange': 'ARCX', 'type': 'ETF', 'active': True, 'currency_name': 'usd', 'cik': '0001776878', 'composite_figi': 'BBG01B0JRCS6', 'share_class_figi': 'BBG01B0JRCT5', 'last_updated_utc': '2023-06-27T00:00:00Z'}, {'ticker': 'AAAU', 'name': 'Goldman Sachs Physical Gold ETF Shares', 'market': 'stocks', 'locale': 'us', 'primary_exchange': 'BATS', 'type': 'ETF', 'active': True, 'currency_name': 'usd', 'cik': '0001708646', 'composite_figi': 'BBG00LPXX872', 'share_class_figi': 'BBG00LPXX8Z1', 'last_updated_utc': '2023-06-27T00:00:00Z'}]


# Exchanges we need to cover: XNAS XNYS XASE (NYSE and NASDAQ)

STOCK_LIST = []

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
