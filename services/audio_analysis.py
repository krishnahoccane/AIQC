import subprocess
import json
import librosa
import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from pydub import AudioSegment
from pydub.silence import detect_silence
import os


class AudioAnalyzer:

    def __init__(self, file_path: str):
        self.file_path = os.path.abspath(file_path)
        self.y = None
        self.sr = None

    # ---------------------------
    # Load Audio
    # ---------------------------

    def load_audio(self):
        self.y, self.sr = librosa.load(self.file_path, sr=None)

    # ---------------------------
    # Basic Technical Checks
    # ---------------------------

    def get_duration(self):
        return float(librosa.get_duration(y=self.y, sr=self.sr))

    def get_sample_rate(self):
        return int(self.sr)

    def get_channels(self):
        with sf.SoundFile(self.file_path) as f:
            return f.channels

    def get_bitrate(self):
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=bit_rate",
            "-of", "json",
            self.file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        output = json.loads(result.stdout)
        bitrate = output["streams"][0].get("bit_rate", None)
        return int(bitrate) if bitrate else None

    def validate_pcm_format(self):
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "json",
            self.file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        output = json.loads(result.stdout)
        codec = output["streams"][0].get("codec_name", "")
        return codec == "pcm_s16le"

    # ---------------------------
    # Loudness
    # ---------------------------

    def get_lufs(self):
        meter = pyln.Meter(self.sr)
        loudness = meter.integrated_loudness(self.y)
        return float(loudness)

    # ---------------------------
    # Silence Detection
    # ---------------------------

    def get_silence_segments(self, silence_thresh=-50, min_silence_len=2000):
        audio = AudioSegment.from_file(self.file_path)
        silence = detect_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh
        )
        return [(start / 1000, end / 1000) for start, end in silence]

    # ---------------------------
    # Tempo (BPM)
    # ---------------------------

    def get_bpm(self):
        tempo, _ = librosa.beat.beat_track(y=self.y, sr=self.sr)
        return float(tempo)

    # ---------------------------
    # Key Detection (Librosa)
    # ---------------------------

    def get_key_detection(self):
        chroma = librosa.feature.chroma_cqt(y=self.y, sr=self.sr)
        chroma_mean = np.mean(chroma, axis=1)

        keys = ['C', 'C#', 'D', 'D#', 'E', 'F',
                'F#', 'G', 'G#', 'A', 'A#', 'B']

        key_index = np.argmax(chroma_mean)
        key = keys[key_index]

        confidence = float(np.max(chroma_mean) / np.sum(chroma_mean))

        return {
            "key": key,
            "confidence": confidence
        }

    # ---------------------------
    # Full Analysis Pipeline
    # ---------------------------

    def analyze(self):
        self.load_audio()

        technical_data = {
            "duration_seconds": self.get_duration(),
            "sample_rate": self.get_sample_rate(),
            "channels": self.get_channels(),
            "bitrate": self.get_bitrate(),
            "pcm_valid": self.validate_pcm_format()
        }

        loudness_data = {
            "lufs": self.get_lufs()
        }

        silence_data = {
            "segments": self.get_silence_segments()
        }

        musical_data = {
            "bpm": self.get_bpm(),
            "key_detection": self.get_key_detection()
        }

        return {
            "technical": technical_data,
            "loudness": loudness_data,
            "silence": silence_data,
            "musical": musical_data
        }
