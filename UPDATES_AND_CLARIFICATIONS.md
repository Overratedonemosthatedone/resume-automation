# Important Updates & Clarifications

## 1. Indeed Switched to Passkeys ⚠️

**What happened:** Indeed now uses passkey authentication (security keys, biometric) instead of traditional username/password login.

**Impact on scraping:**
- ❌ Selenium can't log in with traditional credentials anymore
- ❌ Passkeys require physical interaction (fingerprint, face, security key)
- ✅ But: Indeed public job pages are still scrapable without login

**Solution Options:**

### Option A: Scrape Without Login (RECOMMENDED ✅)
Indeed's public job listings are accessible without authentication. You can still scrape jobs using:

```python
# Example: Scrape Indeed without logging in
from bs4 import BeautifulSoup
import requests
import time

def scrape_indeed_public(query, location='remote', num_jobs=50):
    """
    Scrape Indeed public job listings without authentication.
    This works because job listings are public-facing.
    """
    jobs = []
    start = 0
    
    while len(jobs) < num_jobs:
        url = f"https://www.indeed.com/jobs?q={query}&l={location}&start={start}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job cards
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        
        if not job_cards:
            break
        
        for card in job_cards:
            try:
                title = card.find('h2', class_='jobTitle').text.strip()
                company = card.find('span', class_='companyName').text.strip()
                location_text = card.find('div', class_='companyLocation').text.strip()
                
                # Get job details URL
                job_url = card.find('a', class_='jcs-JobTitle')['href']
                if not job_url.startswith('http'):
                    job_url = 'https://www.indeed.com' + job_url
                
                # Scrape job details page
                detail_response = requests.get(job_url, headers=headers)
                detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                description = detail_soup.find('div', id='jobDescriptionText').text.strip()
                
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location_text,
                    'url': job_url,
                    'description': description,
                    'source': 'indeed'
                })
                
                # Be respectful: rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"Error parsing job card: {e}")
                continue
        
        start += 25
    
    return jobs

# Usage
jobs = scrape_indeed_public("Software Engineer", "Remote", 50)
for job in jobs:
    print(f"{job['company']}: {job['title']}")
```

**Pros:**
- ✅ Works without authentication
- ✅ Public data, legal to scrape
- ✅ No passkey workarounds needed

**Cons:**
- ⚠️ Slower than logged-in scraping (no saved filters)
- ⚠️ Indeed may rate-limit aggressive scrapers

### Option B: Use Indeed's Official API (BEST PRACTICE)

Indeed offers a job search API that's more reliable than scraping:

```python
# Indeed API approach (requires API key)
import requests
import json

class IndeedAPI:
    """Use Indeed's official API for reliable job data"""
    
    def __init__(self, api_key):
        """
        Get API key from: https://opensource.indeedeng.io/api/
        This is Indeed's official job API (free tier available)
        """
        self.api_key = api_key
        self.base_url = "https://api.indeed.com/ads/apisearch"
    
    def search_jobs(self, query, location='', limit=50):
        """Search for jobs using Indeed's API"""
        
        params = {
            'publisher': self.api_key,
            'q': query,
            'l': location,
            'sort': 'date',
            'limit': min(limit, 25),  # API max is 25 per request
            'format': 'json'
        }
        
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        jobs = []
        for result in data.get('results', []):
            jobs.append({
                'title': result.get('jobtitle'),
                'company': result.get('company'),
                'location': result.get('location'),
                'url': result.get('url'),
                'description': result.get('snippet'),
                'posted_date': result.get('date'),
                'source': 'indeed_api'
            })
        
        return jobs

# Usage
api_key = "your-indeed-api-key"
indeed = IndeedAPI(api_key)
jobs = indeed.search_jobs("Senior Engineer", "Remote")
```

**Pros:**
- ✅ Official, approved method
- ✅ Reliable and fast
- ✅ No scraper detection
- ✅ Better data quality

**Cons:**
- ⚠️ Requires API key
- ⚠️ Some limitations on free tier

