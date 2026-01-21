from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    college: Optional[str] = None
    education_level: Optional[str] = None
    target_role: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    college: Optional[str]
    education_level: Optional[str]
    target_role: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Profile schemas
class Project(BaseModel):
    name: str
    description: str
    tech: List[str]
    url: Optional[str] = None

class Experience(BaseModel):
    company: str
    role: str
    duration: str
    description: str

class UserProfileCreate(BaseModel):
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    projects: List[Project] = []
    experience: List[Experience] = []
    achievements: List[str] = []
    certifications: List[str] = []

class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    technical_skills: List[str]
    soft_skills: List[str]
    projects: List[Dict[str, Any]]
    experience: List[Dict[str, Any]]
    achievements: List[str]
    certifications: List[str]
    
    class Config:
        from_attributes = True

# Resume schemas
class ResumeUpload(BaseModel):
    filename: str

class ResumeParsed(BaseModel):
    skills: List[str]
    projects: List[Dict[str, Any]]
    education: Dict[str, Any]
    experience: List[Dict[str, Any]]
    summary: Optional[str] = None

class ResumeResponse(BaseModel):
    id: int
    user_id: int
    original_filename: str
    category: str = "General"
    parsed_data: Optional[Dict[str, Any]] = None
    ats_score: Optional[float] = 0.0
    ats_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Job Description schemas
class JobDescriptionCreate(BaseModel):
    company_name: str
    role: str
    job_description_text: str

class JobDescriptionAnalysis(BaseModel):
    required_skills: List[str]
    priority_keywords: List[str]
    tools_technologies: List[str]
    role_expectations: str

class JobDescriptionResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    role: str
    job_description_text: str
    required_skills: List[str]
    priority_keywords: List[str]
    tools_technologies: List[str]
    role_expectations: Optional[str]
    analyzed_at: datetime
    
    class Config:
        from_attributes = True

# Resume Customization schemas
class CustomizedResumeRequest(BaseModel):
    resume_id: int
    job_description_id: int

class CustomizedResumeResponse(BaseModel):
    id: int
    original_resume_id: int
    job_description_id: int
    customized_data: Dict[str, Any]
    changes_made: Dict[str, Any]
    relevance_score: int
    generated_file_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Application schemas
class ApplicationCreate(BaseModel):
    job_description_id: int
    customized_resume_id: Optional[int] = None
    company_name: str
    role: str
    notes: Optional[str] = None

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_description_id: int
    customized_resume_id: Optional[int]
    company_name: str
    role: str
    application_date: datetime
    status: str
    application_answers: Dict[str, Any]
    notes: Optional[str]
    
    class Config:
        from_attributes = True

# Application Answer schemas
class ApplicationAnswerRequest(BaseModel):
    question: str
    job_description_id: int
    resume_id: int
    word_limit: Optional[int] = 200

class ApplicationAnswerResponse(BaseModel):
    answer: str
    question: str

# Skills schemas
class SkillRecommendationResponse(BaseModel):
    id: int
    user_id: int
    missing_skills: List[str]
    recommended_skills: List[str]
    project_ideas: List[str]
    learning_resources: List[Dict[str, Any]]
    analyzed_jobs_count: int
    generated_at: datetime
    
    class Config:
        from_attributes = True

