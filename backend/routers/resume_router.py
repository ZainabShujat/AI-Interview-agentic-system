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

        # 3. Parse text using Gemini Resume Agent
        parsed_data = gemini_service.parse_resume(raw_text)
        
        # 4. Save to database
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
        
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")

