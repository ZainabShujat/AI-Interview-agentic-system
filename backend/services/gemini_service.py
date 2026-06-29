import os
import json
import re
import urllib.request
import urllib.error
import logging
from typing import Optional, Dict, List, Any
import google.generativeai as genai
from dotenv import load_dotenv
from database import SessionLocal
import models

logger = logging.getLogger(__name__)
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MODEL_FALLBACKS = [
    model.strip()
    for model in os.getenv("GEMINI_MODEL_FALLBACKS", "gemini-2.5-flash,gemini-flash-latest,gemini-2.0-flash").split(",")
    if model.strip()
]
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"Gemini: API Key loaded. Primary model: {GEMINI_MODEL}")
else:
    print("Gemini: API Key missing. Running in Mock Agent fallback mode.")

def call_gemini_json(prompt: str) -> dict:
    """Helper to query Gemini and request a JSON response."""
    if not GEMINI_API_KEY:
        raise ValueError("API Key missing")

    import datetime
    now = datetime.datetime.now()
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    current_year = now.year
    context_prefix = (
        f"[SYSTEM NOTE: The current real-world date and time is {current_time_str}. "
        f"Do NOT treat dates from {current_year - 1}, {current_year}, or earlier as 'future' plans; "
        f"the current year is {current_year}. Any references to dates on or before {current_year} represent past or active current activities.]\n\n"
    )
    prompt = context_prefix + prompt

    model_candidates = []
    for model_name in [GEMINI_MODEL, *GEMINI_MODEL_FALLBACKS]:
        if model_name and model_name not in model_candidates:
            model_candidates.append(model_name)

    last_error = None
    for model_name in model_candidates:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"},
                request_options={"timeout": 30}
            )
            return json.loads(response.text)
        except Exception as e:
            last_error = e
            print(f"Gemini API call failed with model {model_name}: {e}.")

    raise RuntimeError(f"Gemini API call failed for all configured models: {model_candidates}. Last error: {last_error}")

def extract_urls(text: str) -> list:
    urls = re.findall(r"https?://[^\s<>)\]]+", text or "")
    cleaned = []
    for url in urls:
        url = url.rstrip(".,;:'\"")
        if url not in cleaned:
            cleaned.append(url)
    return cleaned[:8]

def fetch_public_link_evidence(urls: list) -> list:
    evidence = []
    for url in urls[:5]:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "HireIntelResumeVerifier/1.0",
                    "Accept": "text/html,text/plain,application/json;q=0.9,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                content_type = response.headers.get("content-type", "")
                raw = response.read(120000).decode("utf-8", errors="ignore")

            text = raw
            if "html" in content_type:
                text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
                text = re.sub(r"(?s)<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            evidence.append({
                "url": url,
                "status": "fetched",
                "content_type": content_type,
                "text_excerpt": text[:5000]
            })
        except Exception as e:
            evidence.append({
                "url": url,
                "status": "unavailable",
                "error": str(e)[:240]
            })
    return evidence

    return evidence

def normalize_resume_parsed(data: dict) -> dict:
    if not isinstance(data, dict):
        data = {}
    
    # Root level fields
    string_fields = [
        "candidate_name", "headline", "email", "phone", "location",
        "linkedin", "github", "portfolio", "website", "summary",
        "career_level", "primary_domain"
    ]
    for field in string_fields:
        data.setdefault(field, None)
        
    data.setdefault("estimated_experience_years", 0.0)
    try:
        data["estimated_experience_years"] = float(data["estimated_experience_years"] or 0)
    except (ValueError, TypeError):
        data["estimated_experience_years"] = 0.0

    list_fields = [
        "skills", "technical_skills", "soft_skills", "programming_languages",
        "frameworks", "databases", "cloud_platforms", "tools", "certifications",
        "achievements", "languages", "domain_experience", "top_strengths", "potential_concerns"
    ]
    for field in list_fields:
        if not isinstance(data.get(field), list):
            data[field] = []
        else:
            data[field] = [str(item) for item in data[field] if item is not None]

    # Projects
    raw_projects = data.get("projects")
    if not isinstance(raw_projects, list):
        raw_projects = []
    projects = []
    for proj in raw_projects:
        if not isinstance(proj, dict):
            continue
        p = {}
        p["title"] = proj.get("title")
        p["description"] = proj.get("description")
        
        # Support fallback tool mapping
        p_tech = proj.get("technologies") or proj.get("tools")
        if not isinstance(p_tech, list):
            p_tech = []
        p["technologies"] = [str(t) for t in p_tech if t is not None]
        
        p["github"] = proj.get("github")
        p["demo"] = proj.get("demo")
        
        p_contrib = proj.get("contributions")
        if not isinstance(p_contrib, list):
            p_contrib = []
        p["contributions"] = [str(c) for c in p_contrib if c is not None]
        projects.append(p)
    data["projects"] = projects

    # Experience
    raw_exp = data.get("experience")
    if not isinstance(raw_exp, list):
        raw_exp = []
    experience = []
    for exp in raw_exp:
        if not isinstance(exp, dict):
            continue
        e = {}
        e["title"] = exp.get("title")
        e["company"] = exp.get("company")
        e["employment_type"] = exp.get("employment_type")
        e["duration"] = exp.get("duration")
        
        e_resp = exp.get("responsibilities")
        if not isinstance(e_resp, list):
            e_resp = []
        e["responsibilities"] = [str(r) for r in e_resp if r is not None]
        
        e_ach = exp.get("achievements")
        if not isinstance(e_ach, list):
            e_ach = []
        e["achievements"] = [str(a) for a in e_ach if a is not None]
        
        e_tech = exp.get("technologies")
        if not isinstance(e_tech, list):
            e_tech = []
        e["technologies"] = [str(t) for t in e_tech if t is not None]
        experience.append(e)
    data["experience"] = experience

    # Education
    raw_edu = data.get("education")
    if not isinstance(raw_edu, list):
        raw_edu = []
    education = []
    for edu in raw_edu:
        if not isinstance(edu, dict):
            continue
        ed = {}
        ed["degree"] = edu.get("degree")
        ed["branch"] = edu.get("branch")
        ed["institution"] = edu.get("institution")
        ed["year"] = str(edu.get("year")) if edu.get("year") is not None else None
        ed["cgpa"] = str(edu.get("cgpa")) if edu.get("cgpa") is not None else None
        education.append(ed)
    data["education"] = education

    # Internships
    raw_intern = data.get("internships")
    if not isinstance(raw_intern, list):
        raw_intern = []
    internships = []
    for intern in raw_intern:
        if not isinstance(intern, dict):
            continue
        i = {}
        i["company"] = intern.get("company")
        i["role"] = intern.get("role")
        i["duration"] = intern.get("duration")
        i["summary"] = intern.get("summary")
        internships.append(i)
    data["internships"] = internships

    # Links
    raw_links = data.get("links")
    if not isinstance(raw_links, list):
        raw_links = []
    links = []
    for link in raw_links:
        if not isinstance(link, dict):
            continue
        lk = {}
        lk["url"] = link.get("url")
        lk["type"] = link.get("type")
        
        verified_val = link.get("verified")
        if verified_val is None:
            verified_val = True
        lk["verified"] = bool(verified_val)
        
        lk["summary"] = link.get("summary")
        
        lk_skills = link.get("skills_found")
        if not isinstance(lk_skills, list):
            lk_skills = []
        lk["skills_found"] = [str(s) for s in lk_skills if s is not None]
        
        lk_projs = link.get("projects_found")
        if not isinstance(lk_projs, list):
            lk_projs = []
        lk["projects_found"] = [str(p) for p in lk_projs if p is not None]
        
        links.append(lk)
    data["links"] = links

    return data

# --- HARDCODED SKILL DATABASE ---
PROGRAMMING_LANGUAGES = {
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", 
    "ruby", "php", "swift", "kotlin", "scala", "r", "perl", "bash", "shell",
    "sql", "html", "css", "groovy", "elixir", "erlang", "clojure"
}

FRAMEWORKS = {
    "react", "angular", "vue", "svelte", "next.js", "nextjs", "gatsby", "nuxt",
    "express", "fastapi", "django", "flask", "spring", "spring boot", "asp.net",
    "rails", "laravel", "symfony", "graphql", "rest", "grpc"
}

DATABASES = {
    "postgres", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "firestore", "oracle", "mssql", "sqlite",
    "cockroachdb", "neo4j", "influxdb", "clickhouse", "bigquery"
}

CLOUD_PLATFORMS = {
    "aws", "amazon web services", "azure", "gcp", "google cloud", "heroku",
    "vercel", "netlify", "digitalocean", "linode", "cloudfoundry", "ibm cloud"
}

TOOLS_AND_PLATFORMS = {
    "docker", "kubernetes", "k8s", "jenkins", "gitlab", "github", "git", "circleci",
    "terraform", "ansible", "chef", "puppet", "grafana", "prometheus", "datadog",
    "slack", "jira", "confluence", "notion", "figma", "postman", "vscode", "vim",
    "emacs", "intellij", "pycharm", "vs code", "xcode", "android studio"
}

SOFT_SKILLS = {
    "leadership", "communication", "teamwork", "collaboration", "problem-solving",
    "critical thinking", "time management", "adaptability", "creativity", "mentoring",
    "negotiation", "presentation", "strategic thinking", "agile", "scrum"
}

def _quick_is_resume(text: str) -> bool:
    """Fast heuristic check if text is a resume (no LLM)."""
    resume_keywords = ['experience', 'education', 'skills', 'project', 'achievement', 
                       'responsibility', 'certification', 'employment']
    text_lower = text.lower()
    keyword_count = sum(1 for keyword in resume_keywords if keyword in text_lower)
    if keyword_count >= 2:
        return True
    if re.search(r'\b(?:B\.?S|B\.?A|M\.?S|M\.?B\.?A|Ph\.?D\.?)\b', text):
        return True
    if re.search(r'\d{4}\s*(?:-|to)\s*\d{4}', text):
        return True
    return False

def _categorize_skills(skills_text: str) -> dict:
    """Categorize skills using hardcoded database (no LLM)."""
    all_skills = []
    skill_matches = re.findall(r'(?:^|\b|,\s*)([A-Z][A-Za-z0-9+\-.*#\s()]{1,30}?)(?:,|\s*$|\n)', skills_text)
    all_skills.extend([s.strip() for s in skill_matches if s.strip()])
    
    for delimiter in [',', '•', '|', '·', '-']:
        if delimiter in skills_text:
            parts = skills_text.split(delimiter)
            all_skills.extend([s.strip() for s in parts if 2 < len(s.strip()) < 50])
    
    categorized = {
        'programming_languages': [],
        'frameworks': [],
        'databases': [],
        'cloud_platforms': [],
        'tools': [],
        'soft_skills': []
    }
    
    seen = set()
    for skill in all_skills:
        skill_lower = skill.lower().strip()
        if skill_lower in seen or len(skill_lower) < 2:
            continue
        seen.add(skill_lower)
        
        if skill_lower in PROGRAMMING_LANGUAGES:
            categorized['programming_languages'].append(skill)
        elif any(fw.lower() in skill_lower or skill_lower in fw.lower() for fw in FRAMEWORKS):
            categorized['frameworks'].append(skill)
        elif any(db.lower() in skill_lower or skill_lower in db.lower() for db in DATABASES):
            categorized['databases'].append(skill)
        elif any(cp.lower() in skill_lower or skill_lower in cp.lower() for cp in CLOUD_PLATFORMS):
            categorized['cloud_platforms'].append(skill)
        elif any(tool.lower() in skill_lower or skill_lower in tool.lower() for tool in TOOLS_AND_PLATFORMS):
            categorized['tools'].append(skill)
        elif skill_lower in SOFT_SKILLS:
            categorized['soft_skills'].append(skill)
        else:
            categorized['tools'].append(skill)
    
    return categorized

