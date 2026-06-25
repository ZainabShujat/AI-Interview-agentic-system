from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from services import gemini_service

router = APIRouter(prefix="/api/jd", tags=["jd"])

@router.post("")
async def upload_jd(payload: schemas.JDRequest, db: Session = Depends(get_db)):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")
        
    try:
        # Parse using Gemini JD Agent
        parsed_data = gemini_service.parse_jd(payload.text)
        
        # Save to database
        db_jd = models.JobDescription(
            raw_text=payload.text,
            parsed_json=parsed_data
        )
        db.add(db_jd)
        db.commit()
        db.refresh(db_jd)
        
        return {
            "id": db_jd.id,
            "parsed": db_jd.parsed_json
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error parsing job description: {str(e)}")
