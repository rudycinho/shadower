from flask import Flask, render_template, request, jsonify, send_file
import os
import re
import html
import io
import uuid
import shutil
import json
import threading
from datetime import timedelta
from googletrans import Translator
from gtts import gTTS

app = Flask(__name__)

# Configuración
UPLOAD_FOLDER = 'temp_uploads'
PROCESSED_FOLDER = 'processed_data'
ALLOWED_EXTENSIONS = {'mp3', 'srt'}

# Crear carpetas si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

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
                    # Eliminar etiquetas HTML
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
    def __init__(self, upload_folder, processed_folder):
        self.upload_folder = upload_folder
        self.processed_folder = processed_folder
    
    def get_media_files(self):
        mp3_files = [f for f in os.listdir(self.upload_folder) if f.endswith('.mp3')]
        
        media_files = []
        for mp3 in mp3_files:
            # Extraer el nombre base sin el UUID
            parts = mp3.split('_', 1)
            if len(parts) < 2:
                continue
            base_name = parts[1].rsplit('.', 1)[0]
            
            # Buscar SRT correspondiente
            srt_match = None
            for f in os.listdir(self.upload_folder):
                if f.endswith('.srt') and f.split('_', 1)[-1] == base_name + '.srt':
                    srt_match = f
                    break
            
            # Buscar archivo procesado
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
    
    def translate_text(self, text, src='auto', dest='es'):
        try:
            translation = self.translator.translate(text, src=src, dest=dest)
            return translation.text
        except Exception as e:
            print(f"Translation error: {e}")
            return "Translation error"
    
    def translate_srt(self, subtitles, dest='es'):
        translated = []
        for sub in subtitles:
            translated_text = self.translate_text(sub['text'], dest=dest)
            translated.append({
                'index': sub['index'],
                'start': sub['start'],
                'end': sub['end'],
                'text': sub['text'],
                'translation': translated_text
            })
        return translated

class TTSService:
    """Clase para generar audio con texto a voz"""
    @staticmethod
    def generate_tts_audio(text, lang='en', slow=False):
        try:
            clean_text = text.replace('♪', '')
            tts = gTTS(text=clean_text, lang=lang, slow=slow)
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            return audio_io
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    @staticmethod
    def generate_all_tts(subtitles, lang='en', output_folder='tts_audio'):
        os.makedirs(output_folder, exist_ok=True)
        tts_files = {}
        
        for sub in subtitles:
            audio_io = TTSService.generate_tts_audio(sub['text'], lang=lang)
            if audio_io:
                filename = f"line_{sub['index']}.mp3"
                filepath = os.path.join(output_folder, filename)
                with open(filepath, 'wb') as f:
                    f.write(audio_io.getvalue())
                tts_files[sub['index']] = filename
        return tts_files

def process_srt_file(srt_path, mp3_filename):
    """Procesa un archivo SRT: traduce y genera audios TTS"""
    try:
        # Obtener nombre base sin el UUID
        original_name = os.path.basename(srt_path).split('_', 1)[1].replace('.srt', '')
        
        # Parsear SRT original
        subtitles = SRTProcessor.parse_srt(srt_path)
        if not subtitles:
            print("No subtitles parsed")
            return None
        
        # Traducir a español
        translator = TranslationService()
        translated_subs = translator.translate_srt(subtitles)
        
        # Generar audios TTS
        tts_folder = os.path.join(app.config['PROCESSED_FOLDER'], f"{original_name}_tts")
        tts_files = TTSService.generate_all_tts(subtitles, output_folder=tts_folder)
        
        # Añadir rutas TTS a los subtítulos
        for sub in translated_subs:
            if sub['index'] in tts_files:
                sub['tts_path'] = f"{original_name}_tts/{tts_files[sub['index']]}"
        
        # Guardar resultado procesado
        processed_filename = f"{original_name}_processed.json"
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
        
        with open(processed_path, 'w', encoding='utf-8') as f:
            json.dump(translated_subs, f, ensure_ascii=False)
        
        return processed_filename
    except Exception as e:
        print(f"Error processing SRT: {e}")
        return None

# Instanciar servicios
media_manager = MediaManager(
    app.config['UPLOAD_FOLDER'],
    app.config['PROCESSED_FOLDER']
)

@app.route('/')
def index():
    media_files = media_manager.get_media_files()
    return render_template('player.html', media_files=media_files)

@app.route('/load_srt/<filename>')
def load_srt(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        subtitles = SRTProcessor.parse_srt(file_path)
        return jsonify(subtitles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load_processed/<filename>')
def load_processed(filename):
    try:
        file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Processed file not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            subtitles = json.load(f)
        return jsonify(subtitles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load_media/<mp3_filename>')
def load_media(mp3_filename):
    try:
        # Extraer el nombre base sin el UUID
        base_name = mp3_filename.split('_', 1)[1].rsplit('.', 1)[0]
        
        # Buscar archivo procesado
        processed_files = [f for f in os.listdir(app.config['PROCESSED_FOLDER']) 
                          if f.startswith(base_name) and f.endswith('_processed.json')]
        
        if processed_files:
            processed_filename = processed_files[0]
            return jsonify({
                'mp3': mp3_filename,
                'processed': processed_filename
            })
        
        return jsonify({'mp3': mp3_filename, 'processed': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path, mimetype='audio/mpeg')

@app.route('/tts_audio/<path:filename>')
def serve_tts_audio(filename):
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
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
    
    # Procesar SRT en segundo plano si existe
    if srt_filename:
        srt_path = os.path.join(app.config['UPLOAD_FOLDER'], srt_filename)
        
        # Ejecutar procesamiento en un hilo separado
        def process_task():
            processed = process_srt_file(srt_path, mp3_filename)
            print(f"Procesamiento completado: {processed}")
        
        thread = threading.Thread(target=process_task)
        thread.start()

    return jsonify({
        'success': True,
        'mp3': mp3_filename,
        'srt': srt_filename
    }), 200

# Limpiar archivos temporales al reiniciar
def clean_temp_folder():
    folders = [
        app.config['UPLOAD_FOLDER'],
        app.config['PROCESSED_FOLDER']
    ]
    
    for folder in folders:
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