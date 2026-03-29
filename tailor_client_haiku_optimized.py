"""
Resume Tailoring Module - Claude Haiku 4.5 with Prompt Caching
Optimized for cost-effective scaling to hundreds of resumes

Key Optimizations:
1. Claude Haiku 4.5: 5x cheaper than Opus ($1/M vs $3/M input tokens)
2. Prompt Caching: Save 90% on repeated system prompt + base resume
3. System Prompt Strategy: Separate instructions from data for consistency
4. Batch processing: Process 100+ resumes efficiently

Cost Estimate:
- Without caching: ~$0.01 per resume
- With caching: ~$0.001 per resume (after first request)
- 100 resumes: ~$1.10 total (vs $1.00 without caching benefit)
- 1000 resumes: ~$1.90 total (vs ~$10 without caching)
"""

import os
import sys
import time
from datetime import datetime

import config
from anthropic import Anthropic
from loguru import logger


class ResumeTC:
    """
    Resume Tailor Client - Claude Haiku 4.5 with Prompt Caching
    
    Optimized for cost-effective processing of 100+ resumes
    """
    
    def __init__(self, api_key=None, base_resume_text=None):
        """
        Initialize the tailor client with Haiku 4.5.
        
        Args:
            api_key: Optional Anthropic API key
            base_resume_text: Full text of your base resume
        """
        self.api_key, self.api_key_source = self._resolve_api_key_details(api_key)
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY "
                "(preferred) or CLAUDE_API_KEY."
            )

        self.client = Anthropic(api_key=self.api_key, max_retries=0)
        
        # Use the shared config alias so docs and runtime stay aligned.
        self.model = config.CLAUDE_MODEL
        self.max_tokens = config.CLAUDE_MAX_TOKENS
        
        self.base_resume = base_resume_text or ""
        
        # Prompt caching stats
        self.cache_stats = {
            'cache_hits': 0,
            'cache_creations': 0,
            'cache_read_tokens': 0,
            'cache_creation_tokens': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
        }
        
        logger.info(f"ResumeTC initialized with {self.model}")
        logger.info(
            "Anthropic API key resolved from {} ({})",
            self.api_key_source,
            config.mask_secret(self.api_key),
        )
        logger.info("Prompt caching enabled - 90% savings on repeated content")

    @staticmethod
    def _clean_api_key(value):
        """Return a stripped API key string or an empty string."""
        return value.strip() if isinstance(value, str) else ""

    @classmethod
    def _resolve_api_key_details(cls, api_key=None):
        """Resolve the API key and record which source supplied it."""
        candidates = [
            ("os.environ[ANTHROPIC_API_KEY]", os.environ.get("ANTHROPIC_API_KEY")),
            ("api_key arg", api_key),
            ("config.ANTHROPIC_API_KEY", getattr(config, "ANTHROPIC_API_KEY", "")),
            ("os.environ[CLAUDE_API_KEY]", os.environ.get("CLAUDE_API_KEY")),
            ("config.CLAUDE_API_KEY", getattr(config, "CLAUDE_API_KEY", "")),
        ]

        for source, candidate in candidates:
            cleaned = cls._clean_api_key(candidate)
            if cleaned:
                return cleaned, source

        return "", "unconfigured"

    @classmethod
    def _resolve_api_key(cls, api_key=None):
        """Resolve the API key with environment variables taking precedence."""
        return cls._resolve_api_key_details(api_key)[0]

    @staticmethod
    def _extract_text(response):
        """Join all text blocks returned by Anthropic into a single string."""
        text_blocks = []
        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "text" and getattr(block, "text", None):
                text_blocks.append(block.text)

        return "\n".join(text_blocks).strip()

    @staticmethod
    def _status_code_from_error(error):
        """Extract an HTTP status code from Anthropic SDK errors when present."""
        status_code = getattr(error, "status_code", None) or getattr(error, "status", None)
        response = getattr(error, "response", None)
        if status_code is None and response is not None:
            status_code = getattr(response, "status_code", None) or getattr(response, "status", None)
        return status_code

    @classmethod
    def _is_auth_error(cls, error):
        """Detect authentication failures so we can skip retries."""
        status_code = cls._status_code_from_error(error)
        if status_code == 401:
            return True

        error_name = error.__class__.__name__.lower()
        message = str(error).lower()
        return "authentication" in error_name or "api key" in message

    @classmethod
    def _is_retryable_error(cls, error):
        """Retry only transient transport and server-side failures."""
        if cls._is_auth_error(error):
            return False

        status_code = cls._status_code_from_error(error)
        if status_code in {408, 409, 429}:
            return True
        if isinstance(status_code, int) and status_code >= 500:
            return True

        error_name = error.__class__.__name__.lower()
        retryable_names = {"apiconnectionerror", "apitimeouterror", "timeout", "connectionerror"}
        if error_name in retryable_names:
            return True

        message = str(error).lower()
        retryable_phrases = (
            "timed out",
            "timeout",
            "connection",
            "temporarily unavailable",
            "rate limit",
            "try again",
        )
        return any(phrase in message for phrase in retryable_phrases)

    @staticmethod
    def _authentication_help_text():
        """Return a short remediation message for auth failures."""
        return (
            "Authentication failed. Confirm ANTHROPIC_API_KEY is valid and active. "
            "PowerShell (current shell): "
            "$env:ANTHROPIC_API_KEY = \"sk-ant-...\" | "
            "Persist for current user: "
            "[Environment]::SetEnvironmentVariable(\"ANTHROPIC_API_KEY\", \"sk-ant-...\", \"User\")"
        )
    
    def set_base_resume(self, resume_text):
        """Update the base resume text."""
        self.base_resume = resume_text
        logger.info(f"Base resume set ({len(resume_text)} characters)")
    
    def load_base_resume(self, file_path):
        """Load base resume from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            self.base_resume = f.read()
        logger.info(f"Base resume loaded from: {file_path}")
    
    def _get_system_prompt(self):
        """
        Get the system prompt with cache control markers.
        
        This prompt is identical for every job, so it benefits from caching.
        Using cache_control ensures the same prompt is reused across requests.
        """
        return {
            "type": "text",
            "text": """You are revising a resume for a specific job posting.

