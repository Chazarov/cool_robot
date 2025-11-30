import numpy as np
import librosa
from sklearn.mixture import GaussianMixture
from scipy.spatial.distance import cdist

# Загрузка и предобработка аудио
def load_audio(file_path, sr=16000):
    audio, _ = librosa.load(file_path, sr=sr, mono=True)
    return audio

# Извлечение MFCC признаков
def extract_features(audio, sr=16000, window_sec=1.0, hop_sec=0.5):
    window_length = int(window_sec * sr)
    hop_length = int(hop_sec * sr)
    
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13, 
                                hop_length=hop_length, 
                                n_fft=window_length)
    return mfcc.T

# Вычисление BIC для сравнения сегментов
def compute_bic(features1, features2):
    n1, n2 = len(features1), len(features2)
    d = features1.shape[1]
    
    combined = np.vstack([features1, features2])
    
    cov1 = np.cov(features1.T) + np.eye(d) * 1e-6
    cov2 = np.cov(features2.T) + np.eye(d) * 1e-6
    cov_combined = np.cov(combined.T) + np.eye(d) * 1e-6
    
    bic = (n1 + n2) * np.log(np.linalg.det(cov_combined)) - \
          n1 * np.log(np.linalg.det(cov1)) - \
          n2 * np.log(np.linalg.det(cov2)) - \
          0.5 * (d + 0.5 * d * (d + 1)) * np.log(n1 + n2)
    
    return bic

# Диаризация через GMM
def diarize_gmm(features, n_speakers=2):
    gmm = GaussianMixture(n_components=n_speakers, covariance_type='full', 
                          max_iter=100, random_state=42)
    labels = gmm.fit_predict(features)
    return labels

# Основная функция диаризации
def diarize_audio(file_path, n_speakers=2):
    audio = load_audio(file_path)
    features = extract_features(audio)
    labels = diarize_gmm(features, n_speakers)
    
    # Формирование временных меток
    hop_sec = 0.5
    timestamps = []
    for i, label in enumerate(labels):
        start_time = i * hop_sec
        end_time = (i + 1) * hop_sec
        timestamps.append((start_time, end_time, f"Speaker_{label}"))
    
    return timestamps

if __name__ == "__main__":
    results = diarize_audio("examples/e1.mp3", n_speakers=2)
    
    print("Результаты диаризации:")
    for start, end, speaker in results[:20]:
        print(f"{start:.1f}s - {end:.1f}s: {speaker}")
    print(f"... всего {len(results)} сегментов")

