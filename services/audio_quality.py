import librosa
import numpy as np


class AudioQualityAnalyzer:
    """
    Production-ready Audio Quality Scoring

    Computes:
    - Signal-to-Noise Ratio (SNR)
    - Clipping ratio
    - Spectral flatness (distortion proxy)

    Final Output:
    {
        "snr_db": float,
        "clipping_ratio": float,
        "spectral_flatness": float,
        "distortion_detected": bool,
        "quality_score": float,
        "quality_label": str
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
    # Estimate SNR (practical method)
    # ---------------------------------
    def calculate_snr(self, y):

        signal_power = np.mean(y ** 2)

        # Estimate noise using high-frequency emphasis
        noise_estimate = y - librosa.effects.preemphasis(y)
        noise_power = np.mean(noise_estimate ** 2)

        snr = 10 * np.log10(signal_power / (noise_power + 1e-10))

        return round(float(snr), 2)

    # ---------------------------------
    # Clipping Detection
    # ---------------------------------
    def calculate_clipping(self, y):

        clipped_samples = np.sum(np.abs(y) >= 0.99)
        total_samples = len(y)

        clipping_ratio = clipped_samples / total_samples

        return round(float(clipping_ratio), 5)

    # ---------------------------------
    # Spectral Flatness (Distortion proxy)
    # ---------------------------------
    def calculate_spectral_flatness(self, y):

        flatness = librosa.feature.spectral_flatness(y=y)

        return round(float(np.mean(flatness)), 5)

    # ---------------------------------
    # Distortion Flag
    # ---------------------------------
    def detect_distortion(self, clipping_ratio, flatness):

        if clipping_ratio > 0.01:
            return True

        if flatness > 0.5:
            return True

        return False

    # ---------------------------------
    # Quality Score (0–1 normalized)
    # ---------------------------------
    def compute_quality_score(self, snr, clipping_ratio, flatness):

        # Normalize SNR (cap at 50 dB)
        snr_score = min(max(snr / 50, 0), 1)

        # Penalize clipping heavily
        clipping_penalty = min(clipping_ratio * 50, 1)

        # Flatness penalty
        flatness_penalty = min(flatness, 1)

        score = snr_score * 0.6
        score -= clipping_penalty * 0.25
        score -= flatness_penalty * 0.15

        score = max(min(score, 1), 0)

        return round(float(score), 3)

    # ---------------------------------
    # Quality Label
    # ---------------------------------
    def get_quality_label(self, score):

        if score >= 0.85:
            return "excellent"

        elif score >= 0.70:
            return "good"

        elif score >= 0.50:
            return "moderate"

        else:
            return "poor"

    # ---------------------------------
    # Main Analyze Function
    # ---------------------------------
    def analyze(self, file_path):

        y, sr = self.load_audio(file_path)

        snr = self.calculate_snr(y)

        clipping_ratio = self.calculate_clipping(y)

        flatness = self.calculate_spectral_flatness(y)

        distortion_detected = self.detect_distortion(
            clipping_ratio,
            flatness
        )

        quality_score = self.compute_quality_score(
            snr,
            clipping_ratio,
            flatness
        )

        quality_label = self.get_quality_label(quality_score)

        return {
            "snr_db": snr,
            "clipping_ratio": clipping_ratio,
            "spectral_flatness": flatness,
            "distortion_detected": distortion_detected,
            "quality_score": quality_score,
            "quality_label": quality_label
        }