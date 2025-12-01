import pyaudio
import wave
import threading
import time
from datetime import datetime
import os


class AudioRecorder:
    """Сервис записи аудио в реальном времени"""
    
    def __init__(self, sample_rate=16000, channels=1, chunk_size=1024):
        """Инициализация рекордера"""
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None
        self.output_file = None
        
        # Параметры для определения пауз
        self.silence_threshold = 500  # Порог тишины
        self.silence_duration = 1.5  # Длительность паузы в секундах
        self.last_sound_time = time.time()
        self.pause_detected = False
        
        # Callback для обработки пауз
        self.on_pause_callback = None
    
    def start_recording(self, output_dir="recordings"):
        """Начать запись"""
        if self.is_recording:
            return False
        
        # Создаем директорию для записей
        os.makedirs(output_dir, exist_ok=True)
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = os.path.join(output_dir, f"recording_{timestamp}.wav")
        
        self.frames = []
        self.is_recording = True
        self.last_sound_time = time.time()
        
        # Открываем поток
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        # Запускаем запись в отдельном потоке
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()
        
        return True
    
    def _record(self):
        """Процесс записи (выполняется в отдельном потоке)"""
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.frames.append(data)
                
                # Проверяем уровень звука для определения пауз
                audio_data = list(data)
                if audio_data:
                    avg_volume = sum(abs(b) for b in audio_data) / len(audio_data)
                    
                    if avg_volume > self.silence_threshold:
                        self.last_sound_time = time.time()
                        self.pause_detected = False
                    else:
                        # Проверяем, прошло ли достаточно времени для паузы
                        if time.time() - self.last_sound_time > self.silence_duration:
                            if not self.pause_detected and self.on_pause_callback:
                                self.pause_detected = True
                                self.on_pause_callback()
            except Exception as e:
                print(f"Ошибка записи: {e}")
                break
    
    def stop_recording(self):
        """Остановить запись и сохранить файл"""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        
        # Ждем завершения потока
        if self.recording_thread:
            self.recording_thread.join()
        
        # Закрываем поток
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Сохраняем в файл
        if self.frames and self.output_file:
            with wave.open(self.output_file, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.frames))
            
            return self.output_file
        
        return None
    
    def get_recording_duration(self):
        """Получить текущую длительность записи в секундах"""
        if not self.frames:
            return 0
        return len(self.frames) * self.chunk_size / self.sample_rate
    
    def set_pause_callback(self, callback):
        """Установить callback для обработки пауз"""
        self.on_pause_callback = callback
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.stop_recording()
        self.audio.terminate()

