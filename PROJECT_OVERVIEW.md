# Project Overview

This repository is a local automation system for capturing job postings from Chrome, staging them in a local queue, and generating tailored resume artifacts on demand.

## High-Level Flow

```text
Browser capture
  -> local intake service
  -> staged JSON in job_queue/pending/
  -> manual Process Queue trigger
  -> background queue worker
  -> existing tailoring engine
  -> DOCX/PDF generation
  -> processed or failed queue outcome
```

## Main Components

### 1. Browser Capture

- A Chrome Manifest V3 extension lives in `chrome_resume_tailor/`.
- The toolbar button is `Send to Resume Tailor`.
- It extracts job posting data from the current page and posts it to the local Python service.

### 2. Intake Service

- `job_intake_service.py` runs locally at `127.0.0.1:8765`.
- It accepts `POST /intake`.
- It normalizes the browser payload into a repeated JSON structure.
- It saves one intake file per capture in `job_queue/pending/`.

### 3. Queue Worker

- `job_queue_processor.py` is a built-in background worker triggered on demand.
- It waits for an explicit batch request instead of automatically watching the queue.
- It validates and processes staged intake files.
- It moves each file to `processed` or `failed`.

### 4. Tailoring Engine

- The worker reuses the existing `tailor_client_haiku_optimized.ResumeTC.tailor(...)` entry point.
- It does not use a second or parallel resume generation path.
- The intake JSON remains the source of truth for the job data handed into tailoring.

### 5. Document Generation

- The worker reuses `DocxGenerator`, `PdfGenerator`, and `FileManager` from `document_generators.py`.
- Generated artifacts go into `resumes/`.
- Naming, versioning, and metadata sidecar behavior come from the existing `FileManager` logic.

## Queue Lifecycle

```text
job_queue/
|-- pending/    # new normalized captures
|-- processed/  # successful tailoring runs
`-- failed/     # failed runs with error details
```

Statuses used in the intake JSON:

- `pending`
- `processing`
- `complete`
- `failed`

## Resume Outputs

Outputs are written to `resumes/` and typically include:

- `YYYY-MM-DD__Company__Role__source__vN.docx`
- `YYYY-MM-DD__Company__Role__source__vN.pdf`
- `YYYY-MM-DD__Company__Role__source__vN.json`

The sidecar JSON records the output paths and artifact relationships.

## What Is Implemented Today

- Chrome extension capture
- Local intake API
- Pending/processed/failed queue lifecycle
- Manual batch processing from the extension popup
- Existing tailoring engine integration
- DOCX/PDF generation after an explicit queue trigger

## Important Limits

- Extraction from job pages is best-effort.
- Company and role title may be imperfect on some sites.
- The system is local-first and file-based.
- Styling polish can still be improved later without changing the automation flow.

## Documentation Hierarchy

- `README.md`
  Main source of truth
- `QUICK_START.md`
  Fastest setup path
- `JOB_INTAKE_SETUP.md`
  Extension + intake details
- `RESUME_AUTOMATION_SPEC.md`
  Historical spec and roadmap
