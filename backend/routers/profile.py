from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User, UserProfile
from schemas import UserProfileCreate, UserProfileResponse
from routers.auth import get_current_user
from database import get_db

router = APIRouter()

@router.get("/", response_model=UserProfileResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        # Create empty profile if doesn't exist
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.post("/", response_model=UserProfileResponse)
def create_or_update_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update user profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if profile:
        # Update existing profile
        profile.technical_skills = profile_data.technical_skills
        profile.soft_skills = profile_data.soft_skills
        profile.projects = [p.dict() if hasattr(p, 'dict') else p for p in profile_data.projects]
        profile.experience = [e.dict() if hasattr(e, 'dict') else e for e in profile_data.experience]
        profile.achievements = profile_data.achievements
        profile.certifications = profile_data.certifications
    else:
        # Create new profile
        profile = UserProfile(
            user_id=current_user.id,
            technical_skills=profile_data.technical_skills,
            soft_skills=profile_data.soft_skills,
            projects=[p.dict() if hasattr(p, 'dict') else p for p in profile_data.projects],
            experience=[e.dict() if hasattr(e, 'dict') else e for e in profile_data.experience],
            achievements=profile_data.achievements,
            certifications=profile_data.certifications
        )
        db.add(profile)
    
    db.commit()
    db.refresh(profile)
    return profile

@router.put("/", response_model=UserProfileResponse)
def update_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    return create_or_update_profile(profile_data, current_user, db)

