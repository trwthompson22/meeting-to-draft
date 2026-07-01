"""
Azure Function HTTP trigger — entry point for the meeting-to-draft pipeline.

Power Automate calls this endpoint with a JSON body:
{
    "meeting_id":      "<Teams online meeting ID>",   // OR
    "transcript":      "<raw transcript text>",        // pass directly to skip Graph fetch
    "conversation_id": "<optional Graph conversation ID for reply threading>",
    "to_recipients":   ["<email>", ...],
    "cc_recipients":   ["<email>", ...],  // optional
    "dry_run":         true               // optional — returns HTML instead of creating a draft
}
"""

import json
import logging

import azure.functions as func

from pipeline import graph, analyze, email

logger = logging.getLogger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="process-recording", methods=["POST"])
def process_recording(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse("Request body must be valid JSON.", status_code=400)

    meeting_id = body.get("meeting_id")
    raw_transcript = body.get("transcript")

    if not meeting_id and not raw_transcript:
        return func.HttpResponse(
            "Missing required field: provide either meeting_id or transcript",
            status_code=400,
        )

    dry_run = body.get("dry_run", False)
    conversation_id = body.get("conversation_id")
    to_recipients = body.get("to_recipients", [])
    cc_recipients = body.get("cc_recipients")

    if not dry_run and not to_recipients:
        return func.HttpResponse("Missing required field: to_recipients", status_code=400)

    try:
        if raw_transcript:
            logger.info("Step 1/3 — using raw transcript passthrough")
            transcript = raw_transcript
        else:
            logger.info("Step 1/3 — fetching transcript for meeting %s", meeting_id)
            transcript = graph.get_transcript(meeting_id)

        logger.info("Step 2/3 — analysing transcript")
        analysis = analyze.analyze_transcript(transcript)

        body_html = email.render_body(
            summary=analysis["summary"],
            key_takeaways=analysis.get("key_takeaways", []),
            action_items=analysis.get("action_items", []),
        )

        if dry_run:
            logger.info("Dry run — returning HTML preview")
            return func.HttpResponse(
                json.dumps({"subject": analysis["subject"], "body_html": body_html}),
                mimetype="application/json",
                status_code=200,
            )

        logger.info("Step 3/3 — creating Outlook draft")
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

    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        return func.HttpResponse(f"Internal error: {exc}", status_code=500)
