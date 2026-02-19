import re
import threading
import spacy
from transformers import pipeline
import unicodedata

from services.profanity_lists import PROFANITY_WORDS


class HybridModeration:
    """
    Production-ready hybrid moderation system

    Combines:
    - Multilingual wordlist detection
    - Transformer-based hate/abuse detection

    Final Logic:
    - >= 0.80 → explicit (high)
    - 0.60–0.79 → moderate (medium)
    - 0.40–0.59 → low
    - < 0.40 → clean (none)
    """

    _nlp = None
    _transformer = None
    _profanity_set = None
    _lock = threading.Lock()

    # -----------------------------
    # Initialize models safely
    # -----------------------------
    def __init__(self):

        with HybridModeration._lock:

            if HybridModeration._nlp is None:
                HybridModeration._nlp = spacy.blank("xx")

            if HybridModeration._transformer is None:
                HybridModeration._transformer = pipeline(
                    "text-classification",
                    model="unitary/multilingual-toxic-xlm-roberta",
                    truncation=True
                )

            if HybridModeration._profanity_set is None:
                flattened = set()
                for language_words in PROFANITY_WORDS.values():
                    for word in language_words:
                        flattened.add(word.lower())
                HybridModeration._profanity_set = flattened

    # -----------------------------
    # Normalize multilingual text
    # -----------------------------
    def normalize(self, text):

        text = unicodedata.normalize("NFKC", text)
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    # -----------------------------
    # Wordlist detection
    # -----------------------------
    def detect_wordlist(self, text):

        normalized = self.normalize(text)
        doc = HybridModeration._nlp(normalized)
        tokens = [token.text for token in doc]

        matched = [
            token for token in tokens
            if token in HybridModeration._profanity_set
        ]

        matched_unique = list(set(matched))

        return {
            "detected": len(matched_unique) > 0,
            "matched_words": matched_unique,
            "count": len(matched_unique),
            "confidence": 1.0 if matched_unique else 0.0
        }

    # -----------------------------
    # Transformer detection
    # -----------------------------
    # -----------------------------
# Transformer detection
# -----------------------------
    def detect_transformer(self, text):

        result = HybridModeration._transformer(text)[0]

        raw_label = result["label"].upper()
        confidence = float(result["score"])

        label_map = {
            "TOXIC": "hate",
            "INSULT": "abusive",
            "OBSCENE": "explicit",
            "IDENTITY_HATE": "hate",
            "OFFENSIVE": "abusive",
            "HATE": "hate",
            "LABEL_0": "clean",
            "LABEL_1": "hate"
        }

        mapped_label = label_map.get(raw_label, raw_label.lower())

        # STRICT RULE: detected only if confidence >= 0.80
        if confidence >= 0.80 and mapped_label in ["hate", "abusive", "explicit"]:
            detected = True
        else:
            detected = False

        return {
            "detected": detected,
            "label": mapped_label,
            "confidence": round(confidence, 3)
        }


    # -----------------------------
    # Combine confidence
    # -----------------------------
    def combine_confidence(self, wordlist, transformer):

        if not wordlist["detected"] and not transformer["detected"]:
            return 0.0

        if wordlist["detected"] and transformer["detected"]:
            return round(
                min(1.0, 0.7 * transformer["confidence"] + 0.3),
                3
            )

        elif wordlist["detected"]:
            return 1.0

        elif transformer["detected"]:
            return round(transformer["confidence"], 3)

        return 0.0

    # -----------------------------
    # Final analysis
    # -----------------------------
    def analyze(self, text, language):

        wordlist = self.detect_wordlist(text)
        transformer = self.detect_transformer(text)

        toxicity_score = self.combine_confidence(
            wordlist,
            transformer
        )

        # -----------------------------
        # Hard classification thresholds
        # -----------------------------
        if toxicity_score >= 0.80:
            status = "explicit"
            severity = "high"

        elif toxicity_score >= 0.60:
            status = "moderate"
            severity = "medium"

        elif toxicity_score >= 0.40:
            status = "low"
            severity = "low"

        else:
            status = "clean"
            severity = "none"

        #clean_confidence = round(1.0 - toxicity_score, 3)

        return {
            "explicit_content": {
                "status": status,
                "severity": severity,
                "confidence": round(toxicity_score, 3),
                #"clean_confidence": clean_confidence
            },
            "language": language,
            "sources": {
                "wordlist": wordlist,
                "transformer": transformer
            }
        }
