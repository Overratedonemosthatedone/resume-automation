# Updates And Clarifications (Archived)

This file is preserved only as historical reference.

It is no longer the right place to learn the current project workflow.

## Use These Files For The Current System

- `README.md`
- `QUICK_START.md`
- `PROJECT_OVERVIEW.md`
- `JOB_INTAKE_SETUP.md`

## Current Live Workflow

```text
Chrome extension capture
  -> local FastAPI intake service at 127.0.0.1:8765
  -> normalized JSON staged in job_queue/pending/
  -> built-in queue worker
  -> existing tailoring engine
  -> resume artifacts saved in resumes/
  -> intake JSON moved to processed/ or failed/
```
