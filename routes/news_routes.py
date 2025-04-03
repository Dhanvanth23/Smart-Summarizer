from flask import Blueprint, request, jsonify
from config import SUPPORTED_LANGUAGES
from utils.text_processing import fetch_article_text
from services.summarization import summarize_text
from services.audio_service import text_to_speech_openai
from services.news_service import get_news_from_api

news_routes = Blueprint('news_routes', __name__)

@news_routes.route('/get_news')
def get_news():
    """Get news articles with pagination"""
    language = request.args.get('language', 'en')
    category = request.args.get('category', 'general')
    count = int(request.args.get('count', 20))
    page = int(request.args.get('page', 1))
    
    articles = get_news_from_api(language, category, count)
    
    start_idx = (page - 1) * (count // 2)
    end_idx = start_idx + (count // 2)
    paginated_articles = articles[start_idx:end_idx] if articles else []
    
    return jsonify({
        'articles': paginated_articles,
        'total': len(articles),
        'page': page,
        'hasMore': end_idx < len(articles)
    })

@news_routes.route('/summarize_news', methods=['POST'])
def summarize_news():
    """Endpoint to summarize a news article URL directly"""
    url = request.form.get('url')
    language = request.form.get('language', 'en')
    max_length = int(request.form.get('max_length', 150))
    
    if not url:
        return jsonify({'error': 'URL is required'})
    
    article_text = fetch_article_text(url)
    if not article_text:
        return jsonify({'error': 'Failed to fetch article content'})
    
    summary, english_summary = summarize_text(article_text, language, max_length)
    
    if not summary:
        return jsonify({'error': 'Failed to generate summary'})
    
    audio_file = text_to_speech_openai(summary, language)
    
    return jsonify({
        'summary': summary,
        'audio_file': audio_file,
        'language': SUPPORTED_LANGUAGES.get(language, language),
        'engine': 'T5'
    })