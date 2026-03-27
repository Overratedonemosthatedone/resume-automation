# Technical Clarifications & Setup Guide

## 1. Indeed Switched to Passkeys — What to Do

### The Problem
Indeed now requires **passkey authentication** (passwordless login), which makes traditional Selenium scraping much harder because:
- You can't programmatically enter credentials
- Passkeys require biometric/device confirmation
- Browser automation can't bypass this security layer

### Your Options (Ranked by Feasibility)

#### **Option A: Use Indeed's Official API (Recommended) ⭐**
**Status:** Available, but limited access

**Setup:**
1. Visit: https://opensource.indeedeng.io/api/
2. Request API access (for developers/automation)
3. Wait for approval (1–5 business days)
4. Get API key for job searching

**Pros:**
- Official, supported method
- No scraping detection issues
- More reliable

**Cons:**
- Limited query flexibility
- Rate limits apply
- Approval process

**Code example (once approved):**
```python
import requests

class IndeedApiScraper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.indeed.com/ads/apisearch'
    
    def search_jobs(self, query, location, limit=50):
        params = {
            'publisher': self.api_key,
            'q': query,
            'l': location,
            'limit': limit,
            'format': 'json'
        }
        resp = requests.get(self.base_url, params=params)
        jobs = resp.json()['results']
        return jobs
```

---

#### **Option B: Use LinkedIn Instead (Recommended)**
**Status:** Works with Selenium + delays

LinkedIn doesn't use passkeys and is more scraper-friendly than Indeed (ironically).

**Modified scrapers/linkedin.py:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class LinkedInScraper:
    def __init__(self, headless=True):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        
        # Mimic real browser behavior
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(20)
    
    def search_jobs(self, query, location='Remote', limit=50):
        """Search LinkedIn jobs and extract details"""
        base_url = 'https://www.linkedin.com/jobs/search/'
        params = f'?keywords={query}&location={location}'
        
        self.driver.get(base_url + params)
        time.sleep(3)  # Let page load
        
        jobs = []
        
        try:
            # Find all job cards
            job_cards = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'base-card'))
            )
            
            for card in job_cards[:limit]:
                try:
                    # Extract job details from card
                    title = card.find_element(By.CSS_SELECTOR, 'h3').text
                    company = card.find_element(By.CSS_SELECTOR, '.base-search-card__subtitle').text
                    job_url = card.get_attribute('href')
                    
                    # Click card to load full description
                    card.click()
                    time.sleep(1.5)
                    
                    # Extract description
                    try:
                        desc_elem = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.show-more-less-html__markup'))
                        )
                        description = desc_elem.text
                    except:
                        description = "See full posting on LinkedIn"
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'url': job_url,
                        'description': description,
                        'source': 'linkedin'
                    })
                    
                except Exception as e:
                    print(f"Error parsing job card: {e}")
                    continue
        
        except Exception as e:
            print(f"Error searching jobs: {e}")
        
        return jobs
    
    def close(self):
        self.driver.quit()

# Usage
scraper = LinkedInScraper(headless=True)
jobs = scraper.search_jobs('Senior Software Engineer', 'Remote', limit=20)
scraper.close()
```

**Key improvements:**
- `WebDriverWait` instead of hard `sleep()` for faster execution
- Mimics real user behavior (delays between clicks)
- Extracts full job description by clicking into cards
- Proper exception handling

---

#### **Option C: Use a Third-Party Scraping Service**
**Status:** Works, but costs money

Services that handle Indeed + other boards:
- **ScraperAPI**: $10–50/month for rotating proxies + parsing
- **Bright Data**: $10–100/month for residential proxies
- **RapidAPI Job Scraping APIs**: $10–30/month pre-built endpoints

**Code example (using ScraperAPI):**
```python
import requests

