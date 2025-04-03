import os
from config import AUDIO_DIR

def cleanup_audio_files(keep_latest=30):
    """Delete old audio files, keeping only the latest n files"""
    try:
        files = [os.path.join(AUDIO_DIR, f) for f in os.listdir(AUDIO_DIR) 
                if f.endswith('.mp3') or f.endswith('.wav')]
        if len(files) <= keep_latest:
            return
        
        files.sort(key=lambda x: os.path.getctime(x))
        for file_to_delete in files[:-keep_latest]:
            os.remove(file_to_delete)
    except Exception as e:
        print(f"Error cleaning up audio files: {e}")