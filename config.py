import os

# Directory configurations
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# T5 model configuration
T5_MODEL_NAME = "t5-base"

# Language configurations
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

# API keys should ideally be in environment variables
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', 'your_newsapi_key_here')
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '0e51d0e9a1mshf756a7e9aad1245p1a8e74jsn05b439507893')