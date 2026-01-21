from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from models import User, Resume, JobDescription, CustomizedResume
from schemas import CustomizedResumeRequest, CustomizedResumeResponse
from routers.auth import get_current_user
from database import get_db
from services.ai_service import AIService
from services.resume_generator import ResumeGenerator
import os

router = APIRouter()

@router.post("/customize", response_model=CustomizedResumeResponse)
def customize_resume(
    request: CustomizedResumeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Customize resume for a specific job description"""
    # Get resume
    resume = db.query(Resume).filter(
        Resume.id == request.resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Get job description
    jd = db.query(JobDescription).filter(
        JobDescription.id == request.job_description_id,
        JobDescription.user_id == current_user.id
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    
    # Prepare data for AI service
    resume_data = resume.parsed_data or {}
    jd_data = {
        "required_skills": jd.required_skills or [],
        "priority_keywords": jd.priority_keywords or [],
        "tools_technologies": jd.tools_technologies or [],
        "role_expectations": jd.role_expectations or "",
        "role": jd.role or "",
        "company_name": jd.company_name or ""
    }
    
    # Customize resume using AI
    ai_service = AIService()
    customization_result = ai_service.customize_resume(resume_data, jd_data)
    
    # Generate PDF/DOCX file
    generator = ResumeGenerator()
    # Add name from user if available
    customized_data = customization_result["customized_data"].copy()
    if not customized_data.get("name") and current_user.name:
        customized_data["name"] = current_user.name
    
    pdf_path = generator.generate_pdf(
        customized_data,
        f"customized_{current_user.id}_{request.resume_id}_{request.job_description_id}"
    )
    
    # Save customized resume
    customized_resume = CustomizedResume(
        original_resume_id=request.resume_id,
        job_description_id=request.job_description_id,
        customized_data=customization_result["customized_data"],
        changes_made=customization_result["changes_made"],
        relevance_score=customization_result["relevance_score"],
        generated_file_path=pdf_path
    )
    db.add(customized_resume)
    db.commit()
    db.refresh(customized_resume)
    
    return customized_resume

@router.get("/{customized_id}", response_model=CustomizedResumeResponse)
def get_customized_resume(
    customized_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customized resume"""
    custom_resume = db.query(CustomizedResume).join(Resume).filter(
        CustomizedResume.id == customized_id,
        Resume.user_id == current_user.id
    ).first()
    if not custom_resume:
        raise HTTPException(status_code=404, detail="Customized resume not found")
    return custom_resume

@router.get("/resume/{resume_id}", response_model=List[CustomizedResumeResponse])
def get_customized_versions(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all customized versions of a resume"""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    custom_resumes = db.query(CustomizedResume).filter(
        CustomizedResume.original_resume_id == resume_id
    ).all()
    return custom_resumes

@router.get("/{customized_id}/download")
def download_customized_resume(
    customized_id: int,
    format: str = "pdf",  # pdf or docx
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download customized resume as PDF or DOCX"""
    custom_resume = db.query(CustomizedResume).join(Resume).filter(
        CustomizedResume.id == customized_id,
        Resume.user_id == current_user.id
    ).first()
    if not custom_resume:
        raise HTTPException(status_code=404, detail="Customized resume not found")
    
    # Generate file if not exists or regenerate
    generator = ResumeGenerator()
    customized_data = custom_resume.customized_data.copy()
    
    # Add user name if not present
    if not customized_data.get("name") and current_user.name:
        customized_data["name"] = current_user.name
    
    if format == "docx":
        file_path = generator.generate_docx(
            customized_data,
            f"customized_{current_user.id}_{custom_resume.id}"
        )
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        file_path = custom_resume.generated_file_path
        if not file_path or not os.path.exists(file_path):
            file_path = generator.generate_pdf(
                customized_data,
                f"customized_{current_user.id}_{custom_resume.id}"
            )
        media_type = "application/pdf"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Resume file not found")
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=os.path.basename(file_path)
    )

