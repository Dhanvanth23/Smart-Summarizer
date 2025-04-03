import requests
from config import RAPIDAPI_KEY, NEWS_API_KEY

def get_news_from_api(language='en', category='general', count=20):
    """Fetch news from primary API"""
    try:
        api_language_map = {'zh': 'zh-CN', 'pt': 'pt-BR'}
        api_lang = api_language_map.get(language, language)
        
        url = f"https://google-news13.p.rapidapi.com/{category}"
        querystring = {"lr": f"{api_lang}-US", "num": count}
        headers = {
            "x-rapidapi-key": "0e51d0e9a1mshf756a7e9aad1245p1a8e74jsn05b439507893",
            "x-rapidapi-host": "india-today-unofficial.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        
        if response.status_code != 200:
            return get_news_from_backup_api(language, category, count)
        
        news_data = response.json()
        articles = []
        
        for article in news_data.get('articles', [])[:count]:
            articles.append({
                'title': article.get('title', 'No title'),
                'description': article.get('snippet', ''),
                'url': article.get('link', '#'),
                'source': article.get('source', {}).get('title', 'Unknown'),
                'image': article.get('image', '/static/img/news-placeholder.jpg'),
                'published_at': article.get('pubDate', '')
            })
        
        return articles
    except Exception as e:
        print(f"Error fetching news: {e}")
        return get_news_from_backup_api(language, category, count)

def get_news_from_backup_api(language='en', category='general', count=20):
    """Backup news API if the primary one fails"""
    try:
        url = "https://newsapi.org/v2/top-headlines"
        
        category_map = {
            'general': 'general', 'business': 'business', 'technology': 'technology',
            'entertainment': 'entertainment', 'sports': 'sports', 'science': 'science',
            'health': 'health', 'politics': 'politics',
        }
        
        api_category = category_map.get(category, 'general')
        
        params = {
            'category': api_category,
            'language': language[:2],
            'pageSize': count,
            'apiKey': NEWS_API_KEY
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return []
            
        news_data = response.json()
        articles = []
        
        for article in news_data.get('articles', []):
            articles.append({
                'title': article.get('title', 'No title'),
                'description': article.get('description', ''),
                'url': article.get('url', '#'),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'image': article.get('urlToImage', '/static/img/news-placeholder.jpg'),
                'published_at': article.get('publishedAt', '')
            })
        
        return articles
    except Exception as e:
        print(f"Error fetching news from backup: {e}")
        return []