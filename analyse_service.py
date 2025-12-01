from transcribation_service import transcribe_audio
from dyarise_service import diarize_audio


def get_speaker_at_time(time, diarization):
    """Определяет спикера в заданное время"""
    for start, end, speaker in diarization:
        if start <= time < end:
            return speaker
    return "Speaker_Unknown"


def merge_transcription_diarization(audio_path, n_speakers=2, progress_callback=None):
    """Объединяет транскрибацию и диаризацию"""
    
    # Этап 1: Транскрибация
    if progress_callback:
        progress_callback("Транскрибация", 0.2, "Запуск распознавания речи...")
    
    transcription = transcribe_audio(audio_path)
    
    if progress_callback:
        progress_callback("Транскрибация", 0.4, "Распознавание завершено")
    
    # Этап 2: Диаризация
    if progress_callback:
        progress_callback("Диаризация", 0.5, "Определение спикеров...")
    
    diarization = diarize_audio(audio_path, n_speakers)
    
    if progress_callback:
        progress_callback("Диаризация", 0.7, "Спикеры определены")
    
    # Этап 3: Объединение
    if progress_callback:
        progress_callback("Объединение", 0.75, "Формирование диалога...")
    
    dialogue = []
    current_speaker = None
    current_text = []
    
    total_results = len(transcription)
    for idx, result in enumerate(transcription):
        if "result" in result:
            for word_info in result["result"]:
                word = word_info["word"]
                time = word_info["start"]
                speaker = get_speaker_at_time(time, diarization)
                
                if speaker != current_speaker:
                    if current_text:
                        dialogue.append((current_speaker, " ".join(current_text)))
                    current_speaker = speaker
                    current_text = [word]
                else:
                    current_text.append(word)
        
        # Обновляем прогресс объединения
        if progress_callback and total_results > 0:
            progress = 0.75 + 0.2 * (idx + 1) / total_results
            progress_callback("Объединение", progress, f"Обработано {idx+1} из {total_results} сегментов")
    
    if current_text:
        dialogue.append((current_speaker, " ".join(current_text)))
    
    if progress_callback:
        progress_callback("Объединение", 0.95, "Финализация результатов...")
    
    return dialogue, diarization


if __name__ == "__main__":
    dialogue, diarization = merge_transcription_diarization("examples/e2.mp3", n_speakers=2)
    
    for speaker, text in dialogue:
        print(f"{speaker}: {text}")

