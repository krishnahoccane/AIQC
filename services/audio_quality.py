import librosa
import numpy as np
from pydub import AudioSegment
from pydub.silence import detect_silence


class AudioQualityAnalyzer:
    """
    Production Audio Quality Scoring (Simplified & Professional)

    Metrics Used:
    - SNR (silence-based estimation)
    - Hard distortion detection (clipping)

    Final Output:
    {
        "snr_db": float,
        "distortion_detected": bool,
        "quality_score": float
    }
    """

    def __init__(self):
        pass

    # ---------------------------------
    # Load Audio
    # ---------------------------------
    def load_audio(self, file_path):
        y, sr = librosa.load(file_path, sr=None, mono=True)
        return y, sr

    # ---------------------------------
    # Silence-Based SNR
    # ---------------------------------
    def calculate_snr(self, file_path, y, sr):

        try:
            audio = AudioSegment.from_file(file_path)

            silence_ranges = detect_silence(
                audio,
                min_silence_len=1000,
                silence_thresh=-40
            )

            if silence_ranges:
                noise_samples = []

                for start_ms, end_ms in silence_ranges:
                    start = int(start_ms / 1000 * sr)
                    end = int(end_ms / 1000 * sr)
                    noise_samples.extend(y[start:end])

                noise_samples = np.array(noise_samples)

                if len(noise_samples) > 0:
                    signal_power = np.mean(y ** 2)
                    noise_power = np.mean(noise_samples ** 2)

                    snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
                    return round(float(snr), 2)

            return self.fallback_snr(y)

        except Exception:
            return self.fallback_snr(y)

    # ---------------------------------
    # Fallback SNR (Energy Percentile)
    # ---------------------------------
    def fallback_snr(self, y):

        rms = librosa.feature.rms(y=y)[0]

        noise_floor = np.percentile(rms, 5)

        signal_power = np.mean(y ** 2)
        noise_power = noise_floor ** 2

        snr = 10 * np.log10(signal_power / (noise_power + 1e-10))

        return round(float(snr), 2)

    # ---------------------------------
    # Distortion Detection (Hard Clipping)
    # ---------------------------------
    def detect_distortion(self, y):

        clipped_samples = np.sum(np.abs(y) >= 0.99)
        total_samples = len(y)

        clipping_ratio = clipped_samples / total_samples

        # Threshold: 1% clipping is considered distortion
        return clipping_ratio > 0.01

    # ---------------------------------
    # Quality Score (SNR + Distortion)
    # ---------------------------------
    def compute_quality_score(self, snr, distortion_detected):

        # Normalize SNR (cap at 50 dB)
        snr_score = min(max(snr / 50, 0), 1)

        distortion_penalty = 0.2 if distortion_detected else 0

        score = snr_score * 0.8
        score -= distortion_penalty

        score = max(min(score, 1), 0)

        return round(float(score), 3)

    # ---------------------------------
    # Main Analyze
    # ---------------------------------
    def analyze(self, file_path):

        y, sr = self.load_audio(file_path)

        snr = self.calculate_snr(file_path, y, sr)

        distortion_detected = self.detect_distortion(y)

        quality_score = self.compute_quality_score(
            snr,
            distortion_detected
        )

        return {
            "snr_db": snr,
            "distortion_detected": distortion_detected,
            "quality_score": quality_score
        }
       