# Resume Automation System

Automatically scrape job postings, tailor your resume with AI, and generate polished .docx & PDF files for hundreds of applications per week.

## 🚀 Quick Start

### Phase 1: Core Resume Tailoring (2–4 weeks)
- [x] Web scraping from LinkedIn, Indeed, Glassdoor
- [x] AI-powered resume tailoring with Claude
- [x] .docx + PDF generation
- [x] Database tracking and CSV export
- [ ] Extended: Web dashboard

### Phase 2: AI Resume Refinement (1–2 weeks)
- [ ] Rezi.com integration for auto-refinement

### Phase 3: Auto-Apply (4+ weeks, stretch goal)
- [ ] Job application form filling and submission
- [ ] Application status tracking

---

## 📋 Prerequisites

- **Python 3.9+** (check with `python3 --version`)
- **Claude API Key** (free tier available, $5+/month for heavy use)
- **Git** (optional, for version control)
- **2–3 GB free disk space** (for resume storage)

---

## ⚙️ Installation

### 1. Clone or Download the Project

```bash
# If using Git
git clone <your-repo-url>
cd resume-automation

# Or download and extract the folder
cd resume-automation
```

### 2. Create a Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `beautifulsoup4` + `selenium` (web scraping)
- `anthropic` (Claude API)
- `python-docx` + `reportlab` (document generation)
- `sqlalchemy` (database)
- `click` (CLI)
- Plus logging, progress bars, and utilities

### 4. Set Up Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Claude API key
nano .env  # or use your preferred editor
```

Your `.env` file should look like:
```bash
CLAUDE_API_KEY=sk-ant-your-actual-key-here
REZI_API_KEY=  # Leave blank for now (Phase 2)
```

**Get your Claude API key:**
1. Visit https://console.anthropic.com/account/keys
2. Create a new API key
3. Copy it and paste into your `.env` file

### 5. Create Your Base Resume

```bash
# Create a plain text resume file
nano base_resume.txt

# Paste your resume content (see template below)
```

**Template for `base_resume.txt`:**
```
Your Name
your.email@example.com | 555-555-5555 | linkedin.com/in/yourprofile | github.com/yourprofile

PROFESSIONAL SUMMARY
2-3 sentence overview of your experience, skills, and career focus.

EXPERIENCE

Senior Software Engineer
Company Name, City, State | Jan 2022 - Present
  - Achievement 1: Specific result with numbers/impact
  - Achievement 2: Technical responsibility and outcome
  - Achievement 3: Leadership or mentoring contribution

Software Engineer
Company Name, City, State | Jun 2019 - Dec 2021
  - Achievement 1
  - Achievement 2
  - Achievement 3

EDUCATION

Bachelor of Science in Computer Science
University Name, City, State | Graduated 2019
  - GPA: 3.8/4.0 (if notable)
  - Relevant coursework: Algorithms, Distributed Systems

TECHNICAL SKILLS
Languages: Python, JavaScript, Go, SQL
Frameworks: Django, React, FastAPI
Databases: PostgreSQL, MongoDB, Redis
Tools & Platforms: Docker, Kubernetes, AWS, Git, GitHub Actions

CERTIFICATIONS & RECOGNITION
- AWS Certified Solutions Architect - Associate
- Open Source Contributor: 500+ GitHub stars
- Recognition: Employee of the Year 2021
```

### 6. Test Your Setup

```bash
# Verify Python and dependencies
python3 --version
pip list | grep anthropic

# Test the configuration
python3 -c "import config; print('✓ Config loaded')"

# Test resume tailor client
python3 tailor_client.py
```

If you see "Resume Tailoring Demo" output, you're ready!

---

## 🎯 Usage

### Option A: Simple Single Job Tailoring

```python
from tailor_client import ResumeTC
from document_generators import DocxGenerator, PdfGenerator

# Load your base resume
with open('base_resume.txt', 'r') as f:
    base_resume = f.read()

# Create tailor client
tailor = ResumeTC(base_resume_text=base_resume)

# Tailor for a specific job
tailored = tailor.tailor(
    job_title="Senior Software Engineer",
    job_description="We're looking for a full-stack engineer...",
    job_requirements="5+ years Python, 3+ years React, AWS experience..."
)