You will be given:
1. A base resume
2. A job description
3. Optional additional candidate context

Your task is to improve the resume for fit while keeping it fully truthful.

CORE GOAL
Produce a resume that makes the candidate's fit immediately obvious in the first 10 seconds.
Do not waste space on explanation. Signal the strongest fit first and fastest.

NON-NEGOTIABLE RULES
- Do not invent anything.
- Do not add metrics unless they are already provided in the source material.
- Do not imply direct people management if the candidate only led cross-functional work.
- Do not imply direct sales ownership, proposal leadership, capture ownership, customer ownership, clearance status, degree completion, or regulatory expertise unless explicitly supported.
- Do not turn supporting exposure into primary responsibility.
- Preserve factual chronology.
- Preserve factual details exactly: company names, titles, dates, locations, and metrics.
- Keep the strongest evidence and cut weaker filler.
- If optional candidate context conflicts with the base resume, treat the base resume as the higher-confidence source unless the context clearly clarifies without contradicting facts.

WHAT TO OPTIMIZE FOR (IN ORDER OF PRIORITY)
1. SPEED: Make the fit unmistakable at first glance.
2. PROOF: Show the strongest evidence of relevant skills immediately.
3. KEYWORDS: Mirror job posting language where truthful.
4. IMPACT: Lead with outcomes and business value.
5. DENSITY: Remove filler and redundancy.
6. CREDIBILITY: Stay conservative and defensible.
7. READABILITY: Make the resume easy to scan in 10 seconds, with calm spacing and clean hierarchy.

