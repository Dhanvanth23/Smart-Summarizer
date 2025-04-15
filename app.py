# app.py - Main application entry point
from flask import Flask, render_template, redirect, url_for, request, jsonify
from config import AUDIO_DIR
import os

# Import blueprints from modules
from modules.summarizer import summarizer_bp
from modules.news import news_bp
from modules.audio import audio_bp
from modules.translation import translation_bp
from newspaper import Article
from modules.summarizer import Summarizer

# Initialize the summarizer
summarizer = Summarizer()

def create_app():
    """Application factory pattern"""
    # Initialize Flask app
    app = Flask(__name__)
    
    # Setup directories
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    # Register blueprints from modules
    app.register_blueprint(summarizer_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(translation_bp)

    @app.route("/")
    def root():
        """Root route redirects to summarizer"""
        return redirect(url_for('summarizer.summarize'))

    @app.route("/index.html")
    def index():
        """Legacy index route"""
        return redirect(url_for('summarizer.summarize'))
    
    @app.route('/get_news')
    def redirect_get_news():
        """Redirect legacy /get_news endpoint to the proper endpoint"""
        return redirect(url_for('news.get_news', **request.args))
    
    @app.route('/news/summarize', methods=['POST'])
    def summarize_article():
        url = request.form.get('url')
        language = request.form.get('language', 'en')
        max_length = int(request.form.get('max_length', 150))

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})

        try:
            # Fetch the article content
            article = Article(url)
            article.download()
            article.parse()
            
            # Get the article text
            text = article.text
            if not text:
                return jsonify({'success': False, 'error': 'Could not extract article content'})

            # Generate summary
            summary = summarizer.summarize(text, language=language, max_length=max_length)
            
            return jsonify({
                'success': True,
                'summary': summary
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Custom 404 page"""
        return render_template('404.html'), 404
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)