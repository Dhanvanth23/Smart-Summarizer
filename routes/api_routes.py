import os
import uuid
from flask import Blueprint, request, jsonify
from config import SUPPORTED_LANGUAGES, AUDIO_DIR
from services.translation import detect_language
from services.audio_service import transcribe_audio_with_whisper, text_to_speech_openai
from services.summarization import summarize_text

api_routes = Blueprint('api_routes', __name__)

@api_routes.route('/detect_language', methods=['POST'])
def detect_language_route():
    """Endpoint to detect the language of a text"""
    try:
        text = request.form.get('text', '')
        if not text.strip():
            return jsonify({'error': 'Text is required'})
        
        detected_lang = detect_language(text)
        
        return jsonify({
            'detected_language': detected_lang,
            'language_name': SUPPORTED_LANGUAGES.get(detected_lang, 'Unknown')
        })
    except Exception as e:
        print(f"Language detection error: {e}")
        return jsonify({'error': 'Failed to detect language'})

@api_routes.route('/process_audio', methods=['POST'])
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
    
    summary, english_summary = summarize_text(transcribed_text, language, max_length)
    if not summary:
        return jsonify({'error': 'Failed to generate summary'})
    
    audio_file = text_to_speech_openai(summary, language)
    
    return jsonify({
        'transcription': transcribed_text,
        'summary': summary,
        'audio_file': audio_file,
        'language': SUPPORTED_LANGUAGES.get(language, language)
    })