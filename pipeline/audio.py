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
    """
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as inp:
        inp.write(mp4_bytes)
        inp_path = inp.name

    out_path = inp_path.replace(".mp4", ".mp3")

    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", inp_path,
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-b:a", _BITRATE,
                out_path,
            ],
            capture_output=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed (exit {result.returncode}):\n"
                + result.stderr.decode(errors="replace")
            )

        logger.info("ffmpeg extracted audio: %s -> %s", inp_path, out_path)

        with open(out_path, "rb") as f:
            return f.read()

    finally:
        os.unlink(inp_path)
        if os.path.exists(out_path):
            os.unlink(out_path)
