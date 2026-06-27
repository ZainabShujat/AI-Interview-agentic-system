import fitz # PyMuPDF
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from services import gemini_service

router = APIRouter(prefix="/api/resume", tags=["resume"])

@router.post("", response_model=schemas.ResumeResponse)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        # Read PDF binary contents
        pdf_bytes = await file.read()
        
        # Open with PyMuPDF
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        raw_text = ""
        extracted_links = []
        for page in pdf_doc:
            raw_text += page.get_text()
            for link in page.get_links():
                uri = link.get("uri")
                if uri and uri not in extracted_links:
                    extracted_links.append(uri)
            
        pdf_doc.close()
        
        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Failed to extract readable text from PDF.")
            
        if extracted_links:
            raw_text += "\n\nExtracted resume links:\n" + "\n".join(extracted_links)

        # Parse text using Gemini Resume Agent, enriched with public portfolio/GitHub/LinkedIn links where available.
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
            "parsed": db_resume.parsed_json,
            "raw_resume_text": db_resume.raw_text
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")
