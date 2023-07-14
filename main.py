import datetime
from classes import *
from benzinga import news_data
from time import sleep
import config
from datetime import datetime, timedelta
from traceback import print_exc

benzinga_news = news_data.News(config.benzinga_key)

completed_articles = []    # IDs of articles that have already been received and processed

last_check = datetime.now()

# Example press release from Benzinga
# obj = {'id': 32995849, 'author': 'PRNewswire', 'created': 'Sat, 24 Jun 2023 00:00:00 -0400', 'updated': 'Sat, 24 Jun 2023 00:00:04 -0400', 'title': 'SHAREHOLDER ALERT: Pomerantz Law Firm Investigates Claims On Behalf of Investors of Expensify, Inc. - EXFY', 'teaser': '', 'body': '', 'url': 'https://www.benzinga.com/pressreleases/23/06/n32995849/shareholder-alert-pomerantz-law-firm-investigates-claims-on-behalf-of-investors-of-expensify-inc-e', 'image': [], 'channels': [{'name': 'Press Releases'}], 'stocks': [{'name': 'EXFY'}], 'tags': [{'name': 'Banking/Financial Services'}]}


# This is the function that repeats forever
def main():
    global last_check
    try:
        # The timedelta indicates how far back we are checking to get any Press Releases received late from Benzinga. (Not doing too much because if benzinga posts it 2 minutes too late, we don't want to alert cuz it will look like we are late)
        stories = benzinga_news.news(publish_since=str(int((last_check - timedelta(seconds=30)).timestamp())), display_output='full', pagesize=100)
    except:
        print_exc()
        logging.exception("")
        sleep(1)
        return None

    if stories:
        logging.info(f"{len(stories)} new press release(s)!")

    last_check = datetime.now()  # Next check will include articles starting from now (minus the timedelta set)

    for story in stories:
        # Do all the article preprocessing
        article = Article(story)    # Use the JSON press release from Benzinga to create an object of the Article class

        # Make sure we have not already processed this article
        if article.id not in completed_articles:
            completed_articles.append(article.id)

            # Confirm the article has all the data we need to make an alert
            #? Some tickers have prefix from benzinga like "CSE:RAIL" might have to preprocess those
            #? Look thru a ton of benzinga releases to find any other possible issues
            if article and article.tickers and article.headline and article.body:
                pass
            else:
                INFO_LOGGER.debug(f"MISSING INFO OR NO TICKERS: {article.id}")
                return None

            # Skip any articles that don't have any of our HEADLINE_KEYWORDS in them
            if any(keyword.lower() in article.headline.lower() for keyword in HEADLINE_KEYWORDS):
                pass
            else:
                INFO_LOGGER.info(f"NO MATCH: {article.headline}")
                continue

            # Change article.tickers to only include tickers in TICKER_LIST
            tickers = []
            for ticker in article.tickers:
                if ticker in TICKER_LIST:
                    tickers.append(ticker)

            if not tickers:
                INFO_LOGGER.info(f"NO PUBLIC US TICKERS: {article.tickers}")
                continue

            # using list() to ensure article.tickers is not tied to same address as tickers
            article.tickers = list(tickers)

            #? Create a thread for each article
            #? Can we send telegram messages from two different threads at the same time?
            process_article(article)

        else:
            logging.info(f"ARTICLE SEEN AGAIN. ID: {story['id']}")

    return None


def process_article(article):
    logging.info("--------------------------------------")
    logging.info(f"Current time: {datetime.now()}")
    logging.info(f"New Article Created: {article.created}")
    logging.info(f"Article Link: {article.url}")
    logging.info(f"Tickers: {article.tickers}")

    # Create the alert object. Everything needed for the alert is done in the __init__ function of Alert class.
    alert = Alert(article)

    # Send to production channels if alert category is in the list of prod alerts, else just send to dev channels
    if alert.category in ALERT_CATEGORIES:
        telegram_channels = config.telegram_channels_prod
    else:
        telegram_channels = config.telegram_channels_dev

    alert.deliver(telegram_channels)


if __name__ == '__main__':
    while True:
        main()
        sleep(1)    # In practice, this is our minimum delay between Benzinga calls
