import logging
from typing import Optional

import cv2
import numpy as np

from services.high_accuracy_cover_ocr import run_high_accuracy_ocr
from services.cover_ocr_engine import run_cover_ocr
from services.cover_text_cleaner import clean_cover_text

logger = logging.getLogger(__name__)


# ── Public API ─────────────────────────────────────────────────────────────────

def extract_text_from_cover(image_bytes: Optional[bytes]) -> str:
    """
    Extract clean multilingual text from cover-art image bytes.

    Pipeline
    --------
    1. Decode raw bytes → OpenCV BGR image.
    2. Attempt high-accuracy dual-reader OCR
       (run_high_accuracy_ocr: en/te/hi/ja/ko  +  ch_sim/en).
    3. If the primary OCR returns nothing, fall back to the lightweight
       single-reader engine (run_cover_ocr) which applies adaptive
       thresholding – often helpful for low-contrast covers.
    4. Clean the raw OCR output (strip artefacts, collapse whitespace).

    Parameters
    ----------
    image_bytes : Raw image bytes (JPEG / PNG / WebP / etc.).

    Returns
    -------
    Cleaned text string, or "" on failure.
    """
    if not image_bytes:
        logger.warning("extract_text_from_cover: no image bytes provided.")
        return ""

    # ── 1. Decode ──────────────────────────────────────────────────────────────
    np_img = np.frombuffer(image_bytes, dtype=np.uint8)
    img    = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        logger.error("extract_text_from_cover: failed to decode image bytes.")
        return ""

    # ── 2. Primary OCR (high-accuracy dual-reader) ─────────────────────────────
    try:
        raw_text = run_high_accuracy_ocr(img)
    except Exception:
        logger.exception("High-accuracy OCR failed; will try fallback engine.")
        raw_text = ""

    # ── 3. Fallback OCR (single reader + adaptive threshold) ───────────────────
    if not raw_text.strip():
        logger.info("Primary OCR returned empty result – running fallback OCR.")
        try:
            raw_text = run_cover_ocr(img)
        except Exception:
            logger.exception("Fallback OCR also failed.")
            raw_text = ""

    # ── 4. Clean & return ──────────────────────────────────────────────────────
    clean_text = clean_cover_text(raw_text)
    logger.debug("Cover OCR result: %r", clean_text)
    return clean_text