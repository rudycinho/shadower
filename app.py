from flask import Flask, render_template, request, jsonify, send_file
import os
import re
from datetime import timedelta
import io
from googletrans import Translator
from gtts import gTTS

app = Flask(__name__)
translator = Translator()

# Parseador de archivos SRT
def parse_srt(file_path):
    subtitles = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    blocks = content.strip().split('\n\n')
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            try:
                index = int(lines[0])
                timecode = lines[1]
                text = ' '.join(lines[2:])
                
                # Parsear tiempos
                start_end = timecode.split(' --> ')
                start = parse_time(start_end[0])
                end = parse_time(start_end[1])
                
                # Dividir en palabras con tiempos aproximados
                words = []
                word_list = text.split()
                duration = (end - start) / len(word_list)
                for i, word in enumerate(word_list):
                    word_start = start + i * duration
                    word_end = word_start + duration
                    words.append({
                        'text': word,
                        'start': word_start,
                        'end': word_end
                    })
                
                subtitles.append({
                    'index': index,
                    'start': start,
                    'end': end,
                    'text': text,
                    'words': words
                })
            except Exception as e:
                print(f"Error parsing block: {e}")
    return subtitles

# Convertir tiempo SRT a segundos
def parse_time(time_str):
    h, m, s = time_str.split(':')
    s, ms = s.split(',')
    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0

@app.route('/')
def index():
    # Buscar automáticamente archivos en el directorio
    srt_files = [f for f in os.listdir() if f.endswith('.srt')]
    mp3_files = [f for f in os.listdir() if f.endswith('.mp3')]
    
    # Emparejar archivos por nombre base
    media_files = []
    for mp3 in mp3_files:
        base_name = os.path.splitext(mp3)[0]
        srt_match = next((s for s in srt_files if s.startswith(base_name)), None)
        media_files.append({
            'mp3': mp3,
            'srt': srt_match
        })
    
    return render_template('player.html', media_files=media_files)

@app.route('/load_srt/<filename>')
def load_srt(filename):
    try:
        subtitles = parse_srt(filename)
        return jsonify(subtitles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/translate', methods=['POST'])
def translate():
    text = request.json['text']
    try:
        translation = translator.translate(text, src='en', dest='es')
        return jsonify({'translation': translation.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts')
def tts():
    text = request.args.get('text', '')
    lang = request.args.get('lang', 'en')
    slow = request.args.get('slow', 'false') == 'true'
    
    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        return send_file(audio_io, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_file(filename, mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)