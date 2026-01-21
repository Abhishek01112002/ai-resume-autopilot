import os
import json
import re
from typing import Dict, List, Any
from pathlib import Path
import PyPDF2
from docx import Document
from collections import defaultdict

# Optional spaCy import
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
        nlp = None
except ImportError:
    print("Warning: spaCy not installed. Some NLP features will be limited.")
    spacy = None
    nlp = None

class ResumeParser:
    def __init__(self):
        self.skills_keywords = [
            "python", "java", "javascript", "react", "node.js", "sql", "mongodb",
            "postgresql", "aws", "docker", "kubernetes", "git", "html", "css",
            "machine learning", "data science", "pandas", "numpy", "tensorflow",
            "pytorch", "flask", "django", "fastapi", "express", "angular", "vue",
            "c++", "c#", "go", "rust", "php", "ruby", "swift", "kotlin",
            "tableau", "power bi", "excel", "r", "matlab", "scikit-learn",
            "communication", "leadership", "teamwork", "problem solving"
        ]
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
        return text
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
    
    def extract_text(self, file_path: str) -> str:
        """Extract text based on file extension"""
        file_ext = Path(file_path).suffix.lower()
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.skills_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill.title())
        
        # Also look for patterns like "Skills: Python, Java, ..."
        skills_section = re.search(r'skills?[:\-]?\s*([^\n]+)', text, re.IGNORECASE)
        if skills_section:
            skills_text = skills_section.group(1)
            # Extract comma or pipe separated skills
            skills_list = re.split(r'[,|•\-\n]', skills_text)
            for skill in skills_list:
                skill = skill.strip()
                if skill and len(skill) > 2:
                    found_skills.append(skill)
        
        return list(set(found_skills))
    
    def extract_education(self, text: str) -> Dict[str, Any]:
        """Extract education information"""
        education = {
            "degree": None,
            "field": None,
            "institution": None,
            "year": None
        }
        
        # Look for education section
        education_patterns = [
            r'education[:\-]?\s*([^\n]+)',
            r'(b\.?tech|b\.?e\.?|m\.?tech|m\.?e\.?|bachelor|master|phd)[:\-]?\s*([^\n]+)',
            r'(bsc|msc|ba|ma)[:\-]?\s*([^\n]+)'
        ]
        
        for pattern in education_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                edu_text = match.group(0)
                # Extract degree
                degree_match = re.search(r'(b\.?tech|b\.?e\.?|m\.?tech|m\.?e\.?|bachelor|master|phd|bsc|msc)', 
                                       edu_text, re.IGNORECASE)
                if degree_match:
                    education["degree"] = degree_match.group(1).title()
                
                # Extract institution (usually after degree)
                institution_match = re.search(r'(?:in|from|at)\s+([A-Z][^\n,]+)', edu_text, re.IGNORECASE)
                if institution_match:
                    education["institution"] = institution_match.group(1).strip()
                
                # Extract year
                year_match = re.search(r'(19|20)\d{2}', edu_text)
                if year_match:
                    education["year"] = year_match.group(0)
                
                break
        
        return education
    
    def extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience"""
        experiences = []
        
        # Look for experience section
        experience_section = re.search(
            r'experience[:\-]?\s*(.+?)(?=\n\n|\n[A-Z][A-Z\s]+\n|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if experience_section:
            exp_text = experience_section.group(1)
            # Split by common patterns
            exp_entries = re.split(r'\n(?=[A-Z][a-z]+\s+[A-Z]|Intern|Developer|Engineer)', exp_text)
            
            for entry in exp_entries:
                if len(entry.strip()) < 20:
                    continue
                
                exp = {
                    "company": None,
                    "role": None,
                    "duration": None,
                    "description": entry.strip()
                }
                
                # Extract role (usually first line)
                lines = entry.split('\n')
                if lines:
                    first_line = lines[0].strip()
                    exp["role"] = first_line
                
                # Extract company (look for patterns)
                company_match = re.search(r'at\s+([A-Z][^\n]+)', entry, re.IGNORECASE)
                if company_match:
                    exp["company"] = company_match.group(1).strip()
                
                # Extract duration
                duration_match = re.search(r'(\d{4}|\w+\s+\d{4})\s*[-–]\s*(\d{4}|present|current)', entry, re.IGNORECASE)
                if duration_match:
                    exp["duration"] = f"{duration_match.group(1)} - {duration_match.group(2)}"
                
                experiences.append(exp)
        
        return experiences
    
    def extract_projects(self, text: str) -> List[Dict[str, Any]]:
        """Extract projects from resume"""
        projects = []
        
        # Look for projects section
        projects_section = re.search(
            r'projects?[:\-]?\s*(.+?)(?=\n\n|\n[A-Z][A-Z\s]+\n|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if projects_section:
            proj_text = projects_section.group(1)
            # Split projects (usually by title or bullet points)
            proj_entries = re.split(r'\n(?=[A-Z][a-z]+|•|\-)', proj_text)
            
            for entry in proj_entries:
                if len(entry.strip()) < 15:
                    continue
                
                project = {
                    "name": None,
                    "description": entry.strip(),
                    "tech": []
                }
                
                # Extract project name (usually first line)
                lines = entry.split('\n')
                if lines:
                    project["name"] = lines[0].strip()
                
                # Extract technologies mentioned
                text_lower = entry.lower()
                for tech in self.skills_keywords:
                    if tech.lower() in text_lower and tech not in project["tech"]:
                        project["tech"].append(tech.title())
                
                projects.append(project)
        
        return projects
    


    def calculate_ats_score(self, text: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate a heuristic ATS score (0-100)"""
        score = 0
        max_score = 100
        analysis = {
            "issues": [],
            "positive_aspects": [],
            "section_presence": {}
        }
        
        # 1. Content Length Check (10 points)
        word_count = len(text.split())
        if 400 <= word_count <= 1000:
            score += 10
            analysis["positive_aspects"].append("Optimal word count")
        elif word_count < 400:
            score += 5
            analysis["issues"].append("Resume might be too short")
        else:
            score += 5
            analysis["issues"].append("Resume might be too long")

        # 2. Section Presence (40 points)
        sections = ["skills", "education", "experience", "projects"]
        present_sections = 0
        for section in sections:
            has_content = bool(parsed_data.get(section))
            analysis["section_presence"][section] = has_content
            if has_content:
                score += 10
                present_sections += 1
            else:
                analysis["issues"].append(f"Missing section: {section.title()}")

        # 3. Contact Info (10 points)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_pattern = r'(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
        
        has_email = bool(re.search(email_pattern, text))
        has_phone = bool(re.search(phone_pattern, text))
        
        if has_email: score += 5
        if has_phone: score += 5
        if not has_email: analysis["issues"].append("Missing email address")
        if not has_phone: analysis["issues"].append("Missing phone number")

        # 4. Skills Parsing (20 points)
        skills_count = len(parsed_data.get("skills", []))
        if skills_count >= 5:
            score += 20
            analysis["positive_aspects"].append(f"Good technical skills detected ({skills_count} found)")
        elif skills_count > 0:
            score += 10
            analysis["issues"].append("Consider adding more relevant technical skills")
        else:
            analysis["issues"].append("No technical skills detected")

        # 5. Formatting/Readability (20 points - heuristic)
        # Check for bullet points (common characters)
        bullet_points = len(re.findall(r'[•\-\*]', text))
        if bullet_points > 5:
            score += 20
            analysis["positive_aspects"].append("Good use of bullet points")
        else:
            score += 10
            analysis["issues"].append("Use more bullet points for better readability")
            
        return {"score": score, "analysis": analysis}

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Main parsing function"""
        text = self.extract_text(file_path)
        
        parsed_data = {
            "raw_text": text,
            "skills": self.extract_skills(text),
            "education": self.extract_education(text),
            "experience": self.extract_experience(text),
            "projects": self.extract_projects(text),
            "summary": None
        }
        
        # Extract summary if present
        summary_match = re.search(r'summary[:\-]?\s*([^\n]+(?:\n[^\n]+){0,3})', text, re.IGNORECASE)
        if summary_match:
            parsed_data["summary"] = summary_match.group(1).strip()
            
        # Calculate ATS Score
        ats_result = self.calculate_ats_score(text, parsed_data)
        parsed_data["ats_score"] = ats_result["score"]
        parsed_data["ats_analysis"] = ats_result["analysis"]
        
        return parsed_data

