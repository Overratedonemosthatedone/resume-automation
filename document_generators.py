"""
Document Generation Module

Converts plain text resumes into .docx and PDF formats.
Maintains clean, ATS-friendly formatting in both outputs.
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import config
from loguru import logger


# ============================================================================
# DOCX Generator
# ============================================================================

class DocxGenerator:
    """Generate .docx (Microsoft Word) resume files"""
    
    def __init__(self, template_path=None):
        """
        Initialize generator.
        
        Args:
            template_path: Optional path to template .docx file
        """
        if template_path and Path(template_path).exists():
            self.doc = Document(template_path)
            logger.info(f"Loaded template: {template_path}")
        else:
            self.doc = Document()
            self._set_default_styles()
    
    def _set_default_styles(self):
        """Set clean, professional, ATS-friendly default styles."""
        # Normal text style
        style = self.doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)
        font.color.rgb = RGBColor(0, 0, 0)
        
        # Heading style for section headers
        try:
            heading = self.doc.styles['Heading 1']
            heading.font.name = 'Calibri'
            heading.font.size = Pt(12)
            heading.font.bold = True
            heading.font.color.rgb = RGBColor(0, 0, 0)
        except:
            pass
    
    def add_text(self, text, style=None, bold=False, size=None):
        """
        Add a paragraph of text.
        
        Args:
            text: Text to add
            style: Paragraph style name
            bold: Whether to bold the text
            size: Font size in points
        """
        p = self.doc.add_paragraph(text, style=style)
        
        if bold or size:
            for run in p.runs:
                if bold:
                    run.bold = True
                if size:
                    run.font.size = Pt(size)
    
    def add_section_header(self, header_text):
        """Add a section header (e.g., 'EXPERIENCE', 'EDUCATION')."""
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(3)
        
        run = p.add_run(header_text)
        run.font.name = 'Calibri'
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)
    
    def add_bullet(self, text, indent_level=0):
        """Add a bullet point."""
        p = self.doc.add_paragraph(text, style='List Bullet')
        p.paragraph_format.left_indent = Inches(0.25 * (1 + indent_level))
        p.paragraph_format.space_after = Pt(3)
    
    def add_job_entry(self, title, company, location, dates, achievements):
        """
        Add a job entry with title, company, location, dates, and bullet points.
        
        Args:
            title: Job title
            company: Company name
            location: Location
            dates: Date range (e.g., "Jan 2022 - Present")
            achievements: List of achievement strings (will be bullet points)
        """
        # Title and company
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(0)
        
        title_run = p.add_run(title)
        title_run.font.bold = True
        title_run.font.size = Pt(11)
        
        p.add_run(f"\n{company}")
        
        # Location and dates
        p = self.doc.add_paragraph(f"{location} | {dates}")
        p.paragraph_format.space_after = Pt(3)
        
        # Achievements as bullets
        for achievement in achievements:
            self.add_bullet(achievement)
    
    def add_education_entry(self, degree, institution, location, year, gpa=None):
        """Add an education entry."""
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        
        degree_run = p.add_run(degree)
        degree_run.font.bold = True
        
        p.add_run(f"\n{institution}, {location}")
        
        gpa_text = f" | GPA: {gpa}" if gpa else ""
        p.add_run(f"\nGraduated: {year}{gpa_text}")
        
        p.paragraph_format.space_after = Pt(3)
    
    def parse_and_add_resume(self, resume_text):
        """
        Parse plain text resume and add to document.
        
        Expects format:
        - ALL CAPS lines = section headers
        - Lines starting with spaces = bullet points
        - Other lines = regular text
        """
        lines = resume_text.strip().split('\n')
        
        for line in lines:
            line = line.rstrip()
            
            if not line.strip():
                # Blank line - add space
                self.doc.add_paragraph()
            
            elif line.isupper() or line.endswith(':'):
                # Section header
                self.add_section_header(line)
            
            elif line.startswith('  ') or line.startswith('\t'):
                # Bullet point
                clean_line = line.lstrip()
                if clean_line.startswith('- ') or clean_line.startswith('• '):
                    clean_line = clean_line[2:].strip()
                self.add_bullet(clean_line)
            
            else:
                # Regular text
                self.add_text(line)
    
    def save(self, file_path):
        """
        Save document to .docx file.
        
        Args:
            file_path: Output file path
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.doc.save(str(file_path))
        logger.info(f"✓ Saved DOCX: {file_path}")


# ============================================================================
# PDF Generator
# ============================================================================

