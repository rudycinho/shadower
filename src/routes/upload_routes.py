from flask import Blueprint, request, jsonify
import os
import threading
from src.services.media_manager import MediaManager
from src.services.srt_processor import SRTProcessor
from config import Config
import json

upload_bp = Blueprint('upload', __name__)
media_manager = MediaManager(Config.UPLOAD_FOLDER, Config.PROCESSED_FOLDER)

def process_srt_file(srt_path, mp3_filename):
    try:
        original_name = os.path.basename(srt_path).split('_', 1)[1].replace('.srt', '')
        subtitles = SRTProcessor.parse_srt(srt_path)
        if not subtitles: return None
        
        from src.services.translation_service import TranslationService
        from src.services.tts_service import TTSService
        
        translator = TranslationService()
        translated_subs = translator.translate_srt(subtitles)
        
        tts_folder = os.path.join(Config.PROCESSED_FOLDER, f"{original_name}_tts")
        tts_files = TTSService.generate_all_tts(subtitles, output_folder=tts_folder)
        
        for sub in translated_subs:
            if sub['index'] in tts_files:
                sub['tts_path'] = f"{original_name}_tts/{tts_files[sub['index']]}"
        
        processed_filename = f"{original_name}_processed.json"
        processed_path = os.path.join(Config.PROCESSED_FOLDER, processed_filename)
        
        with open(processed_path, 'w', encoding='utf-8') as f:
            json.dump(translated_subs, f, ensure_ascii=False)
        
        return processed_filename
    except Exception as e:
        print(f"Error processing SRT: {e}")
        return None

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'mp3' not in request.files:
        return jsonify({'error': 'No MP3 file part'}), 400
        
    mp3_file = request.files['mp3']
    srt_file = request.files.get('srt', None)

    if mp3_file.filename == '':
        return jsonify({'error': 'No selected MP3 file'}), 400

    mp3_filename = media_manager.save_uploaded_file(mp3_file)
    if not mp3_filename:
        return jsonify({'error': 'Invalid MP3 file'}), 400

    srt_filename = None
    if srt_file and srt_file.filename != '':
        srt_filename = media_manager.save_uploaded_file(srt_file)
    
    if srt_filename:
        srt_path = os.path.join(Config.UPLOAD_FOLDER, srt_filename)
        thread = threading.Thread(
            target=process_srt_file, 
            args=(srt_path, mp3_filename)
        )
        thread.start()

    return jsonify({
        'success': True,
        'mp3': mp3_filename,
        'srt': srt_filename
    }), 200