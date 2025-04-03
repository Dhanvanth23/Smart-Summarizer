import requests
from bs4 import BeautifulSoup

def process_text_input(text):
    """Clean and prepare text for summarization"""
    if not text or not isinstance(text, str):
        return None
    
    text = ' '.join(text.strip().split())
    return text if len(text) >= 50 else None

def fetch_article_text(url):
    """Extract article text from URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple strategies to find content
        content_containers = [
            soup.find('article'),
            soup.find('main') or soup.find(id='content') or soup.find(class_='content'),
            soup.find(class_=['article-body', 'story-content', 'entry-content', 'post-content'])
        ]
        
        for container in content_containers:
            if container:
                paragraphs = container.find_all('p')
                if paragraphs:
                    break
        else:
            paragraphs = soup.find_all('p')
        
        if not paragraphs:
            return None
        
        # Filter out short paragraphs (likely ads/navigation)
        article_text = ' '.join(p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30)
        return article_text
    except Exception as e:
        print(f"Error fetching article: {e}")
        return None