import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from io import BufferedReader
from math import ceil
from pathlib import Path

import openai
import pydub
from dotenv import dotenv_values

MAX_FILE_SIZE = 20  # in MB

# from .config import app_settings

# settings = app_settings()

settings = dotenv_values(".env")

# openai.api_key = settings.openai_api_key
openai.api_key = settings["OPENAI_API_KEY"]


def transcribe(audio_file: BufferedReader):
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    audio_file.close()
    return transcript


def split_audio_file(filepath: Path, segements: int) -> list[BufferedReader]:
    """Splits audio file into equal segments"""
    audio = pydub.AudioSegment.from_file(filepath)

    total_duration = len(audio)
    segment_duration = total_duration // segements
    segments = []
    for i in range(segements):
        start = i * segment_duration
        end = (i + 1) * segment_duration
        segment = audio[start:end]

        temp = tempfile.NamedTemporaryFile(suffix=".mp3")
        segments.append(segment.export(temp, format="mp3"))
    return segments


if __name__ == "__main__":
    xmas = Path("/home/jake/Music/xmas.m4a")
    size = os.path.getsize(xmas) / (1024 * 1024)  # in MB

    if size > MAX_FILE_SIZE:
        n = ceil(size / MAX_FILE_SIZE)
        segments = split_audio_file(xmas, n)
        with ThreadPoolExecutor(max_workers=2) as executor:
            result = executor.map(transcribe, segments)
        for seg in segments:
            seg.close()
        transcript = "".join([r["text"] for r in result])
    else:
        segment = open(xmas, "rb")
        transcript = transcribe(segment)["text"]
        segment.close()

    print(transcript)
