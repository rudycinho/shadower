let subtitles = [];
let currentIndex = -1;
let audioPlayer;
let lineAudio = new Audio();
let currentMode = 'tts';
let musicFragmentTimeout;

function handlePlayError(error) {
    if (error.name === 'AbortError') {
        console.log('Playback aborted intentionally');
    } else {
        console.error('Error playing audio:', error);
    }
}

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
    const uploadForm = document.getElementById('uploadForm');
    const uploadStatus = document.getElementById('uploadStatus');
    
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }
    
    function updateProgress() {
        if (audioPlayer.duration) {
            const percent = (audioPlayer.currentTime / audioPlayer.duration) * 100;
            progressFill.style.width = `${percent}%`;
            currentTime.textContent = formatTime(audioPlayer.currentTime);
        }
    }
    
    audioPlayer.addEventListener('loadedmetadata', () => {
        totalTime.textContent = formatTime(audioPlayer.duration);
    });
    
    audioPlayer.addEventListener('timeupdate', updateProgress);
    
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
    
    mediaSelect.addEventListener('change', () => {
        const selectedOption = mediaSelect.options[mediaSelect.selectedIndex];
        const mp3File = selectedOption.value;
        const srtFile = selectedOption.dataset.srt;
        const processedFile = selectedOption.dataset.processed;
        
        if (mp3File) {
            audioPlayer.src = `/audio/${encodeURIComponent(mp3File)}`;
            currentIndex = -1;
            currentLineEl.textContent = "Loading...";
            translationEl.textContent = "";
            
            if (processedFile) {
                // Cargar versión procesada (con traducción y TTS)
                fetch(`/load_processed/${encodeURIComponent(processedFile)}`)
                    .then(response => response.json())
                    .then(data => {
                        subtitles = data;
                        totalLines.textContent = subtitles.length;
                        currentIndex = 0;
                        updateLineDisplay();
                    })
                    .catch(error => {
                        console.error('Error loading processed subtitles:', error);
                        currentLineEl.textContent = "Error loading subtitles";
                    });
            } else if (srtFile) {
                // Cargar SRT original
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
    
    prevBtn.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            updateLineDisplay();
        }
    });
    
    nextBtn.addEventListener('click', () => {
        if (currentIndex < subtitles.length - 1) {
            currentIndex++;
            updateLineDisplay();
        }
    });
    
    playLineBtn.addEventListener('click', () => {
        if (currentIndex >= 0 && currentIndex < subtitles.length) {
            const line = subtitles[currentIndex];
            
            if (currentMode === 'tts') {
                // Usar audio TTS pregenerado si está disponible
                if (line.tts_path) {
                    lineAudio.src = `/tts_audio/${encodeURIComponent(line.tts_path)}`;
                    lineAudio.play().catch(handlePlayError);
                } else {
                    // Fallback a TTS en tiempo real
                    lineAudio.src = `/tts?text=${encodeURIComponent(line.text)}`;
                    lineAudio.play().catch(handlePlayError);
                }
            } else {
                audioPlayer.currentTime = line.start;
                audioPlayer.play().catch(handlePlayError);
            }
        }
    });
    
    playMusicBtn.addEventListener('click', () => {
        if (currentIndex >= 0 && currentIndex < subtitles.length) {
            const line = subtitles[currentIndex];
            
            if (musicFragmentTimeout) clearTimeout(musicFragmentTimeout);
            
            audioPlayer.pause();
            setTimeout(() => {
                audioPlayer.currentTime = line.start;
                audioPlayer.play()
                    .then(() => {
                        const fragmentDuration = (line.end - line.start) * 1000;
                        musicFragmentTimeout = setTimeout(() => {
                            audioPlayer.pause();
                        }, fragmentDuration);
                    })
                    .catch(handlePlayError);
            }, 50);
        }
    });
    
    function updateLineDisplay() {
        if (currentIndex >= 0 && currentIndex < subtitles.length) {
            const line = subtitles[currentIndex];
            currentLineEl.textContent = line.text;
            currentLineNum.textContent = currentIndex + 1;
            
            // Mostrar traducción preprocesada si está disponible
            if (line.translation) {
                translationEl.textContent = line.translation;
            } else {
                // Fallback a traducción en tiempo real
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
            }
            
            if (currentMode === 'music') {
                audioPlayer.currentTime = line.start;
            }
        }
    }
    
    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        
        uploadStatus.textContent = 'Uploading and processing files...';
        uploadStatus.style.color = 'yellow';
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.srt) {
                    uploadStatus.textContent = 'Processing SRT... this may take a moment';
                    uploadStatus.style.color = 'yellow';
                    
                    // Función para verificar el estado de procesamiento
                    const checkProcessingStatus = () => {
                        fetch(`/load_media/${encodeURIComponent(data.mp3)}`)
                            .then(response => response.json())
                            .then(mediaData => {
                                if (mediaData.error) {
                                    uploadStatus.textContent = 'Error checking status: ' + mediaData.error;
                                    uploadStatus.style.color = '#e74c3c';
                                } else if (mediaData.processed) {
                                    uploadStatus.textContent = 'Upload and processing successful!';
                                    uploadStatus.style.color = '#2ecc71';
                                    
                                    // Actualizar la lista de selección
                                    const option = document.createElement('option');
                                    option.value = data.mp3;
                                    option.dataset.srt = data.srt;
                                    option.dataset.processed = mediaData.processed;
                                    option.textContent = `${data.mp3} (with subtitles)`;
                                    mediaSelect.appendChild(option);
                                } else {
                                    // Continuar verificando
                                    setTimeout(checkProcessingStatus, 2000);
                                }
                            })
                            .catch(error => {
                                console.error('Status check error:', error);
                                uploadStatus.textContent = 'Processing check failed, try reloading page later';
                                uploadStatus.style.color = '#e74c3c';
                            });
                    };
                    
                    // Comenzar a verificar después de 3 segundos
                    setTimeout(checkProcessingStatus, 3000);
                } else {
                    uploadStatus.textContent = 'Upload successful!';
                    uploadStatus.style.color = '#2ecc71';
                    
                    // Actualizar la lista de selección
                    const option = document.createElement('option');
                    option.value = data.mp3;
                    option.textContent = data.mp3;
                    mediaSelect.appendChild(option);
                }
            } else {
                uploadStatus.textContent = `Error: ${data.error}`;
                uploadStatus.style.color = '#e74c3c';
            }
        })
        .catch(error => {
            uploadStatus.textContent = 'Upload failed';
            uploadStatus.style.color = '#e74c3c';
            console.error('Upload error:', error);
        });
    });
});