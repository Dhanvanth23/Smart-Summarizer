# modules/utils/text.py

def process_text_input(text):
    """
    Processes raw text input for summarization
    
    Args:
        text (str): Raw input text
        
    Returns:
        str: Processed text ready for summarization
    """
    if not text or not text.strip():
        return None
        
    # Clean up the text
    processed_text = text.strip()
    
    # Check if text is too short (less than 100 characters)
    if len(processed_text) < 100:
        return None
        
    return processed_text