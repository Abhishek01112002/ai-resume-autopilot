from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from models import User, JobDescription, Resume
from routers.auth import get_current_user
from database import get_db
from services.ai_service import AIService

router = APIRouter()

class InterviewQuestionRequest(BaseModel):
    job_description_id: int
    resume_id: int
    count: int = 5

class InterviewEvaluationRequest(BaseModel):
    question: str
    answer: str
    job_description_id: int

@router.post("/generate-questions")
def generate_questions(
    request: InterviewQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate interview questions"""
    resume = db.query(Resume).filter(
        Resume.id == request.resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    jd = db.query(JobDescription).filter(
        JobDescription.id == request.job_description_id,
        JobDescription.user_id == current_user.id
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
        
    ai_service = AIService()
    questions = ai_service.generate_interview_questions(
        resume.parsed_data or {},
        {
            "role": jd.role,
            "company_name": jd.company_name,
            "required_skills": jd.required_skills
        },
        request.count
    )
    
    return {"questions": questions}

@router.post("/evaluate-answer")
def evaluate_answer(
    request: InterviewEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Evaluate interview answer"""
    jd = db.query(JobDescription).filter(
        JobDescription.id == request.job_description_id,
        JobDescription.user_id == current_user.id
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
        
    ai_service = AIService()
    evaluation = ai_service.evaluate_interview_answer(
        request.question,
        request.answer,
        {
            "role": jd.role,
            "required_skills": jd.required_skills
        }
    )
    
    return evaluation
