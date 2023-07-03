from datetime import datetime
from traceback import print_exc
from constants import *
from alert_formatting import generate_html, two_decimal
import openai
from telegram_bot import telegram_message_to_groups
import config

openai.api_key = config.openai_key


class Company:
    def __init__(self, ticker):
        self.ticker = ticker
        self.name = ""
        self.exchange = ""
        self.mkt_cap = 0.0
        self.flt = 0
        self.price = 0.0
        self.volume = 0
        self.amount_chg = 0.0
        self.percent_chg = 0.0
        self.last_close = 0.0

        self.get_name()    # Populate name attribute

    def get_name(self):
        """Get stock name from ticker, using the STOCK_LIST
        :return:
        """
        stock = next((stock for stock in STOCK_LIST if stock['ticker'] == self.ticker), {'name': 'N/A', 'primary_exchange': 'N/A'})    # Default values if ticker not found

        self.name = stock['name']
        self.exchange = stock['primary_exchange']

    def update_financials(self):
        """Get all company financial data from polygon and update the object
        :return: None
        """

        snapshot = POLYGON_STOCKS_CLIENT.get_snapshot(self.ticker)['ticker']
        snapshot_today = snapshot['day']
        snapshot_yesterday = snapshot['prevDay']

        # Don't use 'todaysChange' or 'todaysChangePerc' since they include pre/post market changes

        self.mkt_cap = 0
        self.flt = 0
        self.price = snapshot_today['c']
        self.volume = snapshot_today['v']
        self.amount_chg = snapshot_today['c'] - snapshot_yesterday['c']
        self.percent_chg = snapshot_today['c']/snapshot_yesterday['c'] - 1
        self.last_close = snapshot_yesterday['c']

        #? For market cap, polygon says they use weighted shares outstanding multiplied by last close, what is weighted shares outstanding?? is it an issue if I use regular shares outstanding?

    def generate_alert_lines(self):
        """Generate HTML string for email alerts
        :return:
        """
        alert_lines = []

        # Float
        if self.flt > 1_000_000:
            flt = two_decimal(self.flt, commas=True, append='M', factor=1 / 1_000_000)
        else:
            flt = two_decimal(self.flt, commas=True, append='K', factor=1 / 1_000)

        # Add company data
        alert_lines += [
            ('data', 'Company Name', self.name),
            ('data', 'Ticker', self.ticker),
            ('data', 'Market Cap', two_decimal(self.mkt_cap, decimals=0, commas=True, prepend='$', append='M', factor=1 / 1_000_000)),
            # ('data', 'Float', flt),
            ('data', 'Price', two_decimal(self.price, prepend='$')),
            ('data', 'Volume', two_decimal(self.volume, commas=True, decimals=0)),
            ('data', 'Dollar Change', two_decimal(self.amount_chg, prepend='+')),
            ('data', 'Percent Change', two_decimal(self.percent_chg, prepend='+', append='%'))
        ]

        #? Add red and green colouring for positive/negative change

        return alert_lines

    def generate_telegram_alert_text(self):
        return f"""
<b>${self.ticker}</b> - {self.name}
<b>Market Cap:</b> {two_decimal(self.mkt_cap, decimals=0, commas=True, prepend='$', append='M', factor=1 / 1_000_000)}
<b>Price:</b> {two_decimal(self.price, prepend='$')}
<b>Volume:</b> {two_decimal(self.volume, commas=True, decimals=0)}
<b>Dollar Change:</b> {two_decimal(self.amount_chg, prepend='+')}
<b>Percent Change:</b> {two_decimal(self.percent_chg, prepend='+', append='%', factor=100)}
"""


class Article:
    def __init__(self, article_json):
        self.article_json = article_json
        self.id = article_json['id']
        self.author = article_json['author']
        self.headline = article_json['title']
        self.body = article_json['body']
        self.tickers = [item['name'] for item in article_json['stocks']]
        self.url = article_json['url']
        self.created = datetime.strptime(article_json['created'], '%a, %d %b %Y %H:%M:%S %z')

    def __repr__(self):
        return f"""Created: {self.created}
ID: {self.id}
URL: {self.url}
Headline: {self.headline}
Tickers: {self.tickers}
Body: {self.body}"""


class Alert:
    def __init__(self, article: Article):
        self.article = article
        self.companies = []
        self.summary = ""
        self.category = ""
        self.html_alert = ""
        self.telegram_alert = ""

        # Run methods so that the alert is ready to be delivered  #? Thread these so polygon and OpenAI can work at same time, or look into polygon's async functionality
        self.load_companies()
        self.generate_summary_category()
        self.generate_alert_text()

    def load_companies(self):
        """Use tickers list from article to create company objects and load financials
        :return:
        """
        assert len(self.companies) == 0    # load_companies() should only be called once in the life of an alert

        for ticker in self.article.tickers:
            company = Company(ticker)
            company.update_financials()
            self.companies.append(company)

    def generate_summary_category(self):

        # For now we are just asking gpt-3.5-turbo Davinci to summarize this article, no fine tuning and no special prompts
        #? Try to get it to stop saying "This press release blah blah" and just be more direct
        #? Benzinga gives HTML articles, so we should probably preprocess before feeding into the model. This should be done in the Article class though.

        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are given press releases and you must respond with a category from this list (Drug Approval, Drug Rejection, Clinical Trial, Merger/Acquisition, Earnings, N/A) and a summary of the press release that is somewhat short and contains market related info. Keep the summary under 6 sentences."},  # clues for GPT: "somewhat short" - "market related info" -
                    {"role": "system", "content": "The first line of your response should be just the category and the second line should be just the summary"},
                    {"role": "user", "content": self.article.headline + '\n' + self.article.body}
                ],
                temperature=0.3
            )
        except:
            print_exc()
            self.generate_alert_text()
            return None

        response_str = completion['choices'][0]['message']['content']
        response_list = response_str.split('\n')

        self.category = response_list[0].strip()
        self.summary = response_list[1].strip() if response_list[1] else response_list[2].strip()

        # print(self.category)
        # print(self.summary)
        # print()

    def generate_alert_text(self):
        alert_lines = [
            ('title', self.article.headline, 'small'),
            ('data', 'Category', self.category),
            ('subtitle', 'Public Companies Involved:\n')
        ]

        for company in self.companies:
            alert_lines += company.generate_alert_lines()
            alert_lines.append(('space', 1))

        alert_lines += [
            ('header', 3, 'Summary:'),
            ('text', self.summary, 100),
            ('space', 1),
            ('button', 'Read Full Report', self.article.url)
        ]

        self.html_alert = generate_html(alert_lines)

        self.telegram_alert = \
f"""<b>❗{self.category}❗</b>
{self.article.headline}

<u><b>Public Companies Involved:</b></u>
"""

        for company in self.companies:
            self.telegram_alert += company.generate_telegram_alert_text()

        self.telegram_alert += f"""
<b>Summary:</b>
{self.summary}

<a href='{self.article.url}'><b>READ MORE</b></a>"""

    def deliver(self, tg_channels):
        assert self.html_alert != "" and self.telegram_alert != ""

        # print(self.html_alert)
        # print()
        print(self.telegram_alert)

        telegram_message_to_groups(self.telegram_alert, tg_channels)

    def record(self):
        pass
