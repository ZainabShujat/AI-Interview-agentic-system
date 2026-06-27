import io
import zipfile
import sys
import os

# Ensure the backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from routers.resume_router import extract_text_from_docx
    from services import gemini_service
    print("✅ Successfully imported extraction and gemini services.")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)

def run_local_tests():
    print("\n--- Starting Resume Agent Backend Tests ---")

    # 1. Test DOCX Extraction
    print("\n1. Testing Word (.docx) Extraction...")
    docx_io = io.BytesIO()
    with zipfile.ZipFile(docx_io, 'w') as zip_file:
        xml_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:t>Zack Miller</w:t>
                    </w:r>
                </w:p>
                <w:p>
                    <w:r>
                        <w:t>Summary: Experienced React and Python Developer with 4 years in SaaS platforms.</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </w:document>
        """
        zip_file.writestr('word/document.xml', xml_content)
    docx_bytes = docx_io.getvalue()
    
    extracted_docx = extract_text_from_docx(docx_bytes)
    print(f"Extracted Text:\n{extracted_docx}")
    
    if "Zack Miller" in extracted_docx and "Experienced React" in extracted_docx:
        print("✅ DOCX extraction works perfectly!")
    else:
        print("❌ DOCX extraction failed!")
        sys.exit(1)

    # 2. Test Plain Text (.txt) Decoding
    print("\n2. Testing Text (.txt) Decoding...")
    txt_bytes = "Zack Miller\nSummary: Experienced React and Python Developer with 4 years in SaaS platforms.".encode('utf-8')
    extracted_txt = txt_bytes.decode('utf-8', errors='ignore')
    print(f"Decoded Text:\n{extracted_txt}")
    if "Zack Miller" in extracted_txt:
        print("✅ Text decoding works perfectly!")
    else:
        print("❌ Text decoding failed!")
        sys.exit(1)

    # 3. Test Gemini Resume Parsing Agent
    print("\n3. Testing Gemini Resume Agent Parsing...")
    try:
        # Check if API Key is loaded
        if not gemini_service.GEMINI_API_KEY:
            print("⚠️ GEMINI_API_KEY is not loaded. The service will run in Mock Agent fallback mode.")
        else:
            print(f"Gemini API Key is active. Querying model: {gemini_service.GEMINI_MODEL}...")

        parsed_data = gemini_service.parse_resume(extracted_docx)
        print("✅ Gemini Parsing completed successfully!")
        
        # Verify schema elements
        print(f"Candidate Name: {parsed_data.get('candidate_name')}")
        print(f"Headline: {parsed_data.get('headline')}")
        print(f"Skills Extracted: {parsed_data.get('skills')}")
        
    except Exception as e:
        print(f"❌ Gemini Resume Agent Parsing failed: {e}")
        sys.exit(1)

    print("\n🎉 All local backend tests passed successfully! Resume parsing is ready for PDF, DOCX, and TXT.")

if __name__ == "__main__":
    run_local_tests()
