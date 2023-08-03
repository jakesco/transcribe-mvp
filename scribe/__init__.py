import logging
from contextlib import asynccontextmanager
from logging.config import dictConfig
from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import BackgroundTasks, FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import app_settings, log_config
from .transcribe import get_job_status, job_dump, job_load, transcribe_file

dictConfig(log_config)

logger = logging.getLogger("scribe")
settings = app_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure media and transcription directories exist
    Path(settings.media).mkdir(parents=True, exist_ok=True)
    job_load()
    yield
    job_dump()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/jobs", response_class=HTMLResponse, include_in_schema=False)
async def jobs(request: Request):
    return templates.TemplateResponse(
        "jobs.html", {"request": request, "jobs": get_job_status()}
    )


@app.get("/media/{filename}")
async def download(filename: str):
    return FileResponse(
        f"{settings.media}/{filename}",
        media_type="text/plain",
        filename=filename,
    )


@app.post("/")
async def transcribe(
    request: Request, file: Annotated[UploadFile, File()], tasks: BackgroundTasks
):
    if file is not None:
        destination = Path(f"{settings.media}/{file.filename}")
        async with aiofiles.open(destination, "wb") as f:
            content = await file.read()
            await f.write(content)
        tasks.add_task(transcribe_file, destination)
        message = f"File {file.filename} successfully uploaded"
        color = "#00FF00"
    else:
        message = "File failed to upload"
        color = "#FF0000"

    return templates.TemplateResponse(
        "form.html", {"request": request, "message": message, "color": color}
    )
