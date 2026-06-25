import fitz # PyMuPDF
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from services import gemini_service

router = APIRouter(prefix="/api/resume", tags=["resume"])

@router.post("")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        # Read PDF binary contents
        pdf_bytes = await file.read()
        
        # Open with PyMuPDF
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        raw_text = ""
        for page in pdf_doc:
            raw_text += page.get_text()
            
        pdf_doc.close()
        
        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Failed to extract readable text from PDF.")
            
        # Parse text using Gemini Resume Agent
        parsed_data = gemini_service.parse_resume(raw_text)
        
        # Save to database
        db_resume = models.Resume(
            raw_text=raw_text,
            parsed_json=parsed_data
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        
        return {
            "id": db_resume.id,
            "filename": file.filename,
            "parsed": db_resume.parsed_json
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")
