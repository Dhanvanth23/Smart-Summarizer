# modules/translation/service.py
from mtranslate import translate

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

def detect_language(text):
    """Detect the language of a text"""
    try:
        # This is a bit of a hack - we're using the fact that mtranslate returns
        # language detection info as part of the translation
        detected_lang = translate(text[:100], to_language='en', from_language='auto').split('=')[-1].strip()
        return detected_lang
    except Exception as e:
        print(f"Language detection error: {e}")
        return 'en'  # Default to English