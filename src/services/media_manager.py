import os
import uuid
from src.models import MediaFile
from src.extensions import db

class MediaManager:
    def __init__(self, upload_folder, processed_folder):
        self.upload_folder = upload_folder
        self.processed_folder = processed_folder
    
    def get_media_files(self):
        # Obtener todos los archivos de la base de datos
        media_files = MediaFile.query.all()
        return [{
            'id': mf.id,
            'mp3': mf.mp3_filename,
            'srt': mf.srt_filename,
            'processed': mf.processed_json,
            'tts_folder': mf.tts_folder,
            'original_name': mf.original_name
        } for mf in media_files]
    
    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in {'mp3', 'srt'}
    
    def save_uploaded_file(self, file):
        if file and self.allowed_file(file.filename):
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{unique_id}_{file.filename}"
            file_path = os.path.join(self.upload_folder, filename)
            file.save(file_path)
            return filename
        return None
    
    def create_media_record(self, original_name, mp3_filename, srt_filename=None):
        media_file = MediaFile(
            original_name=original_name,
            mp3_filename=mp3_filename,
            srt_filename=srt_filename
        )
        db.session.add(media_file)
        db.session.commit()
        return media_file
    
    def update_media_record(self, media_id, processed_json=None, tts_folder=None):
        media_file = MediaFile.query.get(media_id)
        if media_file:
            if processed_json:
                media_file.processed_json = processed_json
            if tts_folder:
                media_file.tts_folder = tts_folder
            db.session.commit()
        return media_file