import customtkinter as ctk
from tkinter import messagebox
import threading
import time
from datetime import datetime, timedelta
from recorder_service import AudioRecorder
from realtime_transcription_service import RealtimeTranscriber


class RecorderWindow:
    """Окно диктофона с распознаванием в реальном времени"""
    
    def __init__(self, parent, on_recording_saved=None):
        """Инициализация окна диктофона"""
        self.parent = parent
        self.on_recording_saved = on_recording_saved
        
        self.window = ctk.CTkToplevel(parent)
        self.window.title("ОТКЛИК - Диктофон")
        self.window.geometry("800x600")
        
        # Сервисы
        self.recorder = AudioRecorder()
        
        try:
            self.transcriber = RealtimeTranscriber()
        except Exception as e:
            messagebox.showerror(
                "Ошибка инициализации", 
                f"Не удалось загрузить модель распознавания речи.\n\n"
                f"Убедитесь, что папка 'vosk-model-ru-0.42' находится в директории проекта.\n\n"
                f"Ошибка: {str(e)}"
            )
            self.window.destroy()
            return
        
        # Состояние
        self.is_recording = False
        self.start_time = None
        self.saved_file = None
        self.current_segment = ""
        self.segments = []  # Список сегментов текста (реплик)
        
        # Настройка callbacks
        self.recorder.set_pause_callback(self._on_pause_detected)
        self.transcriber.set_partial_result_callback(self._on_partial_result)
        self.transcriber.set_final_result_callback(self._on_final_result)
        
        self.create_widgets()
        self.update_timer()
        
        # Обработка закрытия окна
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def create_widgets(self):
        """Создание виджетов интерфейса"""
        # Заголовок
        header_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="🎙️ Диктофон", 
                    font=("Segoe UI", 28, "bold"), 
                    text_color="#f0f0f0").pack()
        ctk.CTkLabel(header_frame, text="Распознавание речи в реальном времени", 
                    font=("Segoe UI", 12), 
                    text_color="#f0f0f0").pack()
        
        # Панель управления
        control_frame = ctk.CTkFrame(self.window, fg_color=("#1a1a2e", "#16213e"), corner_radius=20)
        control_frame.pack(fill="x", padx=20, pady=10)
        
        # Таймер
        self.timer_label = ctk.CTkLabel(control_frame, text="00:00:00", 
                                        font=("Segoe UI", 36, "bold"), 
                                        text_color="#f0f0f0")
        self.timer_label.pack(pady=15)
        
        # Кнопки
        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        self.record_button = ctk.CTkButton(
            button_frame, 
            text="⏺ Начать запись", 
            command=self.toggle_recording,
            fg_color="#e63946", 
            hover_color="#d62828",
            font=("Segoe UI", 16, "bold"), 
            corner_radius=25,
            height=50, 
            width=200
        )
        self.record_button.pack(side="left", padx=10)
        
        self.analyze_button = ctk.CTkButton(
            button_frame, 
            text="🔍 Анализировать", 
            command=self.analyze_recording,
            fg_color="#9d4edd", 
            hover_color="#7b2cbf",
            font=("Segoe UI", 16, "bold"), 
            corner_radius=25,
            height=50, 
            width=200,
            state="disabled"
        )
        self.analyze_button.pack(side="left", padx=10)
        
        # Индикатор статуса
        self.status_indicator = ctk.CTkLabel(
            control_frame, 
            text="⚪ Готов к записи", 
            font=("Segoe UI", 12), 
            text_color="#f0f0f0"
        )
        self.status_indicator.pack(pady=(5, 15))
        
        # Область транскрипции
        transcription_frame = ctk.CTkFrame(self.window, fg_color=("#1a1a2e", "#16213e"), corner_radius=20)
        transcription_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(transcription_frame, text="📝 Распознанный текст:", 
                    font=("Segoe UI", 14, "bold"), 
                    text_color="#f0f0f0").pack(anchor="w", padx=20, pady=(15, 5))
        
        # Скроллируемый фрейм для сегментов
        self.text_container = ctk.CTkScrollableFrame(
            transcription_frame,
            fg_color="#0d1b2a",
            corner_radius=15
        )
        self.text_container.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        
        # Начальное сообщение
        self.empty_label = ctk.CTkLabel(
            self.text_container,
            text="Нажмите '⏺ Начать запись' для старта распознавания...",
            font=("Segoe UI", 12),
            text_color="#808080"
        )
        self.empty_label.pack(pady=50)
    
    def toggle_recording(self):
        """Переключение записи"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Начать запись"""
        # Очищаем предыдущие сегменты
        for widget in self.text_container.winfo_children():
            widget.destroy()
        
        self.segments = []
        self.current_segment = ""
        
        # Запускаем запись и транскрипцию
        if self.recorder.start_recording() and self.transcriber.start_transcription():
            self.is_recording = True
            self.start_time = time.time()
            
            self.record_button.configure(
                text="⏹ Остановить запись",
                fg_color="#2a9d8f",
                hover_color="#238a80"
            )
            self.status_indicator.configure(text="🔴 Идет запись...", text_color="#e63946")
            self.analyze_button.configure(state="disabled")
    
    def stop_recording(self):
        """Остановить запись"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # Останавливаем транскрипцию и запись
        self.transcriber.stop_transcription()
        self.saved_file = self.recorder.stop_recording()
        
        self.record_button.configure(
            text="⏺ Начать запись",
            fg_color="#e63946",
            hover_color="#d62828"
        )
        self.status_indicator.configure(text="✅ Запись завершена и сохранена", text_color="#4cc9f0")
        
        if self.saved_file:
            self.analyze_button.configure(state="normal")
    
    def _on_partial_result(self, text):
        """Обработка промежуточных результатов"""
        self.current_segment = text
        self._update_current_segment_display()
    
    def _on_final_result(self, text):
        """Обработка финального результата (конец фразы)"""
        if text.strip():
            # Это уже не нужно, т.к. паузы обрабатываются отдельно
            pass
    
    def _on_pause_detected(self):
        """Обработка обнаружения паузы"""
        if self.current_segment.strip():
            # Добавляем текущий сегмент в список
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.segments.append((timestamp, self.current_segment))
            
            # Обновляем GUI в главном потоке
            self.window.after(0, lambda: self._add_segment_to_display(timestamp, self.current_segment))
            
            # Очищаем текущий сегмент
            self.current_segment = ""
    
    def _add_segment_to_display(self, timestamp, text):
        """Добавить сегмент в отображение"""
        segment_frame = ctk.CTkFrame(self.text_container, fg_color="#1a1a2e", corner_radius=10)
        segment_frame.pack(fill="x", pady=5, padx=5)
        
        # Метка времени
        time_label = ctk.CTkLabel(
            segment_frame,
            text=f"[{timestamp}]",
            font=("Segoe UI", 10, "bold"),
            text_color="#9d4edd"
        )
        time_label.pack(anchor="w", padx=10, pady=(5, 0))
        
        # Текст сегмента
        text_label = ctk.CTkLabel(
            segment_frame,
            text=text,
            font=("Segoe UI", 12),
            text_color="#f0f0f0",
            wraplength=700,
            justify="left"
        )
        text_label.pack(anchor="w", padx=10, pady=(2, 10))
        
        # Разделитель
        separator = ctk.CTkFrame(self.text_container, fg_color="#4cc9f0", height=2)
        separator.pack(fill="x", pady=3)
    
    def _update_current_segment_display(self):
        """Обновить отображение текущего сегмента"""
        # Проверяем, есть ли уже фрейм для текущего сегмента
        children = self.text_container.winfo_children()
        
        if children and hasattr(children[-1], '_is_current'):
            # Обновляем существующий
            current_frame = children[-1]
            for widget in current_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") != "⏱️ Сейчас...":
                    widget.configure(text=self.current_segment)
        else:
            # Создаем новый фрейм для текущего сегмента
            current_frame = ctk.CTkFrame(self.text_container, fg_color="#0a3d62", corner_radius=10)
            current_frame._is_current = True
            current_frame.pack(fill="x", pady=5, padx=5)
            
            time_label = ctk.CTkLabel(
                current_frame,
                text="⏱️ Сейчас...",
                font=("Segoe UI", 10, "bold"),
                text_color="#4cc9f0"
            )
            time_label.pack(anchor="w", padx=10, pady=(5, 0))
            
            text_label = ctk.CTkLabel(
                current_frame,
                text=self.current_segment,
                font=("Segoe UI", 12),
                text_color="#f0f0f0",
                wraplength=700,
                justify="left"
            )
            text_label.pack(anchor="w", padx=10, pady=(2, 10))
    
    def update_timer(self):
        """Обновление таймера"""
        if self.is_recording and self.start_time:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.timer_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Планируем следующее обновление
        self.window.after(100, self.update_timer)
    
    def analyze_recording(self):
        """Запустить полный анализ записи"""
        if not self.saved_file:
            messagebox.showwarning("Предупреждение", "Нет сохраненной записи для анализа")
            return
        
        # Вызываем callback для передачи файла в главное окно
        if self.on_recording_saved:
            self.on_recording_saved(self.saved_file)
            self.window.destroy()
    
    def _on_closing(self):
        """Обработка закрытия окна"""
        if self.is_recording:
            if messagebox.askokcancel("Закрыть", "Запись все еще идет. Остановить и закрыть?"):
                self.stop_recording()
                self._cleanup()
                self.window.destroy()
        else:
            self._cleanup()
            self.window.destroy()
    
    def _cleanup(self):
        """Очистка ресурсов"""
        try:
            self.transcriber.cleanup()
            self.recorder.cleanup()
        except:
            pass

