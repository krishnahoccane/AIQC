import threading
import torch
from transformers import pipeline


class GenreAnalyzer:
    """
    Production-ready Genre Analyzer

    Features:
    - Detects audio type (music vs speech)
    - Runs genre detection only if music
    - Thread-safe singleton model loading
    - CPU/GPU auto-detection
    - Fast inference after first load
    """

    _audio_classifier = None
    _genre_classifier = None
    _lock = threading.Lock()

    def __init__(self):

        with GenreAnalyzer._lock:

            device = 0 if torch.cuda.is_available() else -1

            # ----------------------------
            # Audio Type Classifier
            # ----------------------------
            if GenreAnalyzer._audio_classifier is None:

                print("Loading audio type classifier...")

                GenreAnalyzer._audio_classifier = pipeline(
                    task="audio-classification",
                    model="MIT/ast-finetuned-audioset-10-10-0.4593",
                    device=device
                )

                print("Audio type classifier loaded.")


            # ----------------------------
            # Genre Classifier
            # ----------------------------
            if GenreAnalyzer._genre_classifier is None:

                print("Loading genre classifier...")

                GenreAnalyzer._genre_classifier = pipeline(
                    task="audio-classification",
                    model="dima806/music_genres_classification",
                    device=device
                )

                print("Genre classifier loaded.")


    # ----------------------------------------
    # Detect audio type
    # ----------------------------------------
    def detect_audio_type(self, file_path: str):

        result = GenreAnalyzer._audio_classifier(file_path)[0]

        label = result["label"].lower()
        confidence = float(result["score"])

        # Normalize label
        if "music" in label or "singing" in label:
            audio_type = "music"

        elif "speech" in label or "conversation" in label:
            audio_type = "speech"

        else:
            audio_type = "unknown"

        return {
            "type": audio_type,
            "confidence": round(confidence, 3),
            "raw_label": label
        }


    # ----------------------------------------
    # Detect genre (only for music)
    # ----------------------------------------
    def detect_genre(self, file_path: str):

        result = GenreAnalyzer._genre_classifier(file_path)[0]

        return {
            "genre": result["label"],
            "confidence": round(float(result["score"]), 3)
        }


    # ----------------------------------------
    # Full analysis pipeline
    # ----------------------------------------
    def analyze(self, file_path: str):

        audio_type_result = self.detect_audio_type(file_path)

        if audio_type_result["type"] != "music":

            return {
                "audio_type": audio_type_result,
                "genre": None
            }

        genre_result = self.detect_genre(file_path)

        return {
            "audio_type": audio_type_result,
            "genre": genre_result
        }

