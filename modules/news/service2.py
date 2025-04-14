# modules/news/service2.py
import requests
import logging
import time
import json
from config import RAPIDAPI_KEY, NEWS_API_KEY
from config import INDIA_TODAY_CATEGORIES, NEWS_API_PRIMARY, NEWS_API_BACKUP

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_news_from_api(language='en', category='general', count=20, max_retries=3):
    """
    Fetch news from primary API (India Today) with retry mechanism
    
    Args:
        language (str): Language code
        category (str): News category
        count (int): Number of articles to fetch
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        list: List of news articles
    """
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Map the category to India Today's categories
            api_category = INDIA_TODAY_CATEGORIES.get(category, 'India')
            
            # Updated API endpoint structure to match India Today's actual API
            url = f"https://india-today-unofficial.p.rapidapi.com/news/{api_category}"
            
            headers = {
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "india-today-unofficial.p.rapidapi.com",
                "User-Agent": "NewsAppV2/1.0"
            }
            
            logger.info(f"Fetching news from primary API: {url} (Attempt {retry_count + 1}/{max_retries})")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            # Log the response status
            logger.info(f"Primary API response status: {response.status_code}")
            
            # Check if we're being rate limited
            if response.status_code == 429:
                retry_count += 1
                logger.warning(f"Rate limited by primary API. Retrying in {retry_count * 2} seconds...")
                time.sleep(retry_count * 2)
                continue
                
            if response.status_code != 200:
                logger.warning(f"Primary API returned status code: {response.status_code}")
                
                # Try to get error message from response
                try:
                    error_msg = response.json().get('message', 'Unknown error')
                    logger.warning(f"API error message: {error_msg}")
                except:
                    logger.warning(f"Raw response: {response.text[:100]}...")
                
                # For 4xx codes (except 429), don't retry
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    logger.error("Client error - switching to backup API")
                    return get_news_from_backup_api(language, category, count)
                
                # For 5xx codes, retry
                retry_count += 1
                time.sleep(retry_count * 2)
                continue
            
            # Parse the response
            try:
                news_data = response.json()
                
                # Log response structure for debugging
                logger.debug(f"Primary API response keys: {list(news_data.keys())}")
                
                articles = []
                
                # Updated parsing logic for India Today API response
                if not isinstance(news_data, list):
                    news_items = news_data.get('data', [])
                else:
                    news_items = news_data  # Sometimes the API returns a direct list
                
                if not news_items:
                    logger.warning("Primary API returned no news items")
                    
                for article in news_items[:count]:
                    # Handle different field names that might be present
                    title = article.get('title', article.get('headline', 'No title'))
                    description = (article.get('content', '') or 
                                  article.get('description', '') or 
                                  article.get('summary', ''))
                    url = (article.get('url', '') or 
                          article.get('link', '') or 
                          article.get('article_url', '#'))
                    image = (article.get('image', '') or 
                            article.get('urlToImage', '') or 
                            article.get('image_url', '') or
                            '/static/img/news-placeholder.jpg')
                    published = (article.get('published_date', '') or 
                                article.get('publishedAt', '') or 
                                article.get('date', ''))
                    
                    articles.append({
                        'title': title,
                        'description': description,
                        'url': url,
                        'source': article.get('source', {}).get('name', 'India Today') if isinstance(article.get('source'), dict) else 'India Today',
                        'image': image,
                        'published_at': published
                    })
                
                if articles:
                    logger.info(f"Successfully fetched {len(articles)} articles from primary API")
                    return articles
                else:
                    logger.warning("No articles extracted from primary API response")
                    return get_news_from_backup_api(language, category, count)
                    
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from primary API response")
                logger.debug(f"Response content: {response.text[:100]}...")
                retry_count += 1
                time.sleep(1)
                continue
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for primary API: {e}")
            retry_count += 1
            time.sleep(retry_count * 2)
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timed out for primary API: {e}")
            retry_count += 1
            time.sleep(retry_count * 2)
            
        except Exception as e:
            logger.error(f"Error fetching news from primary API: {type(e).__name__}: {str(e)}")
            retry_count += 1
            time.sleep(1)
    
    logger.error(f"Failed to fetch news from primary API after {max_retries} attempts")
    return get_news_from_backup_api(language, category, count)

# No changes needed to the backup API or other functions
def get_news_from_backup_api(language='en', category='general', count=20, max_retries=3):
    """
    Backup news API (NewsAPI) if the primary one fails
    
    Args:
        language (str): Language code
        category (str): News category
        count (int): Number of articles to fetch
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        list: List of news articles
    """
    # Existing implementation remains unchanged
    # ...
    
    # Simplified for brevity - refer to original code for complete implementation
    return []

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
    articles = get_news_from_api(language, category, count)
    
    if not articles:
        logger.warning("Both primary and backup APIs failed to return articles")
        # Return a placeholder article
        return [{
            'title': 'Unable to fetch news at this time',
            'description': 'Our news services are currently unavailable. Please try again later.',
            'url': '#',
            'source': 'System',
            'image': '/static/img/news-placeholder.jpg',
            'published_at': ''
        }]
        
    return articles