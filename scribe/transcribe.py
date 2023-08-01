import openai

from .config import app_settings

settings = app_settings()

openai.api_key = settings.openai_api_key

audio_file = open("./tests/simple_sentence.m4a", "rb")
transcript = openai.Audio.transcribe("whisper-1", audio_file)
print(transcript)
