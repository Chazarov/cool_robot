def calculate_statistics(dialogue, diarization):
    """Вычисление статистики по диалогу"""
    
    # Количество реплик каждого говорящего
    speaker_turns = {}
    for speaker, text in dialogue:
        speaker_turns[speaker] = speaker_turns.get(speaker, 0) + 1
    
    # Средняя длина высказываний каждого говорящего
    speaker_avg_length = {}
    speaker_total_words = {}
    for speaker, text in dialogue:
        words = len(text.split())
        speaker_total_words[speaker] = speaker_total_words.get(speaker, 0) + words
    
    for speaker in speaker_turns:
        speaker_avg_length[speaker] = speaker_total_words[speaker] / speaker_turns[speaker]
    
    # Активность обсуждения (количество пауз)
    total_pauses = 0
    total_pause_duration = 0
    
    for i in range(len(diarization) - 1):
        pause = diarization[i + 1][0] - diarization[i][1]
        if pause > 0:
            total_pauses += 1
            total_pause_duration += pause
    
    avg_pause = total_pause_duration / total_pauses if total_pauses > 0 else 0
    activity_score = 100 / (1 + avg_pause)
    
    # Коэффициент равномерности распределения речи
    total_turns = sum(speaker_turns.values())
    expected_turns = total_turns / len(speaker_turns) if speaker_turns else 0
    
    variance = sum((turns - expected_turns) ** 2 for turns in speaker_turns.values())
    variance = variance / len(speaker_turns) if speaker_turns else 0
    
    uniformity_coefficient = 100 / (1 + variance / max(expected_turns, 1))
    
    return {
        "speaker_turns": speaker_turns,
        "speaker_avg_length": speaker_avg_length,
        "total_pauses": total_pauses,
        "avg_pause": avg_pause,
        "activity_score": activity_score,
        "uniformity_coefficient": uniformity_coefficient
    }

