import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from io import BufferedReader
from math import ceil
from pathlib import Path

import openai
import pydub

from .config import app_settings

MAX_FILE_SIZE = 20  # in MB

settings = app_settings()


def send_file(audio_file: BufferedReader):
    return openai.Audio.transcribe(
        "whisper-1", audio_file, api_key=settings.openai_api_key
    )


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


def transcribe(filepath: Path) -> str:
    size = os.path.getsize(filepath) / (1024 * 1024)  # in MB
    if size > MAX_FILE_SIZE:
        n = ceil(size / MAX_FILE_SIZE)
        segments = split_audio_file(filepath, n)
        with ThreadPoolExecutor(max_workers=2) as executor:
            result = executor.map(send_file, segments)
        for seg in segments:
            seg.close()
        transcript = "".join([r["text"] for r in result])
    else:
        segment = open(filepath, "rb")
        transcript = send_file(segment)["text"]
        segment.close()

    return transcript


def transcribe_file(filepath: Path):
    """Saves transcription to transcripts directory"""
    transcription_path = Path(
        f"{settings.transcript_dir}/{filepath.with_suffix('.txt').name}"
    )
    transcription = transcribe(filepath)
    print(transcription)
    with open(transcription_path, "w") as f:
        f.write(transcription)
        f.write("\n")
