# Job Intake Setup

This file focuses on the Chrome extension and local intake service. `README.md` is the main source of truth for the whole system.

## What This Covers

- loading the Chrome extension
- starting the local Python service
- understanding the queue folders
- troubleshooting a failed intake

## Start The Local Service

```powershell
venv\Scripts\activate
python job_intake_service.py
```

This starts:

- the FastAPI intake API at `http://127.0.0.1:8765`
- the built-in background queue worker

Optional health check:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8765/health
```

## Load The Chrome Extension

In Chrome:

1. Open `chrome://extensions`
2. Turn on Developer mode
3. Click `Load unpacked`
4. Select:

```text
c:\Users\12485\OneDrive\Desktop\Python\Projects\Resume Automation System\resume-automation\chrome_resume_tailor
```

## Queue Lifecycle

```text
job_queue/
|-- pending/
|-- processed/
`-- failed/
```

- `pending`
  newly staged normalized intake JSON
- `processed`
  successful jobs after tailoring and artifact generation
- `failed`
  failed jobs with `error_message`

## What The Extension Sends

The extension sends best-effort job-page data to `POST /intake`, including:

- page URL
- page title
- source hostname
- best-effort role title
- best-effort company name
- best-effort job description text
- fallback visible page text

## What Success Looks Like

- the service logs `intake received`
- a JSON file is saved in `job_queue/pending/`
- the file stays queued until you click `Process Queue`
- after you trigger processing, the worker picks it up
- the file moves to `job_queue/processed/`
- resume artifacts appear in `resumes/`

## If A Job Ends Up In `failed`

Open the failed JSON file and check:

- `error_message`
- whether `job_description_text` is too short
- whether `base_resume.txt` exists
- whether `ANTHROPIC_API_KEY` is set correctly

## Notes

- Extraction is best-effort and some sites may not produce perfect `company` or `role_title` values.
- The extension gets a staging response quickly; it does not wait for resume generation to finish.
- The worker reuses the existing tailoring engine and document generators.
