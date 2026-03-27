# Quick Start Guide - Get Running in 30 Minutes

## Step 1: Get Your Claude API Key (5 min)

1. Visit: https://console.anthropic.com/account/keys
2. Sign up or log in with Anthropic
3. Click "Create Key"
4. Copy the key (starts with `sk-ant-`)
5. Keep it safe! Don't share it.

## Step 2: Create Project Folder (2 min)

```bash
# Create a folder for the project
mkdir resume-automation
cd resume-automation

# Create subdirectories
mkdir database logs resumes
```

## Step 3: Copy All Files Into Folder

Download/copy these files into your `resume-automation/` folder:
- `config.py`
- `requirements.txt`
- `.env.example`
- `tailor_client.py`
- `document_generators.py`
- `README.md`
- `RESUME_AUTOMATION_SPEC.md`

## Step 4: Set Up Python Environment (3 min)

```bash
# Check Python version (must be 3.9+)
python3 --version

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
# On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 5: Add Your API Key (2 min)

```bash
# Create .env file
cp .env.example .env

# Edit .env with your editor
nano .env

# Change this line:
CLAUDE_API_KEY=sk-ant-your-actual-key-here
```

## Step 6: Create Your Resume File (10 min)

Create `base_resume.txt` with your actual resume:

```bash
nano base_resume.txt
```

Paste your resume in this format:

```
Your Full Name
your.email@email.com | (555) 555-5555 | linkedin.com/in/yourprofile | github.com/yourprofile

PROFESSIONAL SUMMARY
1-2 sentence overview of your experience and skills.

EXPERIENCE

Job Title
Company Name, City, State | Jan 2022 - Present
  - Achievement 1 with measurable impact
  - Achievement 2 with responsibility
  - Achievement 3 with outcome

Previous Job Title
Previous Company, City, State | Jan 2020 - Dec 2021
  - Achievement 1
  - Achievement 2

EDUCATION

Bachelor of Science in Your Field
University Name, City, State | Graduated 2019
  - GPA: 3.8/4.0

TECHNICAL SKILLS
Languages: Python, JavaScript, Go
Frameworks: Django, React, FastAPI
Tools: Docker, Git, AWS

CERTIFICATIONS
- AWS Certified Solutions Architect
- Relevant certification 2
```

## Step 7: Test Your Setup (5 min)

Run the demo:

```bash
python3 tailor_client.py
```

You should see a full tailored resume output! 🎉

---

## 🎯 You're Ready!

Now you have two options:

### Option A: Use Single Job Tailoring (Immediate)

```python
# Create a file called test_tailor.py
from tailor_client import ResumeTC
from document_generators import DocxGenerator, PdfGenerator

with open('base_resume.txt', 'r') as f:
    base = f.read()

tailor = ResumeTC(base_resume_text=base)

# Copy a real job posting description and requirements
job_title = "Senior Software Engineer"
job_desc = "We are looking for... [paste full description]"
job_reqs = "5+ years... [paste requirements]"

# Tailor
tailored = tailor.tailor(job_title, job_desc, job_reqs)

# Generate files
docx_gen = DocxGenerator()
docx_gen.parse_and_add_resume(tailored)
docx_gen.save(f'resumes/{job_title}.docx')

pdf_gen = PdfGenerator()
pdf_gen.create_pdf(tailored, f'resumes/{job_title}.pdf')

print("✓ Generated tailored resume!")
```

Run it:
```bash
python3 test_tailor.py
```

### Option B: Build Full Pipeline (Phase 1, 2-4 weeks)

Follow the timeline in `RESUME_AUTOMATION_SPEC.md`:
- Week 1: Web scraping
- Week 2: Batch tailoring
- Week 3: Database tracking
- Week 4: Polish & scale

---

## 📊 What You Can Do Now

✅ **Immediately:**
- Tailor 1 resume to 1 job posting
- Generate .docx and PDF files
- Test Claude API integration

✅ **This Week:**
- Tailor 10 resumes for different jobs
- Compare different versions
- Export as files for application

✅ **This Month (Phase 1):**
- Scrape 100s of job postings
- Batch tailor resumes
- Track everything in a database

✅ **Next Month (Phase 2):**
- Send to Rezi for AI refinement
- Further optimize resume structure

---

## 🆘 If Something Breaks

**"ModuleNotFoundError: No module named 'anthropic'"**
```bash
pip install anthropic
```

**"CLAUDE_API_KEY not found"**
- Check `.env` file exists in same folder as `config.py`
- Make sure it has `CLAUDE_API_KEY=sk-ant-...`

**"Permission denied"**
```bash
chmod +x *.py
```

**"Python version error"**
```bash
# Install Python 3.9+
python3 --version  # Should be 3.9, 3.10, 3.11, or 3.12+
```

---

## 📚 Next Learning Steps

Once you have this working:

1. **Learn about Claude prompting:** https://docs.anthropic.com/claude/docs/build-with-claude/prompt-engineering/overview

2. **Explore the scrapers:** Start with Indeed (friendlier than LinkedIn)

3. **Customize your career context** in `config.py` for better tailoring

4. **Read Phase 2 & 3** in `RESUME_AUTOMATION_SPEC.md` for next steps

---

## ✨ Success Indicators

You'll know you're ready when:
- ✅ `python3 tailor_client.py` runs without errors
- ✅ You can see a tailored resume output
- ✅ `resumes/` folder has `.docx` and `.pdf` files
- ✅ Files open correctly in Word/PDF reader

---

**You're all set! Start tailoring resumes and land more interviews. Good luck! 🚀**
