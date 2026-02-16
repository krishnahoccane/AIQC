import threading
from faster_whisper import WhisperModel
from transformers import pipeline


import threading
from faster_whisper import WhisperModel


class NLPAnalyzer:
    """
    Production-Level Multilingual STT
    (Segment-level timestamps only)
    """

    _whisper_model = None
    _lock = threading.Lock()

    def __init__(self, model_size: str = "medium"):
        """
        model_size options:
        tiny | base | small | medium 
        """

        with NLPAnalyzer._lock:

            if NLPAnalyzer._whisper_model is None:
                print("Loading Whisper model...")
                NLPAnalyzer._whisper_model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8"
                )
                print("Whisper loaded successfully.")

    # -------------------------------------------------
    # Multilingual Speech-to-Text (Segment Level)
    # -------------------------------------------------
    def transcribe(self, file_path: str):

        segments, info = NLPAnalyzer._whisper_model.transcribe(
            file_path,
            task="transcribe",   # keep original language
            language=None,       # auto-detect
            beam_size=5
        )

        transcript_segments = []
        full_text = ""

        for segment in segments:
            segment_text = segment.text.strip()

            transcript_segments.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment_text
            })

            full_text += segment_text + " "

        return {
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
            "text": full_text.strip(),
            "segments": transcript_segments
        }

    # -------------------------------------------------
    # Full NLP Pipeline
    # -------------------------------------------------
    def analyze(self, file_path: str):
        return self.transcribe(file_path)
