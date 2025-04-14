# modules/utils/web.py
import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of common user agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

def validate_url(url):
    """
    Validate if a URL is properly formatted
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def fetch_article_text(url, max_retries=3):
    """
    Fetch and extract main text content from a news article URL.
    
    Args:
        url (str): The URL of the news article to fetch.
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        str: The extracted text content of the article or None if extraction failed.
    """
    if not validate_url(url):
        logger.error(f"Invalid URL format: {url}")
        return None
        
    retry_count = 0
    while retry_count < max_retries:
        try:
            # Rotate user agents to avoid being blocked
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.google.com/',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
            
            logger.info(f"Attempting to fetch article from: {url} (Attempt {retry_count + 1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 403 or response.status_code == 429:
                logger.warning(f"Access denied (status code: {response.status_code}). Retrying with different user agent.")
                retry_count += 1
                time.sleep(2 * retry_count)  # Exponential backoff
                continue
                
            response.raise_for_status()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'meta', 'noscript']):
                element.decompose()
            
            # Try multiple selection strategies to find content
            content = None
            
            # Strategy 1: Look for article tag
            article = soup.find('article')
            if article:
                content = article.get_text(separator='\n', strip=True)
                logger.info("Content extracted from article tag")
            
            # Strategy 2: Common article content classes
            if not content:
                for class_hint in ['content', 'article', 'post', 'entry', 'story', 'text', 'body']:
                    elements = soup.find_all(class_=lambda c: c and class_hint.lower() in c.lower())
                    if elements:
                        content = max([e.get_text(separator='\n', strip=True) for e in elements], 
                                    key=len, default=None)
                        if content:
                            logger.info(f"Content extracted from class containing '{class_hint}'")
                            break
            
            # Strategy 3: Look for main content tags
            if not content:
                main_content = soup.find('main') or soup.find(id='content') or soup.find(id='main')
                if main_content:
                    content = main_content.get_text(separator='\n', strip=True)
                    logger.info("Content extracted from main content tag")
            
            # Strategy 4: Fallback to body
            if not content:
                if soup.body:
                    content = soup.body.get_text(separator='\n', strip=True)
                    logger.info("Content extracted from body tag")
            
            # Clean up text
            if content:
                import re
                # Remove excessive whitespace
                content = re.sub(r'\s+', ' ', content)
                # Remove excessive newlines
                content = re.sub(r'\n{2,}', '\n\n', content)
                # If content is too short, consider it unsuccessful
                if len(content) < 500:
                    logger.warning(f"Extracted content too short ({len(content)} chars). Might be incomplete.")
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        time.sleep(2)
                        continue
                
                return content
            
            logger.warning("No content could be extracted from the page")
            return None
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            retry_count += 1
            time.sleep(2 * retry_count)  # Exponential backoff
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timed out for {url}: {e}")
            retry_count += 1
            time.sleep(2 * retry_count)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            # Don't retry for 404 errors
            if '404' in str(e):
                return None
            retry_count += 1
            time.sleep(2 * retry_count)
            
        except Exception as e:
            logger.error(f"Error fetching article from {url}: {type(e).__name__}: {str(e)}")
            retry_count += 1
            time.sleep(1)
    
    logger.error(f"Failed to fetch article after {max_retries} attempts: {url}")
    return None