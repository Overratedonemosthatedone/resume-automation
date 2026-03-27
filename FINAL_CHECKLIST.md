# Final Checklist

Use this before you commit the repo to GitHub.

## Core Workflow

- [ ] `python job_intake_service.py` starts without errors.
- [ ] `http://127.0.0.1:8765/health` responds.
- [ ] Chrome extension loads from `chrome_resume_tailor/`.
- [ ] Clicking `Send to Resume Tailor` creates a normalized intake JSON.
- [ ] Successful runs move intake JSON to `job_queue/processed/`.
- [ ] Failed runs move intake JSON to `job_queue/failed/`.
- [ ] Resume artifacts are generated automatically in `resumes/`.

## Required Local Inputs

- [ ] `.env` exists locally.
- [ ] `ANTHROPIC_API_KEY` is set.
- [ ] `base_resume.txt` exists, is not empty, and was created for local use from `base_resume.example.txt`.

## Documentation

- [ ] `README.md` reflects the current architecture and workflow.
- [ ] `QUICK_START.md` gets a new machine to a first successful run.
- [ ] `PROJECT_OVERVIEW.md` matches the actual architecture.
- [ ] `JOB_INTAKE_SETUP.md` matches the current extension + service behavior.
- [ ] Older planning docs no longer read like current setup instructions.

## Queue And Outputs

- [ ] `job_queue/pending/`, `job_queue/processed/`, and `job_queue/failed/` are documented.
- [ ] Resume output naming/versioning is documented.
- [ ] Metadata sidecar behavior is documented.
- [ ] The `failed` workflow tells the user to check `error_message`.

## Git Safety

- [ ] `.env` will not be committed.
- [ ] local env variants will not be committed.
- [ ] `venv/` will not be committed.
- [ ] `logs/`, `resumes/`, and `job_queue/` will not be committed.
- [ ] Personal `base_resume.txt` will not be committed.
- [ ] `base_resume.example.txt` is the tracked safe template instead.

## Honest Notes

- [ ] Docs say extraction is best-effort.
- [ ] Docs say some pages may not extract `company` or `role_title` perfectly.
- [ ] Docs do not claim features that are not implemented.
- [ ] Docs do not imply the old manual job-paste workflow is the main path anymore.
