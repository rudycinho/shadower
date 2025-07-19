from flask import Blueprint, request, jsonify, send_file
import os
from src.services.translation_service import TranslationService
from src.services.tts_service import TTSService
from config import Config

tts_bp = Blueprint('tts', __name__)
translator = TranslationService()

@tts_bp.route('/tts_audio/<path:filename>')
def serve_tts_audio(filename):
    file_path = os.path.join(Config.PROCESSED_FOLDER, filename)
    return send_file(file_path, mimetype='audio/mpeg')

@tts_bp.route('/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    text = data.get('text', '')
    translation = translator.translate_text(text)
    return jsonify({'translation': translation})

@tts_bp.route('/tts', methods=['GET'])
def tts_endpoint():
    text = request.args.get('text', '')
    lang = request.args.get('lang', 'en')
    audio_io = TTSService.generate_tts_audio(text, lang=lang)
    return send_file(audio_io, mimetype='audio/mpeg')