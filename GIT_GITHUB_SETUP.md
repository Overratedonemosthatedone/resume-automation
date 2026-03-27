# Git & GitHub Setup Guide for Your Resume Automation Project

## TL;DR — Quick Answer

**You have 2 options:**

### Option 1: Create Repo on GitHub First (RECOMMENDED ✅)
1. Create repo on GitHub.com
2. Clone it to your computer
3. Add files
4. Git automatically tracks everything
5. **Easier, cleaner, less confusing**

### Option 2: Create Local Git Repo First
1. Create folder on your computer
2. Run `git init` (creates local git repo)
3. Add files
4. Later, create GitHub repo and push to it
5. **Works but more steps**

**My recommendation:** Use **Option 1** (create on GitHub first). It's the standard workflow and fewer steps.

---

## Option 1: Create GitHub Repo First (EASIEST) ✅

### Step 1: Create Repository on GitHub.com (5 minutes)

**If you don't have a GitHub account:**
1. Go to https://github.com
2. Click "Sign up"
3. Follow instructions to create free account
4. Verify email

**If you already have GitHub:**

1. Log in to https://github.com
2. Click **"+"** icon in top right
3. Select **"New repository"**
4. Fill in:
   ```
   Repository name: resume-automation
   Description: Automated resume tailoring with AI and job scraping
   Visibility: Private (keep your data private)
   Initialize with: 
     ☑ Add a README file
     ☑ Add .gitignore (select Python)
     ☑ Choose a license (MIT is fine)
   ```
5. Click **"Create repository"**

### Step 2: Clone Repository to Your Computer (2 minutes)

**On the GitHub page:**
1. Click **"Code"** button (green)
2. Copy the HTTPS URL
   ```
   https://github.com/yourusername/resume-automation.git
   ```

**On your computer:**
```bash
# Navigate to where you want the project
cd ~/Documents  # or wherever

# Clone the repo (creates resume-automation folder)
git clone https://github.com/yourusername/resume-automation.git

# Enter the folder
cd resume-automation
```

### Step 3: Add Your Project Files (5 minutes)

Copy all your project files into this folder:
```
resume-automation/
├── config.py
├── requirements.txt
├── tailor_client.py
├── document_generators.py
├── base_resume.txt
├── .env                    (DO NOT commit this!)
├── README.md
├── QUICK_START.md
├── ... (other docs)
├── venv/                   (DO NOT commit this!)
├── resumes/                (DO NOT commit this!)
└── database/
    └── db.sqlite3         (DO NOT commit this!)
```

### Step 4: Set Up .gitignore (2 minutes)

Create `.gitignore` file (tells Git what NOT to track):

```bash
# Open .gitignore in editor
nano .gitignore
```

Paste this content:
```
# Python
venv/
*.pyc
__pycache__/
*.egg-info/
dist/
build/

# Environment variables (NEVER commit API keys!)
.env
.env.local
.env.*.local

# Project-specific (data is personal)
database/db.sqlite3
resumes/
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary
*.tmp
*.temp
```

Save file (`Ctrl+X`, then `Y`, then `Enter` in nano)

### Step 5: Make Your First Commit (3 minutes)

```bash
# Check what files are ready to commit
git status

# You should see all your project files (not .env, not venv, not resumes)

# Stage all files
git add .

# Create commit with message
git commit -m "Initial commit: resume automation system setup"

# Push to GitHub
git push origin main
```

✅ **Done!** Your project is now on GitHub!

---

## Option 2: Create Local Git Repo First

### Step 1: Initialize Local Git Repository

```bash
# Navigate to your project folder
cd ~/Documents/resume-automation

# Initialize git
git init

# This creates a hidden .git folder (local repository)
```

### Step 2: Create .gitignore

```bash
# Create .gitignore file with content from Option 1 Step 4
nano .gitignore
# (paste content, save)
```

### Step 3: Make First Commit Locally

```bash
git add .
git commit -m "Initial commit: resume automation system"
```

### Step 4: Create GitHub Repo

1. Go to https://github.com
2. Create new repository (same steps as Option 1 Step 1)
3. **DON'T initialize with README or .gitignore** (you already have them locally)

### Step 5: Connect Local Repo to GitHub

```bash
# Add GitHub repo as "origin"
git remote add origin https://github.com/yourusername/resume-automation.git

# Rename branch to main (GitHub default)
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## Common Git Commands You'll Use

### Checking Status
```bash
git status
# Shows what files changed, what's staged
```

### Adding Files
```bash
git add .
# Stage all changes

git add config.py
# Stage only one file
```

### Committing
```bash
git commit -m "Your message here"
# Create a commit with your changes

