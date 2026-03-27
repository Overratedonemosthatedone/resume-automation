# Resume Automation System

This repository automates the current resume-tailoring workflow from browser capture to generated resume artifacts.

## Current Status

The working system today is:

1. Open a job posting in Google Chrome.
2. Click the `Send to Resume Tailor` extension button.
3. The extension sends captured job data to the local intake service at `http://127.0.0.1:8765/intake`.
4. The intake service normalizes the payload and saves one JSON record in `job_queue/pending/`.
5. A built-in background worker automatically processes that staged JSON.
6. The worker reuses the existing tailoring engine and document generators.
7. Generated resume artifacts are saved in `resumes/`.
8. The intake JSON moves to `job_queue/processed/` or `job_queue/failed/`.

This is the main source of truth for the current implementation.

## What The Project Does

- Captures job posting data directly from Chrome with a local extension.
- Normalizes that capture into a repeated JSON intake format.
- Uses the existing Claude-based tailoring engine to tailor your resume.
- Generates `.docx`, `.pdf`, and a metadata sidecar JSON for each tailored resume.
- Keeps a simple file-based queue lifecycle with `pending`, `processed`, and `failed`.

## Current Architecture

```text
Chrome job page
  -> chrome_resume_tailor/
  -> POST http://127.0.0.1:8765/intake
  -> job_intake_service.py
  -> job_queue/pending/*.json
  -> built-in background worker (job_queue_processor.py)
  -> tailor_client_haiku_optimized.ResumeTC.tailor(...)
  -> document_generators.py
  -> resumes/*.docx, resumes/*.pdf, resumes/*.json
  -> intake JSON moved to processed/ or failed/
```

### Components

- `chrome_resume_tailor/`
  Chrome Manifest V3 extension with a toolbar button.
- `job_intake_service.py`
  Local FastAPI app that accepts captures at `POST /intake`.
- `job_queue_processor.py`
  Built-in background worker that processes staged intake JSON files.
- `tailor_client_haiku_optimized.py`
  Existing tailoring entry point used by the worker.
- `document_generators.py`
  Existing DOCX/PDF generation and naming/versioning logic.

## Requirements

- Windows with Google Chrome installed.
- Python 3.9 or newer.
- A valid Anthropic API key.
- A local `base_resume.txt` in the project root.

### Required Environment Variable

- `ANTHROPIC_API_KEY`

### Supported Legacy Fallback

- `CLAUDE_API_KEY`

### Required Local File

- `base_resume.txt`

This should contain the base resume text that the tailoring engine uses. It is a local-only file and should not be committed if it contains your real resume.

Use the tracked template file as your starting point:

```powershell
Copy-Item base_resume.example.txt base_resume.txt
```

If `base_resume.txt` is missing or empty, the queue worker will move intake files to `job_queue/failed/`.

## Project Layout

```text
resume-automation/
|-- chrome_resume_tailor/          # Chrome extension to capture job pages
|-- job_intake_service.py          # Local FastAPI intake service
|-- job_queue_processor.py         # Built-in background queue worker
|-- tailor_client.py               # Original tailoring client
|-- tailor_client_haiku_optimized.py
|-- document_generators.py         # Existing DOCX/PDF + FileManager logic
|-- base_resume.example.txt        # Safe tracked template for local setup
|-- base_resume.txt                # Local-only base resume source (ignored)
|-- .env                           # Local environment variables
|-- .env.example                   # Template environment file
|-- job_queue/
|   |-- pending/
|   |-- processed/
|   `-- failed/
|-- resumes/                       # Generated resume artifacts
|-- logs/                          # Service and runtime logs
`-- README.md
```

## Setup

### 1. Open The Project

If you are using this repo in its current local location, the project root is:

```text
c:\Users\12485\OneDrive\Desktop\Python\Projects\Resume Automation System\resume-automation
```

### 2. Create And Activate A Virtual Environment

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Create `.env`

```powershell
Copy-Item .env.example .env
notepad .env
```

Set at least:

```text
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 5. Create Or Update `base_resume.txt`

Create your local base resume file from the tracked template:

```powershell
Copy-Item base_resume.example.txt base_resume.txt
notepad base_resume.txt
```

Then replace the sample content with your real resume text for local use.

### 6. Start The Local Python Service

This single command starts both the intake API and the background queue worker:

```powershell
venv\Scripts\activate
python job_intake_service.py
```

The service listens on:

- `http://127.0.0.1:8765`
- `POST http://127.0.0.1:8765/intake`

Optional health check:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8765/health
```

### 7. Load The Chrome Extension

Open `chrome://extensions`, enable Developer mode, click `Load unpacked`, and select:

```text
c:\Users\12485\OneDrive\Desktop\Python\Projects\Resume Automation System\resume-automation\chrome_resume_tailor
```

The extension folder inside the repo is also:

```text
chrome_resume_tailor
```

## How The Chrome Extension Works

- It runs on the active Chrome tab when you click the toolbar button.
- It extracts:
  - page URL
  - page title
  - source hostname
  - best-effort role title
  - best-effort company name
  - best-effort job description text
  - fallback visible page text
- It posts that JSON to `POST /intake` on the local service.

