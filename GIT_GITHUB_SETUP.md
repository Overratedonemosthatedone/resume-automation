# Git And GitHub Setup

This is the longer Git/GitHub guide for this repository. `GIT_QUICK_REFERENCE.md` is the short command sheet.

## Recommended Approach

1. Create the repository on GitHub first.
2. Clone it locally.
3. Copy this project into the cloned folder.
4. Review `.gitignore` and local-only files.
5. Commit and push.

## Suggested `.gitignore` Expectations

This project should keep these local:

- `.env`
- `.env.local`
- `venv/`
- `logs/`
- `resumes/`
- `job_queue/`
- `database/db.sqlite3`
- `base_resume.txt`
- `candidate_context.txt`

Also be careful with:

- `base_resume.example.txt`
- `candidate_context.example.txt`

`base_resume.example.txt` is the safe tracked template. `base_resume.txt` is the local-only file the app actually reads.
`candidate_context.example.txt` is the safe tracked template for supplemental context. `candidate_context.txt` is the local-only file used to supply extra candidate framing during tailoring.

## First Push

```powershell
git status
git add .
git commit -m "Initial commit: automated resume intake and tailoring"
git push -u origin main
```

## Before You Push

Verify:

- the docs describe the current Chrome extension -> intake -> queue -> tailoring flow
- sensitive local files are not staged
- generated artifacts are not staged
- the extension folder `chrome_resume_tailor/` is included
- `base_resume.example.txt` is included
- `candidate_context.example.txt` is included
- `base_resume.txt` is not included
- `candidate_context.txt` is not included

## Useful Commands

```powershell
git status
git diff
git add .
git commit -m "Your message"
git push
```

## Commit Guidance

Prefer commit messages that describe the actual change:

- `Add Chrome extension intake flow`
- `Document queue lifecycle and outputs`
- `Clarify local setup and troubleshooting`

Avoid vague messages like:

- `update`
- `fix`
- `stuff`

## Repository Hygiene

- `README.md` should stay the main source of truth.
- `QUICK_START.md` should stay short and practical.
- `PROJECT_OVERVIEW.md` should stay high level.
- `JOB_INTAKE_SETUP.md` should stay focused on the extension and service setup.

If two docs overlap heavily, simplify one and point back to the main source of truth instead of duplicating instructions.
