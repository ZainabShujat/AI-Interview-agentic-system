"""
HireIntel — JD Intelligence Agent
===================================
Parses job description text into a structured hiring blueprint.

Standalone usage:
    from agents.jd_agent import parse_jd
    from agents.gemini_core import GeminiConfig

    config = GeminiConfig(api_key="your-key")
    result = parse_jd("Senior Python Engineer at Fintech Corp...", config=config)
    print(result["title"])             # "Senior Python Engineer"
    print(result["required_skills"])   # ["Python", "SQL", ...]

Works without API key (falls back to keyword-based heuristic parsing).
"""

import re
import json
import logging
from typing import Optional

from .gemini_core import (
    GeminiConfig, get_default_config, call_gemini_json,
    PROGRAMMING_LANGUAGES, FRAMEWORKS, DATABASES,
    CLOUD_PLATFORMS, TOOLS_AND_PLATFORMS,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Fallback Parser
# ---------------------------------------------------------------------------

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
        if re.search(r'\b' + re.escape(skill) + r'\b', raw_lower):
            display_name = skill.upper() if skill in ["aws", "sql", "ci/cd", "gcp"] else skill.capitalize()
            detected.append(display_name)

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


# ---------------------------------------------------------------------------
# Main Agent Entry Point
# ---------------------------------------------------------------------------

def parse_jd(raw_text: str, config: Optional[GeminiConfig] = None) -> dict:
    """
    Parse job description text into a structured hiring blueprint.

    Args:
        raw_text: Raw job description text.
        config: Optional GeminiConfig. If None or missing API key, uses local fallback.

    Returns:
        Dict with title, required_skills, preferred_skills, seniority, industry, etc.
    """
    if config is None:
        config = get_default_config()

    if not config.api_key:
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
        return call_gemini_json(prompt, config)
    except Exception as e:
        logger.warning(f"JD Agent Gemini call failed: {e}. Falling back to local heuristic JD parser.")
        return _parse_jd_heuristics(raw_text)


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

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