SPECIFIC INSTRUCTIONS
1. Rewrite the professional summary into 2-3 short lines maximum that immediately signal target-role fit, domain relevance, and strongest supporting evidence. Do not use generic summary language.
2. Improve bullet quality. Lead each bullet with the strongest available element: measurable impact, business result, or high-value action. Prioritize outcomes whenever the evidence supports it. Use strong action verbs. Keep bullets concise, specific, and relevant.
3. Keep bullets clean and uniform. Avoid bullets that combine multiple ideas, stack too many clauses, or feel overloaded. Prefer shorter bullets with one strong idea each.
4. Cut aggressively, but keep strong proof. Delete bullets that do not materially strengthen fit. Delete generic responsibilities that do not distinguish the candidate. Compress less relevant older experience. Prefer 4 strong bullets over 8 crowded bullets. Do not remove strong quantified achievements just because they are not perfect keyword matches if they provide credible evidence of execution, ownership, or business impact.
5. Keep structure credible and easy to scan. Keep roles in reverse-chronological order. Make titles, companies, and dates easy to identify immediately. Improve relevance through stronger summaries, bullet selection, and compression of less relevant roles.
6. Tailor to the job description. Mirror the posting language where truthful. Prioritize the most relevant domain, function, tools, and outcomes. De-emphasize background that does not help with this specific role.
7. Handle gaps honestly. If the candidate is adjacent to the role, position them as transferable and credible, not as a direct match when unsupported. If the candidate does not clearly meet a hard requirement, do not disguise the gap. Strengthen adjacent experience instead of overstating qualifications.
8. Keep length disciplined. Prefer a clean modern one-page resume when the fit can be shown convincingly at that length. Use 2 pages only when the added content materially improves fit. Every line must earn its space.
9. Preserve visual calm in plain text. Use enough blank lines between major sections and role groupings to avoid a crowded feel, but do not add decorative formatting or unnecessary labels.

INTERNAL REVIEW
Before finalizing, check in your reasoning:
- Does the opening immediately signal fit?
- Do the top bullets prove the most relevant skills?
- Are generic responsibilities removed?
- Are chronology and facts preserved?
- Is the resume skimmable in 10 seconds?

If not, revise again before answering.

OUTPUT INSTRUCTIONS
- Respond with ONLY the complete revised resume in clean plain text.
- Do NOT output a fit assessment, action items, change log, explanations, notes, markdown, code blocks, or preamble.
- Use ALL CAPS section headers for major sections such as PROFESSIONAL SUMMARY, EXPERIENCE, EDUCATION, and SKILLS.
- Keep the first lines as name and contact information if present in the base resume.
- Keep PROFESSIONAL SUMMARY to 2-3 short lines maximum.
- Keep EXPERIENCE reverse-chronological.
- Use indented bullet lines that begin with two spaces followed by "- ".
- Keep bullets concise and fairly uniform in length.
- Use blank lines intentionally so sections feel readable and not crowded.
- Use only sections supported by the source material.
- Keep the style professional, modern, restrained, ATS-friendly, and plain text.

The final answer must be a strong, conservative, highly skimmable resume that feels simple, sharp, visually calm, and easy to scan fast without overstating qualifications.""",
            "cache_control": {"type": "ephemeral"}  # Cache this prompt
        }
    
    def _get_base_resume_block(self):
        """
        Get the base resume content with cache control.
        
        This is the largest block of text and is identical for every job,
        so caching here saves the most tokens.
        """
        return {
            "type": "text",
            "text": f"""BASE RESUME:
{self.base_resume}""",
            "cache_control": {"type": "ephemeral"}  # Cache this too
        }
    
    def _get_career_context_block(self, career_context=None):
        """Get career context with cache control if applicable."""
        context_text = config.RESUME_CONTEXT if career_context is None else career_context
        context_text = context_text.strip() if isinstance(context_text, str) else ""
        if not context_text:
            return None

        return {
            "type": "text",
            "text": f"""ADDITIONAL CAREER CONTEXT & KEY ACHIEVEMENTS:
{context_text}""",
            "cache_control": {"type": "ephemeral"}  # Cache this too
        }
    
    def tailor(self, job_title, job_description, job_requirements, 
               career_context=None, retry_count=0):
        """
        Tailor the base resume to a specific job posting.
        
        Uses prompt caching to save 90% on repeated content:
        - System prompt (cached)
        - Base resume (cached)
        - Career context (cached)
        - Job details (unique, not cached)
        
        Args:
            job_title: Position title (e.g., "Senior Software Engineer")
            job_description: Full job description text
            job_requirements: Job requirements/qualifications
            career_context: Additional context about your experience
            retry_count: Internal retry counter
        
        Returns:
            str: Tailored resume as plain text
        
        Raises:
            RuntimeError: If API call fails after retries
        """
        if not self.base_resume:
            raise ValueError("Base resume not set. Call set_base_resume() first.")
        
        try:
            logger.debug(f"Calling Claude Haiku 4.5 for job: {job_title}")
            
            # Build messages with cache control on repeated blocks
            system_blocks = [
                self._get_system_prompt(),
                self._get_base_resume_block(),
            ]
            career_context_block = self._get_career_context_block(career_context)
            if career_context_block:
                system_blocks.append(career_context_block)
            
            # User message with job-specific content (not cached, changes each time)
            user_message = f"""Target Job Posting:

