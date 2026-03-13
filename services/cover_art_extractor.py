import logging
from typing import Optional

from mutagen import File
from mutagen.mp4 import MP4Cover

logger = logging.getLogger(__name__)


def extract_cover_art(audio_path: str) -> Optional[bytes]:
    """
    Extract embedded cover art from audio metadata.

    Supports:
    - MP3  (ID3 APIC frame)
    - FLAC (picture blocks)
    - M4A / MP4 (covr atom)
    - OGG / Opus (METADATA_BLOCK_PICTURE via mutagen)
    - Any other format mutagen can open

    Returns
    -------
    Raw image bytes if cover art is found, else None.
    """
    try:
        audio = File(audio_path)

        if audio is None:
            logger.warning("Unsupported or unreadable audio format: %s", audio_path)
            return None

        # ── MP3 (ID3 tags) ────────────────────────────────────────────────────
        if hasattr(audio, "tags") and audio.tags:
            for tag in audio.tags.values():

                # Standard APIC frame (MP3)
                if getattr(tag, "FrameID", None) == "APIC":
                    logger.info("MP3 cover art extracted via APIC frame.")
                    return tag.data

                # Vorbis / FLAC picture objects stored inside tag dict
                if tag.__class__.__name__ == "Picture":
                    logger.info("Embedded Picture frame extracted.")
                    return tag.data

        # ── FLAC (picture blocks) ─────────────────────────────────────────────
        if hasattr(audio, "pictures") and audio.pictures:
            logger.info("FLAC cover art extracted.")
            return audio.pictures[0].data

        # ── M4A / MP4 (covr atom) ─────────────────────────────────────────────
        # Fix: MP4Cover is a bytes subclass — cast explicitly so callers always
        # receive plain bytes and cv2.imdecode / np.frombuffer work correctly.
        if hasattr(audio, "tags") and audio.tags and "covr" in audio.tags:
            cover = audio.tags["covr"][0]
            logger.info("M4A/MP4 cover art extracted.")
            return bytes(cover)          # MP4Cover → plain bytes

        logger.info("No embedded cover art found in: %s", audio_path)
        return None

    except Exception:
        logger.exception("Cover art extraction failed for: %s", audio_path)
        return None