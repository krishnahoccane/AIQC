import re
import threading
import spacy
from transformers import pipeline
import unicodedata

from services.profanity_lists import PROFANITY_WORDS


class HybridModeration:

    _nlp = None
    _transformer = None
    _profanity_set = None
    _lock = threading.Lock()

    def __init__(self):

        with HybridModeration._lock:

            # Load spaCy tokenizer once
            if HybridModeration._nlp is None:
                HybridModeration._nlp = spacy.blank("xx")

            # Load transformer once
            if HybridModeration._transformer is None:
                HybridModeration._transformer = pipeline(
    "text-classification",
    model="unitary/multilingual-toxic-xlm-roberta",
    truncation=True
)


            # Flatten multilingual profanity dict into fast lookup set
            if HybridModeration._profanity_set is None:

                flattened = set()

                for language_words in PROFANITY_WORDS.values():

                    for word in language_words:
                        flattened.add(word.lower())

                HybridModeration._profanity_set = flattened

    # ----------------------------------
    # Normalize
    # ----------------------------------
    def normalize(self, text):

    # Unicode normalization (critical for multilingual)
        text = unicodedata.normalize("NFKC", text)

        # Lowercase
        text = text.lower()

        # Remove punctuation safely
        text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    # ----------------------------------
    # Wordlist detection
    # ----------------------------------
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

    # ----------------------------------
    # Transformer detection
    # ----------------------------------
    def detect_transformer(self, text):

        result = HybridModeration._transformer(text)[0]

        label = result["label"].upper()

        confidence = float(result["score"])

        detected = label in ["HATE", "OFFENSIVE"]

        return {

            "detected": detected,

            "label": label,

            "confidence": confidence
        }

    # ----------------------------------
    # Combine confidence
    # ----------------------------------
    def combine_confidence(
        self,
        wordlist,
        transformer
    ):

        if wordlist["detected"] and transformer["detected"]:

            return round(
                min(
                    1.0,
                    0.7 * transformer["confidence"] + 0.3
                ),
                3
            )

        elif wordlist["detected"]:

            return 1.0

        elif transformer["detected"]:

            return round(transformer["confidence"], 3)

        else:

            return round(1.0 - transformer["confidence"], 3)

    # ----------------------------------
    # Severity
    # ----------------------------------
    def severity(self, confidence):

        if confidence >= 0.85:
            return "high"

        elif confidence >= 0.60:
            return "medium"

        elif confidence >= 0.40:
            return "low"

        else:
            return "none"

    # ----------------------------------
    # Final analyze
    # ----------------------------------
    def analyze(self, text, language):

        wordlist = self.detect_wordlist(text)

        transformer = self.detect_transformer(text)

        confidence = self.combine_confidence(
            wordlist,
            transformer
        )

        severity = self.severity(confidence)

        status = "explicit" if severity != "none" else "clean"

        return {

            "explicit_content": {

                "status": status,

                "severity": severity,

                "confidence": confidence
            },

            "language": language,

            "sources": {

                "wordlist": wordlist,

                "transformer": transformer
            }
        }