def extract_email(text: str) -> Optional[str]:
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None

def extract_phone(text: str) -> Optional[str]:
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else None

def _clean_resume_text(text: str) -> str:
    """
    Cleans raw resume text to minimize prompt tokens:
    - Replaces emails, phone numbers, and URLs with small placeholders.
    - Strips lines that contain only contact identifiers, noise, or page numbers.
    - Collapses multiple whitespaces and consecutive blank lines.
    """
    # Replace email, phone, urls
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    text = re.sub(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r"https?://[^\s<>)\]]+", '[URL]', text)
    
    lines = []
    for line in text.split('\n'):
        cleaned_line = line.strip()
        # Skip empty lines or lines with page indicators (e.g. Page 1, 1 of 3)
        if not cleaned_line or re.match(r'^(?i:page)?\s*\d+\s*(?:of\s*\d+)?$', cleaned_line):
            continue
        # Remove placeholders and punctuation to see if semantic text remains
        temp = re.sub(r'\[(?:EMAIL|PHONE|URL)\]', '', cleaned_line)
        temp = re.sub(r'[\s|•·,\-_\/]+', '', temp)
        if not temp:
            continue
        lines.append(line)
        
    cleaned_text = '\n'.join(lines)
    # Remove duplicate empty lines and collapse multiple spaces
    cleaned_text = re.sub(r'\n\s*\n+', '\n\n', cleaned_text)
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
    return cleaned_text.strip()

# --- 1. Resume Parser Agent (HYBRID - Local Extraction + Shrunk Prompt LLM) ---
def _parse_resume_local_fallback(raw_text: str, pre_extracted: dict, link_evidence: list, resume_hash: str) -> dict:
    """Intelligent local resume parsing fallback using regex and hardcoded skills database."""
    logger.warning("Gemini API call failed or missing. Falling back to local heuristic resume parser.")
    edu_list = _extract_education(raw_text)
    grad_years = []
    for edu in edu_list:
        year_str = edu.get("year")
        if year_str:
            years = [int(y) for y in re.findall(r'\b(20\d{2}|19\d{2})\b', str(year_str))]
            if years:
                grad_years.append(max(years))
    fallback_years = 0.0
    if grad_years:
        import datetime
        fallback_years = float(datetime.datetime.now().year - min(grad_years))

    fallback_data = {
        **pre_extracted,
        'estimated_experience_years': fallback_years,
        'summary': f"Professional with {fallback_years} years of experience.",
        'career_level': 'Mid-Level' if fallback_years < 5 else 'Senior',
        'primary_domain': 'Software Engineering',
        'skills': list(_categorize_skills(raw_text).get('tools', []))[:10],
        'projects': [],
        'experience': _extract_experience(raw_text),
        'education': _extract_education(raw_text),
        'certifications': _extract_certifications(raw_text),
        'internships': [],
        'achievements': [],
        'languages': [],
        'domain_experience': [],
        'top_strengths': [],
        'potential_concerns': [],
        'links': [
            {
                'url': evidence['url'],
                'type': 'GitHub' if 'github' in evidence['url'].lower() else 'LinkedIn' if 'linkedin' in evidence['url'].lower() else 'Portfolio',
                'verified': evidence['status'] == 'fetched',
                'summary': evidence.get('text_excerpt', '')[:500],
                'skills_found': [],
                'projects_found': []
            }
            for evidence in link_evidence
        ]
    }
    normalized_data = normalize_resume_parsed(fallback_data)
    
    # Save fallback response to DB cache
    db = SessionLocal()
    try:
        db_cache = models.ResumeCache(raw_text_hash=resume_hash, parsed_json=normalized_data)
        db.add(db_cache)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to save fallback to ResumeCache: {e}")
    finally:
        db.close()
        
    return normalized_data

def parse_resume(raw_text: str, filename: Optional[str] = None) -> dict:
    """
    Parses resume using a hybrid approach:
    1. Checks the SQLite/Postgres database cache to avoid LLM calls for seen files.
    2. Extracts simple fields (Name, Email, Phone, Location, Headline, Links, Experience Years) locally.
    3. Sends cleaned semantic text to Gemini with a highly shrunk prompt to parse complex structured fields.
    4. Merges metadata and LLM outputs locally and saves to DB cache.
    """
    import hashlib
    resume_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()

    # 1. Check database cache first (using SHA256 hash match)
    db = SessionLocal()
    try:
        existing = db.query(models.ResumeCache).filter(models.ResumeCache.raw_text_hash == resume_hash).first()
        if existing and existing.parsed_json:
            cached_name = existing.parsed_json.get("candidate_name")
            is_valid_cache = True
            if cached_name:
                c_lower = cached_name.lower()
                if any(kw in c_lower for kw in ['psychologist', 'engineer', 'developer', 'trainer', 'intern']):
                    is_valid_cache = False
            else:
                is_valid_cache = False
                
            if is_valid_cache:
                return existing.parsed_json
    except Exception as e:
        logger.warning(f"Failed to query ResumeCache: {e}")
    finally:
        db.close()

    # Step 1: Pre-extract simple metadata fields locally
    cand_name = _extract_name(raw_text, filename)
    pre_extracted = {
        'candidate_name': cand_name,
        'email': extract_email(raw_text),
        'phone': extract_phone(raw_text),
        'location': _extract_location(raw_text),
        'headline': _extract_headline(raw_text, cand_name),
    }

    # Extract links and verify evidence
    resume_links = extract_urls(raw_text)
    link_evidence = fetch_public_link_evidence(resume_links) if resume_links else []
    
    linkedin_urls = [url for url in resume_links if 'linkedin.com' in url.lower()]
    github_urls = [url for url in resume_links if 'github.com' in url.lower()]
    portfolio_urls = [url for url in resume_links if any(x in url.lower() for x in ['portfolio', 'site', 'personal'])]
    
    pre_extracted['linkedin'] = linkedin_urls[0] if linkedin_urls else None
    pre_extracted['github'] = github_urls[0] if github_urls else None
    pre_extracted['portfolio'] = portfolio_urls[0] if portfolio_urls else None
    pre_extracted['website'] = None

    # Step 2: Use Gemini to infer and structure the complex fields
    if not GEMINI_API_KEY:
        return _parse_resume_local_fallback(raw_text, pre_extracted, link_evidence, resume_hash)

    # Preprocess text to strip out page numbers, duplicate spaces, and contact info block lines
    cleaned_text = _clean_resume_text(raw_text)

    # Highly optimized prompt containing only fields to be inferred/structured
    prompt = f"""You are Resume Intelligence Agent. Analyze the resume raw text and extract structured information.
Do not extract email, phone, name, location, headline, or links (these are already handled).
For "estimated_experience_years", calculate the total years of professional work experience (excluding college/education years, count only actual working years or years post-graduation).

Resume Raw Text:
{cleaned_text}

Return JSON matching exactly this schema:
{{
  "summary": "",
  "career_level": "",
  "primary_domain": "",
  "estimated_experience_years": 0.0,
  "skills": [], "technical_skills": [], "soft_skills": [], "programming_languages": [], "frameworks": [], "databases": [], "cloud_platforms": [], "tools": [],
  "projects": [{{"title": "", "description": "", "technologies": [], "github": "", "demo": "", "contributions": []}}],
  "experience": [{{"title": "", "company": "", "employment_type": "", "duration": "", "responsibilities": [], "achievements": [], "technologies": []}}],
  "education": [{{"degree": "", "branch": "", "institution": "", "year": "", "cgpa": ""}}],
  "certifications": [],
  "internships": [{{"company": "", "role": "", "duration": "", "summary": ""}}],
  "achievements": [], "languages": [], "domain_experience": [], "top_strengths": [], "potential_concerns": []
}}"""

    try:
        raw_res = call_gemini_json(prompt)
        if not isinstance(raw_res, dict):
            raw_res = {}
            
        # Combine pre-extracted fields with Gemini's inferred fields
        # Priority mapping: prevent Gemini from overwriting local values with null/wrong keys
        parsed_data = {**raw_res}
        for k, v in pre_extracted.items():
            if v:
                parsed_data[k] = v
                
        parsed_data['links'] = [
            {
                'url': evidence['url'],
                'type': 'GitHub' if 'github' in evidence['url'].lower() else 'LinkedIn' if 'linkedin' in evidence['url'].lower() else 'Portfolio',
                'verified': evidence['status'] == 'fetched',
                'summary': evidence.get('text_excerpt', '')[:500],
                'skills_found': [],
                'projects_found': []
            }
            for evidence in link_evidence
        ]
        
        normalized_data = normalize_resume_parsed(parsed_data)
        
        # Save successful result to database cache
        db = SessionLocal()
        try:
            db_cache = models.ResumeCache(raw_text_hash=resume_hash, parsed_json=normalized_data)
            db.add(db_cache)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to save result to ResumeCache: {e}")
        finally:
            db.close()
            
        return normalized_data
    except Exception as e:
        logger.warning(f"Resume Agent Gemini call failed: {e}. Falling back to local heuristic parser.")
        return _parse_resume_local_fallback(raw_text, pre_extracted, link_evidence, resume_hash)

def _extract_name_from_filename(filename: str) -> Optional[str]:
    if not filename:
        return None
    import os
    # Strip extension
    base = os.path.splitext(filename)[0]
    # Replace non-alphabetic separators with spaces
    base = re.sub(r'[^A-Za-z\s]', ' ', base)
    
    # Generic keywords to discard
    generic_kws = {
        'resume', 'cv', 'cover', 'letter', 'job', 'application', 'final', 
        'draft', 'format', 'english', 'update', 'latest', 'hiring', 
        'profile', 'portfolio', 'work', 'experience', 'standard', 'official',
        'candidate', 'assessment', 'template'
    }
    
    words = base.split()
    cleaned_words = [w for w in words if w.lower() not in generic_kws]
    
    if len(cleaned_words) >= 2:
        name = " ".join([w.capitalize() for w in cleaned_words])
        if len(name) > 3 and len(name) < 40:
            return name
    return None

def _extract_name(text: str, filename: Optional[str] = None) -> Optional[str]:
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Skip contact info labels and common section titles
    section_headers = {
        'contact', 'email', 'phone', 'resume', 'cv', 'about', 'summary', 'skills', 
        'education', 'experience', 'projects', 'certifications', 'hobbies', 'languages',
        'achievements', 'objective', 'profile', 'work', 'history', 'timeline'
    }
    
    headline_keywords = {
        'engineer', 'developer', 'architect', 'analyst', 'manager', 'lead', 'senior', 
        'junior', 'student', 'intern', 'certified', 'certification', 'associate', 
        'consultant', 'director', 'specialist', 'professional', 'practitioner',
        'administrator', 'expert', 'scrum', 'agile'
    }
    
    # 1. Heuristic search in top lines (Resume Header / Text)
    for line in lines[:8]:
        line_lower = line.lower()
        
        # Skip if contains contact symbols or is too long
        if '@' in line or '/' in line or '\\' in line or ':' in line or '|' in line or len(line) > 40:
            continue
        if any(char.isdigit() for char in line):
            continue
            
        # Skip if it is a section header or contains headline words
        words = line.split()
        if not words or len(words) < 2 or len(words) > 4:
            continue
            
        if any(w.lower() in section_headers for w in words):
            continue
        if any(w.lower() in headline_keywords for w in words):
            continue
            
        # Check if all words are capitalized (title case) or uppercase
        is_capitalized = all(w[0].isupper() or w.isupper() for w in words if w.isalpha())
        if is_capitalized:
            return " ".join([w.capitalize() for w in words])
            
    # 2. Try filename as a fallback only if header search fails
    if filename:
        filename_name = _extract_name_from_filename(filename)
        if filename_name:
            return filename_name

    # 3. Fallback to the first line if it's short and has no digits
    if lines:
        first_line = lines[0]
        if len(first_line) < 30 and not any(char.isdigit() for char in first_line) and '@' not in first_line:
            words = first_line.split()
            if len(words) >= 1:
                return " ".join([w.capitalize() for w in words])
                
    return "Candidate Name"

