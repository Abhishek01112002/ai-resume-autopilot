from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from database import SessionLocal, engine, Base
from models import User, Application, Resume
from routers import auth, profile, resume, job, application, skills, customize, interview, chat, tracker
from services.ai_service import AIService

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Resume & Internship Autopilot API",
    description="AI-powered platform for resume customization and application management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://10.168.60.18:3000",
        "http://10.168.60.18:3001",
        "http://localhost:3000/",
        "http://127.0.0.1:3000/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])
app.include_router(job.router, prefix="/api/job", tags=["Job Description"])
app.include_router(application.router, prefix="/api/application", tags=["Application"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(customize.router, prefix="/api/customize", tags=["Resume Customization"])
app.include_router(interview.router, prefix="/api/interview", tags=["Interview Prep"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Chatbot"])
app.include_router(tracker.router, prefix="/api/tracker", tags=["Application Tracker"])

@app.get("/")
async def root():
    return {
        "message": "AI Resume & Internship Autopilot API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

