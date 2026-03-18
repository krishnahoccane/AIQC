
from fastapi.responses import JSONResponse
import os
import traceback
import asyncio

from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from middleware.rate_limit import limiter
from services.file_cleanup import cleanup_old_files
from contextlib import asynccontextmanager

from routes import auth, admin, staff, issue
from core.database import engine, Base
from services.audio_pipeline import AudioPipeline
from dotenv import load_dotenv
env_path = os.path.join(os.getcwd(), ".env")
load_dotenv(env_path)
from fastapi import FastAPI, UploadFile, File, HTTPException

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")



app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(staff.router)
app.include_router(issue.router)

Base.metadata.create_all(bind=engine)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in [".wav", ".mp3", ".flac", ".ogg"]:
        raise HTTPException(status_code=400, detail="File format is not supported.")

    try:
        pipeline = AudioPipeline()
        result = await pipeline.process(file)
        return result

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


async def periodic_cleanup():
    while True:
        cleanup_old_files()
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(periodic_cleanup())
    yield