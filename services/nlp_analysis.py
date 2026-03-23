import threading
from faster_whisper import WhisperModel
from services.political_content import PoliticalModerationAnalyzer
import torch
import os


class NLPAnalyzer:

    _whisper_model = None
    _political_moderator = None
    _lock = threading.Lock()

    def __init__(self):

        with NLPAnalyzer._lock:

            if NLPAnalyzer._whisper_model is None:

                model_name = "large-v3"

                if torch.cuda.is_available():
                    NLPAnalyzer._whisper_model = WhisperModel(
                        model_name,
                        device="cuda",
                        compute_type="float16"
                    )
                else:
                    NLPAnalyzer._whisper_model = WhisperModel(
                        model_name,
                        device="cpu",
                        compute_type="int8"
                    )

            if NLPAnalyzer._political_moderator is None:
                NLPAnalyzer._political_moderator = PoliticalModerationAnalyzer()

    # -------------------------------------------------
    # MAXIMUM-RECALL TRANSCRIPTION 
    # -------------------------------------------------

    def transcribe(self, file_path: str):

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        segments, info = NLPAnalyzer._whisper_model.transcribe(
            file_path,
            task="transcribe",
            language=None,                      # Auto detect
            beam_size=8,                        # Wider search
            best_of=8,
            temperature=0,
            condition_on_previous_text=True,    # Preserve context
            vad_filter=False,                   # 🔥 Disable VAD to avoid missing speech
            no_speech_threshold=1.0,            # Never auto-skip
            log_prob_threshold=-2.0,            # Accept low confidence text
            compression_ratio_threshold=3.0     # Avoid hallucination cutoff
        )

        transcript_segments = []
        full_text_parts = []

        for segment in segments:

            text = segment.text.strip()

            # NEVER discard text unless completely empty
            if text == "":
                continue

            transcript_segments.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text
                #"avg_logprob": round(segment.avg_logprob, 3),
                #"no_speech_prob": round(segment.no_speech_prob, 3)
            })

            full_text_parts.append(text)

        full_text = " ".join(full_text_parts).strip()

        return {
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
            "text": full_text,
            "segments": transcript_segments
        }

    # -------------------------------------------------
    # FULL PIPELINE
    # -------------------------------------------------

    def analyze(self, file_path: str):

        transcription = self.transcribe(file_path)

        return {
            "language": transcription["language"],
            "language_probability": transcription["language_probability"],
            "duration": transcription["duration"],
            "text": transcription["text"],
            "segments": transcription["segments"]
        }