import threading
from transformers import pipeline


class PoliticalModerationAnalyzer:
    """
    Production-ready analyzer for:

    - Political content detection
    - Abusive language detection
    - Degrading language detection

    Multilingual support (100+ languages)
    """

    _classifier = None
    _lock = threading.Lock()

    def __init__(self):

        with PoliticalModerationAnalyzer._lock:

            if PoliticalModerationAnalyzer._classifier is None:

                PoliticalModerationAnalyzer._classifier = pipeline(
                    "zero-shot-classification",
                    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
                    device=-1,  # CPU
                    local_files_only=False
                )

    def analyze(self, text: str):

        candidate_labels = [
            "political content",
            "abusive language",
            "degrading language",
            "neutral content"
        ]

        result = PoliticalModerationAnalyzer._classifier(
            text,
            candidate_labels,
            multi_label=True
        )

        labels = result["labels"]
        scores = result["scores"]

        output = {
            "political": False,
            "abusive": False,
            "degrading": False,
            "confidence": 0.0
        }

        max_conf = 0

        for label, score in zip(labels, scores):

            if label == "political content" and score > 0.60:
                output["political"] = True

            if label == "abusive language" and score > 0.60:
                output["abusive"] = True

            if label == "degrading language" and score > 0.60:
                output["degrading"] = True

            if score > max_conf:
                max_conf = score

        output["confidence"] = round(float(max_conf), 3)

        return output
