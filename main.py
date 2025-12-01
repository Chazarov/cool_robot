import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from datetime import datetime
from analyse_service import merge_transcription_diarization
from statistics_service import calculate_statistics

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class StatisticsWindow:
    """Окно отображения статистики"""
    
    def __init__(self, parent, filename, stats):
        """Инициализация окна статистики"""
        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"ОТКЛИК - Статистика: {filename}")
        self.window.geometry("650x600")
        
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text="📊 Статистика анализа", 
                    font=("Segoe UI", 24, "bold"), text_color="#f0f0f0").pack(pady=15)
        
        # Количество реплик
        turns_frame = ctk.CTkFrame(main_frame, fg_color=("#1a1a2e", "#16213e"), corner_radius=20)
        turns_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(turns_frame, text="Индекс активности (количество реплик)", 
                    font=("Segoe UI", 14, "bold"), text_color="#f0f0f0").pack(pady=10, padx=20, anchor="w")
        
        for speaker, turns in stats['speaker_turns'].items():
            ctk.CTkLabel(turns_frame, text=f"{speaker}: {turns} реплик", 
                        font=("Segoe UI", 12), text_color="#f0f0f0").pack(pady=5, padx=30, anchor="w")
        
        # Средняя длина высказываний
        length_frame = ctk.CTkFrame(main_frame, fg_color=("#1a1a2e", "#16213e"), corner_radius=20)
        length_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(length_frame, text="Средняя длина высказываний (слов)", 
                    font=("Segoe UI", 14, "bold"), text_color="#f0f0f0").pack(pady=10, padx=20, anchor="w")
        
        for speaker, avg_len in stats['speaker_avg_length'].items():
            ctk.CTkLabel(length_frame, text=f"{speaker}: {avg_len:.1f} слов", 
                        font=("Segoe UI", 12), text_color="#f0f0f0").pack(pady=5, padx=30, anchor="w")
        
        # Активность обсуждения
        activity_frame = ctk.CTkFrame(main_frame, fg_color=("#1a1a2e", "#16213e"), corner_radius=20)
        activity_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(activity_frame, text="Активность обсуждения", 
                    font=("Segoe UI", 14, "bold"), text_color="#f0f0f0").pack(pady=10, padx=20, anchor="w")
        
        ctk.CTkLabel(activity_frame, text=f"Общее количество пауз: {stats['total_pauses']}", 
                    font=("Segoe UI", 12), text_color="#f0f0f0").pack(pady=2, padx=30, anchor="w")
        ctk.CTkLabel(activity_frame, text=f"Средняя длина паузы: {stats['avg_pause']:.2f} сек", 
                    font=("Segoe UI", 12), text_color="#f0f0f0").pack(pady=2, padx=30, anchor="w")
        ctk.CTkLabel(activity_frame, text=f"Оценка активности: {stats['activity_score']:.1f}/100", 
                    font=("Segoe UI", 12, "bold"), text_color="#f0f0f0").pack(pady=5, padx=30, anchor="w")
        
        # Коэффициент равномерности
        uniform_frame = ctk.CTkFrame(main_frame, fg_color=("#1a1a2e", "#16213e"), corner_radius=20)
        uniform_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(uniform_frame, text="Равномерность распределения речи", 
                    font=("Segoe UI", 14, "bold"), text_color="#f0f0f0").pack(pady=10, padx=20, anchor="w")
        
        ctk.CTkLabel(uniform_frame, 
                    text=f"Коэффициент равномерности: {stats['uniformity_coefficient']:.1f}/100", 
                    font=("Segoe UI", 12, "bold"), text_color="#f0f0f0").pack(pady=5, padx=30, anchor="w")
        ctk.CTkLabel(uniform_frame, 
                    text="(100 - идеально равномерно, 0 - один говорит больше всех)", 
                    font=("Segoe UI", 10), text_color="#d0d0d0").pack(pady=2, padx=30, anchor="w")
        
        ctk.CTkButton(main_frame, text="Закрыть", command=self.window.destroy,
                     fg_color="#c77dff", hover_color="#9d4edd", 
                     font=("Segoe UI", 14, "bold"), corner_radius=25,
                     height=40, width=200).pack(pady=20)


