import os
from pydub import AudioSegment, silence
from datetime import datetime

# Input and log folders
INPUT_FOLDER = "input_songs"
LOG_FOLDER = "error_logs"
os.makedirs(LOG_FOLDER, exist_ok=True)

def detect_blank_spaces(file_path, silence_thresh=-50, min_silence_len=3000):
    """
    Detects blank spaces (silences) in an audio file.
    
    :param file_path: Path to the audio file
    :param silence_thresh: Silence threshold in dBFS (default: -50)
    :param min_silence_len: Minimum silence length in ms (default: 3000 ms = 3s)
    :return: List of (start_time, end_time) in seconds
    """
    audio = AudioSegment.from_file(file_path)

    # Detect silent chunks
    silent_chunks = silence.detect_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh
    )

    # Convert ms ’ seconds
    return [(start / 1000, end / 1000) for start, end in silent_chunks]


def process_files():
    for filename in os.listdir(INPUT_FOLDER):
        if filename.lower().endswith((".mp3", ".wav")):
            file_path = os.path.join(INPUT_FOLDER, filename)
            log_file = os.path.join(LOG_FOLDER, f"{os.path.splitext(filename)[0]}_log.txt")

            try:
                silent_parts = detect_blank_spaces(file_path)

                with open(log_file, "w") as f:
                    f.write(f"=== Silence Report for {filename} ===\n")
                    f.write(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    if silent_parts:
                        f.write(f"Detected silence > 3 sec in {filename}:\n")
                        for start, end in silent_parts:
                            f.write(f" - Silence from {start:.2f}s to {end:.2f}s\n")
                        f.write("\n  Error: Long silence detected!\n")
                    else:
                        f.write(" No long silences detected.\n")

                print(f"Processed {filename}. Log saved to {log_file}")

            except Exception as e:
                with open(log_file, "w") as f:
                    f.write(f"L Failed to process {filename}\nError: {str(e)}\n")
                print(f"Error processing {filename}. Check {log_file}")


if __name__ == "__main__":
    process_files()
