import fitz # PyMuPDF
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from services import gemini_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resume", tags=["resume"])

def extract_text_from_docx(docx_bytes: bytes) -> str:
    """
    Extracts text paragraphs from Word docx XML files using standard zipfile and ET modules.
    """
    try:
        with zipfile.ZipFile(BytesIO(docx_bytes)) as docx:
            xml_content = docx.read('word/document.xml')
        root = ET.fromstring(xml_content)
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs = []
        for p in root.findall('.//w:p', namespaces):
            texts = [t.text for t in p.findall('.//w:t', namespaces) if t.text]
            if texts:
                paragraphs.append(''.join(texts))
        return '\n'.join(paragraphs)
    except Exception as e:
        print(f"Error extracting docx text: {e}")
        return ""

@router.post("", response_model=schemas.ResumeResponse)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename.lower()
    if not filename.endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Only PDF, DOCX, and TXT are supported."
        )
        
    try:
        file_bytes = await file.read()
        raw_text = ""
        
        # 1. Handle different document formats
        if filename.endswith('.pdf'):
            # Open with PyMuPDF
            pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
            extracted_links = []
            for page in pdf_doc:
                raw_text += page.get_text()
                for link in page.get_links():
                    uri = link.get("uri")
                    if uri and uri not in extracted_links:
                        extracted_links.append(uri)
            pdf_doc.close()
            if extracted_links:
                raw_text += "\n\nExtracted resume links:\n" + "\n".join(extracted_links)
                
        elif filename.endswith('.docx'):
            raw_text = extract_text_from_docx(file_bytes)
            
        elif filename.endswith('.txt'):
            raw_text = file_bytes.decode('utf-8', errors='ignore')

        # 2. Check if text extraction succeeded
        if not raw_text.strip():
            raise HTTPException(
                status_code=422, 
                detail=f"Failed to extract readable text from the uploaded {filename.split('.')[-1].upper()} file."
            )

        # Check database cache first (using SHA256 hash match)
        import hashlib
        resume_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()
        existing_cache = db.query(models.ResumeCache).filter(models.ResumeCache.raw_text_hash == resume_hash).first()
        
        if existing_cache and existing_cache.parsed_json:
            cached_name = existing_cache.parsed_json.get("candidate_name")
            is_valid_cache = True
            if cached_name:
                c_lower = cached_name.lower()
                if any(kw in c_lower for kw in ['psychologist', 'engineer', 'developer', 'trainer', 'intern']):
                    is_valid_cache = False
            else:
                is_valid_cache = False
                
            if is_valid_cache:
                # Ensure an associated Resume entity exists for foreign keys / interviews mapping
                db_resume = db.query(models.Resume).filter(models.Resume.raw_text == raw_text).first()
                if not db_resume:
                    db_resume = models.Resume(
                        raw_text=raw_text,
                        parsed_json=existing_cache.parsed_json
                    )
                    db.add(db_resume)
                    db.commit()
                    db.refresh(db_resume)
                return {
                    "id": db_resume.id,
                    "filename": file.filename,
                    "parsed": existing_cache.parsed_json,
                    "raw_resume_text": raw_text,
                    "telemetry": {
                        "cached": True,
                        "model": "SQLite Cache",
                        "cost": 0.0,
                        "mode": "Cache Lookup",
                        "fallback": False
                    }
                }
        # 3. Parse text using Gemini Resume Agent (handles local extraction, LLM parsing)
        parsed_data = gemini_service.parse_resume(raw_text, filename=file.filename)
        
        # Write to ResumeCache (decoupled from the Resume Agent)
        try:
            db_cache = models.ResumeCache(raw_text_hash=resume_hash, parsed_json=parsed_data)
            db.add(db_cache)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to write to ResumeCache: {e}")
        
        # 4. Fetch or insert the Resume entity record for relational mapping
        db_resume = db.query(models.Resume).filter(models.Resume.raw_text == raw_text).first()
        if db_resume:
            cached_name = db_resume.parsed_json.get("candidate_name") if db_resume.parsed_json else None
            is_stale = True
            if cached_name:
                c_lower = cached_name.lower()
                if not any(kw in c_lower for kw in ['psychologist', 'engineer', 'developer', 'trainer', 'intern']):
                    is_stale = False
            if is_stale:
                db_resume.parsed_json = parsed_data
                db.commit()
                db.refresh(db_resume)
        else:
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
            "raw_resume_text": db_resume.raw_text,
            "telemetry": {
                "cached": False,
                "model": "Gemini 2.5 Flash" if gemini_service.GEMINI_API_KEY else "Local Rules Heuristics",
                "cost": 0.00008 if gemini_service.GEMINI_API_KEY else 0.0,
                "mode": "Hybrid",
                "fallback": not bool(gemini_service.GEMINI_API_KEY)
            }
        }
        
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")