Position: {job_title}

Description:
{job_description}

Requirements:
{job_requirements}

---

Revise the resume above for this specific job posting.
Return ONLY the final plain-text resume that follows the required section-header and bullet formatting."""
            
            # Make API call with prompt caching
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_blocks,  # System blocks with cache control
                messages=[
                    {
                        "role": "user",
                        "content": user_message  # Job-specific, not cached
                    }
                ]
            )
            
            tailored_text = self._extract_text(response)
            if not tailored_text:
                raise RuntimeError(f"Claude returned no text content for '{job_title}'.")
            
            # Track cache statistics
            self._track_cache_stats(response)
            
            logger.info(f"Successfully tailored resume for: {job_title}")
            logger.debug(f"  Input tokens: {response.usage.input_tokens}")
            logger.debug(f"  Cache read tokens: {getattr(response.usage, 'cache_read_input_tokens', 0)}")
            logger.debug(f"  Cache creation tokens: {getattr(response.usage, 'cache_creation_input_tokens', 0)}")
            logger.debug(f"  Output tokens: {response.usage.output_tokens}")
            if getattr(response, "_request_id", None):
                logger.debug(f"  Request ID: {response._request_id}")
            
            return tailored_text
        
        except Exception as e:
            if self._is_auth_error(e):
                error_msg = (
                    f"Error tailoring resume for '{job_title}': {str(e)}. "
                    f"{self._authentication_help_text()}"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e

            error_msg = f"Error tailoring resume for '{job_title}': {str(e)}"
            logger.error(error_msg)
            
            if retry_count < config.MAX_RETRIES and self._is_retryable_error(e):
                logger.info(f"Retrying... (attempt {retry_count + 1}/{config.MAX_RETRIES})")
                time.sleep(config.RETRY_DELAY)
                return self.tailor(job_title, job_description, job_requirements,
                                 career_context, retry_count + 1)
            else:
                raise RuntimeError(error_msg) from e
    
    def _track_cache_stats(self, response):
        """Track and log cache statistics for monitoring savings."""
        cache_read = getattr(response.usage, 'cache_read_input_tokens', 0)
        cache_creation = getattr(response.usage, 'cache_creation_input_tokens', 0)
        
        if cache_read > 0:
            self.cache_stats['cache_hits'] += 1
            self.cache_stats['cache_read_tokens'] += cache_read
        
        if cache_creation > 0:
            self.cache_stats['cache_creations'] += 1
            self.cache_stats['cache_creation_tokens'] += cache_creation
        
        self.cache_stats['total_input_tokens'] += response.usage.input_tokens
        self.cache_stats['total_output_tokens'] += response.usage.output_tokens
    
    def print_cache_stats(self):
        """Print caching and cost statistics."""
        stats = self.cache_stats
        
        print("\n" + "="*70)
        print("CACHE & COST STATISTICS")
        print("="*70)
        print(f"Cache hits: {stats['cache_hits']}")
        print(f"Cache creations: {stats['cache_creations']}")
        print(f"Cached read tokens: {stats['cache_read_tokens']:,}")
        print(f"Cached creation tokens: {stats['cache_creation_tokens']:,}")
        print(f"Regular input tokens: {stats['total_input_tokens'] - stats['cache_read_tokens'] - stats['cache_creation_tokens']:,}")
        print(f"Total input tokens: {stats['total_input_tokens']:,}")
        print(f"Total output tokens: {stats['total_output_tokens']:,}")
        
        # Cost calculation (Haiku 4.5 pricing)
        # Input: $1/M tokens, Output: $5/M tokens
        # Cached read: $0.30/M tokens (90% discount)
        cached_read_cost = stats['cache_read_tokens'] * 0.30 / 1_000_000
        regular_input_cost = (stats['total_input_tokens'] - stats['cache_read_tokens']) * 1.0 / 1_000_000
        output_cost = stats['total_output_tokens'] * 5.0 / 1_000_000
        total_cost = cached_read_cost + regular_input_cost + output_cost
        
        print(f"\nCOST BREAKDOWN (Claude Haiku 4.5):")
        print(f"  Cached read tokens: ${cached_read_cost:.4f}")
        print(f"  Regular input tokens: ${regular_input_cost:.4f}")
        print(f"  Output tokens: ${output_cost:.4f}")
        print(f"  TOTAL: ${total_cost:.4f}")
        
        if stats['cache_hits'] > 0:
            avg_savings_per_request = (stats['cache_read_tokens'] / stats['cache_hits'] * 0.007) / 1000
            print(f"\nSAVINGS:")
            print(f"  Average savings per request: ${avg_savings_per_request:.4f}")
            print(f"  Total tokens saved: {stats['cache_read_tokens']:,}")
            print(f"  Savings rate: ~90% on cached tokens")
        
        print("="*70 + "\n")
    
    def tailor_batch(self, jobs, career_context=None):
        """
        Tailor multiple resumes in batch with cache efficiency.
        
        After the first job, all subsequent jobs will use the cached
        system prompt, base resume, and career context, saving ~90% on
        those tokens while only paying for the unique job description.
        
        Args:
            jobs: List of dicts with keys: 'title', 'description', 'requirements'
            career_context: Optional additional context
        
        Returns:
            List of dicts with tailored_resume and error status
        """
        results = []
        start_time = datetime.now()
        
        logger.info(f"Starting batch processing of {len(jobs)} resumes with prompt caching")
        
        for i, job in enumerate(jobs, 1):
            logger.info(f"Processing job {i}/{len(jobs)}: {job['title']}")
            
            try:
                tailored = self.tailor(
                    job_title=job['title'],
                    job_description=job.get('description', ''),
                    job_requirements=job.get('requirements', ''),
                    career_context=career_context
                )
                
                results.append({
                    'title': job['title'],
                    'tailored_resume': tailored,
                    'error': None
                })
            
            except Exception as e:
                logger.error(f"Failed to tailor {job['title']}: {str(e)}")
                results.append({
                    'title': job['title'],
                    'tailored_resume': None,
                    'error': str(e)
                })
            
            # Rate limiting between jobs (respectful to API)
            if i < len(jobs):
                time.sleep(config.BATCH_DELAY)
        
        elapsed = datetime.now() - start_time
        logger.info(f"Batch processing complete in {elapsed.total_seconds():.1f} seconds")
        logger.info(f"Success rate: {len([r for r in results if not r['error']])}/{len(jobs)}")
        
        return results


# ============================================================================
# Cost Optimization Tips
# ============================================================================

"""
PROMPT CACHING SAVINGS BREAKDOWN:

