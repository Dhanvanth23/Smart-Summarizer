import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from config import T5_MODEL_NAME

# Global variables for model and tokenizer
t5_tokenizer = None
t5_model = None

def load_t5_model():
    """Load T5 model and tokenizer on demand"""
    global t5_tokenizer, t5_model
    if t5_tokenizer is None or t5_model is None:
        print("Loading T5 model and tokenizer...")
        t5_tokenizer = T5Tokenizer.from_pretrained(T5_MODEL_NAME)
        t5_model = T5ForConditionalGeneration.from_pretrained(T5_MODEL_NAME)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        t5_model = t5_model.to(device)
        print(f"T5 model loaded on {device}")
    return t5_model, t5_tokenizer

def summarize_with_t5(text, max_length=150, min_length=50):
    """Summarize text using T5 model"""
    try:
        model, tokenizer = load_t5_model()
        
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