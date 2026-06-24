"""
Azure Function HTTP trigger — entry point for the meeting-to-draft pipeline.

Power Automate calls this endpoint with a JSON body:
{
    "file_id":         "<OneDrive item ID of the .mp4 recording>",
    "drive_id":        "<optional drive ID>",
    "conversation_id": "<optional Graph conversation ID for reply threading>",
    "to_recipients":   ["<email>", ...],
    "cc_recipients":   ["<email>", ...]   // optional
}
"""

import json
import logging

import azure.functions as func

from pipeline import graph, audio, transcribe, analyze, email

logger = logging.getLogger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="process-recording", methods=["POST"])
def process_recording(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse("Request body must be valid JSON.", status_code=400)

    file_id = body.get("file_id")
    if not file_id:
        return func.HttpResponse("Missing required field: file_id", status_code=400)

    drive_id = body.get("drive_id")
    conversation_id = body.get("conversation_id")
    to_recipients = body.get("to_recipients", [])
    cc_recipients = body.get("cc_recipients")

    if not to_recipients:
        return func.HttpResponse("Missing required field: to_recipients", status_code=400)

    try:
        logger.info("Step 1/5 — downloading recording %s", file_id)
        mp4_bytes = graph.download_recording(file_id, drive_id=drive_id)

        logger.info("Step 2/5 — extracting audio")
        mp3_bytes = audio.extract_audio(mp4_bytes)

        logger.info("Step 3/5 — transcribing audio")
        transcript = transcribe.transcribe(mp3_bytes)

        logger.info("Step 4/5 — analysing transcript")
        analysis = analyze.analyze_transcript(transcript)

        logger.info("Step 5/5 — creating Outlook draft")
        body_html = email.render_body(
            summary=analysis["summary"],
            action_items=analysis.get("action_items", []),
        )
        draft_id = graph.create_draft(
            subject=analysis["subject"],
            body_html=body_html,
            to_recipients=to_recipients,
            cc_recipients=cc_recipients,
            conversation_id=conversation_id,
        )

        return func.HttpResponse(
            json.dumps({"draft_id": draft_id}),
            mimetype="application/json",
            status_code=200,
        )

    except NotImplementedError as exc:
        logger.error("Pipeline step not yet implemented: %s", exc)
        return func.HttpResponse(f"Not implemented: {exc}", status_code=501)
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        return func.HttpResponse(f"Internal error: {exc}", status_code=500)
