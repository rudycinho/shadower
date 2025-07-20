from googletrans import Translator

class TranslationService:
    def __init__(self):
        self.translator = Translator()
    
    def translate_text(self, text, src='auto', dest='es'):
        if not text or not isinstance(text, str) or text.strip() == '':
            return ""
        try:
            translation = self.translator.translate(text, src=src, dest=dest)
            return translation.text
        except Exception as e:
            print(f"Translation error: {e}")
            return "Translation error"
    
    def translate_srt(self, subtitles, dest='es'):
        if not subtitles:  # Verificar si subtitles es None o vacío
            return []
        
        translated = []
        for sub in subtitles:
            # Verificar si el objeto sub tiene el campo 'text'
            if 'text' not in sub or not sub['text']:
                translated_text = ""
            else:
                translated_text = self.translate_text(sub['text'], dest=dest)
            
            translated.append({
                'index': sub.get('index', 0),
                'start': sub.get('start', 0),
                'end': sub.get('end', 0),
                'text': sub.get('text', ''),
                'translation': translated_text
            })
        return translated