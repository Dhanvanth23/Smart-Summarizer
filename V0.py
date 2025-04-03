from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from mtranslate import translate
import os
import uuid
import time
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Initialize Flask app
app = Flask(__name__)

# Setup directories
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# T5 model initialization
T5_MODEL_NAME = "t5-base"
t5_tokenizer = None
t5_model = None

# Language and category configurations
SUPPORTED_LANGUAGES = {
    'en': 'English',
    # Indian languages
    'ta': 'Tamil', 'hi': 'Hindi', 'bn': 'Bengali', 'te': 'Telugu',
    'mr': 'Marathi', 'ur': 'Urdu', 'gu': 'Gujarati', 'kn': 'Kannada',
    'ml': 'Malayalam', 'pa': 'Punjabi', 'or': 'Odia',
    # Other global languages
    'es': 'Spanish', 'fr': 'French', 'de': 'German', 'zh': 'Chinese',
    'ja': 'Japanese', 'ar': 'Arabic', 'ru': 'Russian', 'pt': 'Portuguese',
    'ko': 'Korean', 'it': 'Italian', 'nl': 'Dutch', 'tr': 'Turkish',
    'vi': 'Vietnamese', 'th': 'Thai', 'id': 'Indonesian', 'ms': 'Malay',
    'sv': 'Swedish', 'pl': 'Polish', 'fi': 'Finnish', 'no': 'Norwegian'
}

TTS_VOICE_MAPPING = {
    'en': 'alloy', 'es': 'nova', 'fr': 'echo', 'de': 'onyx', 'ja': 'shimmer'
    # Default to 'alloy' for other languages
}

NEWS_CATEGORIES = {
    'general': 'General', 'business': 'Business', 'technology': 'Technology',
    'entertainment': 'Entertainment', 'sports': 'Sports', 'science': 'Science',
    'health': 'Health', 'politics': 'Politics', 'world': 'World',
    'finance': 'Finance', 'education': 'Education', 'environment': 'Environment'
}

def load_t5_model():
    """Load T5 model and tokenizer on demand"""
    global t5_tokenizer, t5_model
    if t5_tokenizer is None or t5_model is None:
        print("Loading T5 model and tokenizer...")
        t5_tokenizer = T5Tokenizer.from_pretrained(T5_MODEL_NAME)
        t5_model = T5ForConditionalGeneration.from_pretrained(T5_MODEL_NAME)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        t5_model = t5_model.to(device)
        print(f"T5 model loaded on {device}")

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

def process_text_input(text):
    """Clean and prepare text for summarization"""
    if not text or not isinstance(text, str):
        return None
    
    text = ' '.join(text.strip().split())
    return text if len(text) >= 50 else None

def translate_text(text, target_lang, src_lang='auto'):
    """Translate text using Google Translate"""
    try:
        if not text or not text.strip():
            return None
        
        # Split long text into chunks
        max_chunk_length = 4000
        chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
        
        translated_chunks = []
        for chunk in chunks:
            translated_chunk = translate(chunk, to_language=target_lang, from_language=src_lang)
            if translated_chunk:
                translated_chunks.append(translated_chunk)
        
        return ' '.join(translated_chunks) if translated_chunks else None
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def summarize_text_with_t5(text, max_length=150, min_length=50):
    """Summarize text using T5 model"""
    try:
        load_t5_model()
        
        input_text = "summarize: " + text
        inputs = t5_tokenizer.encode(input_text, return_tensors="pt", truncation=True, max_length=1024)
        
        if torch.cuda.is_available():
            inputs = inputs.to('cuda')
        
        summary_ids = t5_model.generate(
            inputs, 
            max_length=max_length,
            min_length=min_length,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )
        
        summary = t5_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
    except Exception as e:
        print(f"T5 summarization error: {e}")
        return summarize_text_with_gpt(text, max_length, min_length)

def summarize_text_with_gpt(text, max_length=150, min_length=50):
    """Fallback summarization using GPT"""
    try:
        import openai  # Import only when needed
        
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        prompt = f"""Please summarize the following text in a concise and informative way. 
        Aim for a summary that's between {min_length} and {max_length} tokens long.
        
        Text to summarize: {text}
        
        Summary:"""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a highly skilled summarization assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_length,
            temperature=0.5,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT summarization error: {e}")
        return None

def text_to_speech_openai(text, language='en'):
    """Generate speech using OpenAI's TTS API"""
    try:
        import openai  # Import only when needed
        
        filename = f"summary_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(AUDIO_DIR, filename)
        
        cleanup_audio_files(30)
        
        voice = TTS_VOICE_MAPPING.get(language, 'alloy')
        
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        response.stream_to_file(file_path)
        return os.path.basename(file_path)
    except Exception as e:
        print(f"OpenAI TTS error: {e}")
        return text_to_speech_fallback(text, language)