def _extract_location(text: str) -> Optional[str]:
    location_pattern = r'\b([A-Z][a-z]+),\s*([A-Z]{2}|[A-Z][a-z\s]+)\b'
    matches = re.findall(location_pattern, text)
    if matches:
        return f"{matches[0][0]}, {matches[0][1]}"
    return None

def _extract_headline(text: str, candidate_name: Optional[str] = None) -> Optional[str]:
    lines = text.split('\n')
    for line in lines[:15]:
        line = line.strip()
        if candidate_name and line.lower() == candidate_name.lower():
            continue
        if any(keyword in line.lower() for keyword in ['email', 'phone', 'address', 'education', 'experience', 'skills', 'contact']):
            continue
        if 5 < len(line) < 100 and any(title_word in line.lower() for title_word in 
            ['engineer', 'developer', 'architect', 'manager', 'lead', 'senior', 'junior', 
             'analyst', 'scientist', 'designer', 'director', 'specialist', 'consultant']):
            return line
    return None

def _extract_experience(text: str) -> list:
    experience = []
    sections = re.split(r'\n(?:EXPERIENCE|PROFESSIONAL EXPERIENCE|WORK HISTORY|Career History)\s*\n', text, flags=re.IGNORECASE)
    exp_section = sections[1] if len(sections) > 1 else text
    
    job_pattern = r'([A-Z][A-Za-z\s&,]+?)(?:\s+at\s+|\s*@\s*)([A-Z][A-Za-z\s&,0-9.]+?)\s*\|?\s*\(?([\w\s,\-\/]+?)\)?(?:\n|$)'
    
    for match in re.finditer(job_pattern, exp_section):
        job_title, company, duration = match.groups()
        if len(job_title) > 100 or len(company) > 80:
            continue
        experience.append({
            'title': job_title.strip(),
            'company': company.strip(),
            'employment_type': None,
            'duration': duration.strip() if duration else None,
            'responsibilities': [],
            'achievements': [],
            'technologies': []
        })
    
    return experience

def _extract_education(text: str) -> list:
    education = []
    # Split text into sections to locate Education
    sections = re.split(r'\n(?:EDUCATION|ACADEMIC|ACADEMICS|QUALIFICATIONS|EDUCATION & CREDENTIALS)\s*\n', text, flags=re.IGNORECASE)
    if len(sections) > 1:
        edu_block = sections[1]
        edu_block = re.split(r'\n(?:EXPERIENCE|PROFESSIONAL|WORK|SKILLS|PROJECTS|PUBLICATIONS|CERTIFICATIONS|INTERNSHIPS)\b', edu_block, flags=re.IGNORECASE)[0]
    else:
        edu_block = text

    lines = [l.strip() for l in edu_block.split('\n') if l.strip()]
    
    current_edu = {}
    degree_keywords = ['bachelor', 'master', 'ph.d', 'phd', 'diploma', 'associate', 'b.s', 'b.a', 'b.tech', 'm.s', 'm.tech', 'm.b.a', 'mba', 'b.c.a', 'm.c.a', 'school', 'bsc', 'msc']
    inst_keywords = ['university', 'college', 'institute', 'academy', 'school', 'iit', 'nit', 'bits']

    for line in lines:
        line_lower = line.lower()
        
        # Check if line contains a degree
        found_degree = None
        for dk in degree_keywords:
            if re.search(r'\b' + re.escape(dk) + r'\b', line_lower):
                found_degree = dk.upper()
                break
        
        # Check if line contains an institution
        found_inst = None
        for ik in inst_keywords:
            if re.search(r'\b' + re.escape(ik) + r'\b', line_lower):
                found_inst = line
                break
                
        # Look for a year
        year_match = re.search(r'\b(20\d{2}|19\d{2})\b', line)
        
        # Look for CGPA
        cgpa_match = re.search(r'\b(?:gpa|cgpa|grade|score)?\s*:?\s*([0-9]+(?:\.[0-9]+)?(?:\s*/\s*[0-9]+)?)\b', line_lower)
        
        if found_degree or found_inst or year_match:
            if current_edu and found_degree and current_edu.get("degree"):
                education.append({
                    "degree": current_edu.get("degree"),
                    "branch": current_edu.get("branch"),
                    "institution": current_edu.get("institution") or "University",
                    "year": current_edu.get("year"),
                    "cgpa": current_edu.get("cgpa")
                })
                current_edu = {}
                
            if found_degree:
                branch_match = re.search(r'(?:in|of)\s+([A-Za-z\s]{3,30})', line, re.IGNORECASE)
                current_edu["degree"] = line
                if branch_match:
                    current_edu["branch"] = branch_match.group(1).strip()
            
            if found_inst:
                current_edu["institution"] = found_inst
                
            if year_match:
                current_edu["year"] = year_match.group(1)
                
            if cgpa_match:
                current_edu["cgpa"] = cgpa_match.group(1).strip()
                
    if current_edu:
        education.append({
            "degree": current_edu.get("degree") or "Degree",
            "branch": current_edu.get("branch"),
            "institution": current_edu.get("institution") or "University",
            "year": current_edu.get("year"),
            "cgpa": current_edu.get("cgpa")
        })
        
    return education

def _extract_certifications(text: str) -> list:
    certs = []
    cert_patterns = [
        r'(?:Certified|Certification):?\s*([A-Z][^\n,]{15,100})',
        r'AWS Certified[^\n,]+',
        r'Google Cloud Certified[^\n,]+',
        r'Azure Certified[^\n,]+',
        r'Kubernetes[^\n,]+',
        r'(?:PMP|CISSP|CCNA|ACED|OSCP)[^\n,]*'
    ]
    
    for pattern in cert_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        certs.extend(matches)
    
    return list(set(certs))[:10]

# --- 2. JD Parser Agent ---
def _parse_jd_heuristics(raw_text: str) -> dict:
    """Intelligent local JD parser that extracts core requirements using NLP heuristics."""
    logger.warning("Gemini API call failed or missing. Falling back to local heuristic JD parser.")
    
    # 1. Title Extraction
    title = "Software Engineer"
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    for line in lines[:5]:
        if len(line) < 60 and any(keyword in line.lower() for keyword in ['engineer', 'developer', 'architect', 'manager', 'lead', 'senior', 'junior', 'analyst', 'specialist']):
            title = line
            break
            
    # 2. Seniority detection
    seniority = "Mid-level"
    raw_lower = raw_text.lower()
    if "senior" in raw_lower or "sr" in raw_lower:
        seniority = "Senior"
    elif "junior" in raw_lower or "jr" in raw_lower:
        seniority = "Junior"
    elif "lead" in raw_lower or "principal" in raw_lower:
        seniority = "Lead"
    elif "director" in raw_lower or "manager" in raw_lower:
        seniority = "Manager"
        
    # 3. Experience requirements extraction
    exp = "2+ years"
    exp_match = re.search(r'\b(\d+\s*\+?\s*(?:years|yrs))\b', raw_lower)
    if exp_match:
        exp = exp_match.group(1).capitalize()
        
    # 4. Industry/Domain detection
    industry = "Technology"
    if any(k in raw_lower for k in ["fintech", "payment", "bank", "finance"]):
        industry = "Fintech"
    elif any(k in raw_lower for k in ["health", "medical", "clinic", "biotech"]):
        industry = "Healthcare"
    elif any(k in raw_lower for k in ["retail", "commerce", "shop"]):
        industry = "E-Commerce"
        
    # 5. Skills extraction
    required_skills = []
    preferred_skills = []
    
    all_known_skills = PROGRAMMING_LANGUAGES | FRAMEWORKS | DATABASES | CLOUD_PLATFORMS | TOOLS_AND_PLATFORMS
    detected = []
    for skill in all_known_skills:
        # Match using word boundaries
        if re.search(r'\b' + re.escape(skill) + r'\b', raw_lower):
            display_name = skill.upper() if skill in ["aws", "sql", "ci/cd", "gcp"] else skill.capitalize()
            detected.append(display_name)
            
    # Divide detected skills into required (first 5) and preferred (others)
    if detected:
        required_skills = detected[:6]
        preferred_skills = detected[6:10]
    else:
        required_skills = ["Python", "SQL", "Git"]
        preferred_skills = ["Docker", "AWS"]
        
    # 6. Responsibilities extraction
    responsibilities = []
    bullet_lines = [l.strip().lstrip('*-•').strip() for l in raw_text.split('\n') if l.strip().startswith(('*', '-', '•'))]
    if bullet_lines:
        responsibilities = bullet_lines[:5]
    else:
        responsibilities = [
            "Write high-quality, maintainable backend code.",
            "Collaborate with product managers and other engineers.",
            "Design and optimize relational databases."
        ]
        
    return {
        "title": title,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "industry": industry,
        "seniority": seniority,
        "experience": exp,
        "responsibilities": responsibilities,
        "domain": industry,
        "leadership_expectations": ["Mentor junior developers" if seniority in ["Senior", "Lead", "Manager"] else "Participate in team sessions"],
        "communication_expectations": ["Explain technical choices and trade-offs clearly"]
    }

def parse_jd(raw_text: str) -> dict:
    if not GEMINI_API_KEY:
        return _parse_jd_heuristics(raw_text)
        
    prompt = f"""You are an expert recruiter parsing a Job Description. Extract:
- title
- required_skills (must-have)
- preferred_skills (nice-to-have)
- industry
- seniority (Junior, Mid, Senior, Lead, Director)
- experience
- responsibilities
- domain
- leadership_expectations
- communication_expectations

Job Description Raw Text:
{raw_text}

Return JSON matching exactly this schema:
{{
  "title": "",
  "required_skills": [],
  "preferred_skills": [],
  "industry": "",
  "seniority": "",
  "experience": "",
  "responsibilities": [],
  "domain": "",
  "leadership_expectations": [],
  "communication_expectations": []
}}"""
    try:
        return call_gemini_json(prompt)
    except Exception as e:
        logger.warning(f"JD Agent Gemini call failed: {e}. Falling back to local heuristic JD parser.")
        return _parse_jd_heuristics(raw_text)

# --- 3. Match Agent ---
def match_resume_and_jd(resume_parsed: dict, jd_parsed: dict) -> dict:
    return deterministic_match_resume_and_jd(resume_parsed, jd_parsed)

def _normalize_skill(skill: str) -> str:
    return " ".join(str(skill).lower().replace("-", " ").replace("_", " ").split())

def _display_skill(skill: str) -> str:
    cleaned = " ".join(str(skill).replace("_", " ").split())
    return cleaned.upper() if cleaned.lower() in {"aws", "sql", "ci/cd"} else cleaned

