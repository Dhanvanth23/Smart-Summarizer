import time
import uuid
import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from werkzeug.datastructures import ImmutableMultiDict

from config import SUPPORTED_LANGUAGES, NEWS_CATEGORIES, AUDIO_DIR
from utils.text_processing import process_text_input, fetch_article_text
from services.summarization import summarize_text
from services.audio_service import text_to_speech_openai, transcribe_audio_with_whisper
from services.translation import translate_text

main_routes = Blueprint('main_routes', __name__)

@main_routes.route('/')
def index():
    return render_template('index.html', languages=SUPPORTED_LANGUAGES, categories=NEWS_CATEGORIES)

@main_routes.route('/summarize', methods=['POST'])
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
        
        # Get summary
        summary, english_summary = summarize_text(
            text_for_processing, 
            language=language,
            max_length=max_length, 
            min_length=min_length
        )
        
        if not summary:
            raise ValueError("Failed to generate summary.")
            
        translated_text = english_summary
        
        # Generate audio if summarization successful
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

@main_routes.route('/process_input', methods=['POST'])
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
    
    # Create a new dictionary with all the parameters needed for the summarize endpoint
    if input_type == 'url':
        # For URL input
        return summarize_with_params(input_type, language, max_length, min_length, url=content)
    else:
        # For text input
        return summarize_with_params(input_type, language, max_length, min_length, text=content)

def summarize_with_params(input_type, language, max_length, min_length, url=None, text=None):
    """Helper function to call summarize with the right parameters"""
    # Store original request
    original_request = request
    
    # We need to create a new request context or modify the parameters
    # Since we can't modify request.form directly, use this approach:
    
    # Construct request data for the summarize function
    summary = None
    error = None
    audio_file = None
    original_text = None
    translated_text = None
    start_time = time.time()
    
    try:
        if input_type not in ['url', 'text', 'audio']:
            error = "Invalid input type. Please select URL, Text, or Audio."
            raise ValueError(error)
        
        if language not in SUPPORTED_LANGUAGES:
            language = 'en'
            
        if min_length >= max_length:
            min_length = max(10, max_length // 2)
        
        # Process based on input type
        if input_type == 'url':
            if not url or not url.strip():
                raise ValueError("URL is required.")
                
            article_text = fetch_article_text(url)
            if not article_text:
                raise ValueError("Failed to fetch content from URL.")
                
            original_text = article_text
            text_for_processing = article_text
            
        elif input_type == 'text':
            if not text or not text.strip():
                raise ValueError("Text input is required.")
                
            processed_text = process_text_input(text)
            if not processed_text:
                raise ValueError("Text is too short or invalid for summarization.")
                
            original_text = text
            text_for_processing = processed_text
        else:
            raise ValueError("Audio processing not supported through this endpoint.")
        
        # Get summary
        summary, english_summary = summarize_text(
            text_for_processing, 
            language=language,
            max_length=max_length, 
            min_length=min_length
        )
        
        if not summary:
            raise ValueError("Failed to generate summary.")
            
        translated_text = english_summary
        
        # Generate audio if summarization successful
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
    
    # Always return JSON for this endpoint
    return jsonify(response_data)

@main_routes.route('/history')
def history():
    return render_template('history.html', languages=SUPPORTED_LANGUAGES, categories=NEWS_CATEGORIES)