# Good commit messages:
git commit -m "Add Indeed scraper implementation"
git commit -m "Fix Claude API timeout issue"
git commit -m "Update requirements.txt with new dependencies"
```

### Pushing to GitHub
```bash
git push
# Upload commits to GitHub
```

### Pulling from GitHub
```bash
git pull
# Download latest changes (useful if working on multiple computers)
```

### Viewing History
```bash
git log
# See all commits
# Press 'q' to exit
```

---

## Workflow: Making Changes & Committing

### Typical workflow each day:

```bash
# 1. Make changes to files (edit in your editor)
# For example: edit config.py, add new features to tailor_client.py

# 2. Check what changed
git status

# 3. Review changes
git diff config.py

# 4. Stage changes
git add .

# 5. Commit
git commit -m "Add web scraper for Indeed"

# 6. Push to GitHub
git push

# Done! Changes are now on GitHub
```

---

## Important: DON'T Commit These Files

Your `.gitignore` should prevent this, but be careful:

### ❌ NEVER COMMIT:
```
.env                    # Contains API keys!
venv/                   # Virtual environment
resumes/                # Your personal resumes
database/db.sqlite3     # Your job data
logs/                   # Log files
__pycache__/            # Python cache
.DS_Store               # Mac files
```

### ✅ DO COMMIT:
```
config.py               # Configuration template
requirements.txt        # Dependencies list
tailor_client.py        # Source code
document_generators.py  # Source code
README.md               # Documentation
.gitignore              # Git ignore rules
*.md                    # Documentation files
```

---

## What NOT to Do (Common Mistakes)

### ❌ DON'T do this:
```bash
git commit -m "Add my API key sk-ant-xyz123"
# If you accidentally do this, your key is exposed on GitHub!
# Anyone can find it and use your API credits!
```

### ❌ DON'T do this:
```bash
git push -f
# Force push can destroy GitHub history
# Only do this if you REALLY know what you're doing
```

### ❌ DON'T do this:
```bash
# Commit .env file
# Use .gitignore to prevent this
```

### ✅ DO this instead:
```bash
# Use .env.example as template
# Users copy it to .env and fill in their own keys
```

---

## Template: Your GitHub Repository Structure

Here's what your GitHub repo should look like:

```
resume-automation/
├── README.md                              # Project overview
├── QUICK_START.md                         # Setup guide
├── ACTION_PLAN.md                         # Roadmap
├── INDEED_PASSKEYS_GUIDE.md               # Indeed solutions
├── RESUME_AUTOMATION_SPEC.md              # Technical spec
├── UPDATES_AND_CLARIFICATIONS.md          # Clarifications
├── requirements.txt                        # Python deps
├── config.py                              # Config template
├── tailor_client.py                       # Claude integration
├── document_generators.py                 # Word/PDF generation
├── .env.example                           # Template for .env
├── .gitignore                             # Git ignore rules
├── LICENSE                                # (Auto-created by GitHub)
└── [Folders NOT in GitHub]
    ├── venv/                              # Virtual environment
    ├── .env                               # Your API keys
    ├── resumes/                           # Your resumes
    ├── database/                          # Your job data
    └── logs/                              # Log files
```

---

## Step-by-Step: From Nothing to GitHub (15 minutes)

### Step 1: Create GitHub Account (5 min)
```
Go to https://github.com
Click "Sign up"
Follow instructions
```

### Step 2: Create Repository (3 min)
```
Click "+" → "New repository"
Name: resume-automation
Visibility: Private
Initialize with: README, .gitignore (Python), MIT License
Create repository
```

### Step 3: Clone to Computer (2 min)
```bash
git clone https://github.com/yourusername/resume-automation.git
cd resume-automation
```

### Step 4: Add Your Files (3 min)
```bash
# Copy all your project files here
# Make sure .env is NOT here (it's in .gitignore)
```

### Step 5: First Commit (2 min)
```bash
git add .
git commit -m "Initial commit: resume automation system"
git push origin main
```

✅ **You're done!** Your project is on GitHub!

---

## Making Updates (Weekly)

### Each week, as you work:

```bash
# Make changes to files

# Check status
git status

# Commit your work
git add .
git commit -m "Implement Indeed public scraper - Option A"

# Push to GitHub
git push
```

### Good commit messages:
```
git commit -m "Add web scraper for Indeed public jobs"
git commit -m "Fix PDF generation bug with special characters"
git commit -m "Update config with new rate limiting options"
git commit -m "Add Google Drive backup functionality"
```

### Bad commit messages:
```
git commit -m "stuff"
git commit -m "fix"
git commit -m "asdf"
```

---

## Backup Benefits of GitHub

### Why use GitHub (beyond version control):

1. **Cloud Backup** — Your code is safe on GitHub
2. **History** — See all changes you ever made
3. **Collaboration** — Later, work with others
4. **Portfolio** — Show employers your code
5. **Rollback** — Go back to earlier versions if needed

### Example: Rolling back to earlier version
```bash
# See all commits
git log

