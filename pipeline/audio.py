"""
Audio extraction: convert a raw mp4 recording to a compressed mp3 for Whisper.

ffmpeg is expected to be on PATH (included in the Azure Function app bundle
or installed as a custom layer).
"""

import os
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

# Groq Whisper enforces a 25 MB upload limit; 64k bitrate keeps a 60-min
# meeting well under that ceiling.
_BITRATE = "64k"


def extract_audio(mp4_bytes: bytes) -> bytes:
    """
    Convert raw mp4 bytes to mp3 bytes using ffmpeg.

    Args:
        mp4_bytes: Raw bytes of the input video file.

    Returns:
        Raw bytes of the compressed mp3 output.

    Raises:
        RuntimeError: If ffmpeg exits with a non-zero status.
        NotImplementedError: Placeholder — replace body with real impl.
    """
    raise NotImplementedError("audio.extract_audio is not yet implemented")
