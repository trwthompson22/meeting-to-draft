"""
Transcription: send a compressed mp3 to Groq's Whisper endpoint.

Required environment variables:
    GROQ_API_KEY - Groq API key
"""

import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)

_MODEL = "whisper-large-v3"


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
        RuntimeError: If the GROQ_API_KEY env var is missing.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set")

    client = Groq(api_key=api_key)

    transcription = client.audio.transcriptions.create(
        model=_MODEL,
        file=(filename, mp3_bytes, "audio/mpeg"),
        response_format="text",
    )

    logger.info("Transcribed %d bytes via Groq Whisper", len(mp3_bytes))
    return transcription
