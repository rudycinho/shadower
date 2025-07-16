let subtitles = [];
let currentIndex = -1;
let audioPlayer;
let lineAudio = new Audio();
let currentMode = 'tts';
let musicFragmentTimeout;

document.addEventListener('DOMContentLoaded', () => {
    audioPlayer = document.getElementById('audioPlayer');
    const mediaSelect = document.getElementById('media-select');
    const currentLineEl = document.getElementById('currentLine');
    const translationEl = document.getElementById('translation');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const playLineBtn = document.getElementById('playLineBtn');
    const playMusicBtn = document.getElementById('playMusicBtn');
    const ttsModeBtn = document.getElementById('ttsModeBtn');
    const musicModeBtn = document.getElementById('musicModeBtn');
    const currentLineNum = document.getElementById('currentLineNum');
    const totalLines = document.getElementById('totalLines');
    const progressFill = document.getElementById('progressFill');
    const currentTime = document.getElementById('currentTime');
    const totalTime = document.getElementById('totalTime');
    
    // Formatear tiempo para mostrar
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }
    
    // Actualizar barra de progreso
    function updateProgress() {
        if (audioPlayer.duration) {
            const percent = (audioPlayer.currentTime / audioPlayer.duration) * 100;
            progressFill.style.width = `${percent}%`;
            currentTime.textContent = formatTime(audioPlayer.currentTime);
        }
    }
    
    // Actualizar tiempo total
    audioPlayer.addEventListener('loadedmetadata', () => {
        totalTime.textContent = formatTime(audioPlayer.duration);
    });
    
    // Actualizar barra de progreso continuamente
    audioPlayer.addEventListener('timeupdate', updateProgress);
    
    // Cambiar entre modos
    ttsModeBtn.addEventListener('click', () => {
        ttsModeBtn.classList.add('active');
        musicModeBtn.classList.remove('active');
        currentMode = 'tts';
    });
    
    musicModeBtn.addEventListener('click', () => {
        musicModeBtn.classList.add('active');
        ttsModeBtn.classList.remove('active');
        currentMode = 'music';
    });
    
    // Cargar medios seleccionados
    mediaSelect.addEventListener('change', () => {
        const selectedOption = mediaSelect.options[mediaSelect.selectedIndex];
        const mp3File = selectedOption.value;
        const srtFile = selectedOption.dataset.srt;
        
        if (mp3File) {
            audioPlayer.src = `/audio/${encodeURIComponent(mp3File)}`;
            currentIndex = -1;
            currentLineEl.textContent = "Loading...";
            translationEl.textContent = "";
            
            if (srtFile) {
                fetch(`/load_srt/${encodeURIComponent(srtFile)}`)
                    .then(response => response.json())
                    .then(data => {
                        subtitles = data;
                        totalLines.textContent = subtitles.length;
                        currentIndex = 0;
                        updateLineDisplay();
                    })
                    .catch(error => {
                        console.error('Error loading subtitles:', error);
                        currentLineEl.textContent = "Error loading subtitles";
                    });
            } else {
                subtitles = [];
                totalLines.textContent = "0";
                currentLineEl.textContent = "No subtitles available";
            }
        }
    });
    
    // Navegar a línea anterior
    prevBtn.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            updateLineDisplay();
        }
    });
    
    // Navegar a línea siguiente
    nextBtn.addEventListener('click', () => {
        if (currentIndex < subtitles.length - 1) {
            currentIndex++;
            updateLineDisplay();
        }
    });
    
    // Reproducir línea actual según el modo
    playLineBtn.addEventListener('click', () => {
        if (currentIndex >= 0 && currentIndex < subtitles.length) {
            const line = subtitles[currentIndex];
            
            if (currentMode === 'tts') {
                // Modo TTS: Reproducir con síntesis de voz
                lineAudio.src = `/tts?text=${encodeURIComponent(line.text)}`;
                lineAudio.play();
            } else {
                // Modo Música: Saltar al inicio de la línea
                audioPlayer.currentTime = line.start;
                audioPlayer.play();
            }
        }
    });
    
    // Reproducir fragmento musical de la línea actual
    playMusicBtn.addEventListener('click', () => {
        if (currentIndex >= 0 && currentIndex < subtitles.length) {
            const line = subtitles[currentIndex];
            
            // Cancelar cualquier reproducción anterior
            if (musicFragmentTimeout) clearTimeout(musicFragmentTimeout);
            audioPlayer.pause();
            
            // Establecer tiempo de inicio
            audioPlayer.currentTime = line.start;
            audioPlayer.play();
            
            // Calcular duración del fragmento
            const fragmentDuration = (line.end - line.start) * 1000;
            
            // Detener después de la duración del fragmento
            musicFragmentTimeout = setTimeout(() => {
                audioPlayer.pause();
            }, fragmentDuration);
        }
    });
    
    // Actualizar la visualización de la línea
    function updateLineDisplay() {
        if (currentIndex >= 0 && currentIndex < subtitles.length) {
            const line = subtitles[currentIndex];
            currentLineEl.textContent = line.text;
            currentLineNum.textContent = currentIndex + 1;
            
            // Traducir la línea
            fetch('/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: line.text })
            })
            .then(response => response.json())
            .then(data => {
                translationEl.textContent = data.translation;
            })
            .catch(error => {
                console.error('Translation error:', error);
                translationEl.textContent = "Translation error";
            });
            
            // Saltar al tiempo de la línea
            if (currentMode === 'music') {
                audioPlayer.currentTime = line.start;
            }
        }
    }
});