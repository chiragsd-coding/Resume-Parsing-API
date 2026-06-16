"""Resume and JD parsing services using OCR and ML."""
import asyncio
import logging
from typing import Optional
import pytesseract
from pdf2image import convert_from_path
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class ResumeParser:
    """Parse resume PDFs/DOCs to extract structured data."""
    
    @staticmethod
    async def parse_resume(file_path: str) -> dict:
        """Parse resume and extract data."""
        try:
            # Extract text from PDF
            text = await ResumeParser._extract_text(file_path)
            
            # Parse sections
            parsed = {
                "raw_text": text,
                "full_name": ResumeParser._extract_name(text),
                "email": ResumeParser._extract_email(text),
                "phone": ResumeParser._extract_phone(text),
                "location": ResumeParser._extract_location(text),
                "summary": ResumeParser._extract_summary(text),
                "skills": ResumeParser._extract_skills(text),
                "experience": ResumeParser._extract_experience(text),
                "education": ResumeParser._extract_education(text),
                "certifications": ResumeParser._extract_certifications(text),
            }
            
            return parsed
        except Exception as e:
            logger.error(f"Resume parsing error: {e}")
            raise
    
    @staticmethod
    async def _extract_text(file_path: str) -> str:
        """Extract text from PDF using OCR."""
        try:
            images = convert_from_path(file_path)
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
    
    @staticmethod
    def _extract_name(text: str) -> Optional[str]:
        """Extract candidate name."""
        # Heuristic: typically at top of resume
        lines = text.split('\n')
        if lines:
            return lines[0].strip()
        return None
    
    @staticmethod
    def _extract_email(text: str) -> Optional[str]:
        """Extract email using regex."""
        match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        return match.group(0) if match else None
    
    @staticmethod
    def _extract_phone(text: str) -> Optional[str]:
        """Extract phone number."""
        match = re.search(r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}', text)
        return match.group(0) if match else None
    
    @staticmethod
    def _extract_location(text: str) -> Optional[str]:
        """Extract location (simplified)."""
        match = re.search(r'(?:Location|City|Based)[:\s]+([^,\n]+(?:,\s*[A-Z]{2})?)', text, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    @staticmethod
    def _extract_summary(text: str) -> Optional[str]:
        """Extract professional summary."""
        for section in ['SUMMARY', 'OBJECTIVE', 'PROFESSIONAL SUMMARY']:
            pattern = f'{section}[:\s]*(.{{1,500}}?)(?:EXPERIENCE|SKILLS|EDUCATION)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return None
    
    @staticmethod
    def _extract_skills(text: str) -> list:
        """Extract skills section."""
        pattern = r'SKILLS[:\s]*(.{{1,1000}}?)(?:EXPERIENCE|EDUCATION|CERTIFICATIONS|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            skills_text = match.group(1)
            # Split by common delimiters
            skills = re.split(r'[,•\n]', skills_text)
            return [s.strip() for s in skills if s.strip() and len(s.strip()) > 2]
        return []
    
    @staticmethod
    def _extract_experience(text: str) -> list:
        """Extract work experience."""
        pattern = r'EXPERIENCE[:\s]*(.{{1,5000}}?)(?:EDUCATION|SKILLS|CERTIFICATIONS|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            exp_text = match.group(1)
            # Simple parsing - split by job titles
            jobs = re.split(r'(?=^\w+\s+(?:at|@|-)\s+\w+)', exp_text, flags=re.MULTILINE)
            return [j.strip() for j in jobs if j.strip()]
        return []
    
    @staticmethod
    def _extract_education(text: str) -> list:
        """Extract education."""
        pattern = r'EDUCATION[:\s]*(.{{1,2000}}?)(?:SKILLS|EXPERIENCE|CERTIFICATIONS|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            edu_text = match.group(1)
            degrees = re.findall(r'(?:B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?B\.?A\.?|Ph\.?D\.?|Bachelor|Master|Associate)[^,\n]*', edu_text)
            return degrees
        return []
    
    @staticmethod
    def _extract_certifications(text: str) -> list:
        """Extract certifications."""
        pattern = r'CERTIFICATIONS[:\s]*(.{{1,2000}}?)(?:SKILLS|EXPERIENCE|EDUCATION|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            cert_text = match.group(1)
            certs = re.split(r'[•,\n]', cert_text)
            return [c.strip() for c in certs if c.strip() and len(c.strip()) > 2]
        return []


class JDParser:
    """Parse job descriptions to extract requirements."""
    
    @staticmethod
    async def parse_jd(job_description: str) -> dict:
        """Parse job description."""
        return {
            "raw_text": job_description,
            "job_title": JDParser._extract_job_title(job_description),
            "required_skills": JDParser._extract_required_skills(job_description),
            "nice_to_have_skills": JDParser._extract_nice_to_have_skills(job_description),
            "experience_level": JDParser._extract_experience_level(job_description),
            "years_experience": JDParser._extract_years_of_experience(job_description),
            "location": JDParser._extract_location(job_description),
            "salary_range": JDParser._extract_salary(job_description),
        }
    
    @staticmethod
    def _extract_job_title(text: str) -> Optional[str]:
        """Extract job title."""
        match = re.search(r'(?:Job Title|Position|Role)[:\s]+([^\n]+)', text, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    @staticmethod
    def _extract_required_skills(text: str) -> list:
        """Extract required skills."""
        pattern = r'(?:REQUIRED|MUST HAVE)[:\s]*(.{{1,2000}}?)(?:NICE TO HAVE|QUALIFICATIONS|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            skills_text = match.group(1)
            skills = re.split(r'[•,\n]', skills_text)
            return [s.strip() for s in skills if s.strip() and len(s.strip()) > 2]
        return []
    
    @staticmethod
    def _extract_nice_to_have_skills(text: str) -> list:
        """Extract nice-to-have skills."""
        pattern = r'NICE TO HAVE[:\s]*(.{{1,2000}}?)(?:REQUIRED|QUALIFICATIONS|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            skills_text = match.group(1)
            skills = re.split(r'[•,\n]', skills_text)
            return [s.strip() for s in skills if s.strip() and len(s.strip()) > 2]
        return []
    
    @staticmethod
    def _extract_experience_level(text: str) -> Optional[str]:
        """Extract experience level."""
        for level in ['senior', 'mid-level', 'junior', 'lead', 'principal']:
            if level.lower() in text.lower():
                return level
        return None
    
    @staticmethod
    def _extract_years_of_experience(text: str) -> Optional[float]:
        """Extract years of experience required."""
        match = re.search(r'(\d+)\+?\s*years?\s+(?:of\s+)?(?:experience|exp)', text, re.IGNORECASE)
        return float(match.group(1)) if match else None
    
    @staticmethod
    def _extract_location(text: str) -> Optional[str]:
        """Extract location."""
        match = re.search(r'(?:Location|Based)[:\s]+([^\n]+)', text, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    @staticmethod
    def _extract_salary(text: str) -> Optional[dict]:
        """Extract salary range."""
        match = re.search(r'\$?([\d,]+)\s*-\s*\$?([\d,]+)', text)
        if match:
            try:
                return {
                    "min": int(match.group(1).replace(',', '')),
                    "max": int(match.group(2).replace(',', ''))
                }
            except:
                pass
        return None
