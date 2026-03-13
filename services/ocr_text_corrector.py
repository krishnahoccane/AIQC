import re
import logging
import spacy

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Load lightweight NLP model
# ---------------------------------------------------------
nlp = spacy.load("en_core_web_sm")


# ---------------------------------------------------------
# OCR Text Normalization
# ---------------------------------------------------------
def normalize_ocr_text(text: str) -> str:
    """
    Normalize OCR output by cleaning noise
    while preserving artist/title tokens.
    """

    text = text.upper()

    # remove weird OCR symbols but keep letters/numbers
    text = re.sub(r"[^A-Z0-9 /&\-]", " ", text)

    # collapse spaces
    text = " ".join(text.split())

    return text


# ---------------------------------------------------------
# Remove OCR Garbage Tokens
# ---------------------------------------------------------
def remove_noise_tokens(text: str) -> str:
    """
    Remove very small or meaningless OCR fragments
    often produced by stylized album covers.
    """

    tokens = text.split()

    cleaned_tokens = []

    for token in tokens:

        # remove 1-character noise tokens
        if len(token) <= 1:
            continue

        # remove random OCR fragments like 'BR', 'FX'
        if re.fullmatch(r"[A-Z]{1,2}", token):
            continue

        cleaned_tokens.append(token)

    return " ".join(cleaned_tokens)


# ---------------------------------------------------------
# Entity Detection
# ---------------------------------------------------------
def extract_entities(text: str):
    """
    Extract meaningful entities such as:
    - Artist names
    - Album names
    - Song titles
    """

    doc = nlp(text)

    entities = []

    for ent in doc.ents:

        if ent.label_ in ["PERSON", "ORG", "WORK_OF_ART"]:
            entities.append(ent.text)

    return list(set(entities))


# ---------------------------------------------------------
# Final OCR Correction Pipeline
# ---------------------------------------------------------
def correct_ocr_text(text: str) -> str:
    """
    Production OCR cleanup pipeline.
    """

    try:

        if not text:
            return ""

        # Step 1: Normalize OCR output
        text = normalize_ocr_text(text)

        # Step 2: Remove OCR garbage tokens
        text = remove_noise_tokens(text)

        # Step 3: Detect entities (artist/title)
        entities = extract_entities(text)

        # If entities detected, prioritize them
        if entities:
            return " ".join(entities)

        # fallback to cleaned text
        return text

    except Exception as e:

        logger.exception("OCR NLP correction failed")

        return text