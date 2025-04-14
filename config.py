import os

# API Keys
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', "0e51d0e9a1mshf756a7e9aad1245p1a8e74jsn05b439507893")
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', "0e51d0e9a1mshf756a7e9aad1245p1a8e74jsn05b439507893")

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, 'static', 'audio')
os.makedirs(AUDIO_DIR, exist_ok=True)

# Expanded list of languages with ISO 639-1 codes
SUPPORTED_LANGUAGES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German', 'it': 'Italian',
    'pt': 'Portuguese', 'nl': 'Dutch', 'ru': 'Russian', 'zh': 'Chinese', 'ja': 'Japanese',
    'ko': 'Korean', 'ar': 'Arabic', 'hi': 'Hindi', 'bn': 'Bengali', 'pa': 'Punjabi',
    'te': 'Telugu', 'ta': 'Tamil', 'ur': 'Urdu', 'tr': 'Turkish', 'vi': 'Vietnamese',
    'th': 'Thai', 'id': 'Indonesian', 'ms': 'Malay', 'fa': 'Persian', 'sw': 'Swahili',
    'pl': 'Polish', 'uk': 'Ukrainian', 'cs': 'Czech', 'sk': 'Slovak', 'hu': 'Hungarian',
    'ro': 'Romanian', 'bg': 'Bulgarian', 'el': 'Greek', 'he': 'Hebrew', 'sv': 'Swedish',
    'no': 'Norwegian', 'da': 'Danish', 'fi': 'Finnish', 'ca': 'Catalan', 'eu': 'Basque',
    'is': 'Icelandic', 'lt': 'Lithuanian', 'lv': 'Latvian', 'et': 'Estonian', 'sr': 'Serbian',
    'hr': 'Croatian', 'sl': 'Slovenian', 'mk': 'Macedonian', 'sq': 'Albanian', 'cy': 'Welsh',
    'ga': 'Irish', 'af': 'Afrikaans', 'am': 'Amharic', 'hy': 'Armenian', 'az': 'Azerbaijani',
    'my': 'Burmese', 'km': 'Khmer', 'ka': 'Georgian', 'gu': 'Gujarati', 'kn': 'Kannada',
    'ml': 'Malayalam', 'mr': 'Marathi', 'ne': 'Nepali', 'si': 'Sinhala', 'tl': 'Tagalog',
    'uz': 'Uzbek', 'yi': 'Yiddish', 'yo': 'Yoruba', 'zu': 'Zulu', 'gl': 'Galician'
}

# News categories
NEWS_CATEGORIES = {
    'general': 'General', 'business': 'Business', 'entertainment': 'Entertainment',
    'health': 'Health', 'science': 'Science', 'sports': 'Sports', 'technology': 'Technology'
}

# Categories mapping for India Today API
INDIA_TODAY_CATEGORIES = {
    'general': 'india', 'business': 'business', 'technology': 'technology',
    'entertainment': 'entertainment', 'sports': 'sports', 'science': 'science',
    'health': 'health', 'politics': 'politics'
}

# API configurations
NEWS_API_PRIMARY = {
    'base_url': 'https://india-today-unofficial.p.rapidapi.com/news',
    'host': 'india-today-unofficial.p.rapidapi.com',
    'name': 'India Today'
}

NEWS_API_BACKUP = {
    'base_url': 'https://newsapi.org/v2',
    'name': 'NewsAPI'
}

# Summarizer settings
MAX_SUMMARY_LENGTH = 150
MIN_SUMMARY_LENGTH = 50
DEFAULT_LANGUAGE = 'en'

# Available TTS voices
TTS_VOICES = ['alloy', 'echo', 'fable', 'nova', 'onyx', 'shimmer']

# Simple TTS voice mapping for all languages
TTS_VOICE_MAPPING = {}

# Assign voices to language groups
VOICE_GROUPS = {
    'alloy': ['en', 'de', 'nl', 'sv', 'no', 'da', 'fi', 'is', 'pl', 'cs', 'sk', 'hu'],
    'echo': ['fr', 'pt', 'ro', 'vi', 'id', 'ms', 'sq', 'az', 'uz'],
    'fable': ['hi', 'bn', 'pa', 'te', 'ta', 'ur', 'fa', 'gu', 'kn', 'ml', 'mr', 'ne', 'si'],
    'nova': ['es', 'ca', 'it', 'ja', 'th', 'sw', 'cy', 'gl', 'tl', 'hr'],
    'onyx': ['ru', 'uk', 'ar', 'bg', 'el', 'he', 'sr', 'mk', 'hy', 'ka'],
    'shimmer': ['zh', 'ko', 'tr', 'yo', 'zu', 'ga', 'eu', 'am', 'my', 'km']
}

# Populate TTS_VOICE_MAPPING from groups
for voice, langs in VOICE_GROUPS.items():
    for lang in langs:
        if lang in SUPPORTED_LANGUAGES:
            TTS_VOICE_MAPPING[lang] = voice

# Assign remaining languages using a simple algorithm
for lang in SUPPORTED_LANGUAGES:
    if lang not in TTS_VOICE_MAPPING:
        TTS_VOICE_MAPPING[lang] = TTS_VOICES[hash(lang) % len(TTS_VOICES)]

# API retry settings
MAX_API_RETRIES = 3
API_RETRY_DELAY = 2  # seconds

# Helper function to get voice for any language
def get_tts_voice(language_code):
    return TTS_VOICE_MAPPING.get(language_code, TTS_VOICE_MAPPING.get(DEFAULT_LANGUAGE))