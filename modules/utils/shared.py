# modules/utils/shared.py
from modules.summarizer.model import summarize_with_t5, summarize_with_gpt
from modules.translation.service1 import translate_text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def summarize_text(text, language='en', max_length=150, min_length=50):
    """
    Unified text summarization function that handles translation
    
    Args:
        text (str): Text to summarize
        language (str): Target language code
        max_length (int): Maximum length of summary
        min_length (int): Minimum length of summary
        
    Returns:
        tuple: (summary in target language, summary in English)
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for summarization")
        return None, None
    
    # Ensure text is not too short
    if len(text.strip()) < 100:
        logger.warning(f"Text too short for summarization: {len(text.strip())} chars")
        # For very short text, we'll just return it as is (with translation if needed)
        if language == 'en':
            return text.strip(), text.strip()
        else:
            translated = translate_text(text.strip(), language)
            return translated or text.strip(), text.strip()
    
    # First try T5 model for summarization
    logger.info(f"Attempting to summarize text ({len(text)} chars) with T5")
    english_summary = None
    try:
        english_summary = summarize_with_t5(text, max_length, min_length)
        if english_summary:
            logger.info("Successfully summarized with T5 model")
    except Exception as e:
        logger.error(f"Error in T5 summarization: {str(e)}")
    
    # If T5 fails, fall back to GPT
    if not english_summary:
        logger.info("T5 summarization failed, falling back to GPT")
        try:
            english_summary = summarize_with_gpt(text, max_length, min_length)
            if english_summary:
                logger.info("Successfully summarized with GPT model")
        except Exception as e:
            logger.error(f"Error in GPT summarization: {str(e)}")
    
    # If both summarizers fail, create a basic summary
    if not english_summary:
        logger.warning("Both summarizers failed, creating basic summary")
        # Create a simple summary by taking the first few sentences
        sentences = text.split('.')
        if len(sentences) > 3:
            english_summary = '. '.join(sentences[:3]) + '.'
        else:
            english_summary = text[:max_length] + ('...' if len(text) > max_length else '')
    
    # Return English summary directly if language is English
    if language == 'en':
        logger.info(f"Returning English summary (Length: {len(english_summary)} chars)")
        return english_summary, english_summary
    
    # Translate summary to target language
    logger.info(f"Translating summary to {language}")
    try:
        translated_summary = translate_text(english_summary, language)
        
        if translated_summary:
            logger.info(f"Successfully translated summary to {language}")
            return translated_summary, english_summary
    except Exception as e:
        logger.error(f"Error translating summary: {str(e)}")
    
    # Fallback to English if translation fails
    logger.warning(f"Translation to {language} failed, returning English summary")
    return english_summary, english_summary

# Fallback summarization function if models fail
def simple_summarize(text, max_length=150):
    """
    Simple summarization by extracting key sentences
    
    Args:
        text (str): Text to summarize
        max_length (int): Approximate maximum length of summary
        
    Returns:
        str: Summarized text
    """
    if not text or len(text) <= max_length:
        return text
        
    sentences = text.split('.')
    summary = []
    length = 0
    
    # Take sentences until we reach approximate max_length
    for sentence in sentences:
        if length + len(sentence) > max_length:
            break
        if sentence.strip():
            summary.append(sentence.strip())
            length += len(sentence)
    
    return '. '.join(summary) + '.'