"""
Meeting analysis: extract a structured summary from a transcript.

Required environment variables:
    MODEL_PROVIDER    - "anthropic" (default) or "openai"
    ANTHROPIC_API_KEY - required when MODEL_PROVIDER=anthropic
    OPENAI_API_KEY    - required when MODEL_PROVIDER=openai
    OPENAI_MODEL      - OpenAI model to use (default: gpt-4o)
    ANTHROPIC_MODEL   - Anthropic model to use (default: claude-sonnet-4-6)
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

_SYSTEM = """\
You are an executive assistant. Given a raw meeting transcript, extract the
following and return ONLY valid JSON — no markdown, no extra prose:

{
  "subject": "<concise email subject line, ≤ 60 chars>",
  "summary": "<1-2 sentence high-level summary of the meeting>",
  "key_takeaways": [
    "<key takeaway>",
    "<key takeaway>",
    "<key takeaway>",
    "<key takeaway>",
    "<key takeaway>"
  ],
  "action_items": [
    {"description": "<what needs to be done>", "owner": "<person name or role>", "deadline": "<YYYY-MM-DD or null>"}
  ]
}

Provide 5-7 key takeaways as concise bullet strings.
If a field cannot be determined from the transcript use null."""


def _analyze_anthropic(transcript: str) -> dict:
    import anthropic

    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=[{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"Transcript:\n\n{transcript}"}],
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()
    return json.loads(raw)


def _analyze_openai(transcript: str) -> dict:
    import openai

    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"Transcript:\n\n{transcript}"},
        ],
    )
    return json.loads(response.choices[0].message.content.strip())


def analyze_transcript(transcript: str) -> dict:
    """
    Send a meeting transcript to an LLM and return a structured dict.

    Returns a dict with keys: subject, summary, action_items.
    Provider is controlled by the MODEL_PROVIDER environment variable.
    """
    provider = os.environ.get("MODEL_PROVIDER", "anthropic").lower()

    if provider == "openai":
        result = _analyze_openai(transcript)
    elif provider == "anthropic":
        result = _analyze_anthropic(transcript)
    else:
        raise ValueError(f"Unknown MODEL_PROVIDER '{provider}'. Must be 'anthropic' or 'openai'.")

    logger.debug("Analysis result from %s: %s", provider, result)
    return result
