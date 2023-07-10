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
        sleep(1)
        return None

    print(f"{len(stories)} new press release(s)!")

    last_check = datetime.now()  # Next check will include articles starting from now (minus the timedelta set)

    for story in stories:
        if story['id'] not in completed_articles:
            completed_articles.append(story['id'])

            # Thread for each article
            #? Can we send telegram messages from two different threads at the same time?
            process_story(story)
        else:
            print(f"ARTICLE SEEN AGAIN. ID: {story['id']}")

    return None


def process_story(story):
    article = Article(story)

    print("--------------------------------------")
    print(f"Current time: {datetime.now()}")
    print(f"New Article Created: {article.created}")
    print(f"Article Link: {article.url}")
    print(f"Tickers: {article.tickers}")

    # Confirm the article has all the data we need to make an alert, and we haven't already processed it
    #? Something to ensure tickers are NASDAQ NYSE or TSE, maybe polygon has a list of supported tickers. Also Some tickers have prefix from benzinga like "CSE:RAIL" might have to preprocess those
    #? Look thru a ton of benzinga releases to find any other possible issues
    if article and article.tickers and article.headline and article.body:
        pass
    else:
        print("CANCEL: No tickers or info missing")
        return None

    # Change article.tickers to only include tickers in TICKER_LIST
    tickers = []
    for ticker in article.tickers:
        if ticker in TICKER_LIST:
            tickers.append(ticker)

    article.tickers = list(tickers)    # using list() to ensure article.tickers is not tied to same address as tickers

    if not article.tickers:
        print("CANCEL: No tickers")
        return None

    alert = Alert(article)

    # Send to production channels if alert category is in the list of prod alerts, else just send to dev channels
    telegram_channels = []
    if alert.category in ('Drug Approval', 'Drug Rejection', 'Clinical Trial', 'Merger/Acquisition', 'Stock Split'):
        telegram_channels = config.telegram_channels_prod
    else:
        telegram_channels = config.telegram_channels_dev

    alert.deliver(telegram_channels)


if __name__ == '__main__':
    while True:
        main()
        sleep(1)    # In practice, this is our minimum delay between Benzinga calls