def text_to_speech_fallback(text, language='en'):
    """Fallback to gTTS if OpenAI TTS fails"""
    try:
        from gtts import gTTS
        
        tts_language_map = {
            'zh': 'zh-CN', 'no': 'nb-NO', 'ur': 'ur',
        }
        
        tts_lang = tts_language_map.get(language, language)
        filename = f"summary_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(AUDIO_DIR, filename)
        
        try:
            tts = gTTS(text=text, lang=tts_lang, slow=False)
            tts.save(file_path)
            return os.path.basename(file_path)
        except ValueError:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(file_path)
            return os.path.basename(file_path)
    except Exception as e:
        print(f"Text-to-speech fallback error: {e}")
        return None

def cleanup_audio_files(keep_latest=30):
    """Delete old audio files, keeping only the latest n files"""
    try:
        files = [os.path.join(AUDIO_DIR, f) for f in os.listdir(AUDIO_DIR) 
                if f.endswith('.mp3') or f.endswith('.wav')]
        if len(files) <= keep_latest:
            return
        
        files.sort(key=lambda x: os.path.getctime(x))
        for file_to_delete in files[:-keep_latest]:
            os.remove(file_to_delete)
    except Exception as e:
        print(f"Error cleaning up audio files: {e}")

def transcribe_audio_with_whisper(audio_file_path):
    """Transcribe audio using OpenAI's Whisper API"""
    try:
        import openai  # Import only when needed
        
        with open(audio_file_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return None

def get_news_from_api(language='en', category='general', count=20):
    """Fetch news from primary API"""
    try:
        api_language_map = {'zh': 'zh-CN', 'pt': 'pt-BR'}
        api_lang = api_language_map.get(language, language)
        
        url = f"https://google-news13.p.rapidapi.com/{category}"
        querystring = {"lr": f"{api_lang}-US", "num": count}
        headers = {
            "x-rapidapi-key": "0e51d0e9a1mshf756a7e9aad1245p1a8e74jsn05b439507893",
            "x-rapidapi-host": "google-news13.p.rapidapi.com"
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
        api_key = os.environ.get('NEWS_API_KEY', 'your_newsapi_key_here')
        
        params = {
            'category': api_category,
            'language': language[:2],
            'pageSize': count,
            'apiKey': api_key
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

@app.route('/')
def index():
    return render_template('index.html', languages=SUPPORTED_LANGUAGES, categories=NEWS_CATEGORIES)

@app.route('/summarize', methods=['POST'])
def summarize():
    """Main route for text summarization"""
    summary = None
    error = None
    audio_file = None
    original_text = None
    translated_text = None
    start_time = time.time()
    
    try:
        input_type = request.form.get('input_type')
        
        if input_type not in ['url', 'text', 'audio']:
            error = "Invalid input type. Please select URL, Text, or Audio."
            raise ValueError(error)
        
        language = request.form.get('language', 'en')
        if language not in SUPPORTED_LANGUAGES:
            language = 'en'
            
        max_length = int(request.form.get('max_length', 150))
        min_length = int(request.form.get('min_length', 50))
        
        if min_length >= max_length:
            min_length = max(10, max_length // 2)
        
        # Process based on input type
        if input_type == 'url':
            url = request.form.get('url', '')
            if not url.strip():
                raise ValueError("URL is required.")
                
            article_text = fetch_article_text(url)
            if not article_text:
                raise ValueError("Failed to fetch content from URL.")
                
            original_text = article_text
            text_for_processing = article_text
            
        elif input_type == 'text':
            text = request.form.get('text', '')
            if not text.strip():
                raise ValueError("Text input is required.")
                
            processed_text = process_text_input(text)
            if not processed_text:
                raise ValueError("Text is too short or invalid for summarization.")
                
            original_text = text
            text_for_processing = processed_text
            
        elif input_type == 'audio':
            if 'audio_file' not in request.files:
                raise ValueError("No audio file uploaded.")
                
            audio_file = request.files['audio_file']
            if audio_file.filename == '':
                raise ValueError("No audio file selected.")
                
            temp_filename = f"temp_{uuid.uuid4().hex}.mp3"
            temp_path = os.path.join(AUDIO_DIR, temp_filename)
            audio_file.save(temp_path)
            
            transcribed_text = transcribe_audio_with_whisper(temp_path)
            if not transcribed_text:
                raise ValueError("Failed to transcribe audio.")
                
            os.remove(temp_path)
            original_text = transcribed_text
            text_for_processing = transcribed_text
        
        source_lang = request.form.get('source_language', 'auto')
        
        # Handle translation if needed
        if language != 'en':
            english_text = translate_text(text_for_processing, 'en', src_lang=source_lang)
            if not english_text:
                raise ValueError("Failed to translate text to English.")
                
            english_summary = summarize_text_with_t5(english_text, max_length, min_length)
            if not english_summary:
                raise ValueError("Failed to generate summary in English.")
                
            translated_text = english_summary
            
            summary = translate_text(english_summary, language, src_lang='en')
            if not summary:
                raise ValueError("Failed to translate summary to target language.")
        else:
            summary = summarize_text_with_t5(text_for_processing, max_length, min_length)
            if not summary:
                raise ValueError("Failed to generate summary.")
        
        # Generate audio if summarization successful
        if summary:
            audio_file = text_to_speech_openai(summary, language=language)
                
    except ValueError as ve:
        error = str(ve)
    except Exception as e:
        error = f"An error occurred: {str(e)}"
        print(f"Unexpected error: {e}")
    
    processing_time = round(time.time() - start_time, 2)
    
    response_data = {
        'summary': summary,
        'original_text': original_text[:1000] + "..." if original_text and len(original_text) > 1000 else original_text,
        'english_summary': translated_text,
        'error': error,
        'audio_file': audio_file,
        'processing_time': processing_time,
        'language': SUPPORTED_LANGUAGES.get(language, language),
        'engine': 'T5'
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(response_data)
    
    return render_template('index.html', 
                         languages=SUPPORTED_LANGUAGES,
                         categories=NEWS_CATEGORIES,
                         summary=summary, 
                         original_text=original_text,
                         english_summary=translated_text,
                         error=error, 
                         audio_file=audio_file if audio_file else None,
                         processing_time=processing_time,
                         selected_language=language)

@app.route('/process_input', methods=['POST'])
def process_input():
    """Unified endpoint to process both URL and text inputs"""
    input_type = request.form.get('input_type')
    content = request.form.get('content', '')
    language = request.form.get('language', 'en')
    max_length = int(request.form.get('max_length', 150))
    min_length = int(request.form.get('min_length', 50))
    
    if not content.strip() and input_type != 'audio':
        return jsonify({
            'error': f"Please provide {'a URL' if input_type == 'url' else 'text'} to summarize."
        })
    
    form_data = {
        'input_type': input_type,
        'language': language,
        'max_length': max_length,
        'min_length': min_length
    }
    
    if input_type == 'url':
        form_data['url'] = content
    else:
        form_data['text'] = content
    
    from werkzeug.datastructures import ImmutableMultiDict
    request.form = ImmutableMultiDict(form_data)
    
    return summarize()

@app.route('/get_news')
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

@app.route('/summarize_news', methods=['POST'])
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
    
    summary = None
    if language != 'en':
        english_text = translate_text(article_text, 'en')
        if english_text:
            english_summary = summarize_text_with_t5(english_text, max_length)
            if english_summary:
                summary = translate_text(english_summary, language)
    else:
        summary = summarize_text_with_t5(article_text, max_length)
    
    if not summary:
        return jsonify({'error': 'Failed to generate summary'})
    
    audio_file = text_to_speech_openai(summary, language)
    
    return jsonify({
        'summary': summary,
        'audio_file': audio_file,
        'language': SUPPORTED_LANGUAGES.get(language, language),
        'engine': 'T5'
    })

@app.route('/process_audio', methods=['POST'])
def process_audio():
    """Endpoint to process audio input for transcription and summarization"""
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file uploaded'})
    
    audio_file = request.files['audio_file']
    language = request.form.get('language', 'en')
    max_length = int(request.form.get('max_length', 150))
    
    if audio_file.filename == '':
        return jsonify({'error': 'No audio file selected'})
    
    temp_filename = f"temp_{uuid.uuid4().hex}.mp3"
    temp_path = os.path.join(AUDIO_DIR, temp_filename)
    audio_file.save(temp_path)
    
    transcribed_text = transcribe_audio_with_whisper(temp_path)
    os.remove(temp_path)
    
    if not transcribed_text:
        return jsonify({'error': 'Failed to transcribe audio'})
    
    summary = summarize_text_with_t5(transcribed_text, max_length)
    if not summary:
        return jsonify({'error': 'Failed to generate summary'})
    
    audio_file = text_to_speech_openai(summary, language)
    
    return jsonify({
        'transcription': transcribed_text,
        'summary': summary,
        'audio_file': audio_file,
        'language': SUPPORTED_LANGUAGES.get(language, language)
    })

@app.route('/history')
def history():
    return render_template('history.html', languages=SUPPORTED_LANGUAGES, categories=NEWS_CATEGORIES)

@app.route('/detect_language', methods=['POST'])
def detect_language():
    """Endpoint to detect the language of a text"""
    try:
        text = request.form.get('text', '')
        if not text.strip():
            return jsonify({'error': 'Text is required'})
        
        detected_lang = translate(text, to_language='en', from_language='auto').split('=')[-1].strip()
        
        return jsonify({
            'detected_language': detected_lang,
            'language_name': SUPPORTED_LANGUAGES.get(detected_lang, 'Unknown')
        })
    except Exception as e:
        print(f"Language detection error: {e}")
        return jsonify({'error': 'Failed to detect language'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)