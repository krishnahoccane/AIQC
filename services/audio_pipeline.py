import os
import uuid
from fastapi import UploadFile

from services.audio_analysis import AudioAnalyzer
from services.audio_preprocessing import convert_to_standard_wav
from services.nlp_analysis import NLPAnalyzer
from services.moderation import HybridModeration
from services.genre_detection import GenreAnalyzer
from services.political_content import PoliticalModerationAnalyzer
from services.metadata_generator import MetadataGenerator
from services.cover_art_extractor import extract_cover_art
from services.cover_art_analysis import extract_text_from_cover
from services.acr_matcher import ACRYouTubeMatcher
from services.audio_utils import trim_audio_for_acr,build_copyright_status
from utils.logger import logger


UPLOAD_DIR = "uploads"


class AudioPipeline:

    async def process(self, file: UploadFile):

        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Convert
        converted_path = convert_to_standard_wav(file_path)
        acr_input_path = trim_audio_for_acr(converted_path, duration=20)

        # Audio analysis
        analyzer = AudioAnalyzer(converted_path)
        result = analyzer.analyze()

        genre_analyzer = GenreAnalyzer()
        genre_result = genre_analyzer.analyze(converted_path)

        # NLP
        nlp = NLPAnalyzer()
        nlp_result = nlp.analyze(converted_path)

        # Metadata
        metadata_gen = MetadataGenerator()
        metadata = metadata_gen.build_metadata(
            filename=file.filename,
            language=nlp_result["language"],
            transcript=nlp_result["text"]
        )

        # Political moderation
        political_analyzer = PoliticalModerationAnalyzer()
        political_result = political_analyzer.analyze(nlp_result["text"])

        # Explicit moderation
        moderator = HybridModeration()
        moderation_result = moderator.analyze(
            text=nlp_result["text"],
            language=nlp_result["language"]
        )

        flag = moderation_result["moderation_flag"]

        # Cover extraction
        saved_cover_path = None
        advisory_cover_path = None
        cover_text = None

        cover_bytes = extract_cover_art(file_path)

        if cover_bytes:
            cover_filename = f"{uuid.uuid4()}_cover.png"
            saved_cover_path = os.path.join(UPLOAD_DIR, cover_filename)

            with open(saved_cover_path, "wb") as f:
                f.write(cover_bytes)

            cover_text = extract_text_from_cover(cover_bytes)

        # Overlay advisory
        if saved_cover_path and flag.get("explicit") is True and flag.get("advisory_required") is True:
            advisory_cover_path = moderator.overlay_parental_advisory(
                cover_path=saved_cover_path,
                logo_path="assets/parental.png"
            )
            logger.info(f"Advisory cover generated: {advisory_cover_path}")
        else:
            advisory_cover_path = None

        if advisory_cover_path is not None:
            cover_url = "/" + advisory_cover_path.replace("\\", "/")
        else:
            cover_url = None

        # ACR Copyright check
        acr = ACRYouTubeMatcher()
        acr_response = acr.recognize_audio(acr_input_path)

        youtube_match = acr.parse_youtube_match(acr_response)
        spotify_match = acr.parse_spotify_match(acr_response)

        copyright_status = build_copyright_status(
        acr_response,
        youtube_match,
        spotify_match
        )

        return {
            "status": "success",
            "analysis": result,
            "genre": genre_result,
            "metadata": metadata,
            "nlp": nlp_result,
            "Moderation": moderation_result,
            "Political_moderation": political_result,
            "moderation_flag": moderation_result["moderation_flag"],
            "cover_art_analysis": {
                "cover_url": cover_url,
                "ocr_text": cover_text
            },
            "copyright_check": copyright_status
        }