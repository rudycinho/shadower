import re
import html

class SRTProcessor:
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
                    text = html.unescape(text)
                    text = re.sub(r'<[^>]+>', '', text)
                    
                    start_end = timecode.split(' --> ')
                    if len(start_end) != 2:
                        continue
                        
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