class AudioAnalyzerGUI:
    """Главный класс GUI для анализа аудио"""
    
    def __init__(self, root):
        """Инициализация интерфейса"""
        self.root = root
        self.root.title("ОТКЛИК - Анализ аудиозаписей")
        self.root.geometry("1000x700")
        
        self.audio_files = {}
        self.current_file = None
        self.meeting_counter = 0
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание виджетов интерфейса"""
        # Заголовок
        header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="🎙️ ОТКЛИК", 
                    font=("Segoe UI", 32, "bold"), 
                    text_color="#f0f0f0").pack()
        ctk.CTkLabel(header_frame, text="Анализ аудиозаписей встреч", 
                    font=("Segoe UI", 14), 
                    text_color="#f0f0f0").pack()
        
        # Верхняя панель кнопок
        top_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(top_frame, text="📁 Загрузить аудио", command=self.load_audio,
                     fg_color="#4cc9f0", hover_color="#3a9fc7",
                     font=("Segoe UI", 13, "bold"), corner_radius=25,
                     height=40, width=180).pack(side="left", padx=5)
        
        ctk.CTkLabel(top_frame, text="Спикеров:", 
                    font=("Segoe UI", 13), text_color="#f0f0f0").pack(side="left", padx=(20, 5))
        self.speakers_var = ctk.StringVar(value="2")
        ctk.CTkEntry(top_frame, textvariable=self.speakers_var, width=60,
                    font=("Segoe UI", 13), corner_radius=15).pack(side="left", padx=5)
        
        ctk.CTkButton(top_frame, text="▶️ Анализировать", command=self.analyze_audio,
                     fg_color="#9d4edd", hover_color="#7b2cbf",
                     font=("Segoe UI", 13, "bold"), corner_radius=25,
                     height=40, width=180).pack(side="left", padx=5)
        
        ctk.CTkButton(top_frame, text="💾 Сохранить", command=self.save_result,
                     fg_color="#c77dff", hover_color="#9d4edd",
                     font=("Segoe UI", 13, "bold"), corner_radius=25,
                     height=40, width=150).pack(side="left", padx=5)
        
        ctk.CTkButton(top_frame, text="📊 Статистика", command=self.show_statistics,
                     fg_color="#5a189a", hover_color="#3c096c",
                     font=("Segoe UI", 13, "bold"), corner_radius=25,
                     height=40, width=150).pack(side="left", padx=5)
        
        # Список файлов
        list_frame = ctk.CTkFrame(self.root, fg_color=("#1a1a2e", "#16213e"), corner_radius=20)
        list_frame.pack(fill="both", expand=False, padx=20, pady=10, ipady=10)
        
        ctk.CTkLabel(list_frame, text="📋 Загруженные записи:", 
                    font=("Segoe UI", 14, "bold"), 
                    text_color="#f0f0f0").pack(anchor="w", padx=20, pady=(10, 5))
        
        import tkinter as tk
        self.file_listbox = tk.Listbox(list_frame, height=5,
                                       bg="#0d1b2a", fg="#f0f0f0",
                                       font=("Segoe UI", 11),
                                       selectbackground="#9d4edd",
                                       selectforeground="#f0f0f0",
                                       relief="flat",
                                       highlightthickness=0)
        self.file_listbox.pack(fill="x", padx=20, pady=(5, 10))
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # Область результатов
        result_frame = ctk.CTkFrame(self.root, fg_color=("#1a1a2e", "#16213e"), corner_radius=20)
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(result_frame, text="📝 Результат транскрибации:", 
                    font=("Segoe UI", 14, "bold"), 
                    text_color="#f0f0f0").pack(anchor="w", padx=20, pady=(10, 5))
        
        self.result_text = ctk.CTkTextbox(result_frame, wrap="word",
                                          font=("Segoe UI", 12),
                                          fg_color="#0d1b2a",
                                          text_color="#f0f0f0",
                                          corner_radius=15)
        self.result_text.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        
        # Прогресс бар
        self.progress_bar = ctk.CTkProgressBar(self.root, 
                                               mode="determinate",
                                               progress_color="#9d4edd",
                                               height=15,
                                               corner_radius=10)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Скрываем по умолчанию
        
        # Статус бар
        self.status_label = ctk.CTkLabel(self.root, text="✅ Готов к работе",
                                        font=("Segoe UI", 11),
                                        text_color="#f0f0f0",
                                        anchor="w")
        self.status_label.pack(fill="x", padx=20, pady=(0, 10))
    
    def load_audio(self):
        """Загрузка аудиофайлов"""
        files = filedialog.askopenfilenames(
            title="Выберите аудиофайлы",
            filetypes=[("Audio files", "*.mp3 *.wav *.m4a"), ("All files", "*.*")]
        )
        
        for file_path in files:
            if file_path not in self.audio_files:
                self.meeting_counter += 1
                date_str = datetime.now().strftime("%d.%m.%Y")
                display_name = f"Встреча №{self.meeting_counter} от {date_str}"
                
                self.audio_files[file_path] = {
                    'display_name': display_name,
                    'dialogue': None,
                    'diarization': None
                }
                self.file_listbox.insert("end", display_name)
        
        self.status_label.configure(text=f"✅ Загружено файлов: {len(self.audio_files)}")
    
    def on_file_select(self, event):
        """Обработка выбора файла из списка"""
        selection = self.file_listbox.curselection()
        if selection:
            idx = selection[0]
            self.current_file = list(self.audio_files.keys())[idx]
            
            file_data = self.audio_files[self.current_file]
            if file_data.get('dialogue'):
                self.display_result(file_data['dialogue'])
            else:
                self.result_text.delete("0.0", "end")
                self.result_text.insert("0.0", "📌 Файл еще не проанализирован.\nНажмите '▶️ Анализировать' для начала обработки.")
    
    def update_progress(self, stage, progress, message):
        """Обновление прогресса анализа"""
        self.progress_bar.set(progress)
        self.status_label.configure(text=f"⏳ {stage}: {message}")
        self.result_text.delete("0.0", "end")
        
        stages_info = {
            "Загрузка": "🎵 Подготовка аудиофайла...",
            "Транскрибация": "🎤 Распознавание речи...",
            "Диаризация": "👥 Определение спикеров...",
            "Объединение": "🔄 Формирование диалога..."
        }
        
        display_text = "⏳ ПРОЦЕСС АНАЛИЗА\n\n"
        for stage_name, stage_desc in stages_info.items():
            if stage_name == stage:
                display_text += f"➤ {stage_desc} [{int(progress*100)}%]\n"
            else:
                display_text += f"   {stage_desc}\n"
        
        display_text += f"\n{message}"
        self.result_text.insert("0.0", display_text)
    
    def analyze_audio(self):
        """Запуск анализа выбранного аудиофайла"""
        if not self.current_file:
            messagebox.showwarning("Предупреждение", "Выберите файл для анализа")
            return
        
        try:
            n_speakers = int(self.speakers_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество спикеров")
            return
        
        # Показываем прогресс бар
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 5), before=self.status_label)
        self.progress_bar.set(0)
        
        self.root.after(0, lambda: self.update_progress("Загрузка", 0.1, "Подготовка к анализу..."))
        
        def run_analysis():
            """Выполнение анализа в отдельном потоке"""
            try:
                # Callback для обновления прогресса
                def progress_callback(stage, progress, message):
                    self.root.after(0, lambda: self.update_progress(stage, progress, message))
                
                dialogue, diarization = merge_transcription_diarization(
                    self.current_file, n_speakers, progress_callback
                )
                file_data = self.audio_files[self.current_file]
                file_data['dialogue'] = dialogue
                file_data['diarization'] = diarization
                
                self.root.after(0, lambda: self.progress_bar.set(1.0))
                self.root.after(0, lambda: self.display_result(dialogue))
                self.root.after(0, lambda: self.status_label.configure(text="✅ Анализ завершен успешно!"))
                self.root.after(1000, lambda: self.progress_bar.pack_forget())  # Скрываем через 1 сек
            except Exception as e:
                self.root.after(0, lambda: self.progress_bar.pack_forget())
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка анализа: {str(e)}"))
                self.root.after(0, lambda: self.status_label.configure(text="❌ Ошибка анализа"))
        
        thread = threading.Thread(target=run_analysis)
        thread.start()
    
    def display_result(self, dialogue):
        """Отображение результата анализа"""
        self.result_text.delete("0.0", "end")
        
        for speaker, text in dialogue:
            self.result_text.insert("end", f"{speaker}: ", "speaker")
            self.result_text.insert("end", f"{text}\n\n")
        
        self.result_text.tag_config("speaker", foreground="#f0f0f0", font=("Segoe UI", 12, "bold"))
    
    def save_result(self):
        """Сохранение результата в текстовый файл"""
        if not self.current_file:
            messagebox.showwarning("Предупреждение", "Выберите файл")
            return
        
        file_data = self.audio_files[self.current_file]
        if not file_data.get('dialogue'):
            messagebox.showwarning("Предупреждение", "Нет результатов для сохранения")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=file_data['display_name']
        )
        
        if file_path:
            dialogue = file_data['dialogue']
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"ОТКЛИК - {file_data['display_name']}\n")
                f.write("="*50 + "\n\n")
                for speaker, text in dialogue:
                    f.write(f"{speaker}: {text}\n\n")
            
            messagebox.showinfo("Успех", "Результат сохранен")
            self.status_label.configure(text=f"💾 Результат сохранен: {file_path}")
    
    def show_statistics(self):
        """Отображение окна статистики"""
        if not self.current_file:
            messagebox.showwarning("Предупреждение", "Выберите файл")
            return
        
        file_data = self.audio_files[self.current_file]
        if not file_data.get('dialogue'):
            messagebox.showwarning("Предупреждение", "Файл еще не проанализирован")
            return
        
        dialogue = file_data['dialogue']
        diarization = file_data['diarization']
        
        stats = calculate_statistics(dialogue, diarization)
        
        StatisticsWindow(self.root, file_data['display_name'], stats)


def main():
    """Запуск приложения"""
    root = ctk.CTk()
    root.configure(fg_color="#0a0e27")
    app = AudioAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

