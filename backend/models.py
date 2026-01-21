from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    college = Column(String)
    education_level = Column(String)  # B.Tech, M.Tech, etc.
    target_role = Column(String)  # Data Analyst Intern, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True))
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    applications = relationship("Application", back_populates="user")
    resumes = relationship("Resume", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Skills
    technical_skills = Column(JSON, default=list)  # ["Python", "SQL", ...]
    soft_skills = Column(JSON, default=list)  # ["Communication", "Leadership", ...]
    
    # Projects
    projects = Column(JSON, default=list)  # [{"name": "...", "description": "...", "tech": [...]}, ...]
    
    # Experience
    experience = Column(JSON, default=list)  # [{"company": "...", "role": "...", "duration": "...", "description": "..."}, ...]
    
    # Additional info
    achievements = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="profile")

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Original resume
    original_filename = Column(String)
    original_file_path = Column(String)
    category = Column(String, default="General") # Frontend, Backend, Fullstack, General
    
    # Parsed data
    parsed_data = Column(JSON)  # Structured JSON from resume parsing
    
    # ATS Score
    ats_score = Column(Integer)
    ats_analysis = Column(JSON) # {"issues": [], "missing_keywords": [], "section_presence": {}}
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    customized_versions = relationship("CustomizedResume", back_populates="original_resume")

class CustomizedResume(Base):
    __tablename__ = "customized_resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    original_resume_id = Column(Integer, ForeignKey("resumes.id"))
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"))
    
    # Customized content
    customized_data = Column(JSON)  # Modified resume data
    
    # Generated file
    generated_file_path = Column(String)
    
    # Customization metadata
    changes_made = Column(JSON)  # What was changed and why
    relevance_score = Column(Integer)  # Match score with JD
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    original_resume = relationship("Resume", back_populates="customized_versions")
    job_description = relationship("JobDescription", back_populates="customized_resumes")

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Job details
    company_name = Column(String)
    role = Column(String)
    job_description_text = Column(Text)
    
    # Analyzed data
    required_skills = Column(JSON, default=list)
    priority_keywords = Column(JSON, default=list)
    tools_technologies = Column(JSON, default=list)
    role_expectations = Column(Text)
    
    # Analysis metadata
    analyzed_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    customized_resumes = relationship("CustomizedResume", back_populates="job_description")
    applications = relationship("Application", back_populates="job_description")

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"))
    customized_resume_id = Column(Integer, ForeignKey("customized_resumes.id"), nullable=True)
    
    # Application details
    company_name = Column(String)
    role = Column(String)
    application_date = Column(DateTime(timezone=True), default=func.now())
    
    # Status tracking
    status = Column(String, default="Applied")  # Applied, Under Review, Interview, Rejected, Accepted
    
    # Generated answers
    application_answers = Column(JSON, default=dict)  # {"why_hire_you": "...", "why_company": "...", ...}
    
    # Notes
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="applications")
    job_description = relationship("JobDescription", back_populates="applications")

class SkillRecommendation(Base):
    __tablename__ = "skill_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Recommendation data
    missing_skills = Column(JSON, default=list)
    recommended_skills = Column(JSON, default=list)
    project_ideas = Column(JSON, default=list)
    learning_resources = Column(JSON, default=list)  # [{"name": "...", "url": "...", "type": "free/paid"}, ...]
    
    # Analysis metadata
    analyzed_jobs_count = Column(Integer, default=0)
    generated_at = Column(DateTime(timezone=True), default=func.now())
