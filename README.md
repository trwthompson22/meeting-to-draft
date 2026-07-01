# meeting-to-draft2

An Azure Function that turns a Teams meeting transcript into an Outlook draft email. It fetches the transcript directly from Microsoft Graph (or accepts raw transcript text), extracts a summary, key takeaways, and action items using Claude or OpenAI, and creates a draft in an Outlook mailbox.

This is the **M365 transcript variant** — it requires no audio processing or third-party transcription. The transcript is fetched natively from Microsoft Graph using the `OnlineMeetingTranscript.Read.All` application permission.

---

## How it works

```
POST /api/process-recording
  → fetch Teams transcript via Microsoft Graph (or accept raw transcript text)
  → analyze with Claude or OpenAI (summary + key takeaways + action items)
  → create Outlook draft via Microsoft Graph
```

---

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- A Microsoft 365 work/school account with Teams transcripts enabled

---

## Setup

### 1. Register an Azure AD app

1. Go to [portal.azure.com](https://portal.azure.com) and sign in with your M365 account
2. Navigate to **Azure Active Directory → App registrations → New registration**
3. Name it anything (e.g. `meeting-to-draft`), leave other defaults, click **Register**
4. On the app overview page, copy:
   - **Application (client) ID** → `AZURE_CLIENT_ID`
   - **Directory (tenant) ID** → `AZURE_TENANT_ID`

### 2. Create a client secret

1. In your app registration, go to **Certificates & secrets → New client secret**
2. Add a description, choose an expiry, click **Add**
3. Copy the **Value** (shown only once) → `AZURE_CLIENT_SECRET`

> Use the secret **Value**, not the Secret ID (the GUID).

### 3. Grant API permissions

1. Go to **API permissions → Add a permission → Microsoft Graph → Application permissions**
2. Add both:
   - `OnlineMeetingTranscript.Read.All`
   - `Mail.ReadWrite`
3. Click **Grant admin consent for [your tenant]** and confirm

> Without admin consent all Graph API calls will return 403.

### 4. Get API keys

| Key | Where to get it | Required |
|-----|----------------|----------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | If using Anthropic |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | If using OpenAI |

### 5. Configure environment variables

Copy `.env.example` to `local.settings.json` and fill in all values:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "none",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_TENANT_ID": "<from step 1>",
    "AZURE_CLIENT_ID": "<from step 1>",
    "AZURE_CLIENT_SECRET": "<from step 2>",
    "ONEDRIVE_USER_ID": "<UPN of meeting organiser, e.g. user@domain.com>",
    "MAIL_USER_ID": "<UPN of user whose Outlook drafts to write to>",
    "MODEL_PROVIDER": "anthropic",
    "ANTHROPIC_API_KEY": "<your Anthropic key>",
    "OPENAI_API_KEY": "<your OpenAI key>"
  }
}
```

#### Switching LLM providers

Set `MODEL_PROVIDER` to either `anthropic` or `openai` and provide the corresponding API key.

| `MODEL_PROVIDER` | Model used | Key required |
|-----------------|------------|--------------|
| `anthropic` (default) | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| `openai` | `gpt-4o` | `OPENAI_API_KEY` |

To override the model, set `ANTHROPIC_MODEL` or `OPENAI_MODEL` in your settings.

### 6. Install dependencies

```bash
pip install --target=.python_packages/lib/site-packages -r requirements.txt
```

### 7. Run locally

```bash
PYTHONPATH=.python_packages/lib/site-packages func start
```

---

## Usage

### Option 1 — Dry run (preview only, no Outlook draft created)

Use this to test the analysis output without needing Graph permissions. Accepts either a raw transcript string or a VTT-formatted transcript. Returns the email subject and HTML body.

```bash
curl -X POST http://localhost:7071/api/process-recording \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "<raw or VTT transcript text>",
    "dry_run": true
  }'
```

Returns:
```json
{ "subject": "...", "body_html": "..." }
```

### Option 2 — Live (creates Outlook draft)

Use this once Graph permissions are in place. Accepts either `transcript` (raw text) or `meeting_id` (fetches from Teams via Graph).

```bash
curl -X POST http://localhost:7071/api/process-recording \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "<raw or VTT transcript text>",
    "to_recipients": ["recipient@domain.com"],
    "cc_recipients": ["cc@domain.com"],
    "conversation_id": "<optional — threads draft into an existing email conversation>"
  }'
```

Or using a Teams meeting ID directly:

```bash
curl -X POST http://localhost:7071/api/process-recording \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_id": "<Teams online meeting ID>",
    "to_recipients": ["recipient@domain.com"]
  }'
```

On success, returns `{"draft_id": "<Outlook message ID>"}`. The draft will appear in the `MAIL_USER_ID` mailbox.

### Getting a Teams meeting ID

The easiest way is via a Power Automate flow that triggers when a Teams meeting ends and passes the meeting ID to this endpoint. The meeting ID is available as a dynamic value in the Teams connector trigger.

---

## Request body

| Field | Required | Description |
|-------|----------|-------------|
| `meeting_id` | One of `meeting_id` or `transcript` | Teams online meeting ID — fetches transcript from Graph |
| `transcript` | One of `meeting_id` or `transcript` | Raw or VTT transcript text — skips Graph fetch |
| `to_recipients` | Yes (unless `dry_run`) | Array of To: email addresses |
| `cc_recipients` | No | Array of Cc: email addresses |
| `conversation_id` | No | Graph conversation ID to thread the draft as a reply |
| `dry_run` | No | If `true`, returns HTML preview instead of creating a draft |
