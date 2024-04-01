from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_caching import Cache
import requests
from datetime import datetime
import os

app = Flask (__name__)

app.config['CACHE_TYPE'] = 'simple'
cache = Cache (app)

@cache.memoize(timeout=600)
def get_top_headlines(country, api_key=os.getenv('NEWS_API_KEY')):
    url = f'https://newsapi.org/v2/top-headlines?country={country}&apiKey={api_key}'
    r = requests.get(url)
    if r.status_code != 200:
        abort (502, description = "Error fetching data from the news services")
    content = r.json()
    articles = content['articles']
    results = []
    for article in articles:
      
        author = article['author'] if article['author'] else 'Unknown'
        description = article['description'][:200] + '...' if article['description'] else ''
        result = {
            'title': article['title'],
            'author':author,
            'description': description,
            'url': article['url'],
            'image': article['urlToImage'],
            'publishedAt': article ['publishedAt']
        }
        results.append(result)
    return results

@app.template_filter ('format_date')
def format_date(value,format='%d-%m-%Y'):
    """Convert a datetime string"""
    if value:
        date_obj = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        return date_obj.strftime(format)
    return ''

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/top-headlines', methods=['GET', 'POST'])
def top_headlines():
    country_name = None
    if request.method == 'POST':
        country = request.form.get('country')
        if not country:
            flash('Please select a country.', 'info')
        else:            
            country_names = {
                    "us": "United States",
                    "gb": "United Kingdom",
                    "ca": "Canada",
                    "au": "Australia",
                    "de": "Germany",
                    "cz": "Czech Republic"
            }
            country_name = country_names.get(country, "this country")
            news_articles = get_top_headlines(country)
            page = 1
            total_pages = 1
            return render_template('top_headlines.html', articles=news_articles, topic=country , page=page, total_pages=total_pages, country_name=country_name)
    return render_template('top_headlines.html', country_name=country_name)

@cache.memoize(timeout=600)
def get_news(topic = 'ai',page=1, from_date=None, to_date=None, sort_by='publishedAt', language = None, api_key=os.getenv('NEWS_API_KEY')):
    url = f'https://newsapi.org/v2/everything?q={topic}&page={page}&apiKey={api_key}'

    if from_date:
        url +=f'&from={from_date}'
    if to_date:
        url +=f'&to={to_date}'
    if language:
        url += f'&language={language}'    
    url += f'&sortBy={sort_by}'  

    r = requests.get(url)
    if r.status_code != 200:
        abort (502, description = "Error fetching data from the news services")
    content= r.json()
    articles = content['articles']
    total_results = content['totalResults']
    max_size = 20
    total_pages = (total_results + max_size - 1) // max_size
    results = []
    for article in articles:
        description = article['description'][:1000] + '...' if article ['description'] else ''
        author = article['author'] if article['author'] else 'Unknown'
        source = article['source']['name'] if article['source']['name'] else ""
        date = article['publishedAt'] if article ['publishedAt'] else ""
        result = {
            'title': article['title'],
            'description':description,
            'url': article['url'],
            'image': article['urlToImage'],
            'author':author,
            'source':source,
            'publishedAt': date
        }
        results.append(result)
    return results, total_pages

@app.route('/search', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get data from the form submission for the initial search.
        topic = request.form.get('topic', 'world')
        page = 1  # Start from page 1 for a new search
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        language = request.form.get('language')
        sort_by = request.form.get('sort_by', 'publishedAt')
    else:
        # Get data from the query parameters for pagination links.
        topic = request.args.get('topic', 'world')
        page = request.args.get('page', 1, type=int)
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        language = request.args.get('language')
        sort_by = request.args.get('sort_by', 'publishedAt')

    news_articles, total_pages = get_news(topic, page, from_date, to_date, sort_by, language)
   
    return render_template(
        'index.html', 
        articles=news_articles, 
        topic=topic, 
        page=page, 
        total_pages=total_pages, 
        from_date=from_date, 
        to_date=to_date, 
        language=language, 
        sort_by=sort_by
    )


if __name__ == '__main__':
    app.run(debug=True)