# modules/audio/service.py
import os
import uuid
from config import AUDIO_DIR, TTS_VOICE_MAPPING
from modules.utils.file import cleanup_audio_files

def text_to_speech_openai(text, language='en'):
    """Generate speech using OpenAI's TTS API"""
    try:
        import openai  # Import only when needed
        
        filename = f"summary_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(AUDIO_DIR, filename)
        
        cleanup_audio_files(30)
        
        voice = TTS_VOICE_MAPPING.get(language, 'alloy')
        
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        response.stream_to_file(file_path)
        return os.path.basename(file_path)
    except Exception as e:
        print(f"OpenAI TTS error: {e}")
        return text_to_speech_fallback(text, language)

def text_to_speech_fallback(text, language='en'):
    """Fallback to gTTS if OpenAI TTS fails"""
    try:
        from gtts import gTTS
        
        tts_language_map = {
            'zh': 'zh-CN', 'no': 'nb-NO', 'ur': 'ur',
        }
        
        tts_lang = tts_language_map.get(language, language)
        filename = f"summary_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(AUDIO_DIR, filename)
        
        try:
            tts = gTTS(text=text, lang=tts_lang, slow=False)
            tts.save(file_path)
            return os.path.basename(file_path)
        except ValueError:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(file_path)
            return os.path.basename(file_path)
    except Exception as e:
        print(f"Text-to-speech fallback error: {e}")
        return None

def transcribe_audio_with_whisper(audio_file_path):
    """Transcribe audio using OpenAI's Whisper API"""
    try:
        import openai  # Import only when needed
        
        with open(audio_file_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return None