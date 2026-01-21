from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import User, Application, JobDescription, CustomizedResume, Resume
from schemas import ApplicationCreate, ApplicationUpdate, ApplicationResponse, ApplicationAnswerRequest, ApplicationAnswerResponse
from routers.auth import get_current_user
from database import get_db
from services.ai_service import AIService

router = APIRouter()

@router.post("/", response_model=ApplicationResponse)
def create_application(
    app_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new application"""
    # Verify job description exists
    jd = db.query(JobDescription).filter(
        JobDescription.id == app_data.job_description_id,
        JobDescription.user_id == current_user.id
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    
    # Verify customized resume if provided
    if app_data.customized_resume_id:
        custom_resume = db.query(CustomizedResume).filter(
            CustomizedResume.id == app_data.customized_resume_id
        ).first()
        if not custom_resume:
            raise HTTPException(status_code=404, detail="Customized resume not found")
    
    application = Application(
        user_id=current_user.id,
        job_description_id=app_data.job_description_id,
        customized_resume_id=app_data.customized_resume_id,
        company_name=app_data.company_name,
        role=app_data.role,
        notes=app_data.notes
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    
    return application

@router.get("/", response_model=List[ApplicationResponse])
def get_applications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all applications"""
    applications = db.query(Application).filter(Application.user_id == current_user.id).all()
    return applications

@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific application"""
    application = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.put("/{app_id}", response_model=ApplicationResponse)
def update_application(
    app_id: int,
    app_update: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update application status or notes"""
    application = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if app_update.status:
        application.status = app_update.status
    if app_update.notes:
        application.notes = app_update.notes
    
    db.commit()
    db.refresh(application)
    return application

@router.delete("/{app_id}")
def delete_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete application"""
    application = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    return {"message": "Application deleted successfully"}

@router.post("/generate-answer", response_model=ApplicationAnswerResponse)
def generate_application_answer(
    answer_request: ApplicationAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate personalized answer for application questions"""
    # Get resume
    resume = db.query(Resume).filter(
        Resume.id == answer_request.resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Get job description
    jd = db.query(JobDescription).filter(
        JobDescription.id == answer_request.job_description_id,
        JobDescription.user_id == current_user.id
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    
    # Prepare data
    resume_data = resume.parsed_data or {}
    jd_data = {
        "required_skills": jd.required_skills or [],
        "priority_keywords": jd.priority_keywords or [],
        "tools_technologies": jd.tools_technologies or [],
        "role_expectations": jd.role_expectations or "",
        "role": jd.role or "",
        "company_name": jd.company_name or ""
    }
    
    # Generate answer
    ai_service = AIService()
    answer = ai_service.generate_application_answer(
        answer_request.question,
        resume_data,
        jd_data,
        answer_request.word_limit or 200
    )
    
    return ApplicationAnswerResponse(answer=answer, question=answer_request.question)

