import re
from typing import List, Dict, Any

# Optional spaCy import
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        nlp = None
except ImportError:
    spacy = None
    nlp = None

class JobDescriptionAnalyzer:
    def __init__(self):
        self.common_skills = [
            "python", "java", "javascript", "react", "node.js", "sql", "mongodb",
            "postgresql", "aws", "docker", "kubernetes", "git", "html", "css",
            "machine learning", "data science", "pandas", "numpy", "tensorflow",
            "pytorch", "flask", "django", "fastapi", "express", "angular", "vue",
            "c++", "c#", "go", "rust", "php", "ruby", "swift", "kotlin",
            "tableau", "power bi", "excel", "r", "matlab", "scikit-learn",
            "communication", "leadership", "teamwork", "problem solving",
            "agile", "scrum", "jira", "confluence", "ci/cd", "rest api",
            "graphql", "microservices", "linux", "bash", "shell scripting"
        ]
        
        self.tools_technologies = [
            "aws", "azure", "gcp", "docker", "kubernetes", "jenkins",
            "git", "github", "gitlab", "jira", "confluence", "slack",
            "tableau", "power bi", "excel", "looker", "metabase",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "react", "angular", "vue", "next.js", "node.js", "express",
            "django", "flask", "fastapi", "spring", "hibernate"
        ]
    
    def extract_required_skills(self, job_description: str) -> List[str]:
        """Extract required skills from job description"""
        jd_lower = job_description.lower()
        found_skills = []
        
        # Look for skills section
        skills_section = re.search(
            r'(required|must have|skills?|qualifications?)[:\-]?\s*([^\n]+(?:\n[^\n]+){0,10})',
            job_description,
            re.IGNORECASE
        )
        
        if skills_section:
            skills_text = skills_section.group(2)
            # Check for each skill
            for skill in self.common_skills:
                if skill.lower() in skills_text.lower():
                    found_skills.append(skill.title())
        
        # Also check entire JD for skills
        for skill in self.common_skills:
            if skill.lower() in jd_lower and skill.title() not in found_skills:
                found_skills.append(skill.title())
        
        return list(set(found_skills))
    
    def extract_priority_keywords(self, job_description: str) -> List[str]:
        """Extract priority keywords from job description"""
        keywords = []
        jd_lower = job_description.lower()
        
        # Look for emphasis words
        emphasis_patterns = [
            r'(must|required|essential|mandatory|critical|important)\s+([a-z\s]+)',
            r'strong\s+(experience|knowledge|understanding)\s+(?:in|of|with)\s+([a-z\s]+)',
            r'proficient\s+(?:in|with)\s+([a-z\s]+)',
            r'expert\s+(?:in|with)\s+([a-z\s]+)'
        ]
        
        for pattern in emphasis_patterns:
            matches = re.finditer(pattern, jd_lower, re.IGNORECASE)
            for match in matches:
                keyword = match.group(2) if len(match.groups()) > 1 else match.group(1)
                keyword = keyword.strip()
                if len(keyword) > 3 and keyword not in keywords:
                    keywords.append(keyword.title())
        
        return keywords[:20]  # Top 20 keywords
    
    def extract_tools_technologies(self, job_description: str) -> List[str]:
        """Extract tools and technologies mentioned"""
        jd_lower = job_description.lower()
        found_tools = []
        
        for tool in self.tools_technologies:
            if tool.lower() in jd_lower:
                found_tools.append(tool.title())
        
        # Also look for version numbers (e.g., Python 3.9, React 18)
        version_patterns = [
            r'([a-z]+)\s+\d+\.?\d*',
            r'([a-z]+)\s+\(version\s+\d+\)'
        ]
        
        for pattern in version_patterns:
            matches = re.finditer(pattern, jd_lower, re.IGNORECASE)
            for match in matches:
                tool = match.group(1).strip()
                if tool not in found_tools and len(tool) > 2:
                    found_tools.append(tool.title())
        
        return list(set(found_tools))
    
    def extract_role_expectations(self, job_description: str) -> str:
        """Extract role expectations and responsibilities"""
        expectations = []
        
        # Look for responsibilities section
        resp_section = re.search(
            r'(responsibilities?|duties?|what you\'?ll do|key\s+responsibilities?)[:\-]?\s*([^\n]+(?:\n[^\n]+){0,15})',
            job_description,
            re.IGNORECASE
        )
        
        if resp_section:
            resp_text = resp_section.group(2)
            # Extract bullet points
            bullets = re.split(r'\n(?=[•\-\*]|\d+\.)', resp_text)
            for bullet in bullets:
                bullet = re.sub(r'^[•\-\*\d+\.]\s*', '', bullet).strip()
                if len(bullet) > 10:
                    expectations.append(bullet)
        
        # Also look for "you will" patterns
        will_patterns = re.finditer(
            r'you\s+will\s+([^\.]+)',
            job_description,
            re.IGNORECASE
        )
        for match in will_patterns:
            expectation = match.group(1).strip()
            if len(expectation) > 10 and expectation not in expectations:
                expectations.append(expectation)
        
        return ". ".join(expectations[:10])  # Top 10 expectations
    
    def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        """Main analysis function"""
        return {
            "required_skills": self.extract_required_skills(job_description),
            "priority_keywords": self.extract_priority_keywords(job_description),
            "tools_technologies": self.extract_tools_technologies(job_description),
            "role_expectations": self.extract_role_expectations(job_description)
        }

