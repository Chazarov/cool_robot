import json
import queue
import threading
import os
from vosk import Model, KaldiRecognizer
import pyaudio


class RealtimeTranscriber:
    """Сервис распознавания речи в реальном времени"""
    
    def __init__(self, model_path="vosk-model-ru-0.42", sample_rate=16000):
        """Инициализация транскрибера"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Модель не найдена по пути: {model_path}\n"
                f"Скачайте модель с https://alphacephei.com/vosk/models и распакуйте в папку проекта"
            )
        
        self.model = Model(model_path)
        self.sample_rate = sample_rate
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        self.recognizer.SetWords(True)
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_transcribing = False
        self.transcription_thread = None
        
        # Callback для получения результатов
        self.on_partial_result_callback = None
        self.on_final_result_callback = None
        
        # Очередь для аудио данных
        self.audio_queue = queue.Queue()
    
    def start_transcription(self):
        """Начать распознавание"""
        if self.is_transcribing:
            return False
        
        self.is_transcribing = True
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        self.recognizer.SetWords(True)
        
        # Открываем поток аудио
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=4096,
            stream_callback=self._audio_callback
        )
        
        self.stream.start_stream()
        
        # Запускаем обработку в отдельном потоке
        self.transcription_thread = threading.Thread(target=self._process_audio)
        self.transcription_thread.start()
        
        return True
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback для получения аудио данных"""
        self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    def _process_audio(self):
        """Обработка аудио и распознавание (выполняется в отдельном потоке)"""
        while self.is_transcribing:
            try:
                # Получаем данные из очереди с таймаутом
                data = self.audio_queue.get(timeout=0.1)
                
                if self.recognizer.AcceptWaveform(data):
                    # Финальный результат (конец фразы)
                    result = json.loads(self.recognizer.Result())
                    if result.get('text') and self.on_final_result_callback:
                        self.on_final_result_callback(result['text'])
                else:
                    # Промежуточный результат
                    partial = json.loads(self.recognizer.PartialResult())
                    if partial.get('partial') and self.on_partial_result_callback:
                        self.on_partial_result_callback(partial['partial'])
                        
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Ошибка распознавания: {e}")
                break
    
    def stop_transcription(self):
        """Остановить распознавание"""
        if not self.is_transcribing:
            return None
        
        self.is_transcribing = False
        
        # Получаем финальный результат
        final_result = None
        if self.recognizer:
            result = json.loads(self.recognizer.FinalResult())
            if result.get('text'):
                final_result = result['text']
        
        # Останавливаем поток
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Ждем завершения потока обработки
        if self.transcription_thread:
            self.transcription_thread.join(timeout=2)
        
        return final_result
    
    def set_partial_result_callback(self, callback):
        """Установить callback для промежуточных результатов"""
        self.on_partial_result_callback = callback
    
    def set_final_result_callback(self, callback):
        """Установить callback для финальных результатов"""
        self.on_final_result_callback = callback
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.stop_transcription()
        self.audio.terminate()