def _collect_resume_skills(resume_parsed: dict) -> set:
    skills = set()
    
    # 1. Direct skills lists
    skill_fields = [
        "skills",
        "technical_skills",
        "programming_languages",
        "frameworks",
        "databases",
        "cloud_platforms",
        "tools",
        "certifications"
    ]
    for field in skill_fields:
        for val in resume_parsed.get(field, []) or []:
            skills.add(_normalize_skill(val))
            
    # 2. Experience technologies
    for exp in resume_parsed.get("experience", []) or []:
        for tech in exp.get("technologies", []) or []:
            skills.add(_normalize_skill(tech))
            
    # 3. Project technologies
    for proj in resume_parsed.get("projects", []) or []:
        for tech in (proj.get("technologies") or proj.get("tools") or []):
            skills.add(_normalize_skill(tech))
            
    # 4. Link skills
    for link in resume_parsed.get("links", []) or []:
        for skill in link.get("skills_found", []) or []:
            skills.add(_normalize_skill(skill))
            
    return {skill for skill in skills if skill}

def _collect_jd_required(jd_parsed: dict) -> set:
    return {_normalize_skill(skill) for skill in (jd_parsed.get("required_skills", []) or []) if skill}

def _collect_jd_preferred(jd_parsed: dict) -> set:
    return {_normalize_skill(skill) for skill in (jd_parsed.get("preferred_skills", []) or []) if skill}

def deterministic_match_resume_and_jd(resume_parsed: dict, jd_parsed: dict) -> dict:
    """Transparent match model: no LLM scoring, only structured JSON comparison."""
    resume_skills = _collect_resume_skills(resume_parsed)
    required = _collect_jd_required(jd_parsed)
    preferred = _collect_jd_preferred(jd_parsed)
    jd_skills = required | preferred

    matched_required = required & resume_skills
    matched_preferred = preferred & resume_skills
    missing_required = required - resume_skills
    missing_preferred = preferred - resume_skills
    additional = resume_skills - jd_skills

    required_score = (len(matched_required) / len(required) * 70) if required else 70
    preferred_score = (len(matched_preferred) / len(preferred) * 20) if preferred else 20

    domain_values = resume_parsed.get("domain_experience", []) or []
    domain_text = " ".join(str(item).lower() for item in domain_values)
    jd_domain = str(jd_parsed.get("domain") or jd_parsed.get("industry") or "").lower()
    domain_score = 10 if jd_domain and any(part in domain_text for part in jd_domain.split()) else 0
    match_score = min(100, round(required_score + preferred_score + domain_score))

    evidence = []
    for skill in sorted(jd_skills):
        found = skill in resume_skills
        evidence.append({
            "skill": _display_skill(skill),
            "status": "Found" if found else "Not Found",
            "source": "Detected in structured resume skills, project tools, or certifications." if found else "Not present in structured resume profile."
        })

    gaps = [
        {
            "skill": _display_skill(skill),
            "description": "Required capability missing from the structured resume profile."
        }
        for skill in sorted(missing_required)
    ] + [
        {
            "skill": _display_skill(skill),
            "description": "Preferred capability not found; validate during assessment if relevant."
        }
        for skill in sorted(missing_preferred)
    ]

    strengths = [
        f"Matches {len(matched_required)} of {len(required)} required skills."
    ]
    if matched_preferred:
        strengths.append(f"Also covers preferred skills: {', '.join(_display_skill(s) for s in sorted(matched_preferred))}.")
    if additional:
        strengths.append(f"Brings adjacent capabilities: {', '.join(_display_skill(s) for s in sorted(additional)[:6])}.")

    readiness_details = [
        {"name": "Required Skill Coverage", "score": round(len(matched_required) / len(required) * 100) if required else 100},
        {"name": "Preferred Skill Coverage", "score": round(len(matched_preferred) / len(preferred) * 100) if preferred else 100},
        {"name": "Domain Alignment", "score": 100 if domain_score else 55},
        {"name": "Ramp Risk", "score": max(35, 100 - (len(missing_required) * 18) - (len(missing_preferred) * 7))},
        {"name": "Assessment Priority", "score": min(100, 55 + (len(missing_required) * 12) + (len(missing_preferred) * 5))}
    ]

    # Generate explainable matching justifications list
    justifications = []
    
    # 1. Required skills match check
    total_req = len(required)
    match_req = len(matched_required)
    if total_req > 0:
        justifications.append({
            "type": "success" if match_req >= total_req * 0.7 else "warning",
            "text": f"Matches {match_req}/{total_req} required skills ({', '.join(_display_skill(s) for s in sorted(matched_required)[:5])}{' and more' if len(matched_required) > 5 else ''})"
        })
    else:
        justifications.append({
            "type": "success",
            "text": "No required skills specified in Job Description."
        })
        
    # 2. Experience year check
    experience_years = resume_parsed.get("estimated_experience_years")
    if isinstance(experience_years, (int, float)):
        jd_exp_str = str(jd_parsed.get("experience", "") or "")
        match_exp = re.search(r'(\d+)', jd_exp_str)
        if match_exp:
            jd_req_years = int(match_exp.group(1))
            if experience_years >= jd_req_years:
                justifications.append({
                    "type": "success",
                    "text": f"Experience exceeds requirement: candidate has {int(experience_years)} years vs {jd_req_years}+ required"
                })
            else:
                justifications.append({
                    "type": "warning",
                    "text": f"Experience shortfall: candidate has {int(experience_years)} years vs {jd_req_years}+ required"
                })
        else:
            justifications.append({
                "type": "success",
                "text": f"Candidate has {int(experience_years)} years of estimated experience"
            })
            
    # 3. Domain alignment check
    if domain_score > 0:
        justifications.append({
            "type": "success",
            "text": f"Strong domain alignment: {resume_parsed.get('primary_domain', 'Candidate domain')} matches target domain"
        })
    else:
        justifications.append({
            "type": "info",
            "text": "No direct domain overlap detected (candidate domain is different from job description)"
        })
        
    # 4. Gaps checks (up to 3 required missing)
    for s in sorted(missing_required)[:3]:
        justifications.append({
            "type": "warning",
            "text": f"Missing required skill: {_display_skill(s)}"
        })
        
    # If no certifications
    has_certs = bool(resume_parsed.get("certifications", []))
    if not has_certs:
        justifications.append({
            "type": "info",
            "text": "No certifications or professional licenses detected in profile"
        })

    return {
        "matchScore": match_score,
        "calculation": {
            "requiredWeight": 70,
            "preferredWeight": 20,
            "domainWeight": 10,
            "requiredMatched": len(matched_required),
            "requiredTotal": len(required),
            "preferredMatched": len(matched_preferred),
            "preferredTotal": len(preferred)
        },
        "roleInfo": {
            "title": jd_parsed.get("title") or jd_parsed.get("role") or "Target Role",
            "industry": jd_parsed.get("industry", "Not specified"),
            "seniority": jd_parsed.get("seniority", "Not specified")
        },
        "readinessDetails": readiness_details,
        "strengths": strengths,
        "gaps": gaps,
        "justifications": justifications,
        "matched_skills": [_display_skill(skill) for skill in sorted(matched_required | matched_preferred)],
        "missing_skills": [_display_skill(skill) for skill in sorted(missing_required | missing_preferred)],
        "additional_skills": [_display_skill(skill) for skill in sorted(additional)],
        "evidence": evidence
    }

def generate_assessment_blueprint(jd_parsed: dict, match_analysis: dict) -> dict:
    missing_count = len(match_analysis.get("missing_skills", []) or [])
    seniority = str(jd_parsed.get("seniority", "")).lower()
    leadership_questions = 2 if any(key in seniority for key in ["senior", "lead", "director", "manager"]) else 1
    technical_questions = 4 if missing_count >= 3 else 3
    scenario_questions = 3 if missing_count >= 2 else 2
    behavioral_questions = 2
    resume_validation = 2
    total_questions = resume_validation + technical_questions + scenario_questions + behavioral_questions + leadership_questions

    return {
        "modules": [
            {"name": "Resume Validation", "questions": resume_validation, "focus": "Verify claimed experience, ownership, and project evidence."},
            {"name": "Technical Questions", "questions": technical_questions, "focus": "Probe required skills and missing competencies."},
            {"name": "Scenario Questions", "questions": scenario_questions, "focus": "Evaluate applied judgment in realistic role situations."},
            {"name": "Behavioral Questions", "questions": behavioral_questions, "focus": "Assess collaboration, accountability, and operating style."},
            {"name": "Leadership Questions", "questions": leadership_questions, "focus": "Validate mentoring, decision-making, and stakeholder communication."}
        ],
        "estimatedDurationMinutes": max(30, total_questions * 4),
        "priorityGaps": match_analysis.get("missing_skills", [])[:5],
        "role": jd_parsed.get("title") or jd_parsed.get("role") or "Target Role"
    }
# --- 4. Interview Planner Agent ---
def _plan_interview_roadmap_local(resume_parsed: dict, jd_parsed: dict, match_analysis: dict) -> dict:
    """Fallback programmatic planner that outputs question counts dynamically."""
    seniority = jd_parsed.get("seniority", "Mid")
    role = jd_parsed.get("title", "Software Engineer")
    industry = jd_parsed.get("industry", "Technology")
    gaps = match_analysis.get("gaps", [])
    
    roadmap = {"Technical": 1, "Scenario": 1, "Behavioral": 1}
    
    # Adjust programmatically based on gaps
    has_behavioral_gap = False
    for gap in gaps:
        desc = gap.get("description", "").lower()
        if any(k in desc for k in ["compliance", "soc2", "audit", "leadership", "mentoring", "team"]):
            has_behavioral_gap = True
            
    if seniority in ["Senior", "Lead", "Director"]:
        roadmap["Scenario"] = 2
        if has_behavioral_gap:
            roadmap["Leadership"] = 2
        else:
            roadmap["Technical"] = 2
    elif seniority in ["Junior", "Intern"]:
        # Juniors focus heavily on technical fundamentals
        roadmap["Technical"] = 3
        roadmap["Scenario"] = 1
        roadmap["Behavioral"] = 1
    else:
        if has_behavioral_gap:
            roadmap["Behavioral"] = 2
        else:
            roadmap["Technical"] = 2
            
    return roadmap

def plan_interview_roadmap(resume_parsed: dict, jd_parsed: dict, match_analysis: dict) -> dict:
    if not GEMINI_API_KEY:
        return _plan_interview_roadmap_local(resume_parsed, jd_parsed, match_analysis)
        
    prompt = f"""
    You are the Interview Planner Agent. Based on the candidate's parsed Resume, target Job Description (JD), and match analysis (including gaps, seniority, role title, and industry), formulate a custom question distribution roadmap.
    
    Candidate Resume:
    {json.dumps(resume_parsed, indent=2)}
    
    Job Description:
    {json.dumps(jd_parsed, indent=2)}
    
    Match Analysis:
    {json.dumps(match_analysis, indent=2)}
    
    Guidelines:
    - Allocate a question count (integer from 1 to 3) for categories: "Technical", "Scenario", "Behavioral", "Leadership".
    - Total questions must be between 3 and 6.
    - Tailor the roadmap structure based on the candidate's seniority:
      - Juniors: Focus on foundational fundamentals ("Technical": 2-3).
      - Seniors: Focus on design, scaling, and architectural decisions ("Scenario": 2-3).
      - Managers/Leads: Focus on alignment, mentoring, and conflict resolution ("Leadership": 2-3).
    - Tailor the questions to the industry and role (e.g. Fintech needs compliance/security, healthcare needs HIPAA/privacy).
    - Target match weaknesses. If gaps exist in technical tools like Kafka, allocate more Scenario/Technical. If gaps exist in compliance or mentoring, allocate Leadership/Behavioral.
    
    Return JSON matching this schema:
    {{
      "Technical": 2,
      "Scenario": 2,
      "Behavioral": 1,
      "Leadership": 1
    }}
    """
    try:
        return call_gemini_json(prompt)
    except Exception as e:
        logger.warning(f"Interview Planner Agent Gemini call failed: {e}. Falling back to programmatic roadmap planner.")
        return _plan_interview_roadmap_local(resume_parsed, jd_parsed, match_analysis)

