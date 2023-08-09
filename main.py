from classes import *
from time import sleep
import config
from datetime import datetime, timedelta
from traceback import print_exc
from threading import Thread

"""
URGENT TO DO:
- 
"""

completed_articles = []    # IDs of articles that have already been received and processed
completed_headlines = []

last_check = datetime.now()

# Example press release from Benzinga
# obj = {'id': 32995849, 'author': 'PRNewswire', 'created': 'Sat, 24 Jun 2023 00:00:00 -0400', 'updated': 'Sat, 24 Jun 2023 00:00:04 -0400', 'title': 'SHAREHOLDER ALERT: Pomerantz Law Firm Investigates Claims On Behalf of Investors of Expensify, Inc. - EXFY', 'teaser': '', 'body': '', 'url': 'https://www.benzinga.com/pressreleases/23/06/n32995849/shareholder-alert-pomerantz-law-firm-investigates-claims-on-behalf-of-investors-of-expensify-inc-e', 'image': [], 'channels': [{'name': 'Press Releases'}], 'stocks': [{'name': 'EXFY'}], 'tags': [{'name': 'Banking/Financial Services'}]}


# This is the function that repeats forever
def main():
    global last_check
    try:
        # The timedelta indicates how far back we are checking to get any Press Releases received late from Benzinga. (Not doing too much because if benzinga posts it 2 minutes too late, we don't want to alert cuz it will look like we are late)
        stories = BENZINGA_NEWS.news(publish_since=str(int((last_check - timedelta(seconds=30)).timestamp())), display_output='full', pagesize=100)

        # For testing an influx of articles at once. Also need to adjust the keywords list to match more headlines.
        # stories = BENZINGA_NEWS.news(date_from=datetime(2023, 7, 1, 6).strftime('%Y-%m-%d'), date_to=datetime(2023, 7, 1, 8).strftime('%Y-%m-%d'), display_output='full', pagesize=100)
    except:
        print_exc()
        logging.exception("")
        sleep(1)
        return None

    if stories:
        logging.info(f"{len(stories)} new press release(s)!")

    last_check = datetime.now()  # Next check will include articles starting from now (minus the timedelta set)

    # Loop over each new story. All the processing time should happen due to process_article() not before that
    for story in stories:
        # Do all the article preprocessing

        article = Article(story)    # Use the JSON press release from Benzinga to create an object of the Article class

        # Make sure we have not already processed this article. Sometimes the ID is different but headline is same
        if article.id not in completed_articles and article.headline not in completed_headlines:
            completed_articles.append(article.id)
            completed_headlines.append(article.headline)

            # Preprocess article
            article = preprocess_article(article)

            if not article:  # preprocess_article will return None if article should be ignored
                continue

            # Process the article and turn it into an alert
            alert_thread = Thread(target=process_article, args=(article,))
            alert_thread.start()

            logging.info("Started Article Processing Thread")

        else:
            logging.info(f"ARTICLE SEEN AGAIN. ID: {story['id']}")

    return None


def preprocess_article(article, headline_keywords=HEADLINE_KEYWORDS):
    """Check if this article can be considered for an alert, and update some of its properties to make it ready for processing into an alert
    :param article:
    :return: updated article, or None if the article is not worth pursuing
    """

    # Confirm the article has all the data we need to make an alert
    #? Some tickers have prefix from benzinga like "CSE:RAIL" might have to preprocess those
    #? Look thru a ton of benzinga releases to find any other possible issues
    if article and article.tickers and article.headline and article.body:
        pass
    else:
        INFO_LOGGER.debug(f"MISSING INFO OR NO TICKERS: {article.id}")
        return None

    # The article headline must have one of the headline_keywords in it
    if any(keyword.lower() in article.headline.lower() for keyword in headline_keywords):
        pass
    else:
        INFO_LOGGER.info(f"NO KEYWORDS FOUND IN HEADLINE: {article.headline}")
        return None

    # Change article.tickers to only include tickers that are also found in TICKER_LIST
    tickers = []
    for ticker in article.tickers:
        if ticker in TICKER_LIST:
            tickers.append(ticker)

    if not tickers:
        INFO_LOGGER.info(f"NO PUBLIC US TICKERS: {article.tickers}")
        return None
    else:
        # using list() to ensure article.tickers is not tied to same address as tickers
        article.tickers = list(tickers)

    return article


def process_article(article, deliver=True):
    # Create the alert object. Everything needed for the alert is done in the __init__ function of Alert class.
    alert = Alert(article)

    # Ensure the alert is valid before sending it
    if not alert.is_valid():
        INFO_LOGGER.info("Alert is not valid!")
        return
    else:
        INFO_LOGGER.info("Alert is valid!")

    if alert.category in CATEGORIES.PROD:
        telegram_channels = config.telegram_channels_prod
    else:
        telegram_channels = config.telegram_channels_dev

    if deliver:
        alert.deliver(telegram_channels)

    logging.info(f"NEW ALERT! | Article Time: {alert.article.created} | Article Link: {alert.article.url}")


if __name__ == '__main__':
    while True:
        main()
        sleep(1)    # In practice, this is our minimum delay between Benzinga calls
