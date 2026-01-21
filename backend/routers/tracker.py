from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import User, Application, JobDescription
from routers.auth import get_current_user

router = APIRouter()

# --- Schemas ---
class ApplicationCreate(BaseModel):
    company_name: str
    role: str
    status: str = "Applied" # Wishlist, Applied, Interviewing, Offer, Rejected
    notes: Optional[str] = None
    job_description_id: Optional[int] = None

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: int
    company_name: str
    role: str
    status: str
    application_date: datetime
    notes: Optional[str] = None
    job_description_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/", response_model=List[ApplicationResponse])
def get_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all applications for the current user"""
    applications = db.query(Application).filter(Application.user_id == current_user.id).all()
    return applications

@router.post("/", response_model=ApplicationResponse)
def create_application(
    app_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new application tracking entry"""
    new_app = Application(
        user_id=current_user.id,
        company_name=app_data.company_name,
        role=app_data.role,
        status=app_data.status,
        notes=app_data.notes,
        job_description_id=app_data.job_description_id
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app

@router.put("/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(
    application_id: int,
    status_update: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update application status (drag and drop)"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if status_update.status:
        application.status = status_update.status
    if status_update.notes is not None:
        application.notes = status_update.notes
        
    db.commit()
    db.refresh(application)
    return application

@router.delete("/{application_id}")
def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an application"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    return {"message": "Application deleted successfully"}
