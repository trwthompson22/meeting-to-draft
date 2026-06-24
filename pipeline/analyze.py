"""
Meeting analysis: extract a structured summary from a transcript using Claude.

Required environment variables:
    ANTHROPIC_API_KEY - Anthropic API key
"""

import json
import logging
import anthropic

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"

_SYSTEM = """\
You are an executive assistant. Given a raw meeting transcript, extract the
following and return ONLY valid JSON — no markdown, no extra prose:

{
  "subject": "<concise email subject line, ≤ 60 chars>",
  "summary": "<2-4 sentence meeting summary>",
  "action_items": [
    {"description": "<what needs to be done>", "owner": "<person name or role>", "deadline": "<YYYY-MM-DD or null>"}
  ]
}

If a field cannot be determined from the transcript use null."""


def analyze_transcript(transcript: str) -> dict:
    """
    Send a meeting transcript to Claude and return a structured dict.

    Returns a dict with keys: subject, summary, action_items.

    Raises:
        anthropic.APIError: On API failures.
        json.JSONDecodeError: If Claude returns non-JSON output.
    """
    client = anthropic.Anthropic()

    message = client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        system=_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": f"Transcript:\n\n{transcript}",
            }
        ],
    )

    raw = message.content[0].text.strip()
    logger.debug("Claude raw response: %s", raw)

    result = json.loads(raw)
    return result
