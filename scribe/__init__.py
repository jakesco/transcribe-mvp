from typing import Annotated
from fastapi import FastAPI, Request, File, Form, UploadFile
from fastapi.staticfiles import StaticFiles

from .config import app_settings

settings = app_settings()

app = FastAPI()

@app.post("/transcribe")
async def transcribe(file: Annotated[UploadFile, File()]):
    if not file:
        return {"message": "File not uploaded"}
    else:
        return {"filename": file.filename}

# This needs to be defined last to not shadow other endpoints
app.mount("/", StaticFiles(directory="static", html=True), name="static")