### Option C: Use Scraper Service (EASIEST)

Use a third-party scraper that handles Indeed automatically:

**Services:**
- **ScraperAPI** ($10–50/mo): https://www.scraperapi.com
- **Bright Data** ($15–100+/mo): https://brightdata.com
- **Oxylabs** ($20+/mo): https://oxylabs.io

```python
# Example: ScraperAPI handles Indeed passkeys automatically
import requests

class ScraperAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.scraperapi.com"
    
    def scrape_url(self, url):
        """ScraperAPI handles all the complexity (passkeys, etc.)"""
        payload = {
            'api_key': self.api_key,
            'url': url,
        }
        response = requests.get(self.base_url, params=payload)
        return response.text

# Usage
scraper = ScraperAPIClient(api_key='your-key')
html = scraper.scrape_url('https://www.indeed.com/jobs?q=engineer')
```

**Pros:**
- ✅ Handles all complexity (passkeys, JavaScript, etc.)
- ✅ Reliable and maintained
- ✅ Can scrape anywhere

**Cons:**
- ⚠️ Monthly cost
- ⚠️ More for heavy scraping

---

## 2. What is Google Drive Folder ID? 📁

**Simple explanation:** A unique identifier that points to a specific folder in your Google Drive.

**What it looks like:**
```
Folder ID: 1A2B3C4D5E6F7G8H9I0JK1L2M3N4O5P6Q
```

**How to find your Google Drive Folder ID:**

### Step 1: Go to Google Drive
Visit: https://drive.google.com

### Step 2: Create or Find a Folder
Create a folder called "Resume Backups" (or use existing)

### Step 3: Open the Folder
Click to open it

### Step 4: Copy the Folder ID from URL
Look at the URL in your browser:
```
https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0JK1L2M3N4O5P6Q
                                       ↑
                         This is your Folder ID
```

Copy everything after `/folders/`

### Step 5: Store in .env
```bash
# .env
GOOGLE_DRIVE_FOLDER_ID=1A2B3C4D5E6F7G8H9I0JK1L2M3N4O5P6Q
```

**Why you'd use it:**
- Auto-backup tailored resumes to Google Drive
- Sync with phone/tablet
- Access resumes anywhere
- Cloud-based archive

**Example usage in your system:**

```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config

class GoogleDriveBackup:
    """Auto-backup resumes to Google Drive"""
    
    def __init__(self, credentials_file, folder_id):
        """
        credentials_file: Download from Google Cloud Console
        folder_id: Get from Google Drive URL
        """
        self.credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.service = build('drive', 'v3', credentials=self.credentials)
        self.folder_id = folder_id
    
    def upload_resume(self, file_path, file_name):
        """Upload a resume file to Google Drive"""
        file_metadata = {
            'name': file_name,
            'parents': [self.folder_id]  # Upload to specific folder
        }
        
        media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return file.get('id')

# Usage
backup = GoogleDriveBackup(
    credentials_file='google-credentials.json',
    folder_id=config.GOOGLE_DRIVE_FOLDER_ID
)
backup.upload_resume('resumes/company_job.docx', 'company_job.docx')
```

**Status in your system:**
- ⚠️ Optional (Phase 2+)
- Not needed to get started
- Useful for backup/access later

---

## 3. Proxy Settings Explained 🌐

**What is a proxy?**
A proxy is a server that stands between you and the target website. It:
- Makes requests on your behalf
- Hides your IP address
- Handles security challenges
- Rotates IPs to avoid blocking

**When would you use proxies?**
- ❌ Scraping LinkedIn (they actively block)
- ✅ Scraping Indeed (if you get rate-limited)
- ✅ Scraping at scale (1000s of jobs)

**Proxy Settings in Your .env:**

```bash
# Option 1: No proxy (start here)
PROXY_URL=
PROXY_USERNAME=
PROXY_PASSWORD=

# Option 2: Single proxy server
PROXY_URL=http://proxy.company.com:8080
PROXY_USERNAME=username
PROXY_PASSWORD=password

# Option 3: ScraperAPI (proxy service)
PROXY_URL=http://proxy-server.scraperapi.com:8001
PROXY_USERNAME=
PROXY_PASSWORD=
```

