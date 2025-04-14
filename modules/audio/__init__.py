# modules/audio/__init__.py
import os
import uuid
from flask import Blueprint, request, jsonify
from config import AUDIO_DIR, SUPPORTED_LANGUAGES
from modules.audio.service3 import transcribe_audio_with_whisper, text_to_speech_openai
from modules.translation.service1 import detect_language
from modules.utils.shared import summarize_text  # Import from shared utils instead

# Create blueprint
audio_bp = Blueprint('audio', __name__, url_prefix='/audio')

@audio_bp.route('/process', methods=['POST'])
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

@audio_bp.route('/tts', methods=['POST'])
def text_to_speech():
    """Endpoint to convert text to speech"""
    text = request.form.get('text', '')
    language = request.form.get('language', 'en')
    
    if not text.strip():
        return jsonify({'error': 'Text is required'})
    
    audio_file = text_to_speech_openai(text, language)
    
    if not audio_file:
        return jsonify({'error': 'Failed to generate audio'})
    
    return jsonify({
        'audio_file': audio_file,
        'language': SUPPORTED_LANGUAGES.get(language, language)
    })