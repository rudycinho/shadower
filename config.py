import os

class Config:
    UPLOAD_FOLDER = 'temp_uploads'
    PROCESSED_FOLDER = 'processed_data'
    ALLOWED_EXTENSIONS = {'mp3', 'srt'}
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)