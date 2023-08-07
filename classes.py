from datetime import datetime, time
from traceback import print_exc
from constants import *
from text_processing import *
from alert_formatting import generate_html, two_decimal
import openai
from telegram_bot import telegram_message_to_groups
import config

openai.api_key = config.openai_key


class Company:
    def __init__(self, ticker):
        # Company data
        self.ticker = ticker
        self.name = ""
        self.exchange = ""
        self.cik = ""

        self.get_company_data()  # Populate company data attributes

        # Financials
        self.weighted_shares_outstanding = 0.0    # This is the number that you can multiply by price to get mkt_cap
        self.mkt_cap = 0.0
        # self.flt = 0
        self.price = 0.0
        self.volume = 0
        self.amount_chg = 0.0
        self.percent_chg = 0.0
        self.last_close = 0.0

    def get_company_data(self):
        """Get stock name from ticker, using the STOCK_LIST
        :return:
        """
        stock = next((stock for stock in STOCK_LIST if stock['ticker'] == self.ticker), {'name': 'N/A', 'primary_exchange': 'N/A'})    # Default values if ticker not found

        self.name = stock['name']
        self.exchange = stock['primary_exchange']
        self.cik = stock['cik']

        #? Remove "common stock" or "ordinary shares" or "New Common Stock (Canada)" or "Class A Common Stock" or "Class A Common" from end of self.name if it's there

    def update_financials(self):
        """Get all company financial data from polygon and update the object
        :return: None
        """

        # Get all the stock details
        snapshot = POLYGON_STOCKS_CLIENT.get_snapshot(self.ticker)['ticker']
        snapshot_today = snapshot['day']
        snapshot_yesterday = snapshot['prevDay']

        # On market day mornings, today's close is 0 because trading hasn't started yet. In this case we should use the previous day's close as the current price, and have change values equal zero
        # Also if polygons stock price today is 0 but yesterday is not 0, it may just not have been updated today so use yesterday's
        #? If the price is 0 because of a polygon error, and it is before 9:30AM on a weekend, this logic would trigger, but it shouldn't
        if (snapshot_today['c'] == 0 and datetime.now().time() < time(9, 30)) or (snapshot_today['c'] == 0 and snapshot_yesterday['c'] != 0):
            snapshot_today = snapshot_yesterday

        # Don't use 'todaysChange' or 'todaysChangePerc' since they include pre/post market changes

        # If polygon's yesterday data is bad, set everything to 0 (price will be displayed as N/A on the alert)
        if snapshot_yesterday['c'] == 0 or snapshot_today['c'] == 0:

            self.price = 0
            self.volume = 0
            self.amount_chg = 0
            self.percent_chg = 0
            self.last_close = 0

        else:

            self.price = snapshot_today['c']
            self.volume = snapshot_today['v']
            self.amount_chg = snapshot_today['c'] - snapshot_yesterday['c']
            self.percent_chg = snapshot_today['c']/snapshot_yesterday['c'] - 1
            self.last_close = snapshot_yesterday['c']    #? On market day mornings this will be equal to the current price

        # Get shares outstanding and market cap
        ticker_details = POLYGON_REFERENCE_CLIENT.get_ticker_details(self.ticker)['results']  #? This will pull date from most recent available date -- it could be outdated
        self.weighted_shares_outstanding = ticker_details.get('weighted_shares_outstanding', 0)
        self.mkt_cap = self.weighted_shares_outstanding * self.price

    def generate_alert_lines(self):
        """Generate HTML string for email alerts
        :return:
        """
        alert_lines = []

        # Add company data
        alert_lines += [
            ('data', 'Company Name', self.name),
            ('data', 'Ticker', self.ticker),
            ('data', 'Market Cap', two_decimal(self.mkt_cap, decimals=0, commas=True, prepend='$', append='M', factor=1 / 1_000_000)),
            # ('data', 'Float', flt),
            ('data', 'Price', two_decimal(self.price, prepend='$')),
            ('data', 'Volume', two_decimal(self.volume, commas=True, decimals=0)),
            ('data', 'Day Change ($)', two_decimal(self.amount_chg, prepend='+')),
            ('data', 'Percent Change', two_decimal(self.percent_chg, prepend='+', append='%'))
        ]

        #? Add red and green colouring for positive/negative change

        return alert_lines

    def generate_telegram_alert_text(self):
        return f"""
<b>${self.ticker}</b> - {self.name}
<b>Market Cap:</b> {two_decimal(self.mkt_cap, decimals=0, commas=True, prepend='$', append='M', factor=1 / 1_000_000, non_zero=True)}
<b>Price:</b> {two_decimal(self.price, prepend='$', non_zero=True)}
<b>Volume:</b> {two_decimal(self.volume, commas=True, decimals=0, non_zero=True)}
<b>Day Change:</b> {two_decimal(self.amount_chg, prepend='+')} ({two_decimal(abs(self.percent_chg), append='%', factor=100)})
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

        # Things that are not directly from the Benzinga JSON
        self.body_text = html_to_text(self.body)

    def __repr__(self):
        return f"""Created: {self.created}
