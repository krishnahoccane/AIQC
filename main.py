from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import aiofiles
import os
import uuid

from services.audio_analysis import AudioAnalyzer
from services.audio_preprocessing import convert_to_standard_wav
from fastapi import FastAPI
import asyncio
from services.file_cleanup import cleanup_old_files
from contextlib import asynccontextmanager



app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -------------------------------------------------
# Route (Single Clean Entry Point)
# -------------------------------------------------
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):

    # -------------------------
    # Validate File Extension
    # -------------------------
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided."
        )

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower().strip()

    if ext not in [".wav", ".mp3",".flac", ".ogg"]:
        raise HTTPException(
            status_code=400,
            detail="File format is not supported."
        )

    # -------------------------
    # Save Uploaded File
    # -------------------------
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File saving failed: {str(e)}"
        )

    # -------------------------
    # Run Audio Analysis
    # -------------------------
    try:
        converted_path = convert_to_standard_wav(file_path)

        analyzer = AudioAnalyzer(converted_path)
        result = analyzer.analyze()

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

    finally:
        # to keep 3-day retention.
        pass

    return {
        "status": "success",
        "analysis": result
    }


async def periodic_cleanup():
    while True:
        cleanup_old_files()
        await asyncio.sleep(3600)  # Run every hour


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    asyncio.create_task(periodic_cleanup())
    yield
    # Shutdown (optional cleanup here)
