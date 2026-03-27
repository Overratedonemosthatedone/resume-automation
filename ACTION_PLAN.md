# Action Plan

This plan reflects the current working system, not the older manual copy/paste workflow.

## Today: Get The Automated Flow Working

1. Create `.env` with `ANTHROPIC_API_KEY`.
2. Create or confirm `base_resume.txt` from `base_resume.example.txt`.
3. Start the local Python service with `python job_intake_service.py`.
4. Load the Chrome extension from `chrome_resume_tailor/`.
5. Capture one real job posting from Chrome.
6. Confirm the intake JSON moves to `processed` and that resume artifacts appear in `resumes/`.

## What To Check During The First Run

- The service responds at `http://127.0.0.1:8765/health`.
- The extension can post to `POST /intake`.
- A normalized JSON is created in `job_queue/pending/`.
- The background worker starts automatically.
- The worker uses the existing tailoring engine.
- The intake file lands in `processed` or `failed`.

## If The First Run Fails

1. Open the file in `job_queue/failed/`.
2. Read the `error_message`.
3. Check `base_resume.txt`.
4. Check `ANTHROPIC_API_KEY`.
5. Check whether the captured text is too short or incomplete.
6. Retry with a clearer job posting page.

## After The First Successful Run

1. Test two or three different job boards.
2. Review the extracted `company` and `role_title` quality.
3. Review the generated DOCX/PDF output in `resumes/`.
4. Commit the repo only after the docs, ignore rules, and sensitive local files are in good shape.

## Near-Term Improvements

- Improve extraction heuristics for boards that produce weak `company` or `role_title` values.
- Improve output polish if needed.
- Add more operational tooling only after the current local flow feels stable.

## Source Of Truth

- `README.md` is the main source of truth.
- `QUICK_START.md` is the fastest onboarding path.
- `JOB_INTAKE_SETUP.md` covers the extension and intake specifics.