ID: {self.id}
URL: {self.url}
Headline: {self.headline}
Tickers: {self.tickers}"""


class Alert:
    def __init__(self, article: Article):
        self.article = article
        self.companies = []
        self.summary = "N/A"    # Default value in case OpenAI errors
        self.category = "N/A"    # Default value in case OpenAI errors
        self.html_alert = ""
        self.telegram_alert = ""
        self.alert_start_time = datetime.now()

        # Run methods so that the alert is ready to be delivered after initializing it #? Thread these so polygon and OpenAI can work at same time, or look into polygon's async functionality
        self.load_companies()
        self.generate_summary_category()
        self.generate_alert_text()

    def load_companies(self):
        """Use tickers list from article to create company objects and load financials
        :return:
        """
        assert len(self.companies) == 0    # load_companies() should only be called once in the life of an alert

        cik_list = []    # List that contains all the company CIKs

        for ticker in self.article.tickers:
            company = Company(ticker)

            # If one of the companies in the ticker list has the same CIK as this ticker, skip this ticker
            if company.cik in cik_list:
                continue
            else:
                cik_list.append(company.cik)

            company.update_financials()
            self.companies.append(company)

    def generate_summary_category(self):

        # For now we are just asking gpt-3.5-turbo Davinci to summarize this article, no fine tuning and no special prompts
        #? Try to get it to stop saying "This press release blah blah" and just be more direct
        #? We should count the number of tokens in our prompt. The input + ouptut can't exceed 4096.
        #? Retry if error? currently if there's an error summary will be N/A
        #? GPT should be strict when picking categories, if it doesnt fit perfectly then make it Other
        #? Sometimes the tickers that Benzinga includes in the release have nothing to do with the main news, they are just found somewhere in the article. we should ask gpt to check this

        # Other possible categories: Funding, Staff Update, Earnings, Legal

        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": GPT_PROMPT},  # clues for GPT: "somewhat short" - "market related info" -
                    {"role": "system", "content": "Your response should just be \"Category\\nSummary\". Nothing else."},
                    {"role": "user", "content": self.article.headline + '\n' + self.article.body_text}
                ],
                temperature=0.3
            )
        except:
            print_exc()
            logging.exception("")
            # self.generate_summary_category()    # This will make it try forever until it succeeds
            return None

        response_str = completion['choices'][0]['message']['content']
        response_list = response_str.split('\n')

        self.category = response_list[0].strip()
        self.summary = response_list[1].strip() if response_list[1] else response_list[2].strip()

        # print(self.category)
        # print(self.summary)
        # print()

    def post_process(self):
        # If GPT generated a category, check against the respective ANTI_KEYWORD list to confirm, otherwise set to Other
        if any(keyword.lower() in self.article.headline.lower() for keyword in ANTI_KEYWORDS.get(self.category, [])):
            self.category = CATEGORIES.OTHER
            INFO_LOGGER.info(f"Alert is NOT a {self.category}: {self.article.headline}")
        else:
            INFO_LOGGER.info(f"Alert IS a {self.category}: {self.article.headline}")
            pass  # Alert is categorized correctly

    def is_valid(self):
        """Ensure the Alert is valid and worth sending.
        This method should be run after the alert is ready, before sending.
        This function may also change some properties of the alert so that it is ready to be sent
        :return: True if article should be sent, otherwise False
        """
        # Make sure the category is one of the possible options.
        if self.category not in CATEGORIES.ALL:
            return False

        # Check that the companies included in the alert are actually a major part of the news, not companies just mentioned at the end of the release

        return True

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
        INFO_LOGGER.info(f"Alert processing time: {datetime.now() - self.alert_start_time}")
        logging.info(self.telegram_alert)

        telegram_message_to_groups(self.telegram_alert, tg_channels)

    def record(self):
        pass
