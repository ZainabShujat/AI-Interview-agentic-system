"""
HireIntel — Resume Intelligence Agent
=======================================
Parses resume text (from PDF/DOCX/TXT) into a rich structured candidate profile.

Uses a hybrid approach:
1. Local regex extraction for mechanical fields (name, email, phone, links).
2. Link verification (fetches GitHub/LinkedIn/portfolio pages for evidence).
3. Gemini LLM inference for semantic fields (skills, projects, experience).

Standalone usage:
    from agents.resume_agent import parse_resume
    from agents.gemini_core import GeminiConfig

    config = GeminiConfig(api_key="your-key")
    result = parse_resume("John Doe\\nSoftware Engineer...", config=config)
    print(result["candidate_name"])   # "John Doe"
    print(result["skills"])           # ["Python", "React", ...]

Works without API key (falls back to local heuristic parsing).
"""

import re
import logging
from typing import Optional

from .gemini_core import (
    GeminiConfig, get_default_config, call_gemini_json,
    extract_urls, fetch_public_link_evidence,
    extract_email, extract_phone, categorize_skills,
    PROGRAMMING_LANGUAGES, FRAMEWORKS, DATABASES,
    CLOUD_PLATFORMS, TOOLS_AND_PLATFORMS, SOFT_SKILLS,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Resume Text Normalization
# ---------------------------------------------------------------------------

def normalize_resume_parsed(data: dict) -> dict:
    """Normalize and validate a parsed resume dict to a canonical schema."""
    if not isinstance(data, dict):
        data = {}

    # Root level fields
    string_fields = [
        "candidate_name", "headline", "email", "phone", "location",
        "linkedin", "github", "portfolio", "website", "summary",
        "career_level", "primary_domain"
    ]
    for f in string_fields:
        data.setdefault(f, None)

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
    for f in list_fields:
        if not isinstance(data.get(f), list):
            data[f] = []
        else:
            data[f] = [str(item) for item in data[f] if item is not None]

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


# ---------------------------------------------------------------------------
# Local Extraction Helpers
# ---------------------------------------------------------------------------

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


def _clean_resume_text(text: str) -> str:
    """Cleans raw resume text to minimize prompt tokens."""
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    text = re.sub(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r"https?://[^\s<>)\]]+", '[URL]', text)

    lines = []
    for line in text.split('\n'):
        cleaned_line = line.strip()
        if not cleaned_line or re.match(r'^(?i:page)?\s*\d+\s*(?:of\s*\d+)?$', cleaned_line):
            continue
        temp = re.sub(r'\[(?:EMAIL|PHONE|URL)\]', '', cleaned_line)
        temp = re.sub(r'[\s|•·,\-_\/]+', '', temp)
        if not temp:
            continue
        lines.append(line)

    cleaned_text = '\n'.join(lines)
    cleaned_text = re.sub(r'\n\s*\n+', '\n\n', cleaned_text)
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
    return cleaned_text.strip()


def _extract_name_from_filename(filename: str) -> Optional[str]:
    if not filename:
        return None
    import os
    base = os.path.splitext(filename)[0]
    base = re.sub(r'[^A-Za-z\s]', ' ', base)

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

    for line in lines[:8]:
        line_lower = line.lower()
        if '@' in line or '/' in line or '\\' in line or ':' in line or '|' in line or len(line) > 40:
            continue
        if any(char.isdigit() for char in line):
            continue
        words = line.split()
        if not words or len(words) < 2 or len(words) > 4:
            continue
        if any(w.lower() in section_headers for w in words):
            continue
        if any(w.lower() in headline_keywords for w in words):
            continue
        is_capitalized = all(w[0].isupper() or w.isupper() for w in words if w.isalpha())
        if is_capitalized:
            return " ".join([w.capitalize() for w in words])

    if filename:
        filename_name = _extract_name_from_filename(filename)
        if filename_name:
            return filename_name

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

        found_degree = None
        for dk in degree_keywords:
            if re.search(r'\b' + re.escape(dk) + r'\b', line_lower):
                found_degree = dk.upper()
                break

        found_inst = None
        for ik in inst_keywords:
            if re.search(r'\b' + re.escape(ik) + r'\b', line_lower):
                found_inst = line
                break

        year_match = re.search(r'\b(20\d{2}|19\d{2})\b', line)
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


# ---------------------------------------------------------------------------
# Local Fallback Parser
# ---------------------------------------------------------------------------

def _parse_resume_local_fallback(raw_text: str, pre_extracted: dict, link_evidence: list) -> dict:
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
        'skills': list(categorize_skills(raw_text).get('tools', []))[:10],
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
    return normalize_resume_parsed(fallback_data)


# ---------------------------------------------------------------------------
# Main Agent Entry Point
# ---------------------------------------------------------------------------

def parse_resume(raw_text: str, filename: Optional[str] = None,
                 config: Optional[GeminiConfig] = None) -> dict:
    """
    Parse resume text into a structured candidate profile.

    Args:
        raw_text: Raw extracted text from the resume file.
        filename: Optional original filename.
        config: Optional GeminiConfig. If None or missing API key, uses local fallback.
    """
    if config is None:
        config = get_default_config()

    cand_name = _extract_name(raw_text, filename)
    pre_extracted = {
        'candidate_name': cand_name,
        'email': extract_email(raw_text),
        'phone': extract_phone(raw_text),
        'location': _extract_location(raw_text),
        'headline': _extract_headline(raw_text, cand_name),
    }

    resume_links = extract_urls(raw_text)
    link_evidence = fetch_public_link_evidence(resume_links) if resume_links else []

    linkedin_urls = [url for url in resume_links if 'linkedin.com' in url.lower()]
    github_urls = [url for url in resume_links if 'github.com' in url.lower()]
    portfolio_urls = [url for url in resume_links if any(x in url.lower() for x in ['portfolio', 'site', 'personal'])]

    pre_extracted['linkedin'] = linkedin_urls[0] if linkedin_urls else None
    pre_extracted['github'] = github_urls[0] if github_urls else None
    pre_extracted['portfolio'] = portfolio_urls[0] if portfolio_urls else None
    pre_extracted['website'] = None

    if not config.api_key:
        return _parse_resume_local_fallback(raw_text, pre_extracted, link_evidence)

    cleaned_text = _clean_resume_text(raw_text)

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
        raw_res = call_gemini_json(prompt, config)
        if not isinstance(raw_res, dict):
            raw_res = {}

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

        return normalize_resume_parsed(parsed_data)
    except Exception as e:
        logger.warning(f"Resume Agent Gemini call failed: {e}. Falling back to local heuristic parser.")
        return _parse_resume_local_fallback(raw_text, pre_extracted, link_evidence)


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

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
        "summary": "Experienced software engineer with 5+ years of expertise in Python, FastAPI, Docker, and AWS.",
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
