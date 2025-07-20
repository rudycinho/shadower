from src.extensions import db
from datetime import datetime

class MediaFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    mp3_filename = db.Column(db.String(255), nullable=False)
    srt_filename = db.Column(db.String(255))
    processed_json = db.Column(db.String(255))
    tts_folder = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'original_name': self.original_name,
            'mp3_filename': self.mp3_filename,
            'srt_filename': self.srt_filename,
            'processed_json': self.processed_json,
            'tts_folder': self.tts_folder,
            'created_at': self.created_at.isoformat()
        }