# Go back to specific commit
git checkout abc123def456

# Return to latest
git checkout main
```

---

## .gitignore Explained

Your `.gitignore` tells Git which files to ignore (not track).

**Why you need it:**
- API keys (.env file)
- Personal data (resumes folder)
- Temporary files (venv, __pycache__)
- Generated files (database, logs)

**How it works:**
```
# Lines starting with # are comments

# Ignore all .env files
.env

# Ignore entire venv folder
venv/

# Ignore .pyc files
*.pyc

# Ignore database
database/db.sqlite3

# Ignore resumes folder
resumes/
```

When you do `git status`, it won't show these files as "untracked".

---

## Private vs Public Repository

### Private Repository (RECOMMENDED for your project) 🔒
```
Only you can see the code
Others can't steal your setup
Good for personal projects
```

**To make it private:**
1. Go to GitHub repo settings
2. Find "Visibility"
3. Click "Change to private"

### Public Repository (For sharing code later) 🌐
```
Everyone can see the code
Great for portfolio
Good for open source
```

For your resume automation, keep it **PRIVATE** (your job data is personal).

---

## Troubleshooting

### "fatal: not a git repository"
```bash
# You're not in a git folder
git clone https://github.com/yourusername/resume-automation.git
cd resume-automation
```

### "error: failed to push some refs"
```bash
# Your local changes conflict with GitHub
git pull origin main    # Get latest from GitHub
# Resolve conflicts, then:
git push origin main
```

### "Please make sure you have the correct access rights"
```bash
# Authentication issue
# Either:
# 1. Use GitHub personal access token instead of password
# 2. Set up SSH keys (more secure, but complex)
# For now, use option 1
```

### "fatal: 'origin' does not appear to be a 'git' repository"
```bash
# You forgot to add GitHub repo as origin
git remote add origin https://github.com/yourusername/resume-automation.git
git push -u origin main
```

---

## My Recommendation for You

### Week 1: Get Started
1. Create GitHub repo (Option 1 - create on GitHub first)
2. Clone to computer
3. Add all project files
4. Make first commit
5. Push to GitHub
6. Done!

### Week 2+: Regular commits
```bash
# As you implement Phase 1 scraper:
git commit -m "Add Indeed public scraper"
git push

# As you add features:
git commit -m "Implement database tracking"
git push

# As you fix bugs:
git commit -m "Fix PDF generation issue"
git push
```

### Month 1+: Portfolio
- You'll have a GitHub repo showing your project
- Great for portfolio/resume
- Shows employers you can build real systems

---

## Git vs GitHub Cheat Sheet

| Term | What It Is |
|------|-----------|
| **Git** | Version control software (tracks changes) |
| **GitHub** | Website to host Git repositories |
| **Repository** | Folder with all your files + .git folder |
| **Commit** | Snapshot of your code at a point in time |
| **Push** | Upload commits to GitHub |
| **Pull** | Download commits from GitHub |
| **Branch** | Separate version of code (for now, just use "main") |
| **.gitignore** | File that tells Git what to ignore |
| **Remote** | Connection to GitHub (usually called "origin") |

---

## Quick Reference: Git Commands

```bash
# Initial setup
git clone <url>                    # Clone repo from GitHub
git init                           # Initialize local repo

# Daily work
git status                         # See what changed
git add .                          # Stage all changes
git commit -m "message"            # Create commit
git push                           # Upload to GitHub
git pull                           # Download from GitHub

# Viewing
git log                            # See commit history
git diff filename                  # See changes to file
git show abc123                    # See specific commit

# Branches (for later)
git branch                         # List branches
git checkout -b new-branch         # Create new branch
git checkout main                  # Switch to main
```

---

## Summary

### For Your Resume Automation Project:

1. **Create GitHub repo first** (Option 1 is easiest)
2. **Clone to your computer**
3. **Add all your project files**
4. **Create .gitignore** (to protect API keys and personal data)
5. **Make first commit and push**
6. **You're done!**

From then on:
- Make changes locally
- Commit when you complete features
- Push to GitHub regularly

**Total setup time: 15 minutes**

---

## Next Steps

1. Go to https://github.com
2. Create an account (if needed)
3. Create "resume-automation" repository
4. Clone it
5. Add your project files
6. Make first commit
7. Start building!

**That's it! Git/GitHub is just backup + history tracking. Don't overthink it.**

---

**Good luck with your project! Having it on GitHub is great for backup and portfolio. 🚀**