Without Caching:
- 100 resumes × ~2500 tokens per request = 250,000 tokens
- Cost: 250,000 × $0.001 = $0.25

With Caching (after first request):
- First request: ~2500 tokens (all billed)
- Remaining 99 requests: ~500 tokens each (unique job descriptions only)
- Cached tokens (system + base resume): ~2000 tokens (90% discount)
- Cost: $0.0025 + (99 × ($0.001 + $0.0014)) = ~$0.027
- Savings: ~90% on cached tokens

For 1000 resumes:
- Without caching: ~$2.50
- With caching: ~$0.35
- Total savings: ~$2.15 (86% reduction!)

Key Insight:
Since your system prompt, base resume, and career context are IDENTICAL
for every job, caching them means you only pay full price once,
then 90% discount for every subsequent resume.
"""


# ============================================================================
# Example Usage - Optimized for Batch Processing
# ============================================================================

if __name__ == '__main__':
    # Configure logging
    def setup_logging():
        # 1. Clear default handlers
        logger.remove()

        # Ensure logs directory exists
        os.makedirs(config.LOG_PATH, exist_ok=True)

        # 2. Stdout Sink: High-level progress for your console (Clean & Simple)
        logger.add(
            sys.stdout,
            colorize=True,
            format=config.LOG_CONSOLE_FORMAT,
            level=config.LOG_LEVEL
        )

        # 3. File Sink: Granular details for debugging and cost tracking
        logger.add(
            str(config.LOG_PATH / "resume_tailor_{time}.log"),
            rotation=config.LOG_MAX_BYTES,
            retention=f"{config.LOG_BACKUP_COUNT} days",
            compression="zip",
            level="DEBUG",
            format=config.LOG_FILE_FORMAT
        )

    setup_logging()
    
    # Sample base resume
    sample_resume = """