# --- 5. Interview Agent (Adaptive Question Formulation) ---
def generate_question(resume: dict, jd: dict, history: list, category: str, difficulty: str, memory: dict = None) -> str:
    if not GEMINI_API_KEY:
        return get_mock_question(category, difficulty, offset=len(history) if history else 0)
        
    memory_guidelines = ""
    if memory:
        if memory.get("needs_followup") and memory.get("followup_context"):
            ctx = memory["followup_context"]
            memory_guidelines = f"""
            CRITICAL: The candidate's last answer to: "{ctx.get('question')}" was evaluated as lacking depth or clarity.
            The answer was: "{ctx.get('answer')}".
            Do NOT advance to a new topic or category. Instead, formulate a direct, professional follow-up or clarification question targeting their last response. Ask them to clarify or expand.
            """
        else:
            tested = memory.get("tested_skills", [])
            untested = memory.get("untested_skills", [])
            weak = memory.get("weak_skills", [])
            memory_guidelines = f"""
            Guidelines based on Session Memory:
            - Already tested skills: {json.dumps(tested)}. Avoid repeating tested skills or concepts.
            - Untested skills from JD requiring coverage: {json.dumps(untested)}. Target one of these skills if appropriate for the category.
            - Weak areas detected: {json.dumps(weak)}. Focus on asking questions that explore these gaps.
            """
         
    prompt = f"""
    You are an expert interviewer simulating a technical screening for the role: "{jd.get('title', 'Software Engineer')}".
    Formulate the next interview question.
    
    Category requested: {category}
    Difficulty target: {difficulty}
    
    Candidate Background:
    {json.dumps(resume, indent=2)}
    
    JD Core Requirements:
    {json.dumps(jd, indent=2)}
    
    Interview Session History (Questions asked & evaluation):
    {json.dumps(history, indent=2)}
    
    {memory_guidelines}
    
    Guidelines:
    - Create a realistic, high-end professional interview query.
    - KEEP the question extremely brief, direct, and conversational (maximum 1 to 2 sentences, under 40 words total).
    - Do NOT bundle multiple sub-questions, options, or preambles. Focus on asking exactly one clear thing at a time.
    - Do NOT mention "AI", "Agent", or structural instructions. Make it sound like a human peer interviewer.
    - Return ONLY the question text in JSON format.
    
    Return JSON matching this schema:
    {{
      "question": "The question text goes here."
    }}
    """
    try:
        res = call_gemini_json(prompt)
        question = res.get("question")
        if not question:
            raise RuntimeError("Gemini response did not include a question field.")
        return question
    except Exception as e:
        logger.warning(f"Question Generator Agent Gemini call failed: {e}. Falling back to mock question generator.")
        return get_mock_question(category, difficulty, offset=len(history) if history else 0)

def judge_answer_heuristics(question: str, answer: str, signals: dict) -> dict:
    """Fallback rule-based Judge to handle API rate-limit/quota errors dynamically."""
    logger.warning("Gemini API call failed or quota exceeded. Falling back to heuristic scoring model.")
    
    # 1. Base Scores
    accuracy = 70
    depth = 65
    communication = 70
    practicality = 65
    problem_solving = 65
    business_thinking = 65
    
    words = answer.split()
    word_count = len(words)
    
    # Heuristics based on answer details
    # 2. Length-based upgrades
    if word_count > 150:
        communication += 10
        depth += 10
    elif word_count > 80:
        communication += 5
        depth += 5
    elif word_count < 15:
        accuracy -= 20
        depth -= 25
        communication -= 15
        
    # 3. Context keywords indicators
    ans_lower = answer.lower()
    
    # Analytical logic
    if any(k in ans_lower for k in ["because", "since", "why", "therefore", "consequently"]):
        problem_solving += 10
        
    # Technical depth indicators
    tech_keywords = ["trade-off", "performance", "bottleneck", "scaling", "cache", "latency", "index", "database", "concurrency", "architecture", "design pattern", "refactor", "complexity", "big o"]
    matched_tech = sum(1 for kw in tech_keywords if kw in ans_lower)
    depth += min(20, matched_tech * 4)
    
    # Practicality / execution indicators
    practical_keywords = ["implement", "testing", "deploy", "ci/cd", "docker", "kubernetes", "script", "migration", "production", "monitoring", "git", "log", "metrics"]
    matched_prac = sum(1 for kw in practical_keywords if kw in ans_lower)
    practicality += min(20, matched_prac * 4)
    
    # Business / Product alignment indicators
    business_keywords = ["cost", "user experience", "ux", "revenue", "priority", "roi", "sla", "business requirement", "client", "stakeholder", "budget", "deliverable"]
    matched_biz = sum(1 for kw in business_keywords if kw in ans_lower)
    business_thinking += min(20, matched_biz * 4)
    
    # STAR structure detection
    situation_found = any(k in ans_lower for k in ["situation", "context", "background", "project", "when i was", "at my last"]) or word_count > 40
    task_found = any(k in ans_lower for k in ["task", "goal", "objective", "requirement", "needed to", "assigned to"]) or word_count > 60
    action_found = any(k in ans_lower for k in ["action", "did", "implemented", "solved", "wrote", "built", "engineered"]) or word_count > 80
    result_found = any(k in ans_lower for k in ["result", "outcome", "consequently", "reduced", "improved", "saved", "percent", "%", "finally"]) or word_count > 100
    
    # Communication adjustments from signals
    latency = signals.get("latencySeconds") or signals.get("responseTime") or 0.0
    filler_count = signals.get("fillerCount") or 0
    
    if latency > 120:
        communication -= 10 # Extremely slow pacing
    elif 15 <= latency <= 50:
        communication += 10 # Ideal conversational pacing
        
    if filler_count > 8:
        communication -= 8
        
    # Clamp scores to 0-100 range
    accuracy = max(10, min(98, accuracy))
    depth = max(10, min(98, depth))
    communication = max(10, min(98, communication))
    practicality = max(10, min(98, practicality))
    problem_solving = max(10, min(98, problem_solving))
    business_thinking = max(10, min(98, business_thinking))
    
    # Feedback building
    feedback_points = []
    if depth > 80:
        feedback_points.append("Excellent technical depth with detailed architectural references.")
    elif depth < 50:
        feedback_points.append("Try to provide deeper technical justifications and discuss trade-offs.")
        
    if not result_found:
        feedback_points.append("Include specific metric outcomes (STAR Result element) to strengthen your response.")
    else:
        feedback_points.append("Good usage of outcomes and result metrics to anchor the answer.")
        
    if filler_count > 5:
        filler_feedback = f"Slightly high frequency of filler words ({filler_count} pauses detected). Focus on breathing and pacing."
    else:
        filler_feedback = "Strong verbal pacing and clear delivery with low filler counts."
        
    return {
        "accuracy": accuracy,
        "depth": depth,
        "communication": communication,
        "practicality": practicality,
        "problemSolving": problem_solving,
        "businessThinking": business_thinking,
        "starFramework": {
            "situation": situation_found,
            "task": task_found,
            "action": action_found,
            "result": result_found
        },
        "feedback": " ".join(feedback_points) or "Reasonable response structure. Keep discussing practical trade-offs.",
        "fillerWordFeedback": filler_feedback
    }

# --- 6. Judge Agent ---
def judge_answer(question: str, answer: str, signals: dict) -> dict:
    if not GEMINI_API_KEY:
        return get_mock_evaluation(question, answer, signals)
        
    prompt = f"""
    Evaluate the candidate's response to an interview question.
    
    Question Asked:
    {question}
    
    Candidate Answer:
    {answer}
    
    Pacing/Delivery Signals:
    {json.dumps(signals, indent=2)}
    
    Evaluate and score (0 to 100) on:
    1. Accuracy: How correct is the response?
    2. Depth: Does the response demonstrate senior/architectural understanding or is it superficial?
    3. Communication: Is it structured, clear, and professional?
    4. Practicality: How realistic and executable is their described approach?
    5. Problem Solving: Does it solve the query's root constraints?
    6. Business Thinking: Does it align technical trade-offs with business priorities?
    
    Also, detect the STAR Framework structure (Situation, Task, Action, Result) in their answer.
    Determine whether the answer elements cover the Situation, the Task, the Action, and the Result.
    
    Provide constructive feedback points.
    
    Return JSON matching this schema:
    {{
      "accuracy": 85,
      "depth": 80,
      "communication": 90,
      "practicality": 85,
      "problemSolving": 80,
      "businessThinking": 75,
      "starFramework": {{
        "situation": true,
        "task": true,
        "action": true,
        "result": false
      }},
      "feedback": "Short feedback summary.",
      "fillerWordFeedback": "Feedback on speech pace / pauses / filler counts."
    }}
    """
    try:
        return call_gemini_json(prompt)
    except Exception as e:
        logger.warning(f"Judge Agent Gemini call failed: {e}. Degrading gracefully to heuristic rule-based evaluator.")
        return judge_answer_heuristics(question, answer, signals)

