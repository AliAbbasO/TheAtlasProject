from classes import *
from constants import *
import config
from main import process_article, preprocess_article


def article_to_alert(article_url, article_title, article_body, article_tickers):
    article_json = {'id': 1234, 'author': 'FakeNewswire', 'created': 'Sat, 24 Jun 2023 00:00:00 -0400', 'updated': 'Sat, 24 Jun 2023 00:00:04 -0400', 'title': article_title, 'teaser': '', 'body': article_body, 'url': article_url, 'image': [], 'channels': [{'name': 'Press Releases'}], 'stocks': [{'name': ticker} for ticker in article_tickers], 'tags': [{'name': 'Fake Tag'}]}

    article = Article(article_json)

    alert = Alert(article)

    alert.deliver([])


# def filter_testing(parameter_dicts, date_from=datetime(2023, 1, 6), date_to=datetime(2023, 6, 30), number_of_releases=1000):
#     historical_releases = []
#     for i in range(1, number_of_releases//100):
#         historical_releases += BENZINGA_NEWS.news(date_from=date_from.strftime('%Y-%m-%d'), date_to=date_to.strftime('%Y-%m-%d'), display_output='full', pagesize=100, page=i)
#
#     for i in range(len(historical_releases)):
#         release = historical_releases[i]
#
#         article = Article(release)
#         article = preprocess_article(article, HEADLINE_KEYWORDS)
#
#         if not article:
#             continue
#
#         print(f"---PRESS RELEASE #{i}---")
#         print(article)
#
#         for j in range(len(parameter_dicts)):
#             parameters = parameter_dicts[j]
#             # headline_keywords = parameters['headline_keywords']
#             gpt_prompt = parameters['gpt_prompt']
#
#             print()
#             print(f"Parameter Set #{j}")
#
#             try:
#                 completion = openai.ChatCompletion.create(
#                     model="gpt-3.5-turbo",
#                     messages=[
#                         {"role": "system", "content": gpt_prompt},  # clues for GPT: "somewhat short" - "market related info" -
#                         {"role": "system",
#                          "content": "The first line of your response should be just the category and the second line should be just the summary"},
#                         {"role": "user", "content": article.headline + '\n' + article.body_text}
#                     ],
#                     temperature=0.3
#                 )
#             except:
#                 print_exc()
#                 # self.generate_summary_category()    # This will make it try forever until it succeeds
#
#             response_str = completion['choices'][0]['message']['content']
#             response_list = response_str.split('\n')
#
#             category = response_list[0].strip()
#             summary = response_list[1].strip() if response_list[1] else response_list[2].strip()
#
#             # Check alert validity: Alert.is_valid()
#
#             print(f"Category: {category}")
#             print(f"Summary: {summary}")
#
#             print()


#? Add a feature to test a specific article ID

def filter_testing(date_from=datetime(2022, 1, 6), date_to=datetime(2022, 12, 31), number_of_releases=1000, start_page=1):
    historical_releases = []
    for i in range(start_page, start_page+(number_of_releases//100)):
        historical_releases += BENZINGA_NEWS.news(date_from=date_from.strftime('%Y-%m-%d'), date_to=date_to.strftime('%Y-%m-%d'), display_output='full', pagesize=100, page=i)

    for i in range(len(historical_releases)):
        release = historical_releases[i]

        article = Article(release)
        article = preprocess_article(article, HEADLINE_KEYWORDS)

        if not article:
            continue

        alert = Alert(article)
        alert.post_process()

        print(f"---PRESS RELEASE #{i}---")
        print(article)

        print(f"Category: {alert.category}")
        print(f"Summary: {alert.summary}")
        print(f"Valid: {alert.is_valid()}")

        print()


filter_testing(number_of_releases=10_000, start_page=1)
