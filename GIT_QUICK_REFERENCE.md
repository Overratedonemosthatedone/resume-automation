# Git/GitHub Quick Reference — One-Page Cheat Sheet

## TL;DR — 3 Options

```
OPTION 1 (Best - 15 min):
  1. Create repo on GitHub.com
  2. Clone to computer: git clone <url>
  3. Add files
  4. git add .
  5. git commit -m "Initial commit"
  6. git push
  Done!

OPTION 2 (Also works - 20 min):
  1. Create folder locally
  2. git init
  3. Add files
  4. git add .
  5. git commit -m "Initial commit"
  6. Create repo on GitHub
  7. git remote add origin <url>
  8. git push -u origin main
  Done!

OPTION 3 (Not needed):
  Just save files locally without GitHub
  (Bad idea - no backup, no history)
```

---

## Quick Start (Option 1 - Recommended)

### On GitHub.com (5 min)
```
1. Go to https://github.com
2. Log in or sign up
3. Click "+" → "New repository"
4. Name: resume-automation
5. Visibility: Private
6. Initialize with: README, .gitignore (Python), MIT License
7. Create repository
```

### On Your Computer (10 min)
```bash
# Copy the HTTPS URL from GitHub

# Clone
git clone https://github.com/YOUR-USERNAME/resume-automation.git
cd resume-automation

# Copy all your project files here

# First commit
git add .
git commit -m "Initial commit: resume automation system"
git push origin main

# Done!
```

---

## Essential Commands

| Command | What It Does |
|---------|-------------|
| `git clone <url>` | Download repo from GitHub |
| `git status` | See what changed |
| `git add .` | Stage all changes |
| `git commit -m "msg"` | Create snapshot |
| `git push` | Upload to GitHub |
| `git pull` | Download from GitHub |
| `git log` | See all commits |
| `git diff <file>` | See changes to file |

---

## Typical Weekly Workflow

```bash
# 1. You work on code (edit files)

# 2. Check what changed
git status

# 3. Stage changes
git add .

# 4. Commit with message
git commit -m "Add Indeed scraper implementation"

# 5. Upload to GitHub
git push

# Repeat throughout week
```

---

## CRITICAL: .gitignore

Create `.gitignore` file with this content:

```
# Python
venv/
*.pyc
__pycache__/

# YOUR DATA (PRIVATE!)
.env
database/db.sqlite3
resumes/
logs/

# IDE
.vscode/
.idea/
*.swp
```

**Without .gitignore:**
- Your `.env` file with API keys goes to GitHub
- Anyone can find your keys and use your credits!
- **ALWAYS use .gitignore**

---

## Files to COMMIT (✅)

```
✅ config.py
✅ tailor_client.py
✅ document_generators.py
✅ requirements.txt
✅ .env.example (template only)
✅ README.md
✅ QUICK_START.md
✅ All documentation
✅ .gitignore
```

---

## Files to NOT COMMIT (❌)

```
❌ .env (has your API keys!)
❌ venv/ (virtual environment)
❌ resumes/ (your personal resumes)
❌ database/db.sqlite3 (your job data)
❌ logs/
❌ __pycache__/
```

---

## Good Commit Messages

```
✅ "Add Indeed public scraper"
✅ "Fix PDF generation bug"
✅ "Update requirements.txt"
✅ "Implement database tracking"
✅ "Add Google Drive backup"

❌ "stuff"
❌ "fix"
❌ "asdf"
❌ "Update"
```

**Why good messages matter:**
- Future you can understand what you did
- Others can read your history
- Portfolio/employers see clear code history

---

## Common Questions

### Q: Do I HAVE to use GitHub?

A: For this project, no. But:
- ✅ GitHub = cloud backup
- ✅ GitHub = version history
- ✅ GitHub = portfolio piece
- ✅ Recommended: Use it

### Q: Is it free?

A: Yes! Free tier includes:
- ✅ Unlimited public repos
- ✅ Unlimited private repos
- ✅ Great for personal projects

### Q: Can I work on multiple computers?

A: Yes! GitHub keeps everything in sync:
```bash
# On computer 1
git push  # Upload to GitHub

# On computer 2
git pull  # Download from GitHub
```

### Q: What if I make a mistake?

A: You can fix it:
```bash
git log                 # See all commits
git checkout abc123     # Go back to old version
git checkout main       # Return to latest
```

### Q: Will GitHub steal my code?

