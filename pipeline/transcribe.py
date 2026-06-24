"""
Transcription: send a compressed mp3 to Groq's Whisper endpoint.

Required environment variables:
    GROQ_API_KEY - Groq API key
"""

import os
import logging

logger = logging.getLogger(__name__)


def transcribe(mp3_bytes: bytes, filename: str = "recording.mp3") -> str:
    """
    Transcribe audio bytes using Groq's Whisper API.

    Args:
        mp3_bytes: Raw bytes of the mp3 file to transcribe.
        filename:  Filename sent in the multipart upload (Groq uses the
                   extension to infer the audio format).

    Returns:
        Full transcript as a plain-text string.

    Raises:
        NotImplementedError: Placeholder — replace body with real impl.
    """
    raise NotImplementedError("transcribe.transcribe is not yet implemented")
