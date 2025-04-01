from flask import Flask, render_template, request, jsonify, redirect, url_for
from transformers import BartForConditionalGeneration, BartTokenizer
import requests
from bs4 import BeautifulSoup
from mtranslate import translate
from gtts import gTTS
import os
import http.client
import json
import uuid
import time

app = Flask(__name__)

# Directory to store audio files
AUDIO_DIR = "static/audio"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# Load BART model and tokenizer
model_name = "facebook/bart-large-cnn"
model = BartForConditionalGeneration.from_pretrained(model_name)
tokenizer = BartTokenizer.from_pretrained(model_name)

# Supported languages with their codes and names
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'ta': 'Tamil',
    'hi': 'Hindi',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ar': 'Arabic'
}

# News categories
NEWS_CATEGORIES = {
    'general': 'General',
    'business': 'Business',
    'technology': 'Technology',
    'entertainment': 'Entertainment',
    'sports': 'Sports',
    'science': 'Science',
    'health': 'Health'
}

def fetch_article_text(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find article content in different ways
        article_content = soup.find('article')
        if article_content:
            paragraphs = article_content.find_all('p')
        else:
            # Try to find main content
            main_content = soup.find('main') or soup.find(id='content') or soup.find(class_='content')
            if main_content:
                paragraphs = main_content.find_all('p')
            else:
                # Fallback to all paragraphs
                paragraphs = soup.find_all('p')
        
        if not paragraphs:
            return None
        
        article_text = ' '.join([p.get_text() for p in paragraphs])
        return article_text
    except Exception as e:
        print(f"Error fetching article: {e}")
        return None

def translate_text(text, target_lang, src_lang='auto'):
    try:
        if not text or not text.strip():
            print("Translation error: Input text is empty.")
            return None
        
        translated = translate(text, to_language=target_lang, from_language=src_lang)
        
        if not translated:
            print("Translation error: No translation returned.")
            return None
        
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def summarize_text(text, max_length=150, min_length=50):
    try:
        inputs = tokenizer([text], max_length=1024, return_tensors="pt", truncation=True)
        
        # Generate summary with more control
        summary_ids = model.generate(
            inputs["input_ids"], 
            num_beams=4, 
            max_length=max_length, 
            min_length=min_length,
            length_penalty=2.0,
            early_stopping=True
        )
        
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
    except Exception as e:
        print(f"Summarization error: {e}")
        return None

def text_to_speech(text, language='en'):
    try:
        # Generate unique filename
        filename = f"summary_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(AUDIO_DIR, filename)
        
        # Clean up old files (keep only last 20)
        cleanup_audio_files(20)
        
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(file_path)
        return os.path.basename(file_path)
    except Exception as e:
        print(f"Text-to-speech error: {e}")
        return None

def cleanup_audio_files(keep_latest=20):
    """Delete old audio files, keeping only the latest n files"""
    try:
        files = [os.path.join(AUDIO_DIR, f) for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
        if len(files) <= keep_latest:
            return
        
        # Sort files by creation time (oldest first)
        files.sort(key=lambda x: os.path.getctime(x))
        
        # Delete oldest files
        for file_to_delete in files[:-keep_latest]:
            os.remove(file_to_delete)
    except Exception as e:
        print(f"Error cleaning up audio files: {e}")

def get_news_from_api(language='en', category='general'):
    try:
        conn = http.client.HTTPSConnection("newsnow.p.rapidapi.com")
        
        payload = json.dumps({
            "location": "us",
            "language": language,
            "category": category,
            "page": 1,
            "time_bounded": False
        })
        
        headers = {
            'x-rapidapi-key': "0e51d0e9a1mshf756a7e9aad1245p1a8e74jsn05b439507893",
            'x-rapidapi-host': "newsnow.p.rapidapi.com",
            'Content-Type': "application/json"
        }
        
        conn.request("POST", "/newsv2_top_news", payload, headers)
        res = conn.getresponse()
        data = res.read()
        news_data = json.loads(data.decode("utf-8"))
        
        # Process and return only relevant article data
        articles = []
        for article in news_data.get('articles', [])[:10]:  # Limit to 10 articles
            articles.append({
                'title': article.get('title', 'No title'),
                'description': article.get('description', ''),
                'url': article.get('url', '#'),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'image': article.get('urlToImage', '/static/img/news-placeholder.jpg')
            })
        
        return articles
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html', 
                          languages=SUPPORTED_LANGUAGES, 
                          categories=NEWS_CATEGORIES)

@app.route('/summarize', methods=['POST'])
def summarize():
    summary = None
    error = None
    audio_file = None
    original_text = None
    start_time = time.time()
    
    input_type = request.form['input_type']
    language = request.form['language']
    max_length = int(request.form.get('max_length', 150))
    
    if input_type == 'url':
        url = request.form['url']
        article_text = fetch_article_text(url)
        if article_text:
            original_text = article_text[:500] + "..." if len(article_text) > 500 else article_text
            if language != 'en':
                # Translate to English for summarization
                translated_text = translate_text(article_text, 'en', src_lang=language)
                if translated_text:
                    english_summary = summarize_text(translated_text, max_length)
                    if english_summary:
                        # Translate summary back to target language
                        summary = translate_text(english_summary, language, src_lang='en')
                else:
                    error = "Failed to translate text to English for summarization."
            else:
                summary = summarize_text(article_text, max_length)
            
            if summary:
                audio_file = text_to_speech(summary, language=language)
            else:
                error = "Failed to generate summary."
        else:
            error = "Failed to fetch article content from the URL."
    elif input_type == 'text':
        text = request.form['text']
        if text.strip():
            original_text = text
            if language != 'en':
                translated_text = translate_text(text, 'en', src_lang=language)
                if translated_text:
                    english_summary = summarize_text(translated_text, max_length)
                    if english_summary:
                        summary = translate_text(english_summary, language, src_lang='en')
                else:
                    error = "Failed to translate text to English for summarization."
            else:
                summary = summarize_text(text, max_length)
            
            if summary:
                audio_file = text_to_speech(summary, language=language)
            else:
                error = "Failed to generate summary."
        else:
            error = "Please provide some text to summarize."
    
    # Calculate processing time
    processing_time = round(time.time() - start_time, 2)
    
    # Redirect back if requested via Ajax
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'summary': summary,
            'error': error,
            'audio_file': audio_file,
            'processing_time': processing_time
        })
    
    return render_template('index.html', 
                         languages=SUPPORTED_LANGUAGES,
                         categories=NEWS_CATEGORIES,
                         summary=summary, 
                         original_text=original_text,
                         error=error, 
                         audio_file=audio_file if audio_file else None,
                         processing_time=processing_time)

@app.route('/get_news')
def get_news():
    language = request.args.get('language', 'en')
    category = request.args.get('category', 'general')
    articles = get_news_from_api(language, category)
    return jsonify(articles)

@app.route('/history')
def history():
    # This would ideally be fetched from a database
    # For now, we'll just display a message
    return render_template('history.html', languages=SUPPORTED_LANGUAGES, categories=NEWS_CATEGORIES)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)