class PdfGenerator:
    """Generate PDF resume files with clean formatting"""
    
    def __init__(self):
        """Initialize PDF generator with custom styles."""
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add ATS-friendly styles for PDF output."""
        # Normal paragraph style
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            spaceAfter=3,
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=12,
            alignment=TA_LEFT,
            spaceAfter=3,
            spaceBefore=6,
            textColor=RGBColor(0, 0, 0),
        ))
        
        # Contact info style
        self.styles.add(ParagraphStyle(
            name='ContactInfo',
            fontName='Helvetica',
            fontSize=10,
            leading=10,
            alignment=TA_CENTER,
            spaceAfter=6,
        ))
        
        # Bullet style
        self.styles.add(ParagraphStyle(
            name='Bullet',
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            leftIndent=15,
            spaceAfter=2,
        ))
    
    def create_pdf(self, resume_text, output_path):
        """
        Generate PDF from plain text resume.
        
        Args:
            resume_text: Plain text resume content
            output_path: Output PDF file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
        
        elements = []
        lines = resume_text.strip().split('\n')
        
        for line in lines:
            line = line.rstrip()
            
            if not line.strip():
                # Blank line - add small spacer
                elements.append(Spacer(1, 0.05 * inch))
            
            elif line.isupper() or line.endswith(':'):
                # Section header
                elements.append(Paragraph(line, self.styles['SectionHeader']))
            
            elif line.startswith('  ') or line.startswith('\t'):
                # Bullet point
                clean_line = line.lstrip()
                if clean_line.startswith('- ') or clean_line.startswith('• '):
                    clean_line = clean_line[2:].strip()
                elements.append(Paragraph('• ' + clean_line, self.styles['Bullet']))
            
            else:
                # Regular text
                elements.append(Paragraph(line, self.styles['CustomNormal']))
        
        try:
            doc.build(elements)
            logger.info(f"✓ Saved PDF: {output_path}")
        except Exception as e:
            logger.error(f"Failed to generate PDF {output_path}: {e}")
            raise


# ============================================================================
# File Manager - Organize resumes by date and company
# ============================================================================

class FileManager:
    """Manage file organization and naming"""
    
    def __init__(self, base_path):
        """
        Initialize file manager.
        
        Args:
            base_path: Base directory for storing resumes
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileManager base path: {self.base_path}")
    
    def get_path(self, company, job_title, format='docx', date_str=None):
        """
        Get file path for a tailored resume.
        
        Args:
            company: Company name
            job_title: Job title
            format: 'docx' or 'pdf'
            date_str: Optional date string (defaults to current date)
        
        Returns:
            Path object for the file
        """
        from datetime import datetime
        
        if date_str is None:
            date_str = datetime.now().strftime(config.DATE_FORMAT)
        
        # Sanitize company and title names for use in filenames
        company_clean = self._sanitize_name(company)
        title_clean = self._sanitize_name(job_title)
        
        # Create date folder
        date_path = self.base_path / date_str
        date_path.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        filename = f"{company_clean}_{title_clean}.{format}"
        
        return date_path / filename
    
    @staticmethod
    def _sanitize_name(name):
        """Remove special characters from names for filenames."""
        import re
        # Keep only alphanumeric, spaces, hyphens
        clean = re.sub(r'[^\w\s-]', '', name)
        # Replace spaces with underscores
        clean = clean.replace(' ', '_')
        # Remove multiple underscores
        clean = re.sub(r'_+', '_', clean)
        # Limit length
        return clean[:50].strip('_')


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == '__main__':
    from loguru import logger
    
    # Configure logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=''), format="{message}", level="INFO")
    
    sample_resume = """
John Smith
john.smith@email.com | 555-123-4567 | LinkedIn.com/in/johnsmith

PROFESSIONAL SUMMARY
Experienced software engineer with 7+ years building scalable applications.

EXPERIENCE

Senior Software Engineer
Tech Company Inc., San Francisco, CA | Jan 2022 - Present
  - Led microservices platform handling 1M+ daily requests
  - Improved API response time by 60%
  - Mentored team of 4 junior engineers

EDUCATION

Bachelor of Science in Computer Science
University of California, Berkeley, CA | 2016

SKILLS
Languages: Python, JavaScript, SQL
Databases: PostgreSQL, MongoDB
Cloud: AWS, Docker
"""
    
    print("Testing DOCX Generator...")
    docx_gen = DocxGenerator()
    docx_gen.parse_and_add_resume(sample_resume)
    docx_gen.save('test_resume.docx')
    
    print("\nTesting PDF Generator...")
    pdf_gen = PdfGenerator()
    pdf_gen.create_pdf(sample_resume, 'test_resume.pdf')
    
    print("\nTesting File Manager...")
    fm = FileManager('/tmp/resumes')
    path = fm.get_path('Tech Corp', 'Senior Engineer', format='docx')
    print(f"Generated path: {path}")
