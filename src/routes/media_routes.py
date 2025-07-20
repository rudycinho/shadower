from flask import Blueprint, jsonify, send_file
import os
import json
from config import Config
from src.services.srt_processor import SRTProcessor
from src.models import MediaFile
from src.extensions import db

media_bp = Blueprint('media', __name__)

@media_bp.route('/load_srt/<filename>')
def load_srt(filename):
    try:
        # Usamos la carpeta permanente UPLOAD_FOLDER
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
        # Usamos la carpeta permanente PROCESSED_FOLDER
        file_path = os.path.join(Config.PROCESSED_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Processed file not found'}), 404
        with open(file_path, 'r', encoding='utf-8') as f:
            subtitles = json.load(f)
        return jsonify(subtitles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/load_media/<int:media_id>')
def load_media(media_id):
    try:
        media_file = MediaFile.query.get(media_id)
        if not media_file:
            return jsonify({'error': 'Media file not found'}), 404
        
        return jsonify({
            'mp3': media_file.mp3_filename,
            'srt': media_file.srt_filename,
            'processed': media_file.processed_json,
            'tts_folder': media_file.tts_folder
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/audio/<filename>')
def serve_audio(filename):
    # Usamos la carpeta permanente UPLOAD_FOLDER
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(file_path, mimetype='audio/mpeg')