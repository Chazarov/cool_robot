import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinter import ttk
import threading
from analyse_service import merge_transcription_diarization


class AudioAnalyzerGUI:
    """Главный класс GUI для анализа аудио"""
    
    def __init__(self, root):
        """Инициализация интерфейса"""
        self.root = root
        self.root.title("Анализ аудио - Транскрибация и Диаризация")
        self.root.geometry("800x600")
        
        self.audio_files = {}
        self.current_file = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание виджетов интерфейса"""
        # Верхняя панель
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(fill=tk.X)
        
        tk.Button(top_frame, text="Загрузить аудио", command=self.load_audio, 
                 bg="#4CAF50", fg="white", padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        tk.Label(top_frame, text="Кол-во спикеров:").pack(side=tk.LEFT, padx=5)
        self.speakers_var = tk.StringVar(value="2")
        tk.Entry(top_frame, textvariable=self.speakers_var, width=5).pack(side=tk.LEFT)
        
        tk.Button(top_frame, text="Анализировать", command=self.analyze_audio,
                 bg="#2196F3", fg="white", padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        tk.Button(top_frame, text="Сохранить результат", command=self.save_result,
                 bg="#FF9800", fg="white", padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        # Список файлов
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(list_frame, text="Загруженные файлы:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.file_listbox = tk.Listbox(list_frame, height=5)
        self.file_listbox.pack(fill=tk.X, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # Область результатов
        result_frame = tk.Frame(self.root)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(result_frame, text="Результат анализа:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=20)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Статус бар
        self.status_label = tk.Label(self.root, text="Готов к работе", 
                                     bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_audio(self):
        """Загрузка аудиофайлов"""
        files = filedialog.askopenfilenames(
            title="Выберите аудиофайлы",
            filetypes=[("Audio files", "*.mp3 *.wav *.m4a"), ("All files", "*.*")]
        )
        
        for file_path in files:
            if file_path not in self.audio_files:
                self.audio_files[file_path] = None
                self.file_listbox.insert(tk.END, file_path.split("/")[-1])
        
        self.status_label.config(text=f"Загружено файлов: {len(self.audio_files)}")
    
    def on_file_select(self, event):
        """Обработка выбора файла из списка"""
        selection = self.file_listbox.curselection()
        if selection:
            idx = selection[0]
            self.current_file = list(self.audio_files.keys())[idx]
            
            if self.audio_files[self.current_file]:
                self.display_result(self.audio_files[self.current_file])
            else:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, "Файл еще не проанализирован")
    
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
        
        self.status_label.config(text="Идет анализ...")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Обработка... Пожалуйста, подождите...")
        
        def run_analysis():
            """Выполнение анализа в отдельном потоке"""
            try:
                dialogue = merge_transcription_diarization(self.current_file, n_speakers)
                self.audio_files[self.current_file] = dialogue
                
                self.root.after(0, lambda: self.display_result(dialogue))
                self.root.after(0, lambda: self.status_label.config(text="Анализ завершен"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка анализа: {str(e)}"))
                self.root.after(0, lambda: self.status_label.config(text="Ошибка анализа"))
        
        thread = threading.Thread(target=run_analysis)
        thread.start()
    
    def display_result(self, dialogue):
        """Отображение результата анализа"""
        self.result_text.delete(1.0, tk.END)
        
        for speaker, text in dialogue:
            self.result_text.insert(tk.END, f"{speaker}: ", "speaker")
            self.result_text.insert(tk.END, f"{text}\n\n")
        
        self.result_text.tag_config("speaker", font=("Arial", 10, "bold"), foreground="#2196F3")
    
    def save_result(self):
        """Сохранение результата в текстовый файл"""
        if not self.current_file or not self.audio_files[self.current_file]:
            messagebox.showwarning("Предупреждение", "Нет результатов для сохранения")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                for speaker, text in self.audio_files[self.current_file]:
                    f.write(f"{speaker}: {text}\n\n")
            
            messagebox.showinfo("Успех", "Результат сохранен")
            self.status_label.config(text=f"Результат сохранен: {file_path}")


def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = AudioAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

