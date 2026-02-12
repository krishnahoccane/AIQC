import subprocess
import os

def convert_to_standard_wav(input_path: str) -> str:
    """
    Converts audio to 16-bit 44.1kHz WAV format.
    Returns path to converted file.
    """

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ar", "44100",
        "-ac", "2",
        "-sample_fmt", "s16",
        output_path
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_path
