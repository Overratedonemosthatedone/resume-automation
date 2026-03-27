# Resume Automation System — Technical Specification

**Project**: Automated Resume Tailoring & Job Application Pipeline  
**Phase 1 Scope**: Web scraping job postings + tailoring resumes with Claude API + dual output (.docx + PDF)  
**Phase 2 Scope**: Rezi.com integration for resume refinement  
**Phase 3 Scope**: Auto-apply to job portals (stretch goal)  
**Budget**: $0–$50/month  
**Timeline**: Phase 1 = 2–4 weeks, Phase 2 = 1–2 weeks, Phase 3 = 4+ weeks  

---

## 1. System Architecture

### 1.1 Data Flow

```
Job Posting (web) 
    ↓ 
[Scraper: LinkedIn/Indeed/etc.]
    ↓ 
Job Data (title, company, URL, description, requirements)
    ↓ 
[Claude API: Tailor Resume]
    ↓ 
Tailored Resume (text)
    ↓ 
[Generators: .docx + PDF]
    ↓ 
Storage (file + metadata)
    ↓ 
[Database: SQLite]
    ↓ 
Dashboard / Job Tracker (CSV export)
    ↓ 
[Phase 2] → Rezi.com refinement (optional)
    ↓ 
[Phase 3] → Auto-apply to portal (optional)
```

### 1.2 Component Breakdown

| Component | Technology | Purpose | Cost |
|-----------|-----------|---------|------|
| **Job Scraper** | BeautifulSoup4 + Selenium | Extract job postings from LinkedIn, Indeed, Glassdoor | $0 |
| **Resume Tailor** | Claude API | Generate tailored resumes matching job requirements | $0–20/mo |
| **Document Generator** | python-docx + reportlab (PDF) | Create .docx and PDF files | $0 |
| **Database** | SQLite | Track jobs, resumes, hyperlinks, status | $0 |
| **CLI** | Click or argparse | Command-line interface for batch processing | $0 |
| **Dashboard** | HTML + Python Flask (optional) | Web UI to view jobs and status | $0 |
| **Rezi Integration** | Requests + Rezi API | Send resumes for AI refinement | $0–50/mo |
| **Auto-Apply** | Selenium + Zapier | Fill forms and submit applications | $0–15/mo |

---

## 2. Phase 1: Core Resume Tailoring

### 2.1 Project Structure

```
resume-automation/
├── main.py                      # Entry point (CLI)
├── config.py                    # API keys, paths, settings
├── requirements.txt             # Python dependencies
├── database/
│   ├── models.py               # SQLite schema definitions
│   └── db.sqlite3              # Local database file
├── scrapers/
│   ├── __init__.py
│   ├── linkedin.py             # LinkedIn scraper
│   ├── indeed.py               # Indeed scraper
│   └── glassdoor.py            # Glassdoor scraper (optional)
├── tailor/
│   ├── __init__.py
│   ├── claude_client.py        # Claude API wrapper
│   └── prompt.py               # Prompting strategy & templates
├── generators/
│   ├── __init__.py
│   ├── docx_generator.py       # .docx file creation
│   └── pdf_generator.py        # PDF file creation
├── storage/
│   ├── __init__.py
│   └── file_manager.py         # File organization by date/company
├── tracker/
│   ├── __init__.py
│   └── job_tracker.py          # CSV export, status tracking
├── resumes/                    # Output folder
│   ├── 2026-03/
│   │   ├── tailored/
│   │   └── rezi_processed/     # Phase 2
│   └── ...
└── logs/
    └── automation.log          # Execution logs
```

### 2.2 Dependencies

```txt
# requirements.txt

# Web scraping
beautifulsoup4==4.12.2
selenium==4.15.2
requests==2.31.0

# Claude API
anthropic==0.7.1

# Document generation
python-docx==0.8.11
reportlab==4.0.9
pypdf==3.17.1

# Database
sqlalchemy==2.0.23

# CLI & utilities
click==8.1.7
python-dotenv==1.0.0
pandas==2.1.3

# Logging & progress
tqdm==4.66.1
loguru==0.7.2

# Optional: Web UI
flask==3.0.0
```

### 2.3 Database Schema

