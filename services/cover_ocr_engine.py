import cv2
import numpy as np
import easyocr
import logging

logger = logging.getLogger(__name__)

# ── Singleton reader ───────────────────────────────────────────────────────────
# Fallback engine uses English-only for maximum compatibility and speed.
# Full multilingual coverage is handled by high_accuracy_cover_ocr.py
_reader = None


def get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        logger.info("Loading fallback OCR reader (en only)…")
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


# ── Image preprocessing ────────────────────────────────────────────────────────

def enhance_text_regions(img: np.ndarray) -> np.ndarray:
    """Greyscale + adaptive threshold — helps low-contrast cover text."""
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    blur   = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2,
    )
    return thresh


# ── Core OCR function ──────────────────────────────────────────────────────────

def run_cover_ocr(img: np.ndarray, conf_threshold: float = 0.30) -> str:
    """
    Lightweight English-only OCR fallback for cover art.

    Applies adaptive thresholding which helps on low-contrast covers.
    Called automatically by cover_art_analysis.py when high-accuracy OCR fails.
    """
    h, w = img.shape[:2]
    if max(h, w) > 2000:
        scale = 2000 / max(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    processed = enhance_text_regions(img)
    reader    = get_reader()
    results   = reader.readtext(processed, detail=1, paragraph=False)

    texts = [
        text.strip()
        for (_bbox, text, conf) in results
        if conf >= conf_threshold and text.strip()
    ]

    return " ".join(texts)