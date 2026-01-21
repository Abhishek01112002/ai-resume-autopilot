from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import User, UserProfile, JobDescription, SkillRecommendation
from schemas import SkillRecommendationResponse
from routers.auth import get_current_user
from database import get_db
from services.ai_service import AIService

router = APIRouter()

@router.post("/analyze-gaps", response_model=SkillRecommendationResponse)
def analyze_skill_gaps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze skill gaps and generate recommendations"""
    # Get user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please create a profile first.")
    
    # Get all job descriptions
    job_descriptions = db.query(JobDescription).filter(
        JobDescription.user_id == current_user.id
    ).all()
    
    if not job_descriptions:
        raise HTTPException(status_code=400, detail="No job descriptions found. Please analyze some job descriptions first.")
    
    # Get user skills
    user_skills = profile.technical_skills + profile.soft_skills
    
    # Prepare JD data
    jd_data = []
    for jd in job_descriptions:
        jd_data.append({
            "required_skills": jd.required_skills or [],
            "tools_technologies": jd.tools_technologies or []
        })
    
    # Analyze gaps
    ai_service = AIService()
    recommendations = ai_service.analyze_skill_gaps(user_skills, jd_data)
    
    # Save to database
    skill_rec = SkillRecommendation(
        user_id=current_user.id,
        missing_skills=recommendations["missing_skills"],
        recommended_skills=recommendations["recommended_skills"],
        project_ideas=recommendations["project_ideas"],
        learning_resources=recommendations["learning_resources"],
        analyzed_jobs_count=len(job_descriptions)
    )
    db.add(skill_rec)
    db.commit()
    db.refresh(skill_rec)
    
    return skill_rec

@router.get("/recommendations", response_model=List[SkillRecommendationResponse])
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all skill recommendations"""
    recommendations = db.query(SkillRecommendation).filter(
        SkillRecommendation.user_id == current_user.id
    ).order_by(SkillRecommendation.generated_at.desc()).all()
    return recommendations

@router.get("/recommendations/latest", response_model=SkillRecommendationResponse)
def get_latest_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get latest skill recommendations"""
    recommendation = db.query(SkillRecommendation).filter(
        SkillRecommendation.user_id == current_user.id
    ).order_by(SkillRecommendation.generated_at.desc()).first()
    
    if not recommendation:
        raise HTTPException(status_code=404, detail="No recommendations found. Please run skill gap analysis first.")
    
    return recommendation

