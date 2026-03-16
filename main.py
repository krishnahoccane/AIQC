from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import aiofiles
import os
import uuid
import traceback

from services.audio_analysis import AudioAnalyzer
from services.audio_preprocessing import convert_to_standard_wav
import asyncio
from services.file_cleanup import cleanup_old_files
from contextlib import asynccontextmanager
from services.nlp_analysis import NLPAnalyzer
from services.moderation import HybridModeration
from services.genre_detection import GenreAnalyzer
from services.political_content import PoliticalModerationAnalyzer
from services.metadata_generator import MetadataGenerator
from fastapi import Request
from fastapi.staticfiles import StaticFiles

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from middleware.rate_limit import limiter
from utils.logger import logger
from routes import auth , admin , staff, issue
from core.database import engine, Base
#from services.cover_art_analysis import (
    #extract_cover_art,
    #extract_text_from_cover
#)
from services.cover_art_extractor import extract_cover_art
from services.cover_art_analysis import extract_text_from_cover
#from services.cover_art_analysis import extract_text_from_cover

app = FastAPI()
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


#from routes import issues

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(staff.router)
app.include_router(issue.router)

Base.metadata.create_all(bind=engine)

# Attach limiter to app
app.state.limiter = limiter

# Add middleware
app.add_middleware(SlowAPIMiddleware)

# Add exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


#@app.exception_handler(Exception)
#async def global_exception_handler(request: Request, exc: Exception):
    #logger.error(str(exc))
    #return JSONResponse(
        #status_code=500,
        #content={"message": "Internal server error"}
    #)


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

        genre_analyzer = GenreAnalyzer()
        genre_result = genre_analyzer.analyze(converted_path)

        metadata_gen = MetadataGenerator()

        nlp = NLPAnalyzer()
        nlp_result = nlp.analyze(converted_path)

        metadata = metadata_gen.build_metadata(
            filename=file.filename,
            language=nlp_result["language"],
            transcript=nlp_result["text"]
        )

        political_analyzer = PoliticalModerationAnalyzer()
        political_result = political_analyzer.analyze(nlp_result["text"])

        moderator = HybridModeration()
        moderation_result = moderator.analyze(
            text=nlp_result["text"],
            language=nlp_result["language"]
        )

        flag = moderation_result["moderation_flag"]

        # ✅ Initialize variables BEFORE use
        saved_cover_path = None
        advisory_cover_path = None
        cover_text = ""

        #  Extract cover BEFORE overlay
        cover_bytes = extract_cover_art(file_path)

        if cover_bytes:
            cover_filename = f"{uuid.uuid4()}_cover.png"
            saved_cover_path = os.path.join(UPLOAD_DIR, cover_filename)

            with open(saved_cover_path, "wb") as f:
                f.write(cover_bytes)

            cover_text = extract_text_from_cover(cover_bytes)

        # ✅  Overlay AFTER cover exists
        if saved_cover_path and flag.get("explicit") is True and flag.get("advisory_required") is True:
            advisory_cover_path = moderator.overlay_parental_advisory(
                cover_path=saved_cover_path,
                logo_path="assets/parental.png"
            )
            logger.info(f"Advisory cover generated: {advisory_cover_path}")
        else:
            advisory_cover_path = saved_cover_path if saved_cover_path else None

        # ✅  Convert Windows path → URL path
        if advisory_cover_path is not None:
            cover_url = "/" + advisory_cover_path.replace("\\", "/")
        else:
            cover_url = None

    except Exception as e:
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

    finally:
        pass

    return {
        "status": "success",
        "analysis": result,
        "genre": genre_result,
        "metadata": metadata,
        "nlp": nlp_result,
        "Moderation": moderation_result,
        "Political_moderation": political_result,
        "moderation_flag": moderation_result["moderation_flag"],
        "cover_art_analysis": {
            "cover_url": cover_url,
            "ocr_text": cover_text
        },
        
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
