# modules/news/service2.py
import http.client
import json
import logging
import time
import requests
from datetime import datetime
from config import NEWS_API_KEY, NEWS_API_PRIMARY, NEWS_API_BACKUP

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_news_from_news_api(language='en', category='general', count=20, max_retries=3):
    """
    Fetch news from News API with retry mechanism
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
                    formatted_articles.append({
                        'title': article.get('title', 'No title'),
                        'description': article.get('description', 'No description available')[:200] + '...' if article.get('description') else 'No description available',
                        'url': article.get('url', '#'),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'image': article.get('urlToImage', '/static/img/news-placeholder.jpg'),
                        'published_at': article.get('publishedAt', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    })
                    logger.info(f"Processed article: {article.get('title', '')[:50]}...")
                
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
            # Use the backup API URL from config
            url = f"{NEWS_API_BACKUP['base_url']}/top-headlines"
            
            params = {
                'apiKey': NEWS_API_KEY,
                'language': language,
                'country': 'us',  # Adding country parameter for wider compatibility
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
                    formatted_articles.append({
                        'title': article.get('title', 'No title'),
                        'description': article.get('description', 'No description available')[:200] + '...' if article.get('description') else 'No description available',
                        'url': article.get('url', '#'),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'image': article.get('urlToImage', '/static/img/news-placeholder.jpg'),
                        'published_at': article.get('publishedAt', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    })
                    logger.info(f"Processed backup article: {article.get('title', '')[:50]}...")
                
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
            'url': '#',
            'source': 'System',
            'image': '/static/img/news-placeholder.jpg',
            'published_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }]
        
    return articles