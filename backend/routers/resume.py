from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from pathlib import Path
from models import User, Resume, UserProfile
from schemas import ResumeResponse
from routers.auth import get_current_user
from database import get_db
from services.resume_parser import ResumeParser
import traceback
import sys

router = APIRouter()

# Create uploads directory
UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    category: str = Form("General"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and parse resume"""
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Save file
        file_path = UPLOAD_DIR / f"{current_user.id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse resume
        parser = ResumeParser()
        try:
            parsed_data = parser.parse_resume(str(file_path))
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Error parsing resume: {str(e)}")
        
        # Save to database
        resume = Resume(
            user_id=current_user.id,
            original_filename=file.filename,
            original_file_path=str(file_path),
            category=category,
            parsed_data=parsed_data,
            ats_score=parsed_data.get("ats_score", 0),
            ats_analysis=parsed_data.get("ats_analysis", {})
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # --- Auto-Profile Sync ---
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not user_profile:
            user_profile = UserProfile(user_id=current_user.id)
            db.add(user_profile)
        
        # Update skills (merge with existing)
        existing_skills = set(user_profile.technical_skills or [])
        new_skills = set(parsed_data.get("skills", []))
        user_profile.technical_skills = list(existing_skills.union(new_skills))
        
        # Update experience (append if not exists - simplified logic)
        # Ideally checking deeper equality, but appending for now if empty
        if parsed_data.get("experience"):
             if not user_profile.experience:
                 user_profile.experience = parsed_data["experience"]
             else:
                 # simple append for now
                 current_exp = user_profile.experience or []
                 current_exp.extend(parsed_data["experience"])
                 user_profile.experience = current_exp

        # Update projects
        if parsed_data.get("projects"):
            if not user_profile.projects:
                user_profile.projects = parsed_data["projects"]
            else:
                 current_proj = user_profile.projects or []
                 current_proj.extend(parsed_data["projects"])
                 user_profile.projects = current_proj

        db.commit()
        db.refresh(user_profile)
        # -------------------------
        
        return resume
    except Exception as e:
        print("CRITICAL UPLOAD ERROR:", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/", response_model=List[ResumeResponse])
def get_resumes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all user resumes"""
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    return resumes

@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific resume"""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume

@router.delete("/{resume_id}")
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete resume"""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Delete file if exists
    if resume.original_file_path and os.path.exists(resume.original_file_path):
        os.remove(resume.original_file_path)
    
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully"}

