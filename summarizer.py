import nltk
from newspaper import Article
from textblob import TextBlob
from urllib.parse import urlparse
import validators
import requests

nltk.download('punkt')

def summarize_article(url):
    # Validate the URL
    if not validators.url(url):
        raise ValueError('Invalid URL provided.')

    # Attempt to download the article
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f'Failed to download the content of the URL: {e}')

    # Parse the article
    article = Article(url)
    article.download()
    article.parse()
    article.nlp()

    # Extract information
    title = article.title
    authors = article.authors
    publication_date = article.publish_date
    summary = article.summary

    # Perform sentiment analysis
    analysis = TextBlob(summary)
    sentiment = analysis.sentiment

    # Extract website name
    parsed_url = urlparse(url)
    website_name = parsed_url.netloc
    if website_name.startswith("www."):
        website_name = website_name[4:]

    # Compile the results
    result = {
        'title': title,
        'authors': authors,
        'publication_date': publication_date,
        'summary': summary,
        'sentiment': {
            'polarity': sentiment.polarity,
            'subjectivity': sentiment.subjectivity
        },
        'website_name': website_name
    }

    return result