class ThirdPartyScraper:
    def __init__(self, scraper_api_key):
        self.api_key = scraper_api_key
        self.base_url = 'http://api.scraperapi.com'
    
    def search_indeed_jobs(self, query, location):
        """Use ScraperAPI to bypass Indeed's anti-scraping"""
        url = f'https://www.indeed.com/jobs?q={query}&l={location}'
        
        params = {
            'api_key': self.api_key,
            'url': url,
            'render': 'false'  # Set to 'true' if JavaScript rendering needed
        }
        
        resp = requests.get(self.base_url, params=params)
        # Parse the HTML response
        return resp.text
```

---

### **My Recommendation for Your Project**

**Best approach:**
1. **Primary:** LinkedIn (Selenium scraper works great)
2. **Secondary:** Google for job URLs, then visit indeed.com directly (read public posting, no passkey needed for viewing)
3. **Backup:** Request Indeed API access (takes 1 week, then very reliable)
4. **Optional:** Use ScraperAPI if budget allows ($10–20/month)

**Update config.py:**
```python
SCRAPER_SOURCES = {
    'linkedin': {
        'enabled': True,
        'method': 'selenium',  # Use Selenium browser automation
        'rate_limit': 2,
    },
    'indeed': {
        'enabled': True,
        'method': 'api',  # Use official Indeed API (requires approval)
        'rate_limit': 1,
        'api_key': os.getenv('INDEED_API_KEY', ''),
    },
    'glassdoor': {
        'enabled': False,
        'method': 'selenium',
        'rate_limit': 3,
    },
}
```

---

## 2. Google Drive Folder ID — What It Is & How to Get It

### What Is It?
A **unique identifier** for a folder in Google Drive. It's a long alphanumeric string that tells Google Drive which folder to access when uploading/accessing files.

### Why You Need It
For backing up your tailored resumes to Google Drive automatically:
```python
# Example: Auto-backup resumes to Google Drive
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

folder_id = '1A2B3C4D5E6F7G8H9I0J...'  # Your Google Drive folder ID

# Upload file to that folder
file_metadata = {
    'name': 'my_tailored_resume.pdf',
    'parents': [folder_id]
}
media = MediaFileUpload('tailored_resume.pdf', mimetype='application/pdf')
service.files().create(body=file_metadata, media_body=media, fields='id').execute()
```

### How to Find Your Google Drive Folder ID

**Method 1: From the URL (Easiest)**

1. Open Google Drive: https://drive.google.com
2. Create a new folder (right-click → New Folder)
3. Name it `Resume Automation Backups`
4. Open the folder
5. Look at the URL in your browser:

```
https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0JK1L2M3N4O5P6Q
                                        ↑
                                 This is the Folder ID
                    (Everything after /folders/)
```

**Copy the long string after `/folders/`** — that's your folder ID.

**Method 2: Using Google Drive API**

```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Set up Google Drive API (requires service account JSON)
credentials = Credentials.from_service_account_file('service_account.json')
service = build('drive', 'v3', credentials=credentials)

# Find folder by name
results = service.files().list(
    q="name='Resume Automation Backups' and mimeType='application/vnd.google-apps.folder'",
    spaces='drive',
    fields='files(id, name)'
).execute()

folder_id = results['files'][0]['id'] if results['files'] else None
print(f"Folder ID: {folder_id}")
```

### How to Set Up Google Drive Backup (Optional, Phase 3)

**Step 1: Create a service account**
1. Visit: https://console.cloud.google.com/
2. Create a new project: "Resume Automation"
3. Enable Google Drive API
4. Go to Service Accounts (in left menu)
5. Create new service account
6. Create a JSON key for the service account
7. Download the JSON file and save as `service_account.json`

**Step 2: Share the folder with the service account**
1. Get the service account email from the JSON file (looks like: `resume-bot@my-project.iam.gserviceaccount.com`)
2. Open your `Resume Automation Backups` folder in Google Drive
3. Click "Share" → Add the service account email → Give it Editor access

**Step 3: Add to config.py**
```python
GOOGLE_DRIVE_FOLDER_ID = '1A2B3C4D5E6F7G8H9I0JK1L2M3N4O5P6Q'  # Your folder ID
GOOGLE_DRIVE_BACKUP_ENABLED = False  # Set to True when ready

