"""
Resume Tailoring Module - Claude API Integration

This module uses Claude to intelligently tailor resumes to specific job postings.
It matches keywords, highlights relevant skills, and reorders content for relevance.
"""

import os
import time

import config
from anthropic import Anthropic
from loguru import logger


class ResumeTC:
    """Resume Tailor Client - uses Claude to match resumes to jobs"""
    
    def __init__(self, api_key=None, base_resume_text=None):
        """
        Initialize the tailor client.
        
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
        self.base_resume = base_resume_text or ""
        self.model = config.CLAUDE_MODEL
        self.max_tokens = config.CLAUDE_MAX_TOKENS
        
        logger.info(f"ResumeTC initialized with model: {self.model}")
        logger.info(
            "Anthropic API key resolved from {} ({})",
            self.api_key_source,
            config.mask_secret(self.api_key),
        )

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
    
    def tailor(self, job_title, job_description, job_requirements, 
               career_context=None, retry_count=0):
        """
        Tailor the base resume to a specific job posting.
        
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
        
        career_ctx = config.RESUME_CONTEXT if career_context is None else career_context
        career_ctx = career_ctx.strip() if isinstance(career_ctx, str) else ""
        
        # System prompt: instructs Claude how to tailor
        system_prompt = """You are revising a resume for a specific job posting.

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

The final answer must be a strong, conservative, highly skimmable resume that feels simple, sharp, visually calm, and easy to scan fast without overstating qualifications.
"""
        
        user_prompt = f"""Base Resume:
{self.base_resume}

---

Additional Career Context & Key Achievements:
{career_ctx}

---

Target Job Posting:

Position: {job_title}

Description:
{job_description}

Requirements:
{job_requirements}

---

Revise the resume above for this specific job posting.
Return ONLY the final plain-text resume that follows the required section-header and bullet formatting.
"""
        
        try:
            logger.debug(f"Calling Claude API for job: {job_title}")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                system=system_prompt
            )
            
            tailored_text = self._extract_text(response)
            if not tailored_text:
                raise RuntimeError(f"Claude returned no text content for '{job_title}'.")

            logger.info(f"Successfully tailored resume for: {job_title}")
            logger.debug(f"  Input tokens: {response.usage.input_tokens}")
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
    
    def tailor_batch(self, jobs, career_context=None):
        """
        Tailor multiple resumes in batch.
        
        Args:
            jobs: List of dicts with keys: 'title', 'description', 'requirements'
            career_context: Optional additional context
        
        Returns:
            List of dicts with keys: 'title', 'tailored_resume', 'error' (if failed)
        """
        results = []
        
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
            
            # Rate limiting between jobs
            if i < len(jobs):
                time.sleep(config.BATCH_DELAY)
        
        return results


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == '__main__':
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        config.LOG_FILE,
        format=config.LOG_FILE_FORMAT,
        level=config.LOG_LEVEL,
        rotation=config.LOG_MAX_BYTES,
        retention=f"{config.LOG_BACKUP_COUNT} days"
    )
    logger.add(
        lambda msg: print(msg, end=''),  # Also print to console
        format=config.LOG_CONSOLE_FORMAT,
        level=config.LOG_LEVEL
    )
    
    # Example: Load base resume and tailor to a job
    
    # Create sample base resume for testing
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
    
    # Sample job posting
    sample_job = {
        'title': 'Senior Backend Engineer',
        'description': '''
We are looking for an experienced Senior Backend Engineer to join our rapidly growing team.
You will work on building scalable backend services that power our platform used by millions of users.
We value clean code, thorough testing, and continuous improvement.

You will:
- Design and implement new microservices and APIs
- Optimize database queries and infrastructure
- Lead technical discussions and code reviews
- Mentor junior engineers
- Collaborate with frontend and DevOps teams

The role is remote-friendly and offers competitive compensation and benefits.
        ''',
        'requirements': '''
- 5+ years of backend software engineering experience
- Strong experience with Python and/or Go
- Experience with relational databases (PostgreSQL)
- Knowledge of microservices architecture
- Experience with AWS or similar cloud platforms
- Understanding of CI/CD pipelines
- Strong communication and mentorship skills
- BS in Computer Science or equivalent experience
        '''
    }
    
    print("=" * 70)
    print("Resume Tailoring Demo")
    print("=" * 70)
    
    # Initialize the tailor client
    tailor = ResumeTC(base_resume_text=sample_resume)
    
    # Tailor resume for the job
    print(f"\nTailoring resume for: {sample_job['title']}")
    print("-" * 70)
    
    tailored = tailor.tailor(
        job_title=sample_job['title'],
        job_description=sample_job['description'],
        job_requirements=sample_job['requirements']
    )
    
    print("\nTAILORED RESUME:")
    print("-" * 70)
    print(tailored)
    print("-" * 70)