```sql
-- Jobs table
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    job_title TEXT NOT NULL,
    job_url TEXT UNIQUE NOT NULL,
    job_source TEXT,  -- 'linkedin', 'indeed', 'glassdoor'
    job_description TEXT,
    job_requirements TEXT,
    posted_date TIMESTAMP,
    
    -- Resume files
    tailored_resume_docx TEXT,  -- file path
    tailored_resume_pdf TEXT,   -- file path
    
    -- Metadata
    status TEXT DEFAULT 'draft',  -- draft, reviewed, submitted, rejected, accepted
    rezi_processed INTEGER DEFAULT 0,  -- 1 if sent to Rezi
    rezi_output_path TEXT,  -- path to Rezi-refined resume
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP
);

-- Hyperlinks table (for easy reference)
CREATE TABLE hyperlinks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    job_posting_url TEXT,
    tailored_resume_url TEXT,  -- local file URL or cloud link
    rezi_output_url TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- Scrape logs (for debugging)
CREATE TABLE scrape_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    search_query TEXT,
    jobs_found INTEGER,
    jobs_processed INTEGER,
    errors TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.4 Core Modules

#### **A. Scraper: `scrapers/linkedin.py`**

```python
# Pseudo-code outline
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class LinkedInScraper:
    def __init__(self, headless=True):
        self.driver = webdriver.Chrome()  # or Firefox
        self.driver.set_page_load_timeout(15)
    
    def search_jobs(self, query, location='', limit=100):
        """
        Search LinkedIn for jobs matching query.
        Returns list of dicts: {title, company, url, description, ...}
        """
        url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}"
        self.driver.get(url)
        
        jobs = []
        for _ in range(limit // 25):  # Lazy load pagination
            job_cards = self.driver.find_elements(By.CLASS_NAME, 'base-card')
            for card in job_cards:
                job = {
                    'title': card.find_element(...).text,
                    'company': card.find_element(...).text,
                    'url': card.get_attribute('href'),
                    'description': self._get_description(card),
                }
                jobs.append(job)
            self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="View next page"]').click()
            time.sleep(2)  # Rate limiting
        
        return jobs
    
    def _get_description(self, card):
        # Extract full job description from card or detail page
        pass
    
    def close(self):
        self.driver.quit()

# Usage
scraper = LinkedInScraper()
jobs = scraper.search_jobs("Senior Software Engineer", "Remote")
scraper.close()
```

**Key Challenges:**
- LinkedIn blocks scrapers aggressively. Mitigations:
  - Use rotating proxies (ScraperAPI, Bright Data)
  - Add delays between requests (2–5 sec)
  - Use Selenium with realistic browser behavior
  - Consider using official LinkedIn API (limited, but reliable)
- Indeed, Glassdoor are more scraper-friendly

**Alternative (Safer):** Use job board APIs where available:
- LinkedIn: Official API (limited access, but stable)
- Indeed: Offers an unofficial scraping endpoint
- Glassdoor: No official API; use scraping with caution

#### **B. Resume Tailor: `tailor/claude_client.py`**

```python
from anthropic import Anthropic

class ResumeTC:
    def __init__(self, api_key, base_resume_text):
        self.client = Anthropic()
        self.api_key = api_key
        self.base_resume = base_resume_text
    
    def tailor(self, job_title, job_desc, job_reqs, career_context=''):
        """
        Tailor base resume to a specific job.
        Returns tailored resume as plain text.
        """
        system_prompt = """You are an expert resume writer. 
Your task: tailor a resume to match a specific job posting.
- Highlight relevant skills and experience from the provided resume
- Use keywords from the job posting naturally
- Reorder bullet points to emphasize most relevant achievements first
- Keep formatting clean and ATS-friendly
- Do NOT invent experience; only rearrange what's provided
- Output ONLY the tailored resume, no explanations
"""
        
        user_prompt = f"""
Base Resume:
{self.base_resume}

---

Additional Career Context:
{career_context}

---

Target Job:
Title: {job_title}
Description: {job_desc}
Requirements: {job_reqs}

---

Tailor the resume above to match this job. Output the COMPLETE tailored resume in plain text (no markdown, no ### headers).
"""
        
        response = self.client.messages.create(
            model="claude-opus-4-20250203",  # Or claude-sonnet
            max_tokens=2000,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            system=system_prompt
        )
        
        tailored_text = response.content[0].text
        return tailored_text

