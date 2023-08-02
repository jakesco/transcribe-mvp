import os
from io import BufferedReader
from pathlib import Path
from typing import Iterator
import tempfile

from concurrent.futures import ThreadPoolExecutor

import openai
import pydub
from dotenv import dotenv_values
from pydub.utils import mediainfo

# from .config import app_settings

# settings = app_settings()

settings = dotenv_values(".env")

# openai.api_key = settings.openai_api_key
openai.api_key = settings["OPENAI_API_KEY"]


def transcribe(audio_file: BufferedReader):
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    audio_file.close()
    return transcript


def split_audio_file(filepath: Path, segements: int) -> Iterator[BufferedReader]:
    """Splits audio file into equal segments"""
    audio = pydub.AudioSegment.from_file(filepath)

    total_duration = len(audio)
    segment_duration = total_duration // segements
    for i in range(segements):
        start = i * segment_duration
        end = (i + 1) * segment_duration
        segment = audio[start:end]

        temp = tempfile.NamedTemporaryFile(suffix=".mp3")
        yield segment.export(temp, format="mp3")


def main(filepath: str):
    info = mediainfo(filepath)
    sec = info["duration"]
    size = os.path.getsize(filepath) / (1024 * 1024)
    print(f"Size: {size}MB, Duration: {sec}s")


if __name__ == "__main__":
    xmas = Path("/home/jake/Music/xmas.m4a")
    audio_files = split_audio_file(xmas, 5)
    with ThreadPoolExecutor(max_workers=5) as executor:
        result = executor.map(transcribe, audio_files)

    transcript = " ".join([r['text'] for r in result])
    print(transcript)
