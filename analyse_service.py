from transcribation_service import transcribe_audio
from dyarise_service import diarize_audio


def get_speaker_at_time(time, diarization):
    """Определяет спикера в заданное время"""
    for start, end, speaker in diarization:
        if start <= time < end:
            return speaker
    return "Speaker_Unknown"


def merge_transcription_diarization(audio_path, n_speakers=2):
    """Объединяет транскрибацию и диаризацию"""
    transcription = transcribe_audio(audio_path)
    diarization = diarize_audio(audio_path, n_speakers)
    
    dialogue = []
    current_speaker = None
    current_text = []
    
    for result in transcription:
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
    
    if current_text:
        dialogue.append((current_speaker, " ".join(current_text)))
    
    return dialogue


if __name__ == "__main__":
    dialogue = merge_transcription_diarization("examples/e2.mp3", n_speakers=2)
    
    for speaker, text in dialogue:
        print(f"{speaker}: {text}")