# Usage
with open('base_resume.txt', 'r') as f:
    base = f.read()

tailor = ResumeTC(api_key='sk-...', base_resume_text=base)
tailored = tailor.tailor(
    job_title='Senior Software Engineer',
    job_desc='We are looking for a full-stack engineer...',
    job_reqs='5+ years Python, 3+ years React...',
    career_context='Specialized in distributed systems and API design'
)

print(tailored)
```

**Cost Estimate:**
- Average job description: 1000–2000 tokens (input)
- Tailored resume: 500–1000 tokens (output)
- Total per job: ~2500 tokens
- 100 jobs/week = 250K tokens/week ≈ $1–2/week
- **Claude API free tier: 5M tokens/month = ~40 jobs/month, then $0.003/input token**

#### **C. Document Generator: `generators/docx_generator.py`**

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

class DocxGenerator:
    def __init__(self, template_path=None):
        """
        Load template .docx or create blank document.
        """
        if template_path:
            self.doc = Document(template_path)
        else:
            self.doc = Document()
            self._set_default_styles()
    
    def _set_default_styles(self):
        """Set clean, ATS-friendly default styles."""
        style = self.doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)
        font.color.rgb = RGBColor(0, 0, 0)
    
    def add_resume_content(self, resume_text):
        """
        Parse resume text and add to document.
        Assumes resume is in plain text format with sections.
        """
        lines = resume_text.strip().split('\n')
        
        for line in lines:
            line = line.rstrip()
            if not line:
                self.doc.add_paragraph()  # Blank line
            elif line.isupper() or line.endswith(':'):  # Section header
                p = self.doc.add_paragraph(line)
                p_format = p.paragraph_format
                p_format.space_before = Pt(6)
                p_format.space_after = Pt(3)
                for run in p.runs:
                    run.bold = True
            elif line.startswith('  '):  # Bullet point
                self.doc.add_paragraph(line.lstrip(), style='List Bullet')
            else:
                self.doc.add_paragraph(line)
    
    def save(self, file_path):
        """Save document to .docx file."""
        self.doc.save(file_path)

# Usage
gen = DocxGenerator()
gen.add_resume_content(tailored_resume_text)
gen.save('tailored_resume.docx')
```

#### **D. PDF Generator: `generators/pdf_generator.py`**

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

class PdfGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add ATS-friendly styles."""
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            alignment=4,  # Justified
        ))
    
    def create_pdf(self, resume_text, output_path):
        """Generate PDF from plain text resume."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
        )
        
        elements = []
        lines = resume_text.strip().split('\n')
        
        for line in lines:
            line = line.rstrip()
            if not line:
                elements.append(Spacer(1, 0.05*inch))
            elif line.isupper() or line.endswith(':'):
                style = self.styles['Heading2']
                elements.append(Paragraph(line, style))
            else:
                elements.append(Paragraph(line, self.styles['CustomNormal']))
        
        doc.build(elements)

# Usage
gen = PdfGenerator()
gen.create_pdf(tailored_resume_text, 'tailored_resume.pdf')
```

#### **E. Database Manager: `database/models.py`**

```python
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Timestamp
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    company = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    job_url = Column(String, unique=True, nullable=False)
    job_source = Column(String)  # 'linkedin', 'indeed', etc.
    job_description = Column(Text)
    job_requirements = Column(Text)
    posted_date = Column(DateTime)
    
    tailored_resume_docx = Column(String)  # file path
    tailored_resume_pdf = Column(String)   # file path
    
    status = Column(String, default='draft')  # draft, reviewed, submitted, etc.
    rezi_processed = Column(Integer, default=0)
    rezi_output_path = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    applied_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Job({self.company} - {self.job_title})>"

class Hyperlink(Base):
    __tablename__ = 'hyperlinks'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, nullable=False)
    job_posting_url = Column(String)
    tailored_resume_url = Column(String)
    rezi_output_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Initialize database
engine = create_engine('sqlite:///database/db.sqlite3')
Base.metadata.create_all(engine)
```

#### **F. Main CLI: `main.py`**

```python
import click
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scrapers.linkedin import LinkedInScraper
from tailor.claude_client import ResumeTC
from generators.docx_generator import DocxGenerator
from generators.pdf_generator import PdfGenerator
from storage.file_manager import FileManager
from database.models import Job, Base
import config

