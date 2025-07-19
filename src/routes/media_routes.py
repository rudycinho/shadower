from flask import Blueprint, jsonify, send_file, render_template
import os
import json
from src.services.media_manager import MediaManager
from src.services.srt_processor import SRTProcessor
from config import Config

media_bp = Blueprint('media', __name__)
media_manager = MediaManager(Config.UPLOAD_FOLDER, Config.PROCESSED_FOLDER)

@media_bp.route('/load_srt/<filename>')
def load_srt(filename):
    try:
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        subtitles = SRTProcessor.parse_srt(file_path)
        return jsonify(subtitles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/load_processed/<filename>')
def load_processed(filename):
    try:
        file_path = os.path.join(Config.PROCESSED_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Processed file not found'}), 404
        with open(file_path, 'r', encoding='utf-8') as f:
            subtitles = json.load(f)
        return jsonify(subtitles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/load_media/<mp3_filename>')
def load_media(mp3_filename):
    try:
        base_name = mp3_filename.split('_', 1)[1].rsplit('.', 1)[0]
        processed_files = [f for f in os.listdir(Config.PROCESSED_FOLDER) 
                          if f.startswith(base_name) and f.endswith('_processed.json')]
        processed_filename = processed_files[0] if processed_files else None
        return jsonify({
            'mp3': mp3_filename,
            'processed': processed_filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/audio/<filename>')
def serve_audio(filename):
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    return send_file(file_path, mimetype='audio/mpeg')