# meeting-to-draft

An Azure Function that turns a Teams/OneDrive meeting recording into an Outlook draft email. Given a OneDrive file ID, it downloads the recording, transcribes the audio (Groq Whisper), extracts a summary and action items (Claude or OpenAI), and creates a draft in an Outlook mailbox.

---

## How it works

```
POST /api/process-recording
  → download .mp4 from OneDrive
  → extract audio with ffmpeg
  → transcribe with Groq Whisper
  → analyze with Claude or OpenAI (summary + action items)
  → create Outlook draft via Microsoft Graph
```

---

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- `ffmpeg` on your PATH (`brew install ffmpeg` on Mac)
- A Microsoft 365 work/school account

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
   - `Files.Read.All`
   - `Mail.ReadWrite`
3. Click **Grant admin consent for [your tenant]** and confirm

> Application permissions require admin consent. Without it the app will authenticate successfully but all Graph API calls will return 403.

### 4. Get API keys

You need a key for one LLM provider (Anthropic or OpenAI) plus Groq for transcription:

| Key | Where to get it | Required |
|-----|----------------|----------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | If using Anthropic |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | If using OpenAI |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Always |

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
    "ONEDRIVE_USER_ID": "<UPN of user whose OneDrive to access, e.g. user@domain.com>",
    "MAIL_USER_ID": "<UPN of user whose Outlook drafts to write to>",
    "MODEL_PROVIDER": "anthropic",
    "ANTHROPIC_API_KEY": "<your Anthropic key>",
    "OPENAI_API_KEY": "<your OpenAI key>",
    "GROQ_API_KEY": "<from step 4>"
  }
}
```

`ONEDRIVE_USER_ID` and `MAIL_USER_ID` are typically the same — the email address of the M365 user whose recordings you want to process.

#### Switching LLM providers

Set `MODEL_PROVIDER` to either `anthropic` or `openai` and provide the corresponding API key. The other key can be left blank.

| `MODEL_PROVIDER` | Model used | Key required |
|-----------------|------------|--------------|
| `anthropic` (default) | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| `openai` | `gpt-4o` | `OPENAI_API_KEY` |

To override the model, set `ANTHROPIC_MODEL` or `OPENAI_MODEL` in your settings.

### 6. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 7. Run locally

```bash
source .venv/bin/activate
func start
```

---

## Usage

Call the function with the OneDrive item ID of a recording:

```bash
curl -X POST http://localhost:7071/api/process-recording \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "<OneDrive item ID>",
    "to_recipients": ["recipient@domain.com"],
    "cc_recipients": ["cc@domain.com"],
    "conversation_id": "<optional — threads draft into an existing email conversation>"
  }'
```

On success, returns `{"draft_id": "<Outlook message ID>"}`. The draft will appear in the `MAIL_USER_ID` mailbox.

### Getting a OneDrive file ID

The easiest way to supply `file_id` automatically is via a Power Automate flow that triggers when a recording is saved to OneDrive and passes the file ID to this endpoint. To find an ID manually, use [Microsoft Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer) and call `GET /me/drive/root/children`.

---

## Request body

| Field | Required | Description |
|-------|----------|-------------|
| `file_id` | Yes | OneDrive item ID of the `.mp4` recording |
| `to_recipients` | Yes | Array of To: email addresses |
| `cc_recipients` | No | Array of Cc: email addresses |
| `drive_id` | No | OneDrive drive ID (uses user's default drive if omitted) |
| `conversation_id` | No | Graph conversation ID to thread the draft as a reply |