@click.group()
def cli():
    """Resume Automation System CLI"""
    pass

@cli.command()
@click.option('--query', prompt='Job search query', help='e.g., "Senior Python Engineer"')
@click.option('--location', default='Remote', help='Job location')
@click.option('--limit', default=20, help='Number of jobs to scrape')
@click.option('--source', default='linkedin', type=click.Choice(['linkedin', 'indeed', 'glassdoor']))
def scrape(query, location, limit, source):
    """Scrape job postings from job boards."""
    click.echo(f"Scraping {limit} jobs from {source} for '{query}' in {location}...")
    
    if source == 'linkedin':
        scraper = LinkedInScraper(headless=True)
        jobs = scraper.search_jobs(query, location, limit=limit)
        scraper.close()
    elif source == 'indeed':
        # TODO: Implement Indeed scraper
        pass
    
    # Save to DB
    engine = create_engine('sqlite:///database/db.sqlite3')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    for job_data in jobs:
        job = Job(
            company=job_data['company'],
            job_title=job_data['title'],
            job_url=job_data['url'],
            job_source=source,
            job_description=job_data['description'],
        )
        session.add(job)
    
    session.commit()
    click.echo(f"✓ Stored {len(jobs)} jobs in database")

@cli.command()
@click.option('--base-resume', required=True, type=click.Path(exists=True))
@click.option('--batch-size', default=10, help='Resume jobs per batch')
@click.option('--status', default='draft', help='Only tailor jobs with this status')
def tailor_all(base_resume, batch_size, status):
    """Tailor all job postings in the database."""
    with open(base_resume, 'r') as f:
        base_text = f.read()
    
    tailor_client = ResumeTC(api_key=config.CLAUDE_API_KEY, base_resume_text=base_text)
    file_mgr = FileManager(config.RESUME_OUTPUT_PATH)
    
    # Query jobs needing tailoring
    engine = create_engine('sqlite:///database/db.sqlite3')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    jobs_to_tailor = session.query(Job).filter(
        Job.status == status,
        Job.tailored_resume_docx == None
    ).limit(batch_size).all()
    
    click.echo(f"Tailoring {len(jobs_to_tailor)} resumes...")
    
    for job in jobs_to_tailor:
        try:
            click.echo(f"  → {job.company}: {job.job_title}...", nl=False)
            
            # Tailor
            tailored = tailor_client.tailor(
                job_title=job.job_title,
                job_desc=job.job_description,
                job_reqs=job.job_requirements,
            )
            
            # Generate .docx
            docx_gen = DocxGenerator()
            docx_gen.add_resume_content(tailored)
            docx_path = file_mgr.get_path(job.company, job.job_title, format='docx')
            docx_gen.save(docx_path)
            
            # Generate PDF
            pdf_gen = PdfGenerator()
            pdf_path = file_mgr.get_path(job.company, job.job_title, format='pdf')
            pdf_gen.create_pdf(tailored, pdf_path)
            
            # Update DB
            job.tailored_resume_docx = str(docx_path)
            job.tailored_resume_pdf = str(pdf_path)
            job.status = 'reviewed'
            session.commit()
            
            click.echo(" ✓")
        except Exception as e:
            click.echo(f" ✗ Error: {e}")
            session.rollback()

@cli.command()
def export_tracker():
    """Export job tracker as CSV."""
    import pandas as pd
    
    engine = create_engine('sqlite:///database/db.sqlite3')
    query = "SELECT company, job_title, job_url, status, tailored_resume_docx, tailored_resume_pdf, created_at FROM jobs ORDER BY created_at DESC"
    df = pd.read_sql_query(query, engine)
    
    output_path = config.RESUME_OUTPUT_PATH / 'job_tracker.csv'
    df.to_csv(output_path, index=False)
    click.echo(f"✓ Exported {len(df)} jobs to {output_path}")

if __name__ == '__main__':
    cli()
```

### 2.5 Configuration: `config.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Keys
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
REZI_API_KEY = os.getenv('REZI_API_KEY', '')  # Phase 2

