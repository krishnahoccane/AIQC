import librosa
import soundfile as sf
import os

def trim_audio_for_acr(input_path, duration=20):
    """
    Trim first N seconds for ACR recognition
    """
    y, sr = librosa.load(input_path, sr=None)

    trimmed = y[: sr * duration]

    base, ext = os.path.splitext(input_path)
    trimmed_path = f"{base}_acr_trim.wav"

    sf.write(trimmed_path, trimmed, sr)

    return trimmed_path

def build_copyright_status(acr_response, youtube_match, spotify_match):

    music_metadata = acr_response.get("metadata", {}).get("music", [])

    if music_metadata:
        acr_score = music_metadata[0].get("score", 0)
        fingerprint_detected = True
    else:
        acr_score = 0
        fingerprint_detected = False

    confidence_score = acr_score / 100

    if confidence_score > 0.75:
        confidence_level = "high"
    elif confidence_score >= 0.40:
        confidence_level = "moderate"
    else:
        confidence_level = "low"

    detected = fingerprint_detected

    return {
        "detected": detected,
        "confidence_score": round(confidence_score, 2),
        "confidence_level": confidence_level,
        "source": {
            "type": "fingerprint",
            "acr_youtube_match": youtube_match,
            "acr_spotify_match": spotify_match
        }
    }