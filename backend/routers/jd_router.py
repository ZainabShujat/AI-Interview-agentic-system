import fitz
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from services import gemini_service

router = APIRouter(prefix="/api/jd", tags=["jd"])

@router.get("")
async def list_jds(db: Session = Depends(get_db)):
    records = db.query(models.JobDescription).order_by(models.JobDescription.created_at.desc()).limit(50).all()
    return [
        {
            "id": jd.id,
            "title": (jd.parsed_json or {}).get("title") or (jd.parsed_json or {}).get("role") or "Untitled role",
            "industry": (jd.parsed_json or {}).get("industry"),
            "seniority": (jd.parsed_json or {}).get("seniority"),
            "department": jd.department,
            "created_at": jd.created_at.isoformat() if jd.created_at else None,
            "parsed": jd.parsed_json
        }
        for jd in records
    ]

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
            parsed_json=parsed_data,
            passing_score=payload.passing_score,
            available_slots=payload.available_slots
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

@router.post("/upload")
async def upload_jd_file(
    file: UploadFile = File(...),
    passing_score: int = Form(60),
    available_slots: str = Form("[]"),
    db: Session = Depends(get_db)
):
    try:
        file_bytes = await file.read()
        raw_text = ""

        if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
            pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in pdf_doc:
                raw_text += page.get_text()
            pdf_doc.close()
        else:
            raw_text = file_bytes.decode("utf-8", errors="ignore")

        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Failed to extract readable text from job description.")

        import json
        slots_list = []
        try:
            slots_list = json.loads(available_slots)
        except:
            pass

        parsed_data = gemini_service.parse_jd(raw_text)
        db_jd = models.JobDescription(
            raw_text=raw_text, 
            parsed_json=parsed_data,
            passing_score=passing_score,
            available_slots=slots_list
        )
        db.add(db_jd)
        db.commit()
        db.refresh(db_jd)

        return {
            "id": db_jd.id,
            "filename": file.filename,
            "parsed": db_jd.parsed_json
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error parsing job description file: {str(e)}")

@router.put("/{jd_id}/blueprint")
async def update_jd_blueprint(jd_id: str, payload: schemas.BlueprintUpdateRequest, db: Session = Depends(get_db)):
    jd = db.query(models.JobDescription).filter(models.JobDescription.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job Description record not found.")

    try:
        jd.parsed_json = payload.blueprint
        db.commit()
        db.refresh(jd)
        return {
            "id": jd.id,
            "parsed": jd.parsed_json
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating hiring blueprint: {str(e)}")
