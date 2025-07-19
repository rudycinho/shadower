from gtts import gTTS
import io
import os

class TTSService:
    @staticmethod
    def generate_tts_audio(text, lang='en', slow=False):
        try:
            # Manejar texto vacío o nulo
            if not text or text.strip() == '':
                return None
                
            clean_text = text.replace('♪', '').strip()
            if not clean_text:
                return None
                
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
            # Verificar si el subtítulo tiene texto
            if 'text' not in sub or not sub['text']:
                continue
                
            audio_io = TTSService.generate_tts_audio(sub['text'], lang=lang)
            if audio_io:
                filename = f"line_{sub['index']}.mp3"
                filepath = os.path.join(output_folder, filename)
                with open(filepath, 'wb') as f:
                    f.write(audio_io.getvalue())
                tts_files[sub['index']] = filename
        
        return tts_files