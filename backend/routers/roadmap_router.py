from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
import schemas
from services import gemini_service

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])

@router.post("")
async def get_career_roadmap(payload: schemas.RoadmapRequest):
    try:
        roadmap = gemini_service.generate_career_roadmap(
            resume=payload.resume,
            target_role=payload.target_role,
            target_company=payload.target_company,
            target_jd=payload.target_jd
        )
        return roadmap
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating career roadmap: {str(e)}")
