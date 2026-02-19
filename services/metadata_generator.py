import re
import threading
import spacy
from collections import Counter


class MetadataGenerator:

    _nlp = None
    _lock = threading.Lock()

    def __init__(self):

        with MetadataGenerator._lock:
            if MetadataGenerator._nlp is None:
                MetadataGenerator._nlp = spacy.blank("xx")

    # ------------------------------
    # Clean Filename → Title
    # ------------------------------
    def generate_title(self, filename: str, transcript: str):

        name = filename.rsplit(".", 1)[0]

        # Remove UUID-like patterns
        if len(name) > 20 and "-" in name:
            return self.infer_title_from_content(transcript)

        # Clean underscores and numbers
        name = re.sub(r"[_\-]+", " ", name)
        name = re.sub(r"\d+", "", name)

        cleaned = name.strip().title()

        if len(cleaned) < 4:
            return self.infer_title_from_content(transcript)

        return cleaned

    # ------------------------------
    # Infer title from transcript
    # ------------------------------
    def infer_title_from_content(self, transcript: str):

        words = transcript.split()

        if not words:
            return "Unknown Title"

        # Use first meaningful 5 words
        title = " ".join(words[:5])
        return title.title()

    # ------------------------------
    # Generate Tags 
    # ------------------------------
    def generate_tags(self, transcript: str, max_tags: int = 8):

        if not transcript:
            return [] 

        doc = MetadataGenerator._nlp(transcript.lower())

        tokens = [
            token.text
            for token in doc
            if token.is_alpha and len(token.text) > 3
        ]

        freq = Counter(tokens)

        most_common = freq.most_common(max_tags)

        tags = [word for word, _ in most_common]

        return tags

    # ------------------------------
    # Main Metadata Builder
    # ------------------------------
    def build_metadata(self, filename, language, transcript):

        title = self.generate_title(filename, transcript)
        tags = self.generate_tags(transcript)

        return {
            "title": title,
            "language": language,
            "tags": tags
        }
