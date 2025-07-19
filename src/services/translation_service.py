from googletrans import Translator

class TranslationService:
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