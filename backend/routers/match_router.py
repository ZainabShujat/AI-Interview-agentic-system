from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from services import gemini_service

router = APIRouter(prefix="/api/match", tags=["match"])

@router.post("")
async def match_resume_jd(payload: schemas.MatchRequest, db: Session = Depends(get_db)):
    # Retrieve resume
    resume = db.query(models.Resume).filter(models.Resume.id == payload.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume record not found.")
        
    # Retrieve job description
    jd = db.query(models.JobDescription).filter(models.JobDescription.id == payload.jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job Description record not found.")
        
    try:
        # Match deterministically in backend code. LLMs may explain results elsewhere,
        # but the scoring and skill comparison stay transparent.
        match_result = gemini_service.deterministic_match_resume_and_jd(
            resume.parsed_json,
            jd.parsed_json
        )
        match_result["assessmentBlueprint"] = gemini_service.generate_assessment_blueprint(
            jd.parsed_json,
            match_result
        )
        return match_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching profiles: {str(e)}")

from pydantic import BaseModel
from typing import Dict, Any

class RawMatchRequest(BaseModel):
    resume_json: Dict[str, Any]
    jd_json: Dict[str, Any]

@router.post("/raw")
async def match_raw_resume_jd(payload: RawMatchRequest):
    try:
        # Match deterministically in backend code
        match_result = gemini_service.deterministic_match_resume_and_jd(
            payload.resume_json,
            payload.jd_json
        )
        match_result["assessmentBlueprint"] = gemini_service.generate_assessment_blueprint(
            payload.jd_json,
            match_result
        )
        return match_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching raw profiles: {str(e)}")
