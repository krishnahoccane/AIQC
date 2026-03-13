import re


def clean_cover_text(text: str) -> str:
    """
    Clean raw OCR output from cover art.

    Removes stray punctuation / OCR artefacts while preserving:
      - ASCII word characters and whitespace
      - Telugu   (U+0C00–U+0C7F)
      - Hindi / Devanagari (U+0900–U+097F)
      - CJK Unified Ideographs / Chinese (U+4E00–U+9FFF)
      - Japanese hiragana + katakana (U+3040–U+30FF)
      - Korean Hangul syllables (U+AC00–U+D7AF)
    """
    if not text:
        return ""

    # Build the character whitelist as a single raw string to avoid
    # the broken implicit-concatenation bug in the original code.
    pattern = (
        r"[^\w\s"
        r"\u0C00-\u0C7F"   # Telugu
        r"\u0900-\u097F"   # Hindi / Devanagari
        r"\u4E00-\u9FFF"   # Chinese (CJK Unified Ideographs)
        r"\u3040-\u30FF"   # Japanese (hiragana + katakana)
        r"\uAC00-\uD7AF"   # Korean Hangul
        r"]"
    )

    text = re.sub(pattern, " ", text, flags=re.UNICODE)
    text = " ".join(text.split())   # collapse whitespace
    return text.strip()