# Generate .docx
docx_gen = DocxGenerator()
docx_gen.parse_and_add_resume(tailored)
docx_gen.save('tailored_resume.docx')

# Generate PDF
pdf_gen = PdfGenerator()
pdf_gen.create_pdf(tailored, 'tailored_resume.pdf')

print("✓ Generated: tailored_resume.docx and tailored_resume.pdf")
```

### Option B: Batch Processing (Coming Soon)

Once you complete Phase 1, you'll have a full CLI:

```bash
# Scrape job postings
python main.py scrape --query "Senior Python Engineer" --location Remote --limit 50

# Tailor all jobs in the database
python main.py tailor_all --base-resume base_resume.txt --batch-size 20

# Export to CSV tracker
python main.py export_tracker
```

---

## 📁 Project Structure

```
resume-automation/
├── base_resume.txt                    # Your base resume (plain text)
├── config.py                          # Configuration & settings
├── requirements.txt                   # Python dependencies
├── .env                               # API keys (DO NOT commit)
├── .env.example                       # Template for .env
│
├── tailor_client.py                   # Claude resume tailoring
├── document_generators.py             # .docx & PDF generation
│
├── resumes/                           # Output folder for generated resumes
│   ├── 2026-03/
│   │   ├── company_job_title.docx
│   │   └── company_job_title.pdf
│   └── ...
│
├── database/
│   └── db.sqlite3                     # Job tracking database
│
├── logs/
│   └── automation.log                 # System logs
│
├── RESUME_AUTOMATION_SPEC.md          # Full technical specification
└── README.md                          # This file
```

---

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Claude model (Opus = highest quality, Sonnet = faster/cheaper)
CLAUDE_MODEL = 'claude-opus-4-20250203'

# Your career context (used in resume tailoring)
RESUME_CONTEXT = """
Your additional achievements, skills, and certifications.
This is used to provide more context to Claude when tailoring.
"""

# Job scraping sources (LinkedIn, Indeed, Glassdoor)
SCRAPER_SOURCES = {
    'linkedin': {'enabled': True},
    'indeed': {'enabled': True},
    'glassdoor': {'enabled': False},  # More restrictive
}

# Resume output formats
RESUME_FORMATS = ['docx', 'pdf']  # Generate both

# Rate limiting
SCRAPER_DELAY_SECONDS = 2  # Respectful delays
BATCH_SIZE = 10  # Jobs per batch
```

---

## 📊 Claude API Costs

**Current Pricing (as of March 2026):**

- **Claude Opus** (highest quality):
  - Input: $3/M tokens
  - Output: $15/M tokens
  
- **Claude Sonnet** (balanced):
  - Input: $3/M tokens
  - Output: $15/M tokens

**Estimated Cost for 100 Resumes/Week:**
- ~250K input tokens + 100K output tokens = ~$1.05/week
- **Free tier = 5M tokens/month** = enough for ~200 resumes before upgrade needed
- **Monthly subscription ($20/month)** = 1M tokens/month + 100M discounted tokens

→ **Recommendation:** Start free. If you hit the limit, upgrade to $20/month tier.

---

## 🌐 Web Scraping Notes

### LinkedIn
- **Status:** Works but can be blocked
- **Mitigation:** Use delays (2–5 sec), headless browser, rotate user agents
- **Alternative:** Use LinkedIn official API (limited, but more stable)

### Indeed
- **Status:** Works well
- **Delay:** 2 sec between requests recommended
- **Friendly:** More permissive than LinkedIn

### Glassdoor
- **Status:** Most restrictive
- **Delay:** 3+ sec recommended
- **Alternative:** Use web scraping service (ScraperAPI, Bright Data)

**Legal Note:** Always check website's `robots.txt` and Terms of Service. Web scraping is generally legal for personal use, but aggressive scraping may violate ToS.

---

## 🐛 Troubleshooting

### "CLAUDE_API_KEY not found"
- [ ] Check `.env` file exists and is in the project root
- [ ] Check `.env` has `CLAUDE_API_KEY=sk-ant-...` (not empty)
- [ ] Reload terminal: `source venv/bin/activate`

### "LinkedIn blocks scraper"
- [ ] Increase delay: `SCRAPER_DELAY_SECONDS = 5`
- [ ] Use headless mode: `SCRAPER_HEADLESS = True`
- [ ] Try Indeed instead
- [ ] Consider ScraperAPI ($10–50/mo) for reliable scraping

