import os
from vosk import Model


class ModelManager:
    """Singleton менеджер для управления моделями Vosk"""
    
    _instance = None
    _model = None
    _model_path = "vosk-model-ru-0.42"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance
    
    def get_model(self):
        """Получить модель (загружается только один раз)"""
        if self._model is None:
            if not os.path.exists(self._model_path):
                raise FileNotFoundError(
                    f"Модель не найдена по пути: {self._model_path}\n"
                    f"Скачайте модель с https://alphacephei.com/vosk/models и распакуйте в папку проекта"
                )
            
            print(f"⏳ Загрузка модели из {self._model_path}...")
            self._model = Model(self._model_path)
            print("✅ Модель загружена!")
        
        return self._model
    
    def is_loaded(self):
        """Проверить, загружена ли модель"""
        return self._model is not None