A: No. GitHub just hosts it. Private repos are only visible to you.

---

## Troubleshooting (Quick Fixes)

### Error: "fatal: not a git repository"
```bash
# You're not in a git folder
cd /path/to/your/project
git status
```

### Error: "Permission denied"
```bash
# You may need to use GitHub personal access token
# Or set up SSH keys (more complex)
# For now, use: https://github.com/settings/tokens
```

### I accidentally committed .env!
```bash
# Remove it from history (more complex)
# SIMPLER: Regenerate your API key immediately!
# 1. Go to Claude console and create new key
# 2. Update your .env locally
# 3. Update any services using the old key
```

### I want to undo the last commit
```bash
# If you haven't pushed yet:
git reset --soft HEAD~1
# Then make new changes and commit again

# If you already pushed (more complex):
# Ask for help or read: git revert
```

---

## When to Commit

### Good times to commit:
- ✅ After adding a feature
- ✅ After fixing a bug
- ✅ After major changes
- ✅ End of work session

### Bad times to commit:
- ❌ In the middle of debugging
- ❌ With .env file included
- ❌ With half-finished code

---

## GitHub for Portfolio

Later, when you're job hunting:

```
Your GitHub profile shows:
✅ resume-automation project
✅ Shows you can build systems
✅ Shows you use version control
✅ Shows clean code & documentation
✅ Employers like this!

Make sure repo is:
✅ Well-documented
✅ Organized code
✅ Good commit messages
✅ README explaining what it does
```

---

## Private vs Public

### Private Repo (For you)
```
Only you can see code
Good for personal projects
Good for sensitive data
Your resume automation should be PRIVATE
```

### Public Repo (For sharing)
```
Everyone can see code
Good for portfolios
Good for open source
Shows code quality to employers
```

**For this project:** Keep it **PRIVATE** (your data is personal)

---

## Private to Public Later

If you want to share your project later:

```bash
# It's easy to change visibility on GitHub
# Go to repo → Settings → Visibility
# Change to public anytime

# Or create new public version without your data
```

---

## Advanced (Not needed now, but good to know)

```bash
git branch              # Create separate versions
git merge               # Combine branches
git pull --rebase       # Clean history
git stash               # Temporarily save changes
git tag v1.0            # Mark releases
```

**Don't worry about these yet. Just use main branch.**

---

## My Setup Recommendation for You

### Day 1:
```bash
# Create GitHub repo (through website)
# Clone it
git clone https://github.com/USERNAME/resume-automation.git
# Add files
# First commit
git push
```

### Weeks 1-4 (Phase 1):
```bash
# Each time you finish a feature:
git add .
git commit -m "Feature description"
git push

# Example commits:
git commit -m "Implement Indeed public scraper"
git commit -m "Add Claude resume tailoring"
git commit -m "Create Word and PDF generators"
git commit -m "Set up SQLite database tracking"
```

### After Phase 1:
```bash
# Create a release tag (optional)
git tag v1.0
git push --tags

# Continue with Phase 2...
git commit -m "Add Rezi.com integration"
git push
```

---

## Final Checklist

- [ ] Created GitHub account
- [ ] Created resume-automation repository
- [ ] Set it to PRIVATE
- [ ] Cloned it locally
- [ ] Added all project files
- [ ] Created .gitignore
- [ ] Made first commit
- [ ] Pushed to GitHub
- [ ] Can see your files on GitHub.com ✅

---

## One More Thing: .gitignore Verification

**Before first commit, verify:**

```bash
# Should NOT include these:
git status

# You should NOT see:
.env
venv/
resumes/
database/db.sqlite3

# If you see them, check .gitignore
cat .gitignore
```

If they're showing up, your `.gitignore` isn't working. Re-read the .gitignore section above.

---

## Quick Copy-Paste Setup

```bash
# Clone existing repo
git clone https://github.com/YOUR-USERNAME/resume-automation.git
cd resume-automation

# Add your files here

# First commit
git add .
git commit -m "Initial commit: resume automation system"
git push origin main

# Done!
```

---

## That's it!

You now know enough Git/GitHub to:
- ✅ Create a repo
- ✅ Make commits
- ✅ Push to GitHub
- ✅ Backup your work
- ✅ Have version history
- ✅ Share code later if you want

**Don't overthink it. Git/GitHub is just tools for backup and history.**

---

**Ready? Create your repo on GitHub now! 🚀**
