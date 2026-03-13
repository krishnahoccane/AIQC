import cv2
import numpy as np
import easyocr
import logging

logger = logging.getLogger(__name__)

# ── EasyOCR compatibility rule ─────────────────────────────────────────────────
# Every non-Latin script is ONLY compatible with English.
# You CANNOT mix Telugu + Hindi, or Telugu + Japanese, etc.
# Each script needs its own dedicated reader.
#
#   ["en"]           — English only (base)
#   ["te", "en"]     — Telugu + English
#   ["hi", "en"]     — Hindi / Devanagari + English
#   ["ja", "en"]     — Japanese + English
#   ["ko", "en"]     — Korean + English
#   ["ch_sim", "en"] — Simplified Chinese + English

_reader_en = None
_reader_te = None
_reader_hi = None
_reader_ja = None
_reader_ko = None
_reader_zh = None


def get_en_reader() -> easyocr.Reader:
    global _reader_en
    if _reader_en is None:
        logger.info("Loading English OCR reader…")
        _reader_en = easyocr.Reader(["en"], gpu=False)
    return _reader_en


def get_te_reader() -> easyocr.Reader:
    global _reader_te
    if _reader_te is None:
        logger.info("Loading Telugu OCR reader (te/en)…")
        _reader_te = easyocr.Reader(["te", "en"], gpu=False)
    return _reader_te


def get_hi_reader() -> easyocr.Reader:
    global _reader_hi
    if _reader_hi is None:
        logger.info("Loading Hindi OCR reader (hi/en)…")
        _reader_hi = easyocr.Reader(["hi", "en"], gpu=False)
    return _reader_hi


def get_ja_reader() -> easyocr.Reader:
    global _reader_ja
    if _reader_ja is None:
        logger.info("Loading Japanese OCR reader (ja/en)…")
        _reader_ja = easyocr.Reader(["ja", "en"], gpu=False)
    return _reader_ja


def get_ko_reader() -> easyocr.Reader:
    global _reader_ko
    if _reader_ko is None:
        logger.info("Loading Korean OCR reader (ko/en)…")
        _reader_ko = easyocr.Reader(["ko", "en"], gpu=False)
    return _reader_ko


def get_zh_reader() -> easyocr.Reader:
    global _reader_zh
    if _reader_zh is None:
        logger.info("Loading Chinese OCR reader (ch_sim/en)…")
        _reader_zh = easyocr.Reader(["ch_sim", "en"], gpu=False)
    return _reader_zh


# ── Image helpers ──────────────────────────────────────────────────────────────

def resize_safe(img: np.ndarray, max_dim: int = 2000) -> np.ndarray:
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return img


def _preprocess_for_ocr(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


# ── Core OCR function ──────────────────────────────────────────────────────────

def run_high_accuracy_ocr(img: np.ndarray, conf_threshold: float = 0.35) -> str:
    """
    Run high-accuracy multilingual OCR using one reader per script:
      1. English       ["en"]
      2. Telugu        ["te", "en"]
      3. Hindi         ["hi", "en"]
      4. Japanese      ["ja", "en"]
      5. Korean        ["ko", "en"]
      6. Chinese       ["ch_sim", "en"]

    Each reader runs independently. English duplicates from script readers
    are suppressed via a seen-set. Any failing reader is skipped gracefully.
    """
    img = resize_safe(img)
    img = _preprocess_for_ocr(img)

    all_readers = [
        get_en_reader,
        get_te_reader,
        get_hi_reader,
        get_ja_reader,
        get_ko_reader,
        get_zh_reader,
    ]

    seen:  set  = set()
    texts: list = []

    for get_reader in all_readers:
        try:
            reader  = get_reader()
            results = reader.readtext(img, detail=1, paragraph=False)
            for (_bbox, text, conf) in results:
                text = text.strip()
                if conf >= conf_threshold and text and text not in seen:
                    seen.add(text)
                    texts.append(text)
        except Exception:
            logger.exception("OCR reader %s failed — skipping.", get_reader.__name__)

    return " ".join(texts)