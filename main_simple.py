from faster_whisper import WhisperModel

# Load Whisper model (small model for faster testing)
model = WhisperModel("small", device="cpu")

# Fixed audio file name
AUDIO_FILE = "audio.wav"

# Transcribe audio
segments, info = model.transcribe(AUDIO_FILE, beam_size=5)
text = " ".join([segment.text for segment in segments])

print("\n--- Transcription Output ---")
print(text)

# Simple check for political keywords
political_keywords = [
    "election", "vote", "government", "politics", "minister",
    "party", "parliament", "bjp", "congress", "trump", "biden",
    "modi", "rahul", "political", "campaign", "senate", "democracy"
]

if any(word.lower() in text.lower() for word in political_keywords):
    print("\n  Political content detected")
else:
    print("\n No political content detected")
