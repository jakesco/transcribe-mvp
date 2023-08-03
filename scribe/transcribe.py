import time
import pickle
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from io import BufferedReader
from math import ceil
from pathlib import Path
from enum import StrEnum
from dataclasses import dataclass

import openai
import pydub

from .config import app_settings

MAX_FILE_SIZE = 20  # in MB

settings = app_settings()


class JobStatus(StrEnum):
    RUNNING = "Running"
    FAILED = "Failed"
    COMPLETED = "Completed"


@dataclass
class Job:
    infile: Path
    status: JobStatus
    outfile: Path | None = None


job_status: list[Job] = []


def job_dump():
    with open(settings.job_dump, "wb") as f:
        pickle.dump(job_status, f)
    print(job_status)


def job_load():
    if not os.path.isfile(settings.job_dump):
        return
    global job_status
    with open(settings.job_dump, "rb") as f:
        job_status = pickle.load(f)
    print(job_status)

def get_job_status():
    return job_status

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


def transcribe(job: Job) -> str:
    try:
        size = os.path.getsize(job.infile) / (1024 * 1024)  # in MB
        if size > MAX_FILE_SIZE:
            n = ceil(size / MAX_FILE_SIZE)
            segments = split_audio_file(job.infile, n)
            with ThreadPoolExecutor(max_workers=2) as executor:
                result = executor.map(send_file, segments)
            for seg in segments:
                seg.close()
            transcript = "".join([r["text"] for r in result])
        else:
            segment = open(job.infile, "rb")
            transcript = send_file(segment)["text"]
            segment.close()
    except Exception as e:
        job.status = JobStatus.FAILED
        raise e

    return transcript


def transcribe_file(filepath: Path):
    """Saves transcription to transcripts directory"""
    transcript_path = Path(
        f"{settings.media}/{filepath.with_suffix('.txt').name}"
    )
    new_job = Job(filepath, JobStatus.RUNNING, transcript_path)
    job_status.append(new_job)
    transcription = transcribe(new_job)
    new_job.status = JobStatus.COMPLETED
    with open(transcript_path, "w") as f:
        f.write(transcription)
        f.write("\n")
