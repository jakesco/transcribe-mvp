from typing import Annotated
from fastapi import FastAPI, Request, File, Form, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import app_settings

settings = app_settings()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/")
async def transcribe(request: Request, file: Annotated[UploadFile, File()]):
    message = f"{file.filename} uploaded" if file else "File not uploaded"
    return templates.TemplateResponse("messages.html", {"request": request, "message": message})

