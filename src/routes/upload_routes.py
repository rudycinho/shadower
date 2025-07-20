from flask import Blueprint, request, jsonify, current_app
import os
import threading
from src.services.media_manager import MediaManager
from src.services.srt_processor import SRTProcessor
from config import Config
import json
import traceback
from src.models import MediaFile
from src.extensions import db

upload_bp = Blueprint('upload', __name__)

def process_srt_file(app, srt_path, mp3_filename, media_id):
    with app.app_context():
        try:
            if not os.path.exists(srt_path):
                print(f"SRT file not found: {srt_path}")
                return None
                
            srt_basename = os.path.basename(srt_path)
            if '_' not in srt_basename:
                print(f"Invalid SRT filename format: {srt_basename}")
                return None
                
            original_name = srt_basename.split('_', 1)[1].replace('.srt', '')
            
            subtitles = SRTProcessor.parse_srt(srt_path)
            if not subtitles:
                print("No subtitles parsed")
                return None
            
            from src.services.translation_service import TranslationService
            from src.services.tts_service import TTSService
            
            translator = TranslationService()
            translated_subs = translator.translate_srt(subtitles)
            
            tts_folder = os.path.join(Config.PROCESSED_FOLDER, f"{original_name}_tts")
            os.makedirs(tts_folder, exist_ok=True)
            
            tts_files = TTSService.generate_all_tts(subtitles, output_folder=tts_folder)
            
            for sub in translated_subs:
                if sub['index'] in tts_files:
                    sub['tts_path'] = f"{original_name}_tts/{tts_files[sub['index']]}"
            
            processed_filename = f"{original_name}_processed.json"
            processed_path = os.path.join(Config.PROCESSED_FOLDER, processed_filename)
            
            with open(processed_path, 'w', encoding='utf-8') as f:
                json.dump(translated_subs, f, ensure_ascii=False)
            
            # Actualizar registro en base de datos
            media_manager = MediaManager(Config.UPLOAD_FOLDER, Config.PROCESSED_FOLDER)
            media_manager.update_media_record(
                media_id,
                processed_json=processed_filename,
                tts_folder=f"{original_name}_tts"
            )
            
            return processed_filename
        except Exception as e:
            print(f"Error processing SRT: {e}")
            traceback.print_exc()
            return None

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    media_manager = MediaManager(Config.UPLOAD_FOLDER, Config.PROCESSED_FOLDER)
    try:
        if 'mp3' not in request.files:
            return jsonify({'error': 'No MP3 file part'}), 400
            
        mp3_file = request.files['mp3']
        srt_file = request.files.get('srt', None)

        if mp3_file.filename == '':
            return jsonify({'error': 'No selected MP3 file'}), 400

        mp3_filename = media_manager.save_uploaded_file(mp3_file)
        if not mp3_filename:
            return jsonify({'error': 'Invalid MP3 file'}), 400

        # Extraer nombre original sin UUID
        original_name = mp3_filename.split('_', 1)[1] if '_' in mp3_filename else mp3_filename
        
        # Crear registro en base de datos
        srt_filename = None
        if srt_file and srt_file.filename != '':
            srt_filename = media_manager.save_uploaded_file(srt_file)
        
        media_file = media_manager.create_media_record(
            original_name=original_name,
            mp3_filename=mp3_filename,
            srt_filename=srt_filename
        )
        
        if srt_filename:
            srt_path = os.path.join(Config.UPLOAD_FOLDER, srt_filename)
            app = current_app._get_current_object()
            thread = threading.Thread(
                target=process_srt_file, 
                args=(app, srt_path, mp3_filename, media_file.id)
            )
            thread.start()

        return jsonify({
            'success': True,
            'media_id': media_file.id,
            'mp3': mp3_filename,
            'srt': srt_filename
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500