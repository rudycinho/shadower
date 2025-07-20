import os
from pathlib import Path

class Config:
    UPLOAD_FOLDER = 'temp_uploads'
    PROCESSED_FOLDER = 'processed_data'
    ALLOWED_EXTENSIONS = {'mp3', 'srt'}
    SQLALCHEMY_DATABASE_URI = 'sqlite:///media.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
        
        # Crear estructura de carpetas
        Path(Config.UPLOAD_FOLDER).mkdir(exist_ok=True)
        Path(Config.PROCESSED_FOLDER).mkdir(exist_ok=True)