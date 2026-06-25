import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import resume_router, jd_router, match_router, interview_router

# Initialize database tables
Base.metadata.create_all(bind=engine)
print("Database tables initialized successfully")

app = FastAPI(
    title="Career Readiness Simulation Platform",
    description="Backend API managing JD/Resume parsing, role match evaluation, and adaptive interview sessions.",
    version="0.1.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(resume_router.router)
app.include_router(jd_router.router)
app.include_router(match_router.router)
app.include_router(interview_router.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Career Readiness Simulation API Platform",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