# Optional: Auto-backup after generating resumes
AUTO_BACKUP_TO_GOOGLE_DRIVE = False
```

**Step 4: Add backup code to document_generators.py**
```python
def backup_to_google_drive(file_path, folder_id, service_account_json):
    """Optional: Back up generated resume to Google Drive"""
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    
    credentials = Credentials.from_service_account_file(service_account_json)
    service = build('drive', 'v3', credentials=credentials)
    
    file_metadata = {
        'name': Path(file_path).name,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(file_path, mimetype='application/pdf')
    service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    logger.info(f"✓ Backed up to Google Drive: {file_path}")
```

---

## 3. Proxy URL / Proxy Settings — What They Are & Why You Need Them

### What Is a Proxy?

A **proxy server** acts as an intermediary between your computer and the internet. Instead of visiting a website directly, your traffic goes through the proxy:

```
You → Proxy Server → Indeed.com
                   (hides your IP)
```

### Why You'd Need Proxies for Web Scraping

**The Problem:**
- When you scrape LinkedIn/Indeed aggressively, they see repeated requests from your IP
- They flag/block you: `Error 429 Too Many Requests` or `Access Denied`
- Your ISP IP gets blacklisted

**The Solution:**
- Use rotating proxies that change your apparent IP address
- Each request looks like it's from a different user
- Websites can't easily block you

### Types of Proxies

| Type | Speed | Cost | Reliability | Best For |
|------|-------|------|-------------|----------|
| **Free Proxies** | Slow | $0 | Poor (50% fail) | Testing only |
| **Residential Proxies** | Fast | $10–100/mo | Excellent | Production scraping |
| **Datacenter Proxies** | Very Fast | $5–20/mo | Good | Low-detection targets |
| **VPN** | Medium | $5–15/mo | Good | Privacy, not scraping |

### Popular Proxy Services

#### **Option 1: ScraperAPI (Easiest, Recommended)**
You don't have to manage proxies—they handle it for you.

**Cost:** $10–50/month

**How it works:**
```python
import requests

# ScraperAPI handles proxy rotation automatically
url = 'https://www.linkedin.com/jobs/search/'
params = {
    'api_key': 'your-scraper-api-key',
    'url': url,
    'render': 'false'  # false for simple HTML, true for JavaScript rendering
}

response = requests.get('http://api.scraperapi.com', params=params)
print(response.text)  # Already parsed, proxy handling is transparent
```

---

#### **Option 2: Bright Data (More Control)**
**Cost:** $10–100+/month (pay as you go)

**Setup:**
1. Visit: https://www.brightdata.com/
2. Sign up for residential proxies
3. Create a proxy list
4. Get proxy URL (looks like: `http://username-sessionid:password@proxy.provider.com:port`)

**How to use in Selenium:**
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

proxy_url = 'http://user-sessionid:pass@proxy.brightdata.com:33335'

options = Options()
options.add_argument(f'--proxy-server={proxy_url}')

driver = webdriver.Chrome(options=options)
driver.get('https://www.linkedin.com')
```

**How to use in requests:**
```python
import requests

proxy_url = 'http://user-sessionid:pass@proxy.brightdata.com:33335'
proxies = {
    'http': proxy_url,
    'https': proxy_url
}

response = requests.get('https://www.indeed.com/jobs', proxies=proxies)
```

---

#### **Option 3: Do It Yourself (Not Recommended)**
Use free or cheap proxies + rotation. High maintenance, unreliable.

```python
import requests

# List of free proxies (unreliable, high failure rate)
proxy_list = [
    'http://123.45.67.89:8080',
    'http://98.76.54.32:3128',
    # ... many more ...
]

import random
proxy = random.choice(proxy_list)
proxies = {'http': proxy, 'https': proxy}

try:
    response = requests.get('https://indeed.com', proxies=proxies, timeout=5)
except:
    # Try next proxy on failure
    pass
```

---

### Proxy Configuration in Your System

**Update config.py:**
```python
# ============================================================================
# Proxy Settings (for web scraping)
# ============================================================================

PROXY_ENABLED = False  # Set to True to use proxies

PROXY_TYPE = 'none'  # 'none', 'scraper_api', 'bright_data', 'custom'

# ScraperAPI (easiest)
SCRAPER_API_KEY = os.getenv('SCRAPER_API_KEY', '')

# Bright Data (more control)
BRIGHT_DATA_PROXY_URL = os.getenv('BRIGHT_DATA_PROXY_URL', '')
# Format: http://username-sessionid:password@proxy.brightdata.com:33335

# Custom proxy
CUSTOM_PROXY_URL = os.getenv('CUSTOM_PROXY_URL', '')

# Rotating proxy list (if using multiple proxies)
PROXY_LIST = [
    'http://proxy1.com:8080',
    'http://proxy2.com:8080',
    # ...
]
```

**Update .env:**
```bash
# Proxy Settings
SCRAPER_API_KEY=your-scraper-api-key-here
BRIGHT_DATA_PROXY_URL=http://user-sessionid:pass@proxy.brightdata.com:33335
CUSTOM_PROXY_URL=http://your-proxy.com:8080
```

**Updated Selenium scraper with proxy support:**
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import config

class LinkedInScraper:
    def __init__(self, headless=True, use_proxy=False):
        options = Options()
        
        if headless:
            options.add_argument('--headless')
        
        # Add proxy if enabled
        if use_proxy and config.PROXY_ENABLED:
            if config.PROXY_TYPE == 'bright_data':
                proxy_url = config.BRIGHT_DATA_PROXY_URL
                options.add_argument(f'--proxy-server={proxy_url}')
                logger.info(f"Using Bright Data proxy")
            elif config.PROXY_TYPE == 'custom':
                proxy_url = config.CUSTOM_PROXY_URL
                options.add_argument(f'--proxy-server={proxy_url}')
                logger.info(f"Using custom proxy: {proxy_url}")
        
        options.add_argument('--no-sandbox')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(20)
    
    def search_jobs(self, query, location='Remote', limit=50):
        # ... rest of scraper code ...
        pass

# Usage with proxy
scraper = LinkedInScraper(headless=True, use_proxy=True)
jobs = scraper.search_jobs('Senior Engineer', limit=20)
scraper.close()
```

---

### Do You Actually Need Proxies?

**For your Phase 1 project:**

- ✅ **Not strictly necessary if:**
  - You're scraping <50 jobs/week
  - Using reasonable delays (2–5 sec between requests)
  - Mixing LinkedIn + Indeed (don't overload one site)
  - You have a residential ISP (not flagged already)

- ❌ **You'll need proxies if:**
  - Scraping 100+ jobs/day (very aggressive)
  - Getting blocked frequently (HTTP 429, 403)
  - Using multiple accounts on same site
  - Operating from datacenter/VPS

**Recommendation:**
1. **Start without proxies** (save $10–20/month)
2. **If you get blocked**, upgrade to ScraperAPI ($10/mo)
3. **If still having issues**, switch to Indeed API or LinkedIn official

---

## Quick Summary

| Question | Answer |
|----------|--------|
| **Indeed passkeys?** | Use LinkedIn instead (works great with Selenium) or request Indeed API access |
| **Google Drive Folder ID?** | The string after `/folders/` in the Google Drive URL. Needed for cloud backup (Phase 3) |
| **Proxy URL?** | `http://user:pass@proxy.com:port` — only needed if you get blocked during scraping |

---

## Action Items

### Now (Phase 1 Start):
- [ ] Use **LinkedIn** for scraping (most reliable)
- [ ] Set `PROXY_ENABLED = False` in config.py (save money)
- [ ] Skip Google Drive backup (Phase 3 feature)

### Later (If Needed):
- [ ] If Indeed needed: Request API access at https://opensource.indeedeng.io/api/
- [ ] If getting blocked: Add ScraperAPI ($10/mo)
- [ ] If backing up: Set up Google Drive folder + service account

---

**Bottom line:** For your Phase 1 project, **just use LinkedIn + sensible delays**. No proxies or Google Drive needed. Keep it simple! 🎯