# --- 7. Memory Agent ---
def update_memory(current_memory: dict, question: str, answer: str, evaluation: dict, jd_parsed: dict = None) -> dict:
    if not current_memory:
        current_memory = {
            "demonstrated_skills": [],
            "weak_skills": [],
            "topics_covered": [],
            "confidence_by_skill": {},
            "questions_asked": [],
            "tested_skills": [],
            "untested_skills": [],
            "followup_count": 0,
            "needs_followup": False,
            "followup_context": None
        }
        
    if "questions_asked" not in current_memory:
        current_memory["questions_asked"] = []
    if question not in current_memory["questions_asked"]:
        current_memory["questions_asked"].append(question)
        
    # Initialize untested/tested skills from JD if present
    if jd_parsed and not current_memory.get("untested_skills") and not current_memory.get("tested_skills"):
        req = jd_parsed.get("required_skills", [])
        pref = jd_parsed.get("preferred_skills", [])
        all_jd_skills = list(set(req + pref))
        current_memory["untested_skills"] = all_jd_skills
        current_memory["tested_skills"] = []

    # If Gemini API Key is present, extract skills, topics, and evidence using LLM
    if GEMINI_API_KEY:
        prompt = f"""
        You are the Memory Agent. Analyze the interview question, candidate's answer, and evaluation results.
        Extract and return a JSON object with:
        - "demonstrated_skills": list of skills/technologies the candidate showed competence in.
        - "weak_skills": list of skills/technologies where the candidate showed weakness or gaps.
        - "topics_covered": all general topics or concepts discussed.
        - "extracted_confidence": a JSON object mapping each detected skill to a performance structure:
           {{
             "score": 0-100 score rating,
             "evidence": "A brief sentence summarizing the candidate's level of understanding or specific claims made in the answer."
           }}
        
        Interview Context:
        Question: {question}
        Answer: {answer}
        Evaluation: {json.dumps(evaluation)}
        
        Guidelines:
        - Be objective. Extract actual skills mentioned or demonstrated (e.g. "Redis", "Kafka", "React").
        - Keep the list of skills concise.
        
        Return JSON matching this schema:
        {{
          "demonstrated_skills": ["React"],
          "weak_skills": ["Kafka"],
          "topics_covered": ["Message Queues", "Caching"],
          "extracted_confidence": {{
            "React": {{
              "score": 90,
              "evidence": "Candidate explained component lifecycle and state optimization."
            }},
            "Kafka": {{
              "score": 45,
              "evidence": "Candidate struggled to explain partitioning and consumer groups."
            }}
          }}
        }}
        """
        try:
            extracted = call_gemini_json(prompt)
            # Merge extracted data
            for skill in extracted.get("demonstrated_skills", []):
                if skill not in current_memory["demonstrated_skills"]:
                    current_memory["demonstrated_skills"].append(skill)
                if skill in current_memory["weak_skills"]:
                    current_memory["weak_skills"].remove(skill)
                    
            for skill in extracted.get("weak_skills", []):
                if skill not in current_memory["weak_skills"]:
                    current_memory["weak_skills"].append(skill)
                if skill in current_memory["demonstrated_skills"]:
                    current_memory["demonstrated_skills"].remove(skill)
                    
            for topic in extracted.get("topics_covered", []):
                if topic not in current_memory["topics_covered"]:
                    current_memory["topics_covered"].append(topic)
                    
            for skill, details in extracted.get("extracted_confidence", {}).items():
                current_memory["confidence_by_skill"][skill] = details
                # Track tested/untested status
                if skill not in current_memory.setdefault("tested_skills", []):
                    current_memory["tested_skills"].append(skill)
                if current_memory.get("untested_skills") and skill in current_memory["untested_skills"]:
                    current_memory["untested_skills"].remove(skill)
                    
            return current_memory
        except Exception:
            pass  # Fall back to programmatic parsing

    # Programmatic Fallback/Mock Memory Parser
    accuracy = evaluation.get("accuracy", 75)
    depth = evaluation.get("depth", 75)
    score = int((accuracy + depth) / 2)
    
    # Expanded fallback skill list
    skills_list = ["React", "TypeScript", "Python", "FastAPI", "SQL", "Docker", "AWS", "Kafka", "RabbitMQ", "Kubernetes", "Compliance", "SOC2", "Redis", "PostgreSQL", "CI/CD", "Terraform", "GraphQL", "NoSQL", "Microservices"]
    answer_lower = answer.lower()
    question_lower = question.lower()
    
    detected_skills = []
    for skill in skills_list:
        if skill.lower() in answer_lower or skill.lower() in question_lower:
            detected_skills.append(skill)
            
    for skill in detected_skills:
        if skill not in current_memory["topics_covered"]:
            current_memory["topics_covered"].append(skill)
            
        current_memory["confidence_by_skill"][skill] = {
            "score": score,
            "evidence": f"Candidate demonstrated { 'solid' if score >= 75 else 'basic' } familiarity with {skill} during the response."
        }
        
        # Track tested vs untested
        if skill not in current_memory.setdefault("tested_skills", []):
            current_memory["tested_skills"].append(skill)
        if current_memory.get("untested_skills") and skill in current_memory["untested_skills"]:
            current_memory["untested_skills"].remove(skill)
            
        if score >= 75:
            if skill not in current_memory["demonstrated_skills"]:
                current_memory["demonstrated_skills"].append(skill)
            if skill in current_memory["weak_skills"]:
                current_memory["weak_skills"].remove(skill)
        else:
            if skill not in current_memory["weak_skills"]:
                current_memory["weak_skills"].append(skill)
            if skill in current_memory["demonstrated_skills"]:
                current_memory["demonstrated_skills"].remove(skill)
                
    return current_memory

def compile_communication_profile(all_qa: list) -> dict:
    wpm_list = []
    filler_list = []
    latency_list = []
    words_list = []
    accuracy_list = []
    
    # Executive scores lists
    practicality_list = []
    problem_solving_list = []
    business_thinking_list = []
    
    # STAR Framework counts
    star_situations = 0
    star_tasks = 0
    star_actions = 0
    star_results = 0
    
    for qa in all_qa:
        metrics = qa.get("confidence_metrics") or {}
        wpm_list.append(metrics.get("wordsPerMinute", 124) or 124)
        filler_list.append(metrics.get("fillerCount", 3) or 3)
        latency_list.append(metrics.get("latencySeconds", 1.8) or 1.8)
        words_list.append(metrics.get("wordCount", 145) or 145)
        
        eval_data = qa.get("evaluation") or {}
        accuracy_list.append(eval_data.get("accuracy", 80) or 80)
        
        # Collect new executive scores
        practicality_list.append(eval_data.get("practicality", 80) or 80)
        problem_solving_list.append(eval_data.get("problemSolving", 78) or 78)
        business_thinking_list.append(eval_data.get("businessThinking", 75) or 75)
        
        # Collect STAR indicators
        star = eval_data.get("starFramework") or {}
        if star.get("situation"): star_situations += 1
        if star.get("task"): star_tasks += 1
        if star.get("action"): star_actions += 1
        if star.get("result"): star_results += 1
        
    avg_wpm = int(sum(wpm_list) / len(wpm_list)) if wpm_list else 124
    avg_filler = round(sum(filler_list) / len(filler_list), 1) if filler_list else 3.0
    avg_latency = round(sum(latency_list) / len(latency_list), 1) if latency_list else 1.8
    avg_words = int(sum(words_list) / len(words_list)) if words_list else 145
    avg_accuracy = int(sum(accuracy_list) / len(accuracy_list)) if accuracy_list else 80
    
    avg_practicality = int(sum(practicality_list) / len(practicality_list)) if practicality_list else 80
    avg_problem_solving = int(sum(problem_solving_list) / len(problem_solving_list)) if problem_solving_list else 78
    avg_business_thinking = int(sum(business_thinking_list) / len(business_thinking_list)) if business_thinking_list else 75
    
    total_answers = len(all_qa)
    star_framework_summary = {
        "situation": star_situations > 0 or total_answers == 0,
        "task": star_tasks > 0 or total_answers == 0,
        "action": star_actions > 0 or total_answers == 0,
        "result": star_results > 0 or total_answers == 0,
        "situationCount": star_situations if total_answers > 0 else 1,
        "taskCount": star_tasks if total_answers > 0 else 1,
        "actionCount": star_actions if total_answers > 0 else 1,
        "resultCount": star_results if total_answers > 0 else 0,
        "totalCount": total_answers if total_answers > 0 else 1
    }
    
    executive_scores = {
        "practicality": avg_practicality,
        "problemSolving": avg_problem_solving,
        "businessThinking": avg_business_thinking
    }
    
    # 1. Speaking pace
    if avg_wpm < 110:
        wpm_rating = "Measured"
        wpm_fb = "Speaking pace is slow. Pacing sits below the standard 110-140 WPM benchmark, indicating highly cautious delivery or hesitation."
    elif avg_wpm > 140:
        wpm_rating = "Rapid"
        wpm_fb = "Speaking pace is rapid. Delivery is faster than the standard 110-140 WPM benchmark, which may affect comprehension."
    else:
        wpm_rating = "Optimal"
        wpm_fb = "Speaking pace is optimal. Pacing aligns perfectly with the standard 110-140 WPM benchmark for technical presentations. Delivery is measured, deliberate, and clear."
        
    # 2. Response length
    if avg_words < 80:
        words_rating = "Concise"
        words_fb = "Responses are highly concise. Brief answers may occasionally lack supporting examples or structural details expected for senior roles."
    elif avg_words > 220:
        words_rating = "Verbose"
        words_fb = "Responses are detailed. Delivery is highly comprehensive but risks being verbose. Recommend focusing on key design trade-offs."
    else:
        words_rating = "Substantial"
        words_fb = "Response length is substantial. Candidate provides comprehensive, multi-layered responses, detailing execution steps without digressing into verbose descriptions."
        
    # 3. Filler word frequency
    if avg_filler > 5:
        filler_rating = "Needs Prep"
        filler_fb = f"Identified {avg_filler} filler words per answer. Recommend conscious pause practice to reduce verbal clutter."
    else:
        filler_rating = "Low"
        filler_fb = f"Verbal clutter (average {avg_filler} fillers per answer) is well-controlled. Sentence transitions are clean and logically linked."
        
    # 4. Hesitation signals
    if avg_latency > 4.0:
        latency_rating = "Delayed"
        latency_fb = f"Average cognitive pause before speaking is {avg_latency}s. Suggests significant search time or initial hesitation. Practice structured frameworks (e.g. STAR) to reduce latency."
    else:
        latency_rating = "Controlled"
        latency_fb = f"Average pause latency is {avg_latency}s. Cognitive pause latency is within acceptable levels. Natural pauses occur at structural logic gaps, indicating active formulation rather than confusion."
        
    # 5. Answer completeness
    if avg_accuracy >= 80:
        comp_rating = "High"
        comp_fb = "Candidate systematically covers all dimensions of the evaluation prompt—including caching strategies, security parameters, and leadership considerations."
    elif avg_accuracy >= 70:
        comp_rating = "Sufficient"
        comp_fb = "Candidate covers primary prompt dimensions but leaves minor areas unaddressed."
    else:
        comp_rating = "Needs Depth"
        comp_fb = "Candidate misses critical requirements or leaves answers structurally incomplete. Recommend expanding on edge case handling."
        
    # Observations list
    observations = []
    if avg_words <= 160:
        observations.append("Responses were concise and well-structured.")
    else:
        observations.append("Responses were comprehensive and detailed, demonstrating clear articulation.")
        
    if avg_latency < 3.0:
        observations.append("Candidate demonstrated strong subject familiarity with minimal hesitation.")
    else:
        observations.append("Candidate utilized pauses effectively to structure architectural diagrams.")
        
    if avg_accuracy < 75:
        observations.append("Answers occasionally lacked supporting examples or operational depth.")
    else:
        observations.append("Candidate systematically backed assertions with clear technical paradigms.")
        
    if avg_wpm >= 110 and avg_wpm <= 140:
        observations.append("Speaking pace remained consistent throughout the assessment.")
    else:
        observations.append("Speaking pace fluctuated slightly depending on topic complexity.")
        
    if avg_filler < 4:
        observations.append("Filler word usage was below average, indicating clear communication.")
    else:
        observations.append("Recommend deliberate breath control to mitigate minor verbal fillers.")
        
    style = "Structured & Technical" if avg_accuracy >= 80 else "Descriptive & Explanatory"
    presence = "Measured & Authoritative" if avg_latency <= 2.5 else "Reflective & Diligent"
    readiness = "Highly Proficient" if avg_accuracy >= 80 else "Proficient (Some Gaps)"
    quality = "Exhibits clear design paradigms and clean API microservices isolation" if avg_accuracy >= 80 else "Provides functional details with standard execution descriptions"
    
    improvements = []
    if avg_filler > 4:
        improvements.append("Consciously pause at key transitions to reduce minor filler words.")
    if avg_latency > 3.0:
        improvements.append("Use structured frameworks (like STAR) to decrease initial hesitation latency.")
    if avg_accuracy < 80:
        improvements.append("Incorporate more concrete case examples to address all prompt criteria.")
    if not improvements:
        improvements.append("Continue practicing delivery consistency under strict timing bounds.")
        
    return {
        "style": style,
        "presence": presence,
        "readiness": readiness,
        "quality": quality,
        "improvements": improvements,
        "observations": observations,
        "starFramework": star_framework_summary,
        "executiveScores": executive_scores,
        "metrics": {
            "speakingPace": {
                "value": f"{avg_wpm} WPM",
                "rating": wpm_rating,
                "feedback": wpm_fb
            },
            "responseLength": {
                "value": f"Avg {avg_words} Words",
                "rating": words_rating,
                "feedback": words_fb
            },
            "fillerWords": {
                "value": f"{avg_filler} per answer",
                "rating": filler_rating,
                "feedback": filler_fb
            },
            "hesitation": {
                "value": f"{avg_latency}s latency",
                "rating": latency_rating,
                "feedback": latency_fb
            },
            "completeness": {
                "value": comp_rating,
                "rating": comp_rating,
                "feedback": comp_fb
            }
        }
    }

