from fastapi import FastAPI
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, profile, resume, job, application, skills, customize, interview, chat, tracker

app = FastAPI(title="AI Resume & Internship Autopilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth")
app.include_router(profile.router, prefix="/api/profile")
app.include_router(resume.router, prefix="/api/resume")
app.include_router(job.router, prefix="/api/job")
app.include_router(application.router, prefix="/api/application")
app.include_router(skills.router, prefix="/api/skills")
app.include_router(customize.router, prefix="/api/customize")
app.include_router(interview.router, prefix="/api/interview")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(tracker.router, prefix="/api/tracker")

@app.get("/api")
def root():
    return {"status": "Backend is live"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

# 🔥 THIS IS THE KEY LINE (Vercel needs this)
handler = Mangum(app)