# Paths
PROJECT_ROOT = Path(__file__).parent
RESUME_OUTPUT_PATH = PROJECT_ROOT / 'resumes'
DATABASE_PATH = PROJECT_ROOT / 'database' / 'db.sqlite3'

# Scraper settings
SCRAPER_HEADLESS = True
SCRAPER_DELAY_SECONDS = 2  # Rate limiting between requests

# Resume tailoring
CLAUDE_MODEL = 'claude-opus-4-20250203'  # or 'claude-sonnet-4-20250514'
RESUME_CONTEXT = """
Additional context about your career:
- Specialized in distributed systems and cloud architecture
- Led teams of 5–10 engineers
- Open source contributor (Python, Go)
- Passionate about DevOps and infrastructure automation
"""  # Customize with your own context

# Database
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = PROJECT_ROOT / 'logs' / 'automation.log'
```

### 2.6 Environment Setup: `.env`

```bash
# .env (DO NOT commit to Git)
CLAUDE_API_KEY=sk-your-actual-key-here
REZI_API_KEY=  # Add in Phase 2
```

---

## 3. Phase 1 Implementation Timeline

### Week 1: Foundation & Scraping
- [ ] Set up Python project, install dependencies
- [ ] Implement LinkedIn scraper (`scrapers/linkedin.py`)
- [ ] Create database schema and SQLAlchemy models
- [ ] Build `scrape` CLI command
- [ ] Test with 10 job postings

**Deliverable:** `python main.py scrape --query "Senior Engineer" --limit 10`

### Week 2: Resume Tailoring & Output
- [ ] Implement Claude resume tailor (`tailor/claude_client.py`)
- [ ] Build `.docx` generator (`generators/docx_generator.py`)
- [ ] Build PDF generator (`generators/pdf_generator.py`)
- [ ] Create `tailor_all` CLI command
- [ ] Test with 20 jobs, review outputs

**Deliverable:** `python main.py tailor_all --base-resume my_resume.txt --batch-size 20`

### Week 3: Organization & Tracking
- [ ] Implement file manager (`storage/file_manager.py`)
- [ ] Add job tracker CSV export
- [ ] Create simple HTML dashboard (optional)
- [ ] Test full pipeline: scrape → tailor → export
- [ ] Document setup and usage

**Deliverable:** Full pipeline working with 50 jobs; exportable tracker

### Week 4: Polish & Scale
- [ ] Add error handling and retry logic
- [ ] Implement rate limiting for API calls
- [ ] Add logging for debugging
- [ ] Test with 100+ jobs
- [ ] Write setup guide for weekly runs

**Deliverable:** Production-ready Phase 1; can process 100s of jobs/week

---

## 4. Phase 2: Rezi.com Integration (Optional)

### 4.1 Rezi API Wrapper

```python
# tailor/rezi_client.py
import requests
from pathlib import Path

class ReziClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.rezi.io/v1'  # Check actual endpoint
    
    def upload_and_process(self, resume_file_path):
        """
        Upload resume to Rezi, wait for processing, download result.
        Returns path to refined resume.
        """
        with open(resume_file_path, 'rb') as f:
            files = {'file': f}
            resp = requests.post(
                f'{self.base_url}/resumes/analyze',
                headers={'Authorization': f'Bearer {self.api_key}'},
                files=files
            )
        
        result = resp.json()
        job_id = result['job_id']
        
        # Poll for completion
        while True:
            status = requests.get(
                f'{self.base_url}/jobs/{job_id}',
                headers={'Authorization': f'Bearer {self.api_key}'}
            ).json()
            
            if status['status'] == 'completed':
                refined_resume = status['output']['resume']
                # Save to disk
                output_path = resume_file_path.parent / f"{resume_file_path.stem}_rezi.pdf"
                with open(output_path, 'w') as f:
                    f.write(refined_resume)
                return str(output_path)
            
            time.sleep(5)  # Poll every 5 seconds
```

### 4.2 Updated `tailor_all` Command

```python
@cli.command()
@click.option('--rezi', is_flag=True, help='Send to Rezi for refinement')
def tailor_all(base_resume, batch_size, status, rezi):
    """Tailor resumes, optionally refine with Rezi."""
    # ... existing code ...
    
    if rezi:
        rezi_client = ReziClient(api_key=config.REZI_API_KEY)
        for job in jobs_to_tailor:
            # ... tailor as before ...
            
            # Send to Rezi
            docx_path = file_mgr.get_path(...)
            rezi_output = rezi_client.upload_and_process(docx_path)
            job.rezi_output_path = rezi_output
            job.rezi_processed = 1
            session.commit()
