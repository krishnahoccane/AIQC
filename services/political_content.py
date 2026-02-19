import threading
from transformers import pipeline


class PoliticalModerationAnalyzer:
    """
    Production-ready multilingual moderation analyzer

    Strict Rules:
    - political = True only if confidence >= 0.80
    - hate_speech = True only if confidence >= 0.80

    Returns:
    {
        "political": {
            "detected": bool,
            "confidence": float
        },
        "hate_speech": {
            "detected": bool,
            "confidence": float
        }
    }
    """

    _political_classifier = None
    _hate_classifier = None
    _lock = threading.Lock()

    THRESHOLD = 0.80  # Hardcoded threshold

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

        detected = (
            label == "political content"
            and confidence >= self.THRESHOLD
        )

        return {
            "detected": detected,
            "confidence": round(confidence, 3)
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

        detected = (
            raw_label in hate_labels
            and confidence >= self.THRESHOLD
        )

        return {
            "detected": detected,
            "confidence": round(confidence, 3)
        }

    # -----------------------------
    # Final analysis
    # -----------------------------
    def analyze(self, text):

        political_result = self.detect_political(text)
        hate_result = self.detect_hate(text)

        return {
            "political": political_result,
            "hate_speech": hate_result
        }