Important: extraction is best-effort. Some job boards and page templates may not extract company or title perfectly.

## Intake JSON Source Of Truth

Each capture is saved in a repeated structure like this before processing begins:

```json
{
  "captured_at": "2026-03-27T10:15:30.123456+00:00",
  "source": "jobs.example.com",
  "page_url": "https://jobs.example.com/roles/123",
  "page_title": "Senior Engineer - Example Co",
  "company": "Example Co",
  "role_title": "Senior Engineer",
  "job_description_text": "Normalized job description text...",
  "raw_visible_text": "Fallback visible page text...",
  "status": "pending"
}
```

The worker may later add fields such as:

- `processing_started_at`
- `processed_at`
- `failed_at`
- `error_message`
- `output_artifacts`
- `tailoring_engine`

## Queue Lifecycle

- `job_queue/pending/`
  New captures are staged here first.
- `job_queue/processed/`
  Successful captures end up here after tailoring and document generation.
- `job_queue/failed/`
  Failed captures end up here with an error message when available.

The status field moves through:

- `pending`
- `processing`
- `complete`
- `failed`

## Tailoring And Output Generation

The worker does not use a second or replacement resume generator.

It reuses:

- `tailor_client_haiku_optimized.ResumeTC.tailor(...)`
- `document_generators.DocxGenerator`
- `document_generators.PdfGenerator`
- `document_generators.FileManager`

That means the existing output naming and versioning logic is still the one in use.

## Where Outputs Go

Generated resumes are saved in:

```text
resumes/
```

Typical filenames look like:

```text
2026-03-27__Example-Co__Senior-Engineer__jobs.example.com__v1.docx
2026-03-27__Example-Co__Senior-Engineer__jobs.example.com__v1.pdf
2026-03-27__Example-Co__Senior-Engineer__jobs.example.com__v1.json
```

### Naming And Versioning

- The date comes from the intake record capture date.
- Company, role title, and source are sanitized for filesystem-safe names.
- The `__vN` suffix increments when the same base stem already exists.

### Metadata Sidecar

For each resume set, a JSON sidecar with the same stem is written beside the resume artifacts. It records:

- company
- role title
- source job board
- source URL
- resume type
- filename
- full output path
- sibling artifact paths

## What Success Looks Like

After clicking the Chrome extension button:

- the service logs that intake was received
- a JSON file appears briefly in `job_queue/pending/`
- the worker logs that tailoring started
- new resume artifacts appear in `resumes/`
- the intake JSON moves to `job_queue/processed/`

If something goes wrong:

- the intake JSON moves to `job_queue/failed/`
- the file should contain `error_message`
- the service logs show where the failure happened

## Troubleshooting

### The extension shows `ERR`

- Confirm `python job_intake_service.py` is still running.
- Confirm the service is reachable at `http://127.0.0.1:8765/health`.
- Reload the extension in `chrome://extensions`.

### The intake JSON ends up in `failed`

Open the failed JSON and check:

- `error_message`
- `page_url`
- `page_title`
- `job_description_text`
- `raw_visible_text`

Common reasons:

- `base_resume.txt` is missing or empty.
- `ANTHROPIC_API_KEY` is missing or invalid.
- The captured job text is too short or incomplete.
- The page extraction did not produce enough usable text.

### Company Or Role Title Is Wrong Or Blank

- The browser extraction is best-effort.
- Some sites hide or dynamically render important fields differently.
- The fallback page text should still be captured, but metadata fields may be imperfect.

### The worker does not seem to process new files

- Check `http://127.0.0.1:8765/health` and confirm `worker_running` is `true`.
- Check the service console logs.
- Restart the service. The worker scans `job_queue/pending/` on startup.

### Styling Or Output Polish Needs Work

- The system currently focuses on consistent automation and ATS-safe output.
- Visual polish can still be refined later without changing the intake/queue architecture.

## Documentation Map

- `README.md`
  Main source of truth for the current working system.
- `QUICK_START.md`
  Fastest path from zero to a successful test.
- `PROJECT_OVERVIEW.md`
  High-level architecture and component roles.
- `JOB_INTAKE_SETUP.md`
  Extension and intake-service focused setup notes.
- `GIT_QUICK_REFERENCE.md`
  Short Git/GitHub commands for this repo.
- `GIT_GITHUB_SETUP.md`
  Longer Git/GitHub setup guide.
- `RESUME_AUTOMATION_SPEC.md`
  Historical specification and roadmap. Useful for future planning, but not the main source of truth for what is implemented today.
- `CLARIFICATIONS.md`, `ANSWER_YOUR_QUESTIONS.md`, `SUMMARY_OF_UPDATES.md`, `UPDATES_AND_CLARIFICATIONS.md`
  Archived reference docs kept only for historical context.

## Commit Safety

- `.env` and local env variants are local-only and should not be committed.
- `base_resume.txt` is local-only and should not be committed if it contains your real resume.
- `base_resume.example.txt` is the safe tracked template intended for the repository.

## Honest Notes

- Chrome extraction is best-effort, not guaranteed perfect.
- The current system is local-first and file-based. There is no intake database.
- The worker processes one staged job at a time by design.
- The extension gets a staging response immediately; it does not wait for resume generation to finish.
