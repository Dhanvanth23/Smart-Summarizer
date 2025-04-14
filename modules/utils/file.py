# modules/utils/file.py
import os
import time
import glob

def cleanup_audio_files(max_age_minutes=30):
    """
    Clean up old audio files to prevent disk space issues
    
    Args:
        max_age_minutes (int): Maximum age of files in minutes before deletion
    """
    try:
        from config import AUDIO_DIR
        
        # Get all mp3 files in the audio directory
        audio_files = glob.glob(os.path.join(AUDIO_DIR, "*.mp3"))
        
        # Current time
        current_time = time.time()
        
        # Delete files older than max_age_minutes
        for file_path in audio_files:
            # Skip if file doesn't exist
            if not os.path.exists(file_path):
                continue
                
            # Get file modification time
            file_mod_time = os.path.getmtime(file_path)
            file_age_minutes = (current_time - file_mod_time) / 60
            
            # Delete if older than max_age_minutes
            if file_age_minutes > max_age_minutes:
                try:
                    os.remove(file_path)
                    print(f"Deleted old audio file: {file_path}")
                except:
                    pass
    except Exception as e:
        print(f"Error cleaning up audio files: {e}")