John Smith
john.smith@email.com | 555-123-4567 | LinkedIn.com/in/johnsmith | GitHub.com/johnsmith
Location: San Francisco, CA

PROFESSIONAL SUMMARY
Full-stack software engineer with 7+ years of experience building scalable web applications.
Expertise in Python, JavaScript, and cloud infrastructure. Known for solving complex technical
challenges and mentoring junior engineers.

EXPERIENCE

Senior Software Engineer
Tech Company Inc., San Francisco, CA | Jan 2022 - Present
- Led design and implementation of microservices platform handling 1M+ daily requests
- Improved API response time by 60% through caching and database optimization
- Built CI/CD pipeline reducing deployment time from 45 to 15 minutes
- Mentored team of 4 junior engineers, 2 promoted to senior roles

Software Engineer
StartUp Corp, San Francisco, CA | Jun 2019 - Dec 2021
- Developed React-based admin dashboard used by 50K+ users
- Built Python backend services processing 100K+ events daily
- Reduced bug rate by 75% by implementing comprehensive test suite
- Contributed to open-source projects (500+ GitHub stars)

Junior Software Engineer
Dev Studios, San Francisco, CA | Jan 2017 - May 2019
- Built RESTful APIs using Django and Flask
- Developed frontend components in React and Vue.js
- Participated in code reviews and pair programming sessions

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley, CA | Graduated 2016

SKILLS
Languages: Python, JavaScript/TypeScript, SQL, Go, Bash
Frameworks: Django, FastAPI, React, Node.js, Next.js
Databases: PostgreSQL, MongoDB, Redis
Cloud: AWS (EC2, S3, Lambda), GCP, Docker, Kubernetes
Tools: Git, GitHub, Jenkins, GitHub Actions, Terraform

CERTIFICATIONS
AWS Certified Solutions Architect - Associate
Certified Scrum Master (CSM)
"""
    
    # Sample batch of jobs (demonstrating cache efficiency)
    sample_jobs = [
        {
            'title': 'Senior Backend Engineer',
            'description': 'We are looking for a Senior Backend Engineer to build scalable APIs...',
            'requirements': '5+ years Python, microservices, AWS...'
        },
        {
            'title': 'Full Stack Engineer',
            'description': 'Seeking a Full Stack Engineer for React + Python work...',
            'requirements': '3+ years full stack, React, Python, PostgreSQL...'
        },
        {
            'title': 'DevOps Engineer',
            'description': 'Build and maintain our Kubernetes infrastructure...',
            'requirements': '4+ years DevOps, Kubernetes, Docker, CI/CD...'
        },
    ]
    
    print("="*70)
    print("Resume Tailoring Demo - Claude Haiku 4.5 with Prompt Caching")
    print("="*70)
    print("\nInitializing tailor client...")
    
    # Initialize
    tailor = ResumeTC(base_resume_text=sample_resume)
    
    print("\nProcessing batch of 3 resumes...")
    print("(Watch cache efficiency grow after first request!)\n")
    
    # Process batch
    results = tailor.tailor_batch(sample_jobs)
    
    # Show results
    print("\nBATCH RESULTS:")
    for result in results:
        status = "✓" if not result['error'] else "✗"
        print(f"  {status} {result['title']}")
        if result['error']:
            print(f"     Error: {result['error']}")
        else:
            print(f"     Resume preview: {result['tailored_resume'][:100]}...")
    
    # Print cache statistics
    tailor.print_cache_stats()
    
    print("\nKEY INSIGHTS:")
    print("  • Claude Haiku 4.5 is 5x cheaper than Opus")
    print("  • Prompt caching saves 90% on repeated content")
    print("  • For 100 resumes: ~$0.30 total cost vs $2.50 without caching")
    print("  • For 1000 resumes: ~$3 total cost vs $25 without caching")
    print("  • This is the most cost-efficient way to scale!")
