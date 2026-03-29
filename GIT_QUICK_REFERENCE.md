# Git Quick Reference

Use this file as the short command cheat sheet. `GIT_GITHUB_SETUP.md` is the longer walkthrough.

## First Commit

```powershell
git status
git add .
git commit -m "Document current automated resume intake flow"
git push
```

## Typical Update Cycle

```powershell
git status
git add .
git commit -m "Describe the change clearly"
git push
```

## Files You Usually Want To Commit

- source code in the repo root
- `chrome_resume_tailor/`
- Markdown documentation
- `.env.example`
- `.gitignore`

## Files You Should Not Commit

- `.env`
- `.env.local`
- `venv/`
- `logs/`
- `resumes/`
- `job_queue/`
- `database/db.sqlite3`
- `base_resume.txt`
- `candidate_context.txt`

## Quick Repo Safety Check

Run this before a commit:

```powershell
git status
```

You should not see these staged:

- `.env`
- `.env.local`
- `venv/`
- `logs/`
- `resumes/`
- `job_queue/`
- `database/db.sqlite3`
- `base_resume.txt`
- `candidate_context.txt`

You should see this available to commit:

- `base_resume.example.txt`
- `candidate_context.example.txt`

## Good Commit Message Examples

- `Document Chrome extension intake flow`
- `Wire intake service to background queue worker`
- `Clarify queue lifecycle and troubleshooting`
- `Polish README and quick start`

## Repo Notes For This Project

- Keep the repository private if it contains personal resume content or job data.
- The main docs to keep accurate are `README.md`, `QUICK_START.md`, `PROJECT_OVERVIEW.md`, and `JOB_INTAKE_SETUP.md`.
