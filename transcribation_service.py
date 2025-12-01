import json
import wave
import io
import numpy as np
from vosk import KaldiRecognizer
import librosa
from model_manager import ModelManager


def convert_to_wav(audio_path):
    """Конвертирует аудиофайл в WAV формат"""
    audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    audio_int16 = (audio * 32767).astype(np.int16)
    
    wav_data = io.BytesIO()
    with wave.open(wav_data, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_int16.tobytes())
    wav_data.seek(0)
    return wav_data


def transcribe_audio(audio_path):
    """Транскрибирует аудиофайл"""
    # Используем общую модель через менеджер
    model_manager = ModelManager()
    model = model_manager.get_model()
    
    wav_data = convert_to_wav(audio_path)
    wf = wave.open(wav_data, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    
    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            results.append(json.loads(rec.Result()))
    
    results.append(json.loads(rec.FinalResult()))
    
    return results


if __name__ == "__main__":
    results = transcribe_audio("examples/e2.mp3")
    
    for result in results:
        if "text" in result:
            print(result["text"])

