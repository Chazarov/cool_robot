from analyse_service import merge_transcription_diarization

if __name__ == "__main__":
    dialogue = merge_transcription_diarization("examples/e1.mp3", n_speakers=2)
    
    for speaker, text in dialogue:
        print(f"{speaker}: {text}")

