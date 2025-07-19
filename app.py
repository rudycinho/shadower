from flask import Flask, render_template, request, jsonify, send_file
import os
import re
import html
import io
import uuid
import shutil
from datetime import timedelta
from googletrans import Translator
from gtts import gTTS

app = Flask(__name__)
translator = Translator()

# Configuración
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'mp3', 'srt'}

# Crear carpeta temporal si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class SRTProcessor:
    """Clase para procesar archivos SRT"""
    @staticmethod
    def parse_srt(file_path):
        subtitles = []
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            blocks = content.strip().split('\n\n')
            for block in blocks:
                lines = block.split('\n')
                if len(lines) >= 3:
                    index = int(lines[0])
                    timecode = lines[1]
                    text = ' '.join(lines[2:])
                    
                    # Decodificar caracteres especiales
                    text = html.unescape(text)
                    text = re.sub(r'<[^>]+>', '', text)
                    
                    # Parsear tiempos
                    start_end = timecode.split(' --> ')
                    start = SRTProcessor.parse_time(start_end[0])
                    end = SRTProcessor.parse_time(start_end[1])
                    
                    subtitles.append({
                        'index': index,
                        'start': start,
                        'end': end,
                        'text': text
                    })
            return subtitles
        except Exception as e:
            print(f"Error parsing SRT: {e}")
            return []

    @staticmethod
    def parse_time(time_str):
        parts = time_str.replace(',', ':').split(':')
        if len(parts) == 4:
            h, m, s, ms = map(int, parts)
            return h*3600 + m*60 + s + ms/1000.0
        elif len(parts) == 3:
            h, m, s = map(int, parts)
            return h*3600 + m*60 + s
        return 0

class MediaManager:
    """Clase para gestionar archivos multimedia"""
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
    
    def get_media_files(self):
        srt_files = [f for f in os.listdir(self.upload_folder) if f.endswith('.srt')]
        mp3_files = [f for f in os.listdir(self.upload_folder) if f.endswith('.mp3')]
        
        media_files = []
        for mp3 in mp3_files:
            base_name = os.path.splitext(mp3)[0]
            srt_match = next((s for s in srt_files if s.startswith(base_name)), None)
            media_files.append({
                'mp3': mp3,
                'srt': srt_match
            })
        return media_files
    
    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    def save_uploaded_file(self, file):
        if file and self.allowed_file(file.filename):
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{unique_id}_{file.filename}"
            file_path = os.path.join(self.upload_folder, filename)
            file.save(file_path)
            return filename
        return None

class TranslationService:
    """Clase para manejar traducciones"""
    def __init__(self):
        self.translator = Translator()
    
    def translate_text(self, text, src='en', dest='es'):
        try:
            translation = self.translator.translate(text, src=src, dest=dest)
            return translation.text
        except Exception as e:
            print(f"Translation error: {e}")
            return "Translation error"

class TTSService:
    """Clase para generar audio con texto a voz"""
    @staticmethod
    def generate_tts_audio(text, lang='en', slow=False):
        try:
            tts = gTTS(text=text, lang=lang, slow=slow)
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            return audio_io
        except Exception as e:
            print(f"TTS error: {e}")
            return None

# Instanciar servicios
media_manager = MediaManager(app.config['UPLOAD_FOLDER'])
translation_service = TranslationService()

@app.route('/')
def index():
    media_files = media_manager.get_media_files()
    return render_template('player.html', media_files=media_files)

@app.route('/load_srt/<filename>')
def load_srt(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        subtitles = SRTProcessor.parse_srt(file_path)
        return jsonify(subtitles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/translate', methods=['POST'])
def translate():
    text = request.json['text']
    translation = translation_service.translate_text(text)
    return jsonify({'translation': translation})

@app.route('/tts')
def tts():
    text = request.args.get('text', '')
    lang = request.args.get('lang', 'en')
    slow = request.args.get('slow', 'false') == 'true'
    
    audio_io = TTSService.generate_tts_audio(text, lang, slow)
    if audio_io:
        return send_file(audio_io, mimetype='audio/mpeg')
    return jsonify({'error': 'TTS generation failed'}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path, mimetype='audio/mpeg')

@app.route('/upload', methods=['POST'])
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

    return jsonify({
        'success': True,
        'mp3': mp3_filename,
        'srt': srt_filename
    }), 200

# Limpiar archivos temporales al reiniciar
def clean_temp_folder():
    folder = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

if __name__ == '__main__':
    # Limpiar archivos temporales al iniciar
    clean_temp_folder()
    app.run(host='0.0.0.0', port=5000, debug=True)