**How to use proxies in your scraper:**

```python
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
import os

class ProxiedScraper:
    def __init__(self, use_proxy=False):
        self.use_proxy = use_proxy
        self.driver = self._create_driver()
    
    def _create_driver(self):
        """Create Selenium driver with optional proxy"""
        
        if self.use_proxy:
            proxy_url = os.getenv('PROXY_URL')
            proxy_user = os.getenv('PROXY_USERNAME')
            proxy_pass = os.getenv('PROXY_PASSWORD')
            
            # Format proxy with credentials
            if proxy_user and proxy_pass:
                proxy_addr = f"http://{proxy_user}:{proxy_pass}@{proxy_url.replace('http://', '')}"
            else:
                proxy_addr = proxy_url
            
            # Configure proxy
            proxy = Proxy()
            proxy.proxy_type = ProxyType.MANUAL
            proxy.http_proxy = proxy_addr
            proxy.ssl_proxy = proxy_addr
            
            # Create driver with proxy
            options = webdriver.ChromeOptions()
            options.add_argument('--proxy-server=' + proxy_addr)
            
            driver = webdriver.Chrome(options=options)
        else:
            # No proxy
            driver = webdriver.Chrome()
        
        return driver
    
    def scrape_with_proxy(self, url):
        """Scrape a URL through proxy"""
        self.driver.get(url)
        return self.driver.page_source

# Usage
# Without proxy (works for public sites)
scraper = ProxiedScraper(use_proxy=False)

# With proxy (use if getting blocked)
scraper = ProxiedScraper(use_proxy=True)
```

**Popular Proxy Services:**

| Service | Cost | Type | Best For |
|---------|------|------|----------|
| **ScraperAPI** | $10–50/mo | Residential | Resume automation |
| **Bright Data** | $15–100+/mo | Rotating | Heavy scraping |
| **Oxylabs** | $20+/mo | Rotating | LinkedIn, etc. |
| **Free proxies** | $0 | Public | Testing only |

⚠️ **Warning:** Free proxies are slow, unreliable, and potentially unsafe. Use only for testing.

**Recommendation for your system:**
- **Start:** No proxy (public Indeed/Glassdoor are fine)
- **If blocked:** Use ScraperAPI ($10/mo)
- **If scaling:** Use Bright Data or Oxylabs

---

## 4. Updated Configuration for Indeed Passkeys

Add this to your `config.py`:

```python
# ============================================================================
# Indeed Scraping (Updated for Passkeys)
# ============================================================================

# Since Indeed switched to passkeys, use one of these options:

INDEED_SCRAPING_METHOD = 'public'  # Options: 'public', 'api', 'scraper_service'

if INDEED_SCRAPING_METHOD == 'public':
    # Scrape public Indeed job listings (no login needed)
    INDEED_SETTINGS = {
        'enabled': True,
        'base_url': 'https://www.indeed.com/jobs',
        'rate_limit': 2,  # seconds between requests
        'max_retries': 3,
    }

elif INDEED_SCRAPING_METHOD == 'api':
    # Use Indeed's official API (recommended)
    INDEED_API_KEY = os.getenv('INDEED_API_KEY', '')
    INDEED_SETTINGS = {
        'enabled': True,
        'api_key': INDEED_API_KEY,
        'rate_limit': 1,  # API is faster
        'max_jobs_per_request': 25,  # API limit
    }

elif INDEED_SCRAPING_METHOD == 'scraper_service':
    # Use ScraperAPI or similar service
    SCRAPER_API_KEY = os.getenv('SCRAPER_API_KEY', '')
    INDEED_SETTINGS = {
        'enabled': True,
        'service': 'scraperapi',
        'api_key': SCRAPER_API_KEY,
        'rate_limit': 1,  # Service handles rate limiting
    }

# Update .env with these if using API or service:
# INDEED_API_KEY=your-key-here
# SCRAPER_API_KEY=your-key-here
```

