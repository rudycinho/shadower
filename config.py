import os
from pathlib import Path

class Config:
    # Cambiamos los nombres de las carpetas a permanentes
    UPLOAD_FOLDER = 'uploads'  # De temp_uploads a uploads
    PROCESSED_FOLDER = 'processed'  # De processed_data a processed
    ALLOWED_EXTENSIONS = {'mp3', 'srt'}
    SQLALCHEMY_DATABASE_URI = 'sqlite:///media.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        # Creamos las carpetas si no existen, pero sin limpiarlas
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
        
        # Crear estructura de carpetas permanente
        Path(Config.UPLOAD_FOLDER).mkdir(exist_ok=True)
        Path(Config.PROCESSED_FOLDER).mkdir(exist_ok=True)