import threading
from transformers import pipeline


class PoliticalModerationAnalyzer:
    """
    Production-ready multilingual moderation analyzer

    Strict Rules:
    - political = True only if confidence >= 0.80
    - hate_speech = True only if confidence >= 0.80
    - If detected == False → do NOT return confidence

    Returns:
    {
        "political": {
            "detected": bool,
            "confidence": float (only if detected=True)
        },
        "hate_speech": {
            "detected": bool,
            "confidence": float (only if detected=True)
        }
    }
    """

    _political_classifier = None
    _hate_classifier = None
    _lock = threading.Lock()

    THRESHOLD = 0.80

    def __init__(self):

        with PoliticalModerationAnalyzer._lock:

            if PoliticalModerationAnalyzer._political_classifier is None:
                PoliticalModerationAnalyzer._political_classifier = pipeline(
                    task="zero-shot-classification",
                    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
                    device=-1
                )

            if PoliticalModerationAnalyzer._hate_classifier is None:
                PoliticalModerationAnalyzer._hate_classifier = pipeline(
                    task="text-classification",
                    model="unitary/multilingual-toxic-xlm-roberta",
                    truncation=True,
                    device=-1
                )

    # -----------------------------
    # Political detection
    # -----------------------------
    def detect_political(self, text):

        result = PoliticalModerationAnalyzer._political_classifier(
            text,
            candidate_labels=[
                "political content",
                "non-political content"
            ]
        )

        label = result["labels"][0]
        confidence = float(result["scores"][0])

        if label == "political content" and confidence >= self.THRESHOLD:
            return {
                "detected": True,
                "confidence": round(confidence, 3)
            }

        return {
            "detected": False
        }

    # -----------------------------
    # Hate speech detection
    # -----------------------------
    def detect_hate(self, text):

        result = PoliticalModerationAnalyzer._hate_classifier(text)[0]

        raw_label = result["label"].upper()
        confidence = float(result["score"])

        hate_labels = {
            "TOXIC",
            "HATE",
            "OFFENSIVE",
            "INSULT",
            "IDENTITY_HATE"
        }

        if raw_label in hate_labels and confidence >= self.THRESHOLD:
            return {
                "detected": True,
                "confidence": round(confidence, 3)
            }

        return {
            "detected": False
        }

    # -----------------------------
    # Final analysis
    # -----------------------------
    def analyze(self, text):

        return {
            "political": self.detect_political(text),
            "hate_speech": self.detect_hate(text)
        }