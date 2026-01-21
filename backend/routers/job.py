from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import User, JobDescription
from schemas import JobDescriptionCreate, JobDescriptionResponse, JobDescriptionAnalysis
from routers.auth import get_current_user
from database import get_db
from services.job_analyzer import JobDescriptionAnalyzer
from services.scraper import JobScraper
from pydantic import BaseModel

class JobImportUrl(BaseModel):
    url: str

router = APIRouter()

@router.post("/analyze", response_model=JobDescriptionResponse)
def analyze_job_description(
    job_data: JobDescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze job description and extract key information"""
    analyzer = JobDescriptionAnalyzer()
    analysis = analyzer.analyze_job_description(job_data.job_description_text)
    
    # Save to database
    job_description = JobDescription(
        user_id=current_user.id,
        company_name=job_data.company_name,
        role=job_data.role,
        job_description_text=job_data.job_description_text,
        required_skills=analysis["required_skills"],
        priority_keywords=analysis["priority_keywords"],
        tools_technologies=analysis["tools_technologies"],
        role_expectations=analysis["role_expectations"]
    )
    db.add(job_description)
    db.commit()
    db.refresh(job_description)
    
    return job_description

@router.post("/import")
def import_job_description(
    import_data: JobImportUrl,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)  
):
    """Scrape and return job description from URL"""
    try:
        scraped_data = JobScraper.scrape_url(import_data.url)
        return scraped_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[JobDescriptionResponse])
def get_job_descriptions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all analyzed job descriptions"""
    jds = db.query(JobDescription).filter(JobDescription.user_id == current_user.id).all()
    return jds

@router.get("/{jd_id}", response_model=JobDescriptionResponse)
def get_job_description(
    jd_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific job description"""
    jd = db.query(JobDescription).filter(
        JobDescription.id == jd_id,
        JobDescription.user_id == current_user.id
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd

@router.delete("/{jd_id}")
def delete_job_description(
    jd_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete job description"""
    jd = db.query(JobDescription).filter(
        JobDescription.id == jd_id,
        JobDescription.user_id == current_user.id
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    
    db.delete(jd)
    db.commit()
    return {"message": "Job description deleted successfully"}

