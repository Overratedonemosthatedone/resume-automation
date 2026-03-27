# Resume Automation System Specification (Archived)

This file is kept as historical planning context.

For the current working implementation, use:

- `README.md` for the main source of truth
- `QUICK_START.md` for the fastest first-run path
- `PROJECT_OVERVIEW.md` for the high-level architecture
- `JOB_INTAKE_SETUP.md` for the Chrome extension + local intake flow

## What This File Represents

- earlier planning around phased automation goals
- architectural ideas that were broader than the current implementation
- roadmap thinking that may still be useful later

## Important Note

Do not use this file as the current setup or workflow guide.

The current live flow is:

```text
Chrome job page
  -> Send to Resume Tailor extension button
  -> POST http://127.0.0.1:8765/intake
  -> normalized JSON saved in job_queue/pending/
  -> built-in background queue worker
  -> existing tailoring engine
  -> generated artifacts in resumes/
  -> intake JSON moved to processed/ or failed/
```
