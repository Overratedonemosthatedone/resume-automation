"""
Configuration for Resume Automation System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

# ============================================================================
# API Keys & Credentials
# ============================================================================
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '').strip() or os.getenv('CLAUDE_API_KEY', '').strip()
CLAUDE_API_KEY = ANTHROPIC_API_KEY  # Backward-compatible alias during migration
REZI_API_KEY = os.getenv('REZI_API_KEY', '')
MAX_RETRIES = 3
RETRY_DELAY = 5.0  # seconds between retries for API calls
BATCH_DELAY = 1.0  # seconds between batch requests


def mask_secret(value: str | None, prefix: int = 12, suffix: int = 4) -> str:
    """Return a short, non-sensitive fingerprint for a secret-like value."""
    if not isinstance(value, str):
        return "<empty>"

    cleaned = value.strip()
    if not cleaned:
        return "<empty>"

    visible_prefix = cleaned[:prefix]
    visible_suffix = cleaned[-suffix:] if len(cleaned) > suffix else cleaned
    return f"len={len(cleaned)} prefix='{visible_prefix}' suffix='{visible_suffix}'"


def load_optional_text(path: Path) -> str:
    """Load a local text file when present, otherwise return an empty string."""
    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8").strip()
# ============================================================================
# File Paths
# ============================================================================
PROJECT_ROOT = Path(__file__).parent
RESUME_OUTPUT_PATH = PROJECT_ROOT / 'resumes'
DATABASE_PATH = PROJECT_ROOT / 'database' / 'db.sqlite3'
LOG_PATH = PROJECT_ROOT / 'logs'
BASE_RESUME_PATH = PROJECT_ROOT / 'base_resume.txt'
CANDIDATE_CONTEXT_PATH = PROJECT_ROOT / 'candidate_context.txt'
JOB_QUEUE_ROOT = PROJECT_ROOT / 'job_queue'
JOB_QUEUE_PENDING_PATH = JOB_QUEUE_ROOT / 'pending'
JOB_QUEUE_PROCESSED_PATH = JOB_QUEUE_ROOT / 'processed'
JOB_QUEUE_FAILED_PATH = JOB_QUEUE_ROOT / 'failed'
JOB_INTAKE_HOST = '127.0.0.1'
JOB_INTAKE_PORT = 8765
JOB_QUEUE_POLL_SECONDS = 2.0

# Create directories if they don't exist
RESUME_OUTPUT_PATH.mkdir(exist_ok=True)
DATABASE_PATH.parent.mkdir(exist_ok=True)
LOG_PATH.mkdir(exist_ok=True)
JOB_QUEUE_PENDING_PATH.mkdir(parents=True, exist_ok=True)
JOB_QUEUE_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
JOB_QUEUE_FAILED_PATH.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Web Scraping Settings
# ============================================================================
SCRAPER_HEADLESS = True  # Run browser in headless mode (faster, quieter)
SCRAPER_DELAY_SECONDS = 2  # Delay between requests (be respectful)
SCRAPER_TIMEOUT = 15  # Page load timeout in seconds
SCRAPER_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# ============================================================================
# Claude API Settings
# ============================================================================
CLAUDE_MODEL = 'claude-haiku-4-5'  # Latest Haiku 4.5 alias
CLAUDE_MAX_TOKENS = 2000  # Max tokens for resume generation

# Optional local candidate context used in tailoring prompts.
# Keep the actual resume content in base_resume.txt and supplemental framing here.
RESUME_CONTEXT = load_optional_text(CANDIDATE_CONTEXT_PATH)

# ============================================================================
# Database Settings
# ============================================================================
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'
DATABASE_ECHO = False  # Set True for SQL debugging

# ============================================================================
# Job Scraping Sources
# ============================================================================
SCRAPER_SOURCES = {
    'linkedin': {
        'enabled': True,
        'base_url': 'https://www.linkedin.com/jobs/search/',
        'rate_limit': 2,  # seconds between requests
        'method': 'selenium',  # Use browser automation
        'note': 'Most reliable, works great with Selenium'
    },
    'indeed': {
        'enabled': True,
        'base_url': 'https://www.indeed.com/jobs',
        'rate_limit': 2,
        'method': 'api',  # Use official Indeed API (requires approval)
        'api_key': os.getenv('INDEED_API_KEY', ''),
        'note': 'Now requires passkey auth. Use official API or stick to LinkedIn.'
    },
    'glassdoor': {
        'enabled': False,  # Disabled by default (more restrictive)
        'base_url': 'https://www.glassdoor.com/Job/jobs.htm',
        'rate_limit': 3,
        'method': 'selenium',
        'note': 'Most restrictive, not recommended'
    },
}

# Default job search parameters
DEFAULT_JOB_SEARCH = {
    'query': 'Senior Software Engineer',
    'location': 'Remote',
    'limit': 20,
    'source': 'linkedin',
}

# ============================================================================
# Resume Generation
# ============================================================================
RESUME_FORMATS = ['docx', 'pdf']  # Generate both formats
DOCX_TEMPLATE = None  # Optional: path to template .docx file
PDF_MARGINS = {
    'top': 0.5,      # inches
    'bottom': 0.5,
    'left': 0.5,
    'right': 0.5,
}
PDF_FONT_SIZE = 10  # points

# ============================================================================
# Rezi.com Integration (Phase 2)
# ============================================================================
REZI_ENABLED = False
REZI_API_ENDPOINT = 'https://api.rezi.io/v1'
REZI_POLL_INTERVAL = 5  # seconds
REZI_TIMEOUT = 300  # max seconds to wait for processing

# ============================================================================
# Application Auto-Submit (Phase 3)
# ============================================================================
AUTO_APPLY_ENABLED = False
AUTO_APPLY_CONFIRM = True  # Require manual confirmation before submitting
AUTO_APPLY_ATTACH_PDF = True  # Attach PDF instead of DOCX

# ============================================================================
# Logging
# ============================================================================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = LOG_PATH / 'automation.log'
LOG_CONSOLE_FORMAT = '<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}'
LOG_FILE_FORMAT = '{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}'
LOG_FORMAT = LOG_FILE_FORMAT  # Backward-compatible alias for older log setup code
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# ============================================================================
# Proxy Settings (for web scraping — optional)
# ============================================================================
# Only needed if you get blocked by job sites
# See CLARIFICATIONS.md for detailed setup

PROXY_ENABLED = False  # Set to True if you get blocked during scraping

PROXY_TYPE = 'none'  # Options: 'none', 'scraper_api', 'bright_data', 'custom'

# ScraperAPI (easiest, recommended if needed)
# Sign up at: https://www.scraperapi.com/
# Cost: $10–50/month
SCRAPER_API_KEY = os.getenv('SCRAPER_API_KEY', '')

# Bright Data (more control)
# Sign up at: https://www.brightdata.com/
# Cost: $10–100+/month
# Format: http://username-sessionid:password@proxy.brightdata.com:33335
BRIGHT_DATA_PROXY_URL = os.getenv('BRIGHT_DATA_PROXY_URL', '')

# Custom proxy
# If using your own proxy service
CUSTOM_PROXY_URL = os.getenv('CUSTOM_PROXY_URL', '')

# Note: Start with PROXY_ENABLED=False. Only enable if you get blocked.
# Most likely you won't need this for Phase 1 if you:
# - Use reasonable delays (2–5 seconds between requests)
# - Don't scrape too aggressively (<100 jobs/day)
# - Mix different job sites (don't overload one)

# ============================================================================
# Google Drive Cloud Backup (optional, Phase 3)
# ============================================================================
# Automatically back up your tailored resumes to Google Drive

GOOGLE_DRIVE_BACKUP_ENABLED = False

# Your Google Drive folder ID (the long string in the folder URL)
# See CLARIFICATIONS.md Section 2 on how to find this
# Format: 1A2B3C4D5E6F7G8H9I0JK1L2M3N4O5P6Q (from: drive.google.com/drive/folders/1A2B3C...)
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')

# Path to Google service account JSON (for API access)
# Only needed if you want automated backup
# See CLARIFICATIONS.md Section 2 for setup instructions
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '')

# ============================================================================
# Indeed API Configuration (if using official API instead of scraping)
# ============================================================================
# Indeed offers an official API, but requires approval
# Request access at: https://opensource.indeedeng.io/api/

INDEED_API_ENABLED = False
INDEED_API_KEY = os.getenv('INDEED_API_KEY', '')

# Recommendation: For Phase 1, use LinkedIn Selenium scraper instead of Indeed.
# Indeed now requires passkey authentication which is harder to automate.
# See CLARIFICATIONS.md Section 1 for detailed information on Indeed alternatives.

# Date/time format for file organization
DATE_FORMAT = '%Y-%m'  # Year-Month folders: 2026-03

# File naming convention
# Available placeholders: {company}, {title}, {date}, {source}
FILE_NAME_TEMPLATE = '{date}_{company}_{title}'

# ============================================================================
# Feature Flags
# ============================================================================
FEATURES = {
    'scraping': True,
    'tailoring': True,
    'docx_generation': True,
    'pdf_generation': True,
    'database_tracking': True,
    'csv_export': True,
    'rezi_integration': False,  # Enable in Phase 2
    'auto_apply': False,  # Enable in Phase 3
    'web_dashboard': False,  # Enable later for visualization
}

# ============================================================================
# Validation
# ============================================================================
# Minimum job requirements to accept
MIN_DESCRIPTION_LENGTH = 200  # characters
MIN_REQUIREMENTS_LENGTH = 100  # characters

# Job filtering (skip jobs matching these patterns)
SKIP_PATTERNS = [
    'visa sponsorship',  # Adjust based on your preferences
]

# Salary range filter (optional)
MIN_SALARY_USD = 0  # Set to 0 to disable filtering
MAX_SALARY_USD = 999999999

# ============================================================================
# External Service Limits
# ============================================================================
LINKEDIN_JOBS_PER_BATCH = 25  # LinkedIn lazy-loads 25 at a time
INDEED_JOBS_PER_BATCH = 50
CLAUDE_API_RATE_LIMIT = 30  # requests/min on free tier