### "PDF generation fails"
- [ ] Reinstall reportlab: `pip install --upgrade reportlab`
- [ ] Check resume text has no special characters that cause encoding issues
- [ ] Verify file path is writable

### "Database locked"
- [ ] Close other Python processes using the database
- [ ] SQLite uses WAL mode by default (safe for concurrent access)
- [ ] Delete `database/db.sqlite3-wal` if stuck

### "Out of API quota"
- [ ] Check remaining tokens: https://console.anthropic.com/account/usage
- [ ] Upgrade to paid plan: https://console.anthropic.com/account/billing/plans
- [ ] Or wait for next month's free allocation

---

## 🚀 Next Steps

### Immediate (This Week)
- [ ] Get Claude API key
- [ ] Install Python + dependencies
- [ ] Create base_resume.txt
- [ ] Test `tailor_client.py` with a sample job

### Phase 1 (2–4 Weeks)
- [ ] Complete Week 1: Implement scraper
- [ ] Complete Week 2: Implement tailoring + document generation
- [ ] Complete Week 3: Add database tracking
- [ ] Complete Week 4: Test full pipeline, polish

### Phase 2 (1–2 Weeks)
- [ ] Integrate Rezi.com API
- [ ] Test resume refinement
- [ ] Compare original vs. Rezi-refined resumes

### Phase 3 (4+ Weeks)
- [ ] Research job application APIs
- [ ] Implement form filling (Selenium)
- [ ] Test with 10 live applications
- [ ] Scale to auto-apply

---

## 📖 Resources

- **Claude API Docs:** https://docs.anthropic.com
- **Python Beautiful Soup:** https://beautiful-soup-4.readthedocs.io
- **Selenium WebDriver:** https://selenium-python.readthedocs.io
- **python-docx Docs:** https://python-docx.readthedocs.io
- **ReportLab (PDF):** https://www.reportlab.com/docs/reportlab-userguide.pdf
- **SQLAlchemy ORM:** https://docs.sqlalchemy.org/

---

## 🤝 Contributing & Customization

This is your personal project—feel free to:
- Customize the resume tailoring prompt
- Add new scraping sources
- Implement phase 2 and 3 features
- Extend with your own features (cover letter generation, application tracking, etc.)

---

## 📝 License

This project is for personal use. If you share it, please include attribution to Claude and Anthropic.

---

## 💡 Tips for Success

1. **Start small:** Test with 5 jobs first, then scale
2. **Review resumes:** Always review generated resumes before applying
3. **Track applications:** Use the CSV export to track which jobs you've applied to
4. **Iterate:** Adjust your base resume and career context based on results
5. **Be respectful:** Use appropriate delays when scraping to avoid overloading servers
6. **Backup data:** Export CSV tracker regularly
7. **Experiment:** Try different Claude models; Sonnet is faster/cheaper, Opus is higher quality

---

## ❓ FAQ

**Q: Can I use this to apply to 1000s of jobs?**
A: Technically yes, but strategically no. Quality > Quantity. Target 50–100 high-fit roles per week.

**Q: Will this guarantee interviews?**
A: No. AI-tailored resumes improve your chances, but strong fundamentals (actual experience, skills match) matter most.

**Q: Is web scraping legal?**
A: Generally yes for personal use, but check each site's `robots.txt` and ToS. LinkedIn is aggressive about blocking.

**Q: How much does this cost to run?**
A: $0–20/month depending on job volume and which services you use.

**Q: Can I use this for other positions (internships, freelance)?**
A: Yes! The system works for any job posting with title, description, and requirements.

**Q: What if a job site requires a special form?**
A: Phase 3 (auto-apply) will handle common forms, but rare formats may need manual work.

---

## 🎓 Learning Resources

Completed your Phase 1? Here are next steps:
- Study web scraping best practices
- Learn prompt engineering for better resume tailoring
- Explore job board APIs (LinkedIn Official, Indeed API)
- Implement Phase 3: Selenium for form automation

---

**Questions? Stuck? Need help?**

Check the full technical specification in `RESUME_AUTOMATION_SPEC.md` for deeper details on each module.

---

**Good luck with your job search! 🎯**
