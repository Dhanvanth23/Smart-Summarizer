# modules/news/__init__.py
import logging
from flask import Blueprint, request, jsonify, render_template, abort
from config import SUPPORTED_LANGUAGES, NEWS_CATEGORIES
from .service2 import get_news_from_api
from ..utils.web import fetch_article_text, validate_url
from modules.utils.shared import summarize_text
from ..audio.service3 import text_to_speech_openai

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
news_bp = Blueprint('news', __name__, url_prefix='/news')

@news_bp.route('/')
def news_home():
    """News homepage"""
    return render_template('news.html', 
                          languages=SUPPORTED_LANGUAGES, 
                          categories=NEWS_CATEGORIES)

@news_bp.route('/get_articles')
def get_news():
    """Get news articles with pagination"""
    try:
        language = request.args.get('language', 'en')
        category = request.args.get('category', 'general')
        count = int(request.args.get('count', 20))
        page = int(request.args.get('page', 1))
        
        # Validate inputs
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language requested: {language}")
            language = 'en'  # Default to English
            
        if category not in NEWS_CATEGORIES:
            logger.warning(f"Unsupported category requested: {category}")
            category = 'general'  # Default to general news
            
        if count < 1 or count > 50:
            logger.warning(f"Invalid count requested: {count}")
            count = 20  # Default to 20 articles
            
        if page < 1:
            logger.warning(f"Invalid page requested: {page}")
            page = 1  # Default to first page
        
        # Fetch articles
        logger.info(f"Fetching news: language={language}, category={category}, count={count}, page={page}")
        articles = get_news_from_api(language, category, count)
        
        # Handle pagination
        start_idx = (page - 1) * (count // 2)
        end_idx = start_idx + (count // 2)
        
        # Check if we have any articles
        if not articles:
            logger.warning("No articles returned from API")
            return jsonify({
                'articles': [{
                    'title': 'Unable to fetch news at this time',
                    'description': 'Please try again later or select a different category.',
                    'url': '#',
                    'source': 'System',
                    'image': '/static/img/news-placeholder.jpg',
                    'published_at': ''
                }],
                'total': 1,
                'page': page,
                'hasMore': False
            })
        
        # Ensure start_idx is within bounds
        if start_idx >= len(articles):
            logger.warning(f"Requested page {page} exceeds available articles ({len(articles)})")
            start_idx = 0
            page = 1
            
        # Get the paginated articles
        paginated_articles = articles[start_idx:end_idx] if articles else []
        
        return jsonify({
            'articles': paginated_articles,
            'total': len(articles),
            'page': page,
            'hasMore': end_idx < len(articles)
        })
    except Exception as e:
        logger.error(f"Error in get_news endpoint: {type(e).__name__}: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred. Please try again later.',
            'articles': [],
            'total': 0,
            'page': 1,
            'hasMore': False
        }), 500

@news_bp.route('/summarize', methods=['POST'])
def summarize_news():
    """Endpoint to summarize a news article URL directly"""
    try:
        url = request.form.get('url')
        language = request.form.get('language', 'en')
        max_length = int(request.form.get('max_length', 150))
        
        # Validate URL
        if not url or not validate_url(url):
            logger.warning(f"Invalid URL submitted: {url}")
            return jsonify({
                'error': 'Please provide a valid URL',
                'success': False
            }), 400
        
        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language requested: {language}")
            language = 'en'  # Default to English
        
        # Validate max_length
        if max_length < 50 or max_length > 500:
            logger.warning(f"Invalid max_length requested: {max_length}")
            max_length = 150  # Default to 150
        
        logger.info(f"Fetching article from URL: {url}")
        article_text = fetch_article_text(url)
        
        if not article_text:
            logger.warning(f"Failed to fetch article content from URL: {url}")
            return jsonify({
                'error': 'Failed to fetch article content. The URL might be inaccessible or blocked.',
                'success': False,
                'suggestions': [
                    'Check if the URL is correct',
                    'Try a different article',
                    'The website might be blocking our access'
                ]
            }), 404
        
        # Summarize text
        logger.info(f"Summarizing article (length: {len(article_text)} chars) in language: {language}")
        summary, english_summary = summarize_text(article_text, language, max_length)
        
        if not summary:
            logger.warning("Failed to generate summary")
            return jsonify({
                'error': 'Failed to generate summary. Please try again later.',
                'success': False
            }), 500
        
        # Generate audio if requested
        try:
            audio_file = text_to_speech_openai(summary, language)
            logger.info(f"Generated audio file: {audio_file}")
        except Exception as e:
            logger.error(f"Error generating audio: {type(e).__name__}: {str(e)}")
            audio_file = None
        
        return jsonify({
            'summary': summary,
            'audio_file': audio_file,
            'language': SUPPORTED_LANGUAGES.get(language, language),
            'engine': 'T5',
            'success': True,
            'article_length': len(article_text),
            'summary_length': len(summary)
        })
    except Exception as e:
        logger.error(f"Error in summarize_news endpoint: {type(e).__name__}: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred while summarizing the article.',
            'success': False
        }), 500

@news_bp.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@news_bp.errorhandler(500)
def internal_server_error(e):
    return jsonify({'error': 'Internal server error'}), 500