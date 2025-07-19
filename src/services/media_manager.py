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
            # Manejar nombres de archivo sin '_'
            if '_' not in mp3:
                continue
                
            parts = mp3.split('_', 1)
            if len(parts) < 2: 
                continue
                
            # Usar os.path para manejar extensiones correctamente
            base_name = os.path.splitext(parts[1])[0]
            
            srt_match = None
            for f in os.listdir(self.upload_folder):
                if f.endswith('.srt') and f.split('_', 1)[-1] == base_name + '.srt':
                    srt_match = f
                    break
            
            processed_match = None
            for f in os.listdir(self.processed_folder):
                # Manejar múltiples posibles archivos procesados
                if f.endswith('_processed.json') and f.split('_', 1)[0] == base_name:
                    processed_match = f
                    # Preferir el más reciente si hay múltiples?
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