---

## 5. Updated .env.example

```bash
# Resume Automation System - Environment Variables

# ============================================================================
# Claude API (REQUIRED)
# ============================================================================
CLAUDE_API_KEY=sk-ant-your-actual-key-here

# ============================================================================
# Web Scraping - Indeed (Choose one method)
# ============================================================================

# Method 1: Public scraping (FREE, recommended for now)
# No keys needed - scrape public job listings

# Method 2: Indeed Official API (FREE tier available)
# Get key from: https://opensource.indeedeng.io/api/
INDEED_API_KEY=

# Method 3: ScraperAPI (Handles passkeys automatically)
# Get key from: https://www.scraperapi.com/
SCRAPER_API_KEY=

# ============================================================================
# LinkedIn (Passkeys also apply here - recommend skipping)
# ============================================================================
# LinkedIn scraping is heavily restricted. Use Indeed instead.
# If you must: use SCRAPER_API_KEY above

# ============================================================================
# Google Drive Backup (Optional - Phase 2+)
# ============================================================================
# Get folder ID from Google Drive URL: /drive/folders/YOUR_ID_HERE
GOOGLE_DRIVE_FOLDER_ID=

# Google Cloud credentials file (download from Google Cloud Console)
# GOOGLE_CREDENTIALS_FILE=google-credentials.json

# ============================================================================
# Proxy Settings (Optional - use if getting blocked)
# ============================================================================
# Most users won't need this. Start without proxy.

# Single proxy server
PROXY_URL=

# Proxy credentials (if required)
PROXY_USERNAME=
PROXY_PASSWORD=

# Or use a service like ScraperAPI as proxy
# PROXY_URL=http://proxy-server.scraperapi.com:8001

# ============================================================================
# Rezi.com (Phase 2 - Optional)
# ============================================================================
REZI_API_KEY=

# ============================================================================
# Email (Phase 3+ - Optional auto-apply)
# ============================================================================
EMAIL_ADDRESS=
EMAIL_PASSWORD=

# ============================================================================
# Cloud Storage Backup (Optional)
# ============================================================================
# AWS S3
AWS_ACCESS_KEY=
AWS_SECRET_KEY=
AWS_BUCKET_NAME=

# ============================================================================
# Application Settings
# ============================================================================
DEBUG_MODE=False
LOG_LEVEL=INFO
```

---

## 🎯 Summary & Recommendations

### For Indeed Passkeys:
✅ **Best:** Use public scraping (no auth needed) + rate limiting
✅ **Better:** Use Indeed's official API (reliable, approved)
✅ **Alternative:** Use ScraperAPI ($10/mo, handles everything)
❌ **Avoid:** Trying to bypass passkeys (brittle, against ToS)

### For Google Drive:
- Get folder ID from Google Drive URL
- Store in `.env` as `GOOGLE_DRIVE_FOLDER_ID`
- Implement in Phase 2 (optional backup)

### For Proxies:
- Start without proxies (public sites work fine)
- Use ScraperAPI ($10/mo) if you get rate-limited
- Only use if necessary to avoid cost

---

## 📝 Updated Setup Instructions

```bash
# 1. Get your API keys (if needed)

# For public Indeed scraping: No key needed! ✅

# For Indeed API: 
# Visit https://opensource.indeedeng.io/api/
# Get free API key

# For ScraperAPI:
# Visit https://www.scraperapi.com/
# Get free trial or $10/mo plan

# 2. Create .env
cp .env.example .env

# 3. Add your keys
# For starting: only need CLAUDE_API_KEY

# 4. Edit config.py
# Set: INDEED_SCRAPING_METHOD = 'public'  # Start here

# 5. Test
python3 test_scraper.py
```

**That's it! You're ready to scrape Indeed without worrying about passkeys.**

---

**Key Takeaway:** Indeed's passkey switch isn't a blocker for your system. Just use public scraping or their API instead of trying to log in. Even simpler than before!
