# Quick Start

Use this guide to get from zero to one successful end-to-end run as quickly as possible.

## 1. Open The Project

If you are using the repo at its current local location:

```text
c:\Users\12485\OneDrive\Desktop\Python\Projects\Resume Automation System\resume-automation
```

## 2. Create And Activate The Virtual Environment

```powershell
python -m venv venv
venv\Scripts\activate
```

## 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

## 4. Create `.env`

```powershell
Copy-Item .env.example .env
notepad .env
```

Set:

```text
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## 5. Create Or Confirm `base_resume.txt`

Create it from the tracked sample file:

```powershell
Copy-Item base_resume.example.txt base_resume.txt
notepad base_resume.txt
```

Then replace the sample content with your real resume text. `base_resume.txt` is local-only and should not be committed.

## 6. Start The Local Python Service

```powershell
venv\Scripts\activate
python job_intake_service.py
```

Optional health check:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8765/health
```

## 7. Load The Chrome Extension

Open `chrome://extensions`, enable Developer mode, click `Load unpacked`, and select:

```text
c:\Users\12485\OneDrive\Desktop\Python\Projects\Resume Automation System\resume-automation\chrome_resume_tailor
```

## 8. Run Your First Real Test

1. Open a job posting page in Chrome.
2. Click `Send to Resume Tailor`.
3. Watch the service logs.

## 9. Success Looks Like

- The service prints the saved intake JSON path.
- The intake file appears in `job_queue/pending/` and then moves to `job_queue/processed/`.
- New files appear in `resumes/`:
  - `.docx`
  - `.pdf`
  - `.json` metadata sidecar

## 10. If The Job Ends Up In `failed`

Check:

- `job_queue/failed/<file>.json`
- the `error_message` field inside that file
- whether `base_resume.txt` exists and is not empty
- whether `ANTHROPIC_API_KEY` is set correctly
- whether the captured page text looks too short or incomplete

## Source Of Truth

- `README.md` is the main source of truth.
- `JOB_INTAKE_SETUP.md` has the extension/intake-specific details.
