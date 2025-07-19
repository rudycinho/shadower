import os
import uuid

class MediaManager:
    def __init__(self, upload_folder, processed_folder):
        self.upload_folder = upload_folder
        self.processed_folder = processed_folder
    
    def get_media_files(self):
        mp3_files = [f for f in os.listdir(self.upload_folder) if f.endswith('.mp3')]
        
        media_files = []
        for mp3 in mp3_files:
            parts = mp3.split('_', 1)
            if len(parts) < 2: continue
            base_name = parts[1].rsplit('.', 1)[0]
            
            srt_match = None
            for f in os.listdir(self.upload_folder):
                if f.endswith('.srt') and f.split('_', 1)[-1] == base_name + '.srt':
                    srt_match = f
                    break
            
            processed_match = None
            for f in os.listdir(self.processed_folder):
                if f.endswith('_processed.json') and f.split('_', 1)[0] == base_name:
                    processed_match = f
                    break
            
            media_files.append({
                'mp3': mp3,
                'srt': srt_match,
                'processed': processed_match
            })
        return media_files
    
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