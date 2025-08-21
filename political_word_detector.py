import os
from faster_whisper import WhisperModel

# Folders
input_folder = "input_songs"
log_folder = "error_logs"
os.makedirs(log_folder, exist_ok=True)

# Political keyword list
political_keywords = [
    "election", "vote", "president", "prime minister",
    "government", "bjp", "congress", "modi",
    "biden", "trump", "minister", "parliament"
]

# Load Whisper model (medium size for better accuracy)
model = WhisperModel("medium", device="cpu")  # use "cuda" if you have GPU

def detect_political_words(file_path):
    segments, _ = model.transcribe(file_path)
    transcript = " ".join(segment.text.lower() for segment in segments)
    
    detected = [word for word in political_keywords if word in transcript]
    return transcript, detected

# Process each song
for filename in os.listdir(input_folder):
    if filename.endswith((".mp3", ".wav")):
        file_path = os.path.join(input_folder, filename)
        transcript, detected_words = detect_political_words(file_path)

        log_file = os.path.join(log_folder, f"{os.path.splitext(filename)[0]}_politics_log.txt")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Transcript for {filename}:\n{transcript}\n\n")
            if detected_words:
                f.write(f"  Political words detected: {', '.join(detected_words)}\n")
            else:
                f.write(" No political words detected.\n")

        print(f"Processed {filename}, log saved to {log_file}")