```

---

## 5. Phase 3: Auto-Apply (Stretch Goal)

This phase is the most complex. Options:

### 5.1 LinkedIn Easy Apply (via Selenium)
- Automate clicking "Easy Apply" button
- Fill standard form fields (email, phone, etc.)
- Upload tailored resume
- Submit

### 5.2 Zapier/Make Integration
- Create Zap: "When new job is added to DB, apply to job"
- More reliable than Selenium, but $10–15/month

### 5.3 Hybrid: Manual Review + One-Click Submit
- Generate checklist of jobs ready to apply
- One-click button to open job URL + fill form
- Less automation, but higher success rate

---

## 6. Budget & Cost Breakdown

| Item | Cost/Month | Notes |
|------|-----------|-------|
| Claude API | $0–20 | Free tier = 5M tokens/mo; 100 jobs/week = ~250K tokens/week |
| Rezi API | $0–50 | Check free tier; may require subscription for volume |
| Selenium/WebDriver | $0 | Free |
| Zapier (Phase 3) | $10–15 | Only if auto-applying |
| **Total** | **$0–50** | Start free, upgrade as needed |

---

## 7. Security & Best Practices

- **API Keys**: Use `.env` file (add to `.gitignore`)
- **Scraping**: Respect `robots.txt`, use delays, rotate user agents
- **Rate Limiting**: 2–5 second delays between requests
- **Error Handling**: Log failures, allow manual retry
- **Data Backup**: Weekly export of CSV tracker
- **Resume Privacy**: Store locally, don't upload to cloud without encryption

---

## 8. Testing Checklist

- [ ] Scraper extracts job details correctly
- [ ] Claude API tailoring works end-to-end
- [ ] .docx and PDF files generate without errors
- [ ] Database records are created and updated
- [ ] CSV export is complete and readable
- [ ] Full pipeline works with 50+ jobs
- [ ] Error handling doesn't crash the system
- [ ] Logs capture important events

---

## 9. Future Enhancements

- **Multi-Resume Variants**: Maintain 2–3 base resumes for different role types
- **Cover Letter Generation**: Extend to generate tailored cover letters
- **Application Analytics**: Track apply rate, response rate, interview rate
- **Smart Filtering**: Auto-skip jobs below a certain salary/seniority threshold
- **Backup to Cloud**: Auto-upload resumes to Google Drive or S3
- **Slack Notifications**: Get alerts when jobs are tailored and ready to review

---

## 10. Setup Instructions (for running this system)

```bash
# 1. Clone repo (you'll create this from the provided code)
git clone <your-repo>
cd resume-automation

# 2. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your CLAUDE_API_KEY

# 5. Initialize database
python -c "from database.models import engine, Base; Base.metadata.create_all(engine)"

# 6. Test scraper
python main.py scrape --query "Senior Engineer" --limit 5

# 7. Test tailoring
python main.py tailor_all --base-resume base_resume.txt --batch-size 5

# 8. View results
ls resumes/
cat job_tracker.csv
```

---

## 11. Troubleshooting

| Issue | Solution |
|-------|----------|
| LinkedIn blocks scraper | Use rotating proxies, increase delays, or switch to Indeed |
| Claude API rate limit | Upgrade to paid tier, or batch smaller jobs |
| PDF generation fails | Check reportlab install, verify resume text formatting |
| Database locked | Close other connections; use WAL mode (SQLite default) |
| Files not saving | Check permissions on `resumes/` directory |

---

## 12. Questions & Decisions Still Needed

1. **Indeed vs. LinkedIn focus?** LinkedIn is more restrictive; Indeed is friendlier to scrapers.
2. **Manual resume review needed?** Currently set to 'reviewed' status after tailoring; you should spot-check before applying.
3. **Cloud backup?** Google Drive, AWS S3, or local only?
4. **Scheduling?** Cron job for weekly runs, or manual triggering?

---

**End of Specification**
