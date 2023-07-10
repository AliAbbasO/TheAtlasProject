from classes import *
from constants import *
import config


def article_to_alert(article_url, article_title, article_body, article_tickers):
    article_json = {'id': 1234, 'author': 'FakeNewswire', 'created': 'Sat, 24 Jun 2023 00:00:00 -0400', 'updated': 'Sat, 24 Jun 2023 00:00:04 -0400', 'title': article_title, 'teaser': '', 'body': article_body, 'url': article_url, 'image': [], 'channels': [{'name': 'Press Releases'}], 'stocks': [{'name': ticker} for ticker in article_tickers], 'tags': [{'name': 'Fake Tag'}]}

    article = Article(article_json)

    alert = Alert(article)

    alert.deliver([])

