# modules/summarizer/model.py
import importlib.util

# Check if torch and transformers are available
torch_available = importlib.util.find_spec("torch") is not None
transformers_available = importlib.util.find_spec("transformers") is not None

# Global variables for model and tokenizer
t5_tokenizer = None
t5_model = None

def load_t5_model():
    """Load T5 model and tokenizer on demand"""
    global t5_tokenizer, t5_model
    
    if not torch_available or not transformers_available:
        print("Warning: Required libraries (torch or transformers) not available")
        return None, None
        
    if t5_tokenizer is None or t5_model is None:
        try:
            import torch
            from transformers import T5ForConditionalGeneration, T5Tokenizer
            from config import T5_MODEL_NAME
            
            print("Loading T5 model and tokenizer...")
            t5_tokenizer = T5Tokenizer.from_pretrained(T5_MODEL_NAME)
            t5_model = T5ForConditionalGeneration.from_pretrained(T5_MODEL_NAME)
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            t5_model = t5_model.to(device)
            print(f"T5 model loaded on {device}")
        except Exception as e:
            print(f"Failed to load T5 model: {e}")
            return None, None
            
    return t5_model, t5_tokenizer

def summarize_with_t5(text, max_length=150, min_length=50):
    """Summarize text using T5 model"""
    try:
        model, tokenizer = load_t5_model()
        
        if model is None or tokenizer is None:
            print("T5 model not available, falling back to alternative method")
            return None
            
        import torch
            
        input_text = "summarize: " + text
        inputs = tokenizer.encode(input_text, return_tensors="pt", truncation=True, max_length=1024)
        
        if torch.cuda.is_available():
            inputs = inputs.to('cuda')
        
        summary_ids = model.generate(
            inputs, 
            max_length=max_length,
            min_length=min_length,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )
        
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
    except Exception as e:
        print(f"T5 summarization error: {e}")
        return None

def summarize_with_gpt(text, max_length=150, min_length=50):
    """Fallback summarization using GPT"""
    try:
        openai_spec = importlib.util.find_spec("openai")
        if openai_spec is None:
            print("OpenAI library not available")
            return None
            
        import openai
        
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