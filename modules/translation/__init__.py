# modules/translation/__init__.py
from flask import Blueprint, request, jsonify
from config import SUPPORTED_LANGUAGES
from .service1 import detect_language, translate_text

# Create blueprint
translation_bp = Blueprint('translation', __name__, url_prefix='/translation')

@translation_bp.route('/detect', methods=['POST'])
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

@translation_bp.route('/translate', methods=['POST'])
def translate_route():
    """Endpoint to translate text"""
    try:
        text = request.form.get('text', '')
        target_lang = request.form.get('target_lang', 'en')
        source_lang = request.form.get('source_lang', 'auto')
        
        if not text.strip():
            return jsonify({'error': 'Text is required'})
            
        translated = translate_text(text, target_lang, source_lang)
        
        if not translated:
            return jsonify({'error': 'Translation failed'})
            
        return jsonify({
            'translated_text': translated,
            'source_language': source_lang,
            'target_language': target_lang,
            'target_language_name': SUPPORTED_LANGUAGES.get(target_lang, target_lang)
        })
    except Exception as e:
        print(f"Translation error: {e}")
        return jsonify({'error': f'Translation error: {str(e)}'})