import re
import threading
import unicodedata
from typing import Optional

import spacy
from transformers import pipeline
from PIL import Image

from services.profanity_lists import PROFANITY_WORDS
import os


class HybridModeration:

    _nlp = None
    _transformer = None
    _profanity_set = None
    _lock = threading.Lock()

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
                for words in PROFANITY_WORDS.values():
                    for w in words:
                        flattened.add(w.lower())
                HybridModeration._profanity_set = flattened

    def normalize(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def detect_wordlist(self, text: str):

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

    # STEP-2: Lower transformer threshold
    def detect_transformer(self, text: str):

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

        # CHANGED 0.80 → 0.65
        if confidence >= 0.65 and mapped_label in ["hate", "abusive", "explicit"]:
            return {
                "detected": True,
                "label": mapped_label,
                "confidence": round(confidence, 3)
            }

        return {
            "detected": False,
            "label": "clean",
            "confidence": round(confidence, 3)
        }

    def combine_confidence(self, wordlist, transformer, text):

        if not wordlist["detected"] and not transformer["detected"]:
            return 0.0

        if wordlist["detected"] and transformer["detected"]:
            score = min(1.0, 0.7 * transformer["confidence"] + 0.3)

        elif wordlist["detected"]:
            score = 0.55

        elif transformer["detected"]:
            score = transformer["confidence"]

        else:
            score = 0.0

        # STEP-3: STT hallucination guard
        if wordlist["count"] == 1 and transformer["confidence"] < 0.6:
            score *= 0.4

        # STEP-4: repetition boost
        if wordlist["count"] >= 5:
            score += 0.2

        # STEP-6: profanity density normalization
        density = wordlist["count"] / max(1, len(text.split()))
        score *= min(1.2, density * 10)

        return round(min(1.0, score), 3)

    def analyze(self, text: str, language: str):

        wordlist = self.detect_wordlist(text)
        transformer = self.detect_transformer(text)

        toxicity_score = self.combine_confidence(wordlist, transformer, text)

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

        explicit_flag = status in ["explicit", "moderate"]

        return {
            "moderation_flag": {
                "explicit": explicit_flag,
                "advisory_required": explicit_flag,
                "status": status,
                "severity": severity,
                "confidence": round(toxicity_score, 3)
            },
            "language": language,
            "sources": {
                "wordlist": wordlist,
                "context_explicit": transformer
            }
        }

    def overlay_parental_advisory(
        self,
        cover_path: str,
        logo_path: str,
        output_path: Optional[str] = None
    ) -> str:

        base = Image.open(cover_path).convert("RGBA")
        logo = Image.open(logo_path).convert("RGBA")

        logo_size = int(base.width * 0.22)
        logo = logo.resize((logo_size, logo_size))

        position = (
            base.width - logo.width - 30,
            base.height - logo.height - 30
        )

        base.paste(logo, position, logo)

        if output_path is None:
            base_name, ext = os.path.splitext(cover_path)
            output_path = f"{base_name}_advisory.png"

        base.convert("RGB").save(output_path)

        return output_path