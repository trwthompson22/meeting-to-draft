"""
Microsoft Graph API integration: auth, OneDrive download, Outlook draft creation.

Uses app-only (client credentials) auth — compatible with Microsoft 365 work/school accounts.

Required environment variables:
    AZURE_TENANT_ID      - Azure AD tenant ID
    AZURE_CLIENT_ID      - App registration client ID
    AZURE_CLIENT_SECRET  - App registration client secret
    ONEDRIVE_USER_ID     - UPN or object ID of the user whose drive to access
    MAIL_USER_ID         - UPN or object ID of the user whose mailbox to write to
"""

import os
import logging
from typing import Optional
import requests
import msal

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPE = ["https://graph.microsoft.com/.default"]


def _get_app() -> msal.ConfidentialClientApplication:
    tenant_id = os.environ["AZURE_TENANT_ID"]
    client_id = os.environ["AZURE_CLIENT_ID"]
    client_secret = os.environ["AZURE_CLIENT_SECRET"]
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    return msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority,
    )


def get_token() -> str:
    """Acquire an app-only access token via client credentials flow."""
    app = _get_app()

    result = app.acquire_token_silent(SCOPE, account=None)
    if result and "access_token" in result:
        logger.debug("Token served from MSAL cache.")
        return result["access_token"]

    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in result:
        error = result.get("error")
        description = result.get("error_description", "")
        raise RuntimeError(f"MSAL token acquisition failed: {error} — {description}")

    logger.debug("New token acquired via client credentials flow.")
    return result["access_token"]


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {get_token()}"}


def _raise_for_graph(response: requests.Response) -> None:
    """Raise a descriptive RuntimeError for non-2xx Graph API responses."""
    if not response.ok:
        try:
            body = response.json()
            code = body.get("error", {}).get("code", response.status_code)
            message = body.get("error", {}).get("message", response.text)
        except Exception:
            code = response.status_code
            message = response.text
        raise RuntimeError(f"Graph API error {code}: {message}")


def download_recording(file_id: str, drive_id: Optional[str] = None) -> bytes:
    """
    Download a recording file from OneDrive and return its raw bytes.

    Args:
        file_id:  The OneDrive item ID of the recording file.
        drive_id: Optional drive ID. When omitted the default drive of
                  ONEDRIVE_USER_ID is used.

    Returns:
        Raw bytes of the downloaded file (typically an .mp4).
    """
    user_id = os.environ["ONEDRIVE_USER_ID"]

    if drive_id:
        url = f"{GRAPH_BASE}/drives/{drive_id}/items/{file_id}/content"
    else:
        url = f"{GRAPH_BASE}/users/{user_id}/drive/items/{file_id}/content"

    logger.info("Downloading OneDrive item %s", file_id)
    response = requests.get(url, headers=_auth_headers(), allow_redirects=True, timeout=300)
    _raise_for_graph(response)

    logger.info("Downloaded %d bytes for item %s", len(response.content), file_id)
    return response.content


def create_draft(
    subject: str,
    body_html: str,
    to_recipients: list[str],
    cc_recipients: Optional[list] = None,
    conversation_id: Optional[str] = None,
) -> str:
    """
    Create an Outlook draft message in the mailbox of MAIL_USER_ID.

    Args:
        subject:         Email subject line.
        body_html:       HTML email body.
        to_recipients:   List of To: email addresses.
        cc_recipients:   Optional list of Cc: email addresses.
        conversation_id: When provided the draft is threaded into this
                         conversation (reply-all style).

    Returns:
        The Graph item ID of the newly created draft message.
    """
    user_id = os.environ["MAIL_USER_ID"]
    url = f"{GRAPH_BASE}/users/{user_id}/messages"

    def _address_list(emails: list[str]) -> list[dict]:
        return [{"emailAddress": {"address": addr}} for addr in emails]

    payload: dict = {
        "subject": subject,
        "body": {
            "contentType": "HTML",
            "content": body_html,
        },
        "toRecipients": _address_list(to_recipients),
    }

    if cc_recipients:
        payload["ccRecipients"] = _address_list(cc_recipients)

    if conversation_id:
        payload["conversationId"] = conversation_id

    headers = {**_auth_headers(), "Content-Type": "application/json"}
    logger.info("Creating draft: '%s' → %s", subject, to_recipients)
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    _raise_for_graph(response)

    draft_id: str = response.json()["id"]
    logger.info("Draft created with id %s", draft_id)
    return draft_id
