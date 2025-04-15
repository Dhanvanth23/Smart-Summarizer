# modules/news/service2.py
import http.client
import json
import logging
import time
import requests
from datetime import datetime
from config import NEWS_API_KEY, NEWS_API_PRIMARY, NEWS_API_BACKUP
from modules.utils.web import fetch_article_text
from modules.utils.shared import summarize_text

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def summarize_article(url, description, language='en', max_length=150):
    """Helper function to summarize article content"""
    try:
        # First try to fetch and summarize the full article
        article_text = fetch_article_text(url)
        if article_text:
            summary, _ = summarize_text(article_text, language, max_length)
            if summary:
                return summary
        
        # If full article fetch fails, summarize the description
        if description:
            summary, _ = summarize_text(description, language, max_length)
            if summary:
                return summary
            
    except Exception as e:
        logger.error(f"Error summarizing article {url}: {str(e)}")
    
    return description[:200] + '...' if description else 'No description available'

def get_news_from_news_api(language='en', category='general', count=20, max_retries=3):
    """
    Fetch news from News API with retry mechanism and summarization
    """
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            url = f"https://newsapi.org/v2/top-headlines"
            
            params = {
                'apiKey': NEWS_API_KEY,
                'language': language,
                'category': category,
                'pageSize': count
            }
            
            logger.info(f"Making request to News API: {url}")
            response = requests.get(url, params=params, timeout=10)
            
            logger.info(f"News API response status: {response.status_code}")
            
            if response.status_code == 429:
                logger.warning("Rate limited by News API")
                retry_count += 1
                time.sleep(retry_count * 2)
                continue
                
            if response.status_code != 200:
                logger.error(f"News API error: {response.text}")
                retry_count += 1
                time.sleep(1)
                continue
            
            try:
                news_data = response.json()
                articles = news_data.get('articles', [])
                
                logger.info(f"Found {len(articles)} articles from News API")
                
                formatted_articles = []
                for article in articles:
                    # Get article details
                    title = article.get('title', 'No title')
                    description = article.get('description', 'No description available')
                    url = article.get('url', '#')
                    
                    # Generate summary
                    summary = summarize_article(url, description, language)
                    
                    formatted_articles.append({
                        'title': title,
                        'description': description,
                        'summary': summary,
                        'url': url,
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'image': article.get('urlToImage', '/static/img/news-placeholder.jpg'),
                        'published_at': article.get('publishedAt', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    })
                    logger.info(f"Processed and summarized article: {title[:50]}...")
                
                if formatted_articles:
                    logger.info(f"Returning {len(formatted_articles)} articles from News API")
                    return formatted_articles
                else:
                    logger.warning("No articles extracted from response")
                    retry_count += 1
                    continue
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {str(e)}")
                retry_count += 1
                time.sleep(1)
                continue
                
        except requests.exceptions.RequestException as e:
            logger.error(f"News API request error: {str(e)}")
            retry_count += 1
            time.sleep(1)
            continue
    
    logger.error(f"Failed to fetch news after {max_retries} attempts")
    return get_news_from_backup_api(language, category, count)

def get_news_from_backup_api(language='en', category='general', count=20, max_retries=3):
    """
    Backup news API if the primary one fails
    """
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            url = f"{NEWS_API_BACKUP['base_url']}/top-headlines"
            
            params = {
                'apiKey': NEWS_API_KEY,
                'language': language,
                'country': 'us',
                'category': category,
                'pageSize': count
            }
            
            logger.info(f"Trying backup API: {url}")
            response = requests.get(url, params=params, timeout=10)
            
            logger.info(f"Backup API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Backup API error: {response.text}")
                retry_count += 1
                time.sleep(1)
                continue
            
            try:
                news_data = response.json()
                articles = news_data.get('articles', [])
                
                logger.info(f"Found {len(articles)} articles from backup API")
                
                formatted_articles = []
                for article in articles:
                    # Get article details
                    title = article.get('title', 'No title')
                    description = article.get('description', 'No description available')
                    url = article.get('url', '#')
                    
                    # Generate summary
                    summary = summarize_article(url, description, language)
                    
                    formatted_articles.append({
                        'title': title,
                        'description': description,
                        'summary': summary,
                        'url': url,
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'image': article.get('urlToImage', '/static/img/news-placeholder.jpg'),
                        'published_at': article.get('publishedAt', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    })
                    logger.info(f"Processed and summarized backup article: {title[:50]}...")
                
                if formatted_articles:
                    logger.info(f"Returning {len(formatted_articles)} articles from backup API")
                    return formatted_articles
                    
            except json.JSONDecodeError as e:
                logger.error(f"Backup API JSON parse error: {str(e)}")
                retry_count += 1
                continue
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Backup API request error: {str(e)}")
            retry_count += 1
            time.sleep(1)
            continue
    
    logger.error("Both primary and backup APIs failed")
    return [{
        'title': 'Unable to fetch news at this time',
        'description': 'Our news services are currently unavailable. Please try again later.',
        'summary': 'Service unavailable',
        'url': '#',
        'source': 'System',
        'image': '/static/img/news-placeholder.jpg',
        'published_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }]

def get_news(language='en', category='general', count=20):
    """
    Main function to get news with appropriate error handling
    
    Args:
        language (str): Language code
        category (str): News category
        count (int): Number of articles to fetch
        
    Returns:
        list: List of news articles
    """
    articles = get_news_from_news_api(language, category, count)
    
    if not articles:
        logger.warning("Both primary and backup APIs failed to return articles")
        # Return a placeholder article
        return [{
            'title': 'Unable to fetch news at this time',
            'description': 'Our news services are currently unavailable. Please try again later.',
            'summary': 'Service unavailable',
            'url': '#',
            'source': 'System',
            'image': '/static/img/news-placeholder.jpg',
            'published_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }]
        
    return articles