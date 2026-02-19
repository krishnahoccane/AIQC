import threading
from faster_whisper import WhisperModel
from services.political_content import PoliticalModerationAnalyzer
import torch
from services.genre_detection import GenreAnalyzer



class NLPAnalyzer:

    _whisper_model = None
    _political_moderator = None
    _lock = threading.Lock()

    def __init__(self):

        with NLPAnalyzer._lock:

            # Load Whisper once
            if NLPAnalyzer._whisper_model is None:

                if torch.cuda.is_available():
                    NLPAnalyzer._whisper_model = WhisperModel(
                        "large-v3",
                        device="cuda",
                        compute_type="float16"
                    )
                else:
                    NLPAnalyzer._whisper_model = WhisperModel(
                        "turbo",
                        device="cpu",
                        compute_type="int8"
                    )

            # Load political moderation once
            if NLPAnalyzer._political_moderator is None:
                NLPAnalyzer._political_moderator = PoliticalModerationAnalyzer()


    # -------------------------------------------------
    # Transcription
    # -------------------------------------------------

    def transcribe(self, file_path: str):

        segments, info = NLPAnalyzer._whisper_model.transcribe(
            file_path,
            task="transcribe",
            language=None,
            beam_size=5,
            best_of=3,
            temperature=0,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 800,   # More stable for music
                "speech_pad_ms": 300              # Prevent clipping words
            }
        )

        transcript_segments = []
        full_text = ""

        for segment in segments:

            text = segment.text.strip()

            if not text:
                continue

            transcript_segments.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text
            })

            full_text += text + " "

        return {
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
            "text": full_text.strip(),
            "segments": transcript_segments
        }

    # -------------------------------------------------
    # Full NLP Pipeline (UPDATED)
    # -------------------------------------------------

    def analyze(self, file_path: str):

        transcription = self.transcribe(file_path)
        #political_analyzer = PoliticalModerationAnalyzer()

        #political_result =  political_analyzer.analyze(
           # transcription["text"]
        #)

        return {
            "language": transcription["language"],
            "language_probability": transcription["language_probability"],
            "duration": transcription["duration"],
            "text": transcription["text"],
            "segments": transcription["segments"],
            #"political_moderation": political_result
        }
