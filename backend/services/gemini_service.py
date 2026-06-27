import os
import json
import re
import urllib.request
import urllib.error
import google.generativeai as genai
from dotenv import load_dotenv

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

# --- 1. Resume Parser Agent ---
def parse_resume(raw_text: str) -> dict:
    if not GEMINI_API_KEY:
        return get_mock_resume_parsed()

    # Pre-check: Verify if the text content resembles a resume
    if not raw_text or len(raw_text.strip()) < 100:
        raise ValueError("Unable to parse resume.")

    check_prompt = f"""
    You are an AI assistant verifying if a document is a professional resume, CV, or candidate profile.
    Analyze the following text excerpt. If it is a menu, essay, receipt, log file, book chapter, random conversation, completely empty/corrupted text, or overall not a candidate resume/CV, reply with NO.
    If it is a valid resume or CV, reply with YES.
    
    Reply with exactly one word: YES or NO.
    
    Text:
    {raw_text[:3000]}
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(check_prompt, request_options={"timeout": 10})
        is_resume = response.text.strip().upper()
        if "YES" not in is_resume:
            raise ValueError("Unable to parse resume.")
    except ValueError:
        raise
    except Exception as e:
        # Proceed as fallback on transient network/API issues to avoid false negatives
        print(f"Resume validation pre-check failed: {e}. Proceeding with fallback.")

    resume_links = extract_urls(raw_text)
    link_evidence = fetch_public_link_evidence(resume_links) if resume_links else []

    prompt = f"""
You are Resume Intelligence Agent.

Analyze the candidate's resume and extract structured information.

Use the supplied public link evidence only to verify or enrich information.
Never invent information.

Rules:
- Return ONLY valid JSON.
- Do NOT include markdown.
- Do NOT include explanations.
- Do NOT omit any key.
- If information is unavailable, return null or [].

Resume:
{raw_text}

Verified Link Evidence:
{json.dumps(link_evidence, separators=(",", ":"))}

Return JSON matching exactly this schema:

{{
  "candidate_name": "",
  "headline": "",
  "email": "",
  "phone": "",
  "location": "",

  "linkedin": "",
  "github": "",
  "portfolio": "",
  "website": "",

  "summary": "",

  "career_level": "",
  "estimated_experience_years": 0,
  "primary_domain": "",

  "skills": [],
  "technical_skills": [],
  "soft_skills": [],
  "programming_languages": [],
  "frameworks": [],
  "databases": [],
  "cloud_platforms": [],
  "tools": [],

  "projects": [
    {{
      "title": "",
      "description": "",
      "technologies": [],
      "github": "",
      "demo": "",
      "contributions": []
    }}
  ],

  "experience": [
    {{
      "title": "",
      "company": "",
      "employment_type": "",
      "duration": "",
      "responsibilities": [],
      "achievements": [],
      "technologies": []
    }}
  ],

  "education": [
    {{
      "degree": "",
      "branch": "",
      "institution": "",
      "year": "",
      "cgpa": ""
    }}
  ],

  "certifications": [],

  "internships": [
    {{
      "company": "",
      "role": "",
      "duration": "",
      "summary": ""
    }}
  ],

  "achievements": [],

  "languages": [],

  "domain_experience": [],

  "top_strengths": [],

  "potential_concerns": [],

  "links": [
    {{
      "url": "",
      "type": "",
      "verified": true,
      "summary": "",
      "skills_found": [],
      "projects_found": []
    }}
  ]
}}
"""

    try:
        raw_res = call_gemini_json(prompt)
        return normalize_resume_parsed(raw_res)
    except Exception as e:
        raise RuntimeError(f"Resume Agent failed while using Gemini API: {e}") from e

# --- 2. JD Parser Agent ---
def parse_jd(raw_text: str) -> dict:
    if not GEMINI_API_KEY:
        return get_mock_jd_parsed()
        
    prompt = f"""
    You are an expert recruiter parsing a Job Description.
    Extract the following details from the text:
    - Target Job Title
    - Required Skills (must have)
    - Preferred Skills (nice to have)
    - Target Industry
    - Seniority Level (Junior, Mid, Senior, Lead, Director)
    - Experience expectations
    - Responsibilities
    - Domain
    - Leadership expectations
    - Communication expectations

    Job Description Raw Text:
    {raw_text}

    Return JSON matching this schema:
    {{
      "title": "Software Engineer",
      "required_skills": ["skill1", "skill2"],
      "preferred_skills": ["skill1"],
      "industry": "Finance / SaaS",
      "seniority": "Senior",
      "experience": "5+ years",
      "responsibilities": ["responsibility1"],
      "domain": "Payments",
      "leadership_expectations": ["Mentors engineers"],
      "communication_expectations": ["Explains trade-offs clearly"]
    }}
    """
    try:
        return call_gemini_json(prompt)
    except Exception as e:
        raise RuntimeError(f"JD Agent failed while using Gemini API: {e}") from e

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
def plan_interview_roadmap(resume_parsed: dict, jd_parsed: dict, match_analysis: dict) -> dict:
    if not GEMINI_API_KEY:
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
        raise RuntimeError(f"Interview Planner Agent failed while using Gemini API: {e}") from e

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
        raise RuntimeError(f"Question Generator Agent failed while using Gemini API: {e}") from e

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
        raise RuntimeError(f"Judge Agent failed while using Gemini API: {e}") from e

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
        raise RuntimeError(f"Report Agent failed while using Gemini API: {e}") from e

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
