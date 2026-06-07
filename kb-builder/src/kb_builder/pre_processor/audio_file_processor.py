import whisper

from pathlib import Path

from shared.logger import Logger

 
def process_audio(audio_file_path: str):   
    model = whisper.load_model("base")  # Adjust model size as needed
    output = model.transcribe(audio_file_path)

    return output['text']


