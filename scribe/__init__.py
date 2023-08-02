from pathlib import Path
from typing import Annotated

import aiofiles
from aiofiles.os import scandir
from fastapi import BackgroundTasks, FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import app_settings
from .transcribe import transcribe_file

settings = app_settings()

# Ensure media and transcription directories exist
Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
Path(settings.transcript_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/transcriptions", response_class=HTMLResponse, include_in_schema=False)
async def transcriptions(request: Request):
    files = await scandir(settings.transcript_dir)
    transcriptions = [file.name for file in files if file.is_file()]
    return templates.TemplateResponse(
        "transcriptions.html", {"request": request, "transcriptions": transcriptions}
    )


@app.get("/media/{filename}")
async def download(filename: str):
    return FileResponse(
        f"{settings.transcript_dir}/{filename}",
        media_type="text/plain",
        filename=filename,
    )


@app.post("/")
async def transcribe(
    request: Request, file: Annotated[UploadFile, File()], tasks: BackgroundTasks
):
    if file is not None:
        filepath = Path(f"{settings.media_dir}/{file.filename}")
        async with aiofiles.open(filepath, "wb") as f:
            content = await file.read()
            await f.write(content)
        tasks.add_task(transcribe_file, filepath)
        message = f"File {file.filename} successfully uploaded"
    else:
        message = "File failed to upload"

    return templates.TemplateResponse(
        "messages.html", {"request": request, "message": message}
    )
