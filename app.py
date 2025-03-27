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
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    # Attempt to download the article
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f'Failed to download the content of the URL: {e}')
    
    if response.status_code == 403:
        raise ValueError(f"Access Denied (403 Forbidden) for URL: {url}")

    # Parse the article
    article = Article(url, browser_user_agent=headers["User-Agent"])
    article.download()
    article.parse()
    article.nlp()

    # print("Extracted Text:", article.text)  # Debugging output

    if not article.text.strip():
        raise ValueError("Article extraction failed! No text found.")

    article.nlp()
    print("Generated Summary:", article.summary)  # Debugging output

    # Extract information
    title = article.title
    authors = article.authors
    publication_date = article.publish_date
    summary = article.summary

    # Perform sentiment analysis
    analysis = TextBlob(summary)
    # sentiment = analysis.sentiment
    sentiment_polarity = analysis.sentiment.polarity
    sentiment_subjectivity = analysis.sentiment.subjectivity

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
            'polarity': sentiment_polarity,
            'subjectivity': sentiment_subjectivity
        },
        'website_name': website_name
    }

    return result

import feedparser
from flask import Flask, render_template, request, redirect
# from pyspark.sql.connect.functions import array_insert
# from summarizer import summarize_article

app = Flask(__name__)

# RSS_FEEDS = {
#     'Yahoo Finance': 'https://finance.yahoo.com/news/rssindex',
#     'Hacker News': 'https://news.ycombinator.com/rss',
#     'Wall Street Journal': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
#     'CNBC': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069'
# }
import os

# File to store the RSS feed sources
SOURCE_FILE = "sources.txt"

def load_sources():
    """Read the RSS sources from the text file and return a dictionary."""
    sources = {}
    
    if os.path.exists(SOURCE_FILE):
        with open(SOURCE_FILE, 'r') as file:
            for line in file:
                line = line.strip()
                if line:  # Ignore empty lines
                    try:
                        name, url = line.split(", ", 1)  # Split into name and URL
                        sources[name] = url
                    except ValueError:
                        print(f"Skipping invalid line in sources.txt: {line}")
    
    return sources

# Load sources at startup
RSS_FEEDS = load_sources()


@app.route('/')
def index():
    articles = []
    for source, feed in RSS_FEEDS.items():
        parsed_feed = feedparser.parse(feed)
        entries = [(source, entry) for entry in parsed_feed.entries]
        articles.extend(entries)

    articles = sorted(articles, key=lambda x: x[1].published_parsed, reverse=True)

    # print(articles)

    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_articles = len(articles)
    start = (page-1) * per_page
    end = start + per_page
    paginated_articles = articles[start:end]

    return render_template('index.html', articles=paginated_articles, page=page,
                           total_pages = total_articles // per_page + 1, length = len(paginated_articles))


@app.route('/search')
def search():
    query = request.args.get('q')

    articles = []
    for source, feed in RSS_FEEDS.items():
        parsed_feed = feedparser.parse(feed)
        entries = [(source, entry) for entry in parsed_feed.entries]
        articles.extend(entries)

    results = [article for article in articles if query.lower() in article[1].title.lower()]

    return render_template('search_results.html', articles=results, query=query)

@app.route('/summarize')
def summarize():
    url = request.args.get('url')
    data = summarize_article(url)

    # print(data["summary"])

    return render_template('testing.html', data = data)

@app.route('/add_source', methods=['GET', 'POST'])
def add_source():
    if request.method == 'POST':
        source_name = request.form.get('source_name', '').strip()  # Default to empty string
        source_url = request.form.get('source_url', '').strip()    # Default to empty string

        if source_name and source_url:
            # Append the new source (name + URL) to sources.txt
            with open(SOURCE_FILE, 'a') as file:
                file.write(f"{source_name}, {source_url}\n")
            
            # Reload sources
            global RSS_FEEDS
            RSS_FEEDS = load_sources()
        
        return redirect('/')

    return render_template('add_source.html')

if __name__ == '__main__':
    app.run(debug=True)