# --- 8. Report Agent ---
def generate_final_report(all_qa: list, memory: dict) -> dict:
    if not GEMINI_API_KEY:
        return get_mock_report_final(all_qa, memory)
        
    prompt = f"""
    You are compiling the final Career Readiness Report.
    Review all questions, answers, evaluations, and memory files.
    
    Evaluation Records:
    {json.dumps(all_qa, indent=2)}
    
    Session Memory:
    {json.dumps(memory, indent=2)}
    
    Generate:
    1. Overall Score (0-100). Average of evaluations.
    2. Hiring Recommendation (Strong Hire, Hire, Follow-up, Needs Development).
    3. Exec Summary: 3-4 sentence diagnostic of their performance, pacing, and readiness.
    4. Dimension Scores (Accuracy, Depth, Communication, Scenario Handling, Leadership) out of 100.
    5. Heatmap rating for 6 skills relevant to the session.
    6. Actionable recommendations/next steps.
    
    Return JSON matching this schema:
    {{
      "overallScore": 84,
      "recommendation": "Strong Hire",
      "summary": "Summary diagnostics...",
      "dimensionScores": [
        {{"subject": "Accuracy", "A": 85, "fullMark": 100}},
        {{"subject": "Depth", "A": 80, "fullMark": 100}},
        {{"subject": "Communication", "A": 90, "fullMark": 100}},
        {{"subject": "Scenario Handling", "A": 78, "fullMark": 100}},
        {{"subject": "Leadership", "A": 88, "fullMark": 100}}
      ],
      "categoryScores": [
        {{"name": "Technical", "score": 85}},
        {{"name": "Scenario", "score": 78}},
        {{"name": "Behavioral", "score": 90}},
        {{"name": "Leadership", "score": 88}}
      ],
      "heatmap": [
        {{"skill": "React & TS Architecture", "rating": "High", "color": "rgba(45, 212, 191, 0.15)", "textColor": "var(--color-accent-teal)", "border": "rgba(45, 212, 191, 0.3)"}},
        {{"skill": "Microservices & API Design", "rating": "High", "color": "rgba(45, 212, 191, 0.15)", "textColor": "var(--color-accent-teal)", "border": "rgba(45, 212, 191, 0.3)"}},
        {{"skill": "Docker & AWS Ops", "rating": "High", "color": "rgba(45, 212, 191, 0.15)", "textColor": "var(--color-accent-teal)", "border": "rgba(45, 212, 191, 0.3)"}},
        {{"skill": "Distributed System Design", "rating": "Medium", "color": "rgba(129, 140, 248, 0.1)", "textColor": "var(--color-accent-indigo)", "border": "rgba(129, 140, 248, 0.25)"}},
        {{"skill": "H-F Message Queues", "rating": "Needs Prep", "color": "rgba(251, 113, 133, 0.1)", "textColor": "var(--color-accent-coral)", "border": "rgba(251, 113, 133, 0.25)"}},
        {{"skill": "Fintech SOC2 Compliance", "rating": "Needs Prep", "color": "rgba(251, 113, 133, 0.1)", "textColor": "var(--color-accent-coral)", "border": "rgba(251, 113, 133, 0.25)"}}
      ],
      "strengths": ["Strength 1 text", "Strength 2 text"],
      "recommendations": ["Advice 1 text", "Advice 2 text"]
    }}
    """
    try:
        report_json = call_gemini_json(prompt)
        report_json["communicationProfile"] = compile_communication_profile(all_qa)
        report_json["all_qa"] = all_qa
        return report_json
    except Exception as e:
        logger.warning(f"Report Agent Gemini call failed: {e}. Falling back to mock final report.")
        report_json = get_mock_report_final(all_qa, memory)
        report_json["communicationProfile"] = compile_communication_profile(all_qa)
        report_json["all_qa"] = all_qa
        return report_json

# --- MOCK FALLBACKS ---

def get_mock_resume_parsed() -> dict:
    return {
        "candidate_name": "John Doe",
        "headline": "Senior Software Engineer | Backend & Cloud Systems",
        "email": "johndoe@example.com",
        "phone": "+1-555-0199",
        "location": "San Francisco, CA",
        "linkedin": "https://linkedin.com/in/johndoe-mock",
        "github": "https://github.com/johndoe-mock",
        "portfolio": "https://johndoe.dev",
        "website": "https://johndoe.dev",
        "summary": "Experienced software engineer with 5+ years of expertise in Python, FastAPI, Docker, and AWS. Passionate about building highly scalable distributed services and robust APIs.",
        "career_level": "Senior",
        "estimated_experience_years": 5.5,
        "primary_domain": "Backend Systems & Cloud Engineering",
        "skills": ["React", "TypeScript", "JavaScript", "Python", "FastAPI", "PostgreSQL", "Docker", "Git", "AWS"],
        "technical_skills": ["API Design", "Distributed Systems", "Database Optimization", "CI/CD"],
        "soft_skills": ["Mentoring", "Technical Writing", "Team Collaboration"],
        "programming_languages": ["Python", "TypeScript", "JavaScript", "SQL"],
        "frameworks": ["FastAPI", "React", "Next.js"],
        "databases": ["PostgreSQL", "Redis"],
        "cloud_platforms": ["AWS"],
        "tools": ["Docker", "Git", "Kubernetes"],
        "projects": [
            {
                "title": "E-Commerce Microservices",
                "description": "Designed custom order dispatch queue processing 10k orders/day.",
                "technologies": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
                "github": "https://github.com/johndoe-mock/ecommerce-microservices",
                "demo": "https://ecommerce-demo.johndoe.dev",
                "contributions": ["Implemented asynchronous task workers", "Configured PostgreSQL connection pooling"]
            }
        ],
        "experience": [
            {
                "title": "Software Engineer",
                "company": "SaaS Ventures Ltd",
                "employment_type": "Full-time",
                "duration": "2024 - Present",
                "responsibilities": [
                    "Maintain frontends in React and TypeScript while supporting python microservice features.",
                    "Optimize slow SQL queries on PostgreSQL, reducing response latency by 20%."
                ],
                "achievements": [
                    "Led the containerization effort using Docker, improving local setup times for the team."
                ],
                "technologies": ["React", "TypeScript", "Python", "FastAPI", "PostgreSQL", "Docker"]
            }
        ],
        "education": [
            {
                "degree": "B.S. Computer Science",
                "branch": "Computer Science",
                "institution": "State Tech University",
                "year": "2023",
                "cgpa": "3.8/4.0"
            }
        ],
        "certifications": ["AWS Certified Solutions Architect"],
        "internships": [
            {
                "company": "Tech Interns Inc",
                "role": "Backend Intern",
                "duration": "Summer 2022",
                "summary": "Assisted with REST API development using Python and Flask, and created unit tests."
            }
        ],
        "achievements": ["Valedictorian runner-up at State Tech University"],
        "languages": ["English (Native)", "Spanish (Conversational)"],
        "domain_experience": ["SaaS", "E-Commerce"],
        "top_strengths": ["Clean API Design", "Containerization & Cloud Deployments"],
        "potential_concerns": ["Limited high-frequency message queue experience"],
        "links": [
            {
                "url": "https://github.com/johndoe-mock/ecommerce-microservices",
                "type": "GitHub",
                "verified": True,
                "summary": "Repository evidence for FastAPI and PostgreSQL project work.",
                "skills_found": ["FastAPI", "PostgreSQL", "Docker"],
                "projects_found": ["E-Commerce Microservices"]
            }
        ]
    }

def get_mock_jd_parsed() -> dict:
    return {
      "title": "Senior Software Engineer",
      "required_skills": ["React", "TypeScript", "Python", "Kafka", "Distributed Systems", "PCI-DSS Security Compliance"],
      "preferred_skills": ["Kubernetes", "AWS", "FastAPI"],
      "industry": "Financial Technology",
      "seniority": "Senior",
      "experience": "5+ years",
      "responsibilities": [
        "Design resilient services",
        "Own technical delivery",
        "Collaborate with product and security teams"
      ],
      "domain": "Payments",
      "leadership_expectations": ["Mentor engineers", "Lead design reviews"],
      "communication_expectations": ["Explain technical trade-offs", "Write clear implementation plans"]
    }

def get_mock_match_analysis(resume_parsed: dict, jd_parsed: dict) -> dict:
    return {
      "matchScore": 82,
      "roleInfo": {
        "title": jd_parsed.get("title", "Senior Software Engineer"),
        "industry": jd_parsed.get("industry", "Financial Technology"),
        "seniority": jd_parsed.get("seniority", "Senior")
      },
      "readinessDetails": [
        {"name": "Core Coding & Architecture", "score": 85},
        {"name": "System Design & Scalability", "score": 75},
        {"name": "Team Leadership & Culture", "score": 90},
        {"name": "Domain Experience (Fintech)", "score": 70},
        {"name": "Tooling & CI/CD Pipelines", "score": 90}
      ],
      "strengths": [
        "Deep expertise in React, TypeScript, and state management architectures (Redux, Zustand).",
        "Proven track record of designing REST and GraphQL APIs with Python-based microservices.",
        "Strong deployment and operations expertise using Docker, Kubernetes, and AWS Cloud services."
      ],
      "gaps": [
        {
          "skill": "High-Frequency Messaging Networks",
          "description": "The job requires familiarity with Apache Kafka or RabbitMQ. Your profile highlights database caching but lacks message queue orchestration."
        },
        {
          "skill": "Fintech Security Compliance",
          "description": "The description emphasizes PCI-DSS or SOC2 compliance experience. Your background is primarily in consumer product SaaS without direct audit exposure."
        }
      ],
      "matched_skills": ["React", "TypeScript", "Python", "FastAPI", "Docker", "AWS"],
      "missing_skills": ["Kafka", "SOC2 Compliance"],
      "evidence": [
        {"skill": "React", "status": "Found", "source": "Found in Experience: Software Engineer at SaaS Ventures Ltd"},
        {"skill": "TypeScript", "status": "Found", "source": "Found in Experience: Software Engineer at SaaS Ventures Ltd"},
        {"skill": "Python", "status": "Found", "source": "Found in Project: E-Commerce Microservices"},
        {"skill": "FastAPI", "status": "Found", "source": "Found in Project: E-Commerce Microservices"},
        {"skill": "Docker", "status": "Found", "source": "Found in Project: E-Commerce Microservices"},
        {"skill": "AWS", "status": "Found", "source": "Found in Certifications: AWS Certified Solutions Architect"},
        {"skill": "Kafka", "status": "Not Found", "source": "Not found in resume text"},
        {"skill": "SOC2 Compliance", "status": "Not Found", "source": "Not found in resume text"}
      ]
    }

