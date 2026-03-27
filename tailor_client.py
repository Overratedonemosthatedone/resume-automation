"""
Resume Tailoring Module - Claude API Integration

This module uses Claude to intelligently tailor resumes to specific job postings.
It matches keywords, highlights relevant skills, and reorders content for relevance.
"""

import os
import time
from anthropic import Anthropic
import config
from loguru import logger


class ResumeTC:
    """Resume Tailor Client - uses Claude to match resumes to jobs"""
    
    def __init__(self, api_key=None, base_resume_text=None):
        """
        Initialize the tailor client.
        
        Args:
            api_key: Claude API key (falls back to config.CLAUDE_API_KEY)
            base_resume_text: Full text of your base resume
        """
        self.api_key = api_key or config.CLAUDE_API_KEY
        self.client = Anthropic(api_key=self.api_key)
        self.base_resume = base_resume_text or ""
        self.model = config.CLAUDE_MODEL
        self.max_tokens = config.CLAUDE_MAX_TOKENS
        
        logger.info(f"ResumeTC initialized with model: {self.model}")
    
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
        
        career_ctx = career_context or config.RESUME_CONTEXT
        
        # System prompt: instructs Claude how to tailor
        system_prompt = """You are an expert resume writer and career coach.

Your task: Tailor a resume to match a specific job posting perfectly.

INSTRUCTIONS:
1. Analyze the job posting to identify key requirements and keywords
2. Review the provided resume and career context
3. Reorder and adjust the resume to emphasize the most relevant skills and experiences
4. Use keywords from the job posting naturally throughout the resume
5. Highlight achievements that demonstrate the required competencies
6. Keep the format clean and ATS-friendly (applicant tracking system compatible)
7. Do NOT invent or exaggerate experience - only rearrange and reframe what's provided
8. Do NOT remove core sections (contact info, summary, etc.)
9. Maintain professional language and formatting

OUTPUT FORMAT:
- Provide ONLY the complete tailored resume in plain text
- No markdown, no ### headers, no explanations or preamble
- Use standard resume format:
  * Name and contact at top
  * Optional: brief professional summary
  * Experience section with bullet points
  * Education section
  * Skills section (if present)
  * Certifications/Additional sections (if present)
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

Tailor the resume above to maximize relevance to this job posting.
Output the COMPLETE tailored resume in plain text (no markdown formatting).
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
            
            tailored_text = response.content[0].text
            
            logger.info(f"✓ Successfully tailored resume for: {job_title}")
            logger.debug(f"  Input tokens: {response.usage.input_tokens}")
            logger.debug(f"  Output tokens: {response.usage.output_tokens}")
            
            return tailored_text
        
        except Exception as e:
            error_msg = f"Error tailoring resume for '{job_title}': {str(e)}"
            logger.error(error_msg)
            
            if retry_count < config.MAX_RETRIES:
                logger.info(f"Retrying... (attempt {retry_count + 1}/{config.MAX_RETRIES})")
                time.sleep(config.RETRY_DELAY)
                return self.tailor(job_title, job_description, job_requirements,
                                 career_context, retry_count + 1)
            else:
                raise RuntimeError(error_msg)
    
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
                    job_description=job['description'],
                    job_requirements=job['requirements'],
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
        format=config.LOG_FORMAT,
        level=config.LOG_LEVEL,
        rotation=f"{config.LOG_MAX_BYTES} MB",
        retention=f"{config.LOG_BACKUP_COUNT} days"
    )
    logger.add(
        lambda msg: print(msg, end=''),  # Also print to console
        format=config.LOG_FORMAT,
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
