from models.t5_model import summarize_with_t5
from services.translation import translate_text

def summarize_text(text, language='en', max_length=150, min_length=50):
    """Manage the entire summarization process"""
    if language != 'en':
        # Translate to English, summarize, then translate back
        english_text = translate_text(text, 'en')
        if not english_text:
            return None, None
            
        english_summary = summarize_with_t5(english_text, max_length, min_length)
        if not english_summary:
            return None, None
            
        translated_summary = translate_text(english_summary, language, src_lang='en')
        return translated_summary, english_summary
    else:
        # Directly summarize in English
        summary = summarize_with_t5(text, max_length, min_length)
        return summary, None

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