MOCK_QUESTIONS_POOL = {
    "Technical": [
        "How do you design a robust caching layer in a high-frequency financial system?",
        "Explain the differences between optimistic and pessimistic locking, and when you would use each.",
        "How do you handle memory allocation and memory leak detection in a long-running production service?"
    ],
    "Scenario": [
        "Explain how you would handle schema migrations in a distributed multi-tenant database with zero downtime.",
        "How would you troubleshoot a sudden spike in latency across a microservices mesh during peak traffic?",
        "Design a file-upload service that needs to process and generate thumbnails for 10 million images daily."
    ],
    "Behavioral": [
        "Tell me about a time when you had to advocate for code quality over speed of delivery.",
        "Describe a situation where you had to work with a difficult stakeholder to agree on a technical roadmap.",
        "Tell me about a time when a production deployment failed. What did you do, and what did you learn?"
    ],
    "Leadership": [
        "How do you handle conflict or architectural disagreements with senior staff developers?",
        "Describe how you mentor junior engineers and help them level up their engineering skills.",
        "How do you manage technical debt and convince business leadership to allocate time to refactoring?"
    ]
}

def get_mock_question(category: str, difficulty: str, offset: int = 0) -> str:
    pool = MOCK_QUESTIONS_POOL.get(category, MOCK_QUESTIONS_POOL["Technical"])
    idx = offset % len(pool)
    return pool[idx]

def get_mock_evaluation(question: str, answer: str, signals: dict) -> dict:
    accuracy = 80 if len(answer) > 40 else 65
    depth = 75 if len(answer) > 80 else (55 if len(answer) <= 30 else 60)
    confidence = max(50, 100 - (signals.get("fillerCount", 0) * 8) - int(signals.get("latencySeconds", 0)))
    
    return {
      "accuracy": accuracy,
      "depth": depth,
      "communication": 85,
      "confidence": confidence,
      "practicality": 80,
      "problemSolving": 75,
      "businessThinking": 70,
      "starFramework": {
        "situation": len(answer) > 30,
        "task": len(answer) > 50,
        "action": len(answer) > 80,
        "result": len(answer) > 100
      },
      "feedback": "Response is structured, but could expand more on cache eviction protocols and distributed synchronization risks.",
      "fillerWordFeedback": f"Identified {signals.get('fillerCount', 0)} filler words. Pacing was measured at {signals.get('wordsPerMinute', 120)} words per minute."
    }

def get_mock_report_final(all_qa: list, memory: dict) -> dict:
    profile = compile_communication_profile(all_qa)
    return {
      "overallScore": 84,
      "recommendation": "Strong Hire",
      "summary": "The candidate demonstrates exceptional technical articulation and architecture foundations. Communications pace was highly consistent with standard senior engineering benchmarks. Minor adjustments recommended in fintech compliance contexts and message queue depth.",
      "dimensionScores": [
        {"subject": "Accuracy", "A": 85, "fullMark": 100},
        {"subject": "Depth", "A": 80, "fullMark": 100},
        {"subject": "Communication", "A": 90, "fullMark": 100},
        {"subject": "Scenario Handling", "A": 78, "fullMark": 100},
        {"subject": "Leadership", "A": 88, "fullMark": 100}
      ],
      "categoryScores": [
        {"name": "Technical", "score": 85},
        {"name": "Scenario", "score": 78},
        {"name": "Behavioral", "score": 90},
        {"name": "Leadership", "score": 88}
      ],
      "heatmap": [
        {"skill": "React & TS Architecture", "rating": "High", "color": "rgba(45, 212, 191, 0.15)", "textColor": "var(--color-accent-teal)", "border": "rgba(45, 212, 191, 0.3)"},
        {"skill": "Microservices & API Design", "rating": "High", "color": "rgba(45, 212, 191, 0.15)", "textColor": "var(--color-accent-teal)", "border": "rgba(45, 212, 191, 0.3)"},
        {"skill": "Docker & AWS Ops", "rating": "High", "color": "rgba(45, 212, 191, 0.15)", "textColor": "var(--color-accent-teal)", "border": "rgba(45, 212, 191, 0.3)"},
        {"skill": "Distributed System Design", "rating": "Medium", "color": "rgba(129, 140, 248, 0.1)", "textColor": "var(--color-accent-indigo)", "border": "rgba(129, 140, 248, 0.25)"},
        {"skill": "H-F Message Queues", "rating": "Needs Prep", "color": "rgba(251, 113, 133, 0.1)", "textColor": "var(--color-accent-coral)", "border": "rgba(251, 113, 133, 0.25)"},
        {"skill": "Fintech SOC2 Compliance", "rating": "Needs Prep", "color": "rgba(251, 113, 133, 0.1)", "textColor": "var(--color-accent-coral)", "border": "rgba(251, 113, 133, 0.25)"}
      ],
      "strengths": [
        "Articulates React render cycles and state transitions with high logical clarity.",
        "Formulates clear microservice isolation protocols and API validation schemas.",
        "Exhibits solid collaboration patterns, emphasizing mentoring and clear developer path structures."
      ],
      "recommendations": [
        "Review basic event-driven topologies and explore Kafka queue structures (producers, consumers, and consumer-groups).",
        "Familiarize yourself with ISO-27001 and SOC2 checklist rules regarding data residency and encryption-in-transit."
      ],
      "communicationProfile": profile,
      "all_qa": all_qa
    }

def get_mock_career_roadmap(resume_parsed: dict, target_role: str, target_company: str, target_jd: dict) -> dict:
    return {
      "current_readiness": 68,
      "estimated_time": "4 Months",
      "success_probability": "High",
      "missing_skills": ["Docker", "Kubernetes", "CI/CD Platforms", "Apache Kafka"],
      "weekly_milestones": [
        {
          "week": "Weeks 1-2",
          "focus": "Foundations & Docker containerization",
          "tasks": [
            "Learn containerization basics: Dockerfile, volumes, and networks.",
            "Containerize the local python interview microservices application.",
            "Deploy the container locally and practice mapping environment variables."
          ]
        },
        {
          "week": "Weeks 3-4",
          "focus": "Kubernetes orchestration basics",
          "tasks": [
            "Understand Kubernetes Pods, Deployments, and Services schemas.",
            "Write basic YAML manifests to run the containerized python application.",
            "Deploy onto a local minikube cluster and verify logs."
          ]
        },
        {
          "week": "Weeks 5-8",
          "focus": "CI/CD & AWS Deployment pipelines",
          "tasks": [
            "Set up a GitHub Actions workflow to build and test code on every push.",
            "Integrate Docker build and push to Amazon ECR.",
            "Deploy to Amazon ECS (Fargate) using GitHub Actions secrets."
          ]
        },
        {
          "week": "Weeks 9-12",
          "focus": "High-throughput messaging & system design",
          "tasks": [
            "Familiarize with Apache Kafka topics, producers, and consumer-groups.",
            "Implement a test producer and consumer inside python to process mock logs.",
            "Draft a multi-region scalable system design blueprint for high-frequency hiring data."
          ]
        }
      ],
      "projects_to_build": [
        {
          "title": "Scalable Containerized Interview Simulator",
          "spec": "FastAPI + Docker + minikube + GitHub Actions",
          "tasks": [
            "Write a multi-stage Dockerfile to shrink image size.",
            "Configure a local minikube cluster to run backend nodes behind a LoadBalancer service.",
            "Create a GitHub Actions CI pipeline mapping secrets to build clean images."
          ]
        },
        {
          "title": "Event-Driven Log Analytics Queue",
          "spec": "FastAPI + Kafka + Docker Compose",
          "tasks": [
            "Set up a single-node Kafka broker using Docker Compose.",
            "Develop a background publisher node sending interview evaluations data.",
            "Run multiple consumer nodes executing log processing in parallel."
          ]
        }
      ],
      "learning_resources": [
        {
          "name": "Docker and Kubernetes: The Complete Guide",
          "type": "Course / Reference",
          "link": "https://www.udemy.com/"
        },
        {
          "name": "Confluent Kafka Developer Tutorials",
          "type": "Documentation",
          "link": "https://developer.confluent.io/"
        }
      ],
      "resume_checkpoint_upgrades": [
        {
          "milestone": "Month 1",
          "checkpoints": [
            "Add the 'Containerized Interview Simulator' project description to the projects section.",
            "List 'Docker' and 'Kubernetes' under technical skills list."
          ]
        },
        {
          "milestone": "Month 2",
          "checkpoints": [
            "Update the 'Work Experience' or 'Projects' sections to highlight GitHub Actions CI/CD automation pipelines.",
            "Add 'AWS ECR/ECS' to the tools section."
          ]
        },
        {
          "milestone": "Month 3",
          "checkpoints": [
            "Highlight event-driven architecture experience with 'Apache Kafka' inside the projects section.",
            "Re-run readiness analysis on HireIntel to verify name scores."
          ]
        }
      ]
    }

def generate_career_roadmap(resume: dict, target_role: Optional[str] = None, target_company: Optional[str] = None, target_jd: Optional[dict] = None) -> dict:
    if not GEMINI_API_KEY:
        return get_mock_career_roadmap(resume, target_role or "", target_company or "", target_jd or {})
        
    prompt = f"""
    You are a Senior Career Mentor & Coach Agent. Your job is to create a realistic, personalized, and highly actionable learning roadmap and resume upgrade checkpoint list.
    
    Candidate Resume:
    {json.dumps(resume, indent=2)}
    
    Target Role: {target_role or "N/A"}
    Target Company: {target_company or "N/A"}
    Target Job Description (JD):
    {json.dumps(target_jd, indent=2) if target_jd else "N/A"}
    
    Analyze:
    - Current strengths vs Gaps (Skills, Projects, Experience, Certifications).
    - Map readiness percentage score (integer 0 to 100) and Success Probability ("Low", "Medium", "High").
    - Estimate the timeline in months (e.g. "3 Months", "4 Months").
    
    Formulate:
    1. A list of specific "missing_skills".
    2. A week-by-week or phase-by-phase learning "weekly_milestones" plan. Include containerized, specific action tasks (e.g. instead of "Learn React", say "Week 3: Learn React routing -> Implement navigation -> Deploy page").
    3. Specific personalized "projects_to_build" (with title, target technical specs, and subtasks) tailored to bridge their project/experience gaps.
    4. Relevant "learning_resources" links or course topics.
    5. Actionable "resume_checkpoint_upgrades" mapped to monthly milestones (telling the candidate exactly what projects or certifications to add to their resume over time).
    
    Guidelines:
    - Tailor the plan dynamically to what the candidate *already knows* (e.g. if they already know React, do NOT tell them to learn basic React; focus on advanced optimizations or gaps).
    - Return ONLY valid JSON format.
    
    Return JSON matching exactly this schema:
    {{
      "current_readiness": 72,
      "estimated_time": "4 Months",
      "success_probability": "High",
      "missing_skills": ["Docker", "Kubernetes"],
      "weekly_milestones": [
        {{
          "week": "Weeks 1-2",
          "focus": "Topic details",
          "tasks": ["Task 1 description", "Task 2 description"]
        }}
      ],
      "projects_to_build": [
        {{
          "title": "Project Title",
          "spec": "Tech stack details",
          "tasks": ["Subtask 1", "Subtask 2"]
        }}
      ],
      "learning_resources": [
        {{
          "name": "Resource Name",
          "type": "Type description",
          "link": "URL link (if known, or placeholder)"
        }}
      ],
      "resume_checkpoint_upgrades": [
        {{
          "milestone": "Month 1",
          "checkpoints": ["Action 1 details", "Action 2 details"]
        }}
      ]
    }}
    """
    try:
        return call_gemini_json(prompt)
    except Exception as e:
        logger.warning(f"Career Intelligence Agent Gemini call failed: {e}. Falling back to mock career roadmap.")
        return get_mock_career_roadmap(resume, target_role or "", target_company or "", target_jd or {})
