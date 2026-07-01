"""
HireIntel — Interview Planner Agent
===================================
Formulates custom question category distributions based on a candidate's profile
and identified skill gaps.

Standalone usage:
    from agents.planner_agent import plan_interview_roadmap
    from agents.gemini_core import GeminiConfig

    config = GeminiConfig(api_key="your-key")
    result = plan_interview_roadmap(resume, jd, match, config=config)
    print(result)  # {"Technical": 2, "Scenario": 1, "Behavioral": 1, "Leadership": 1}

Works without API key (falls back to programmatic roadmap planner).
"""

import json
import logging
from typing import Optional

from .gemini_core import GeminiConfig, get_default_config, call_gemini_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Fallback Planner
# ---------------------------------------------------------------------------

def _plan_interview_roadmap_local(resume_parsed: dict, jd_parsed: dict, match_analysis: dict) -> dict:
    """Fallback programmatic planner that outputs question counts dynamically."""
    seniority = jd_parsed.get("seniority", "Mid")
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


# ---------------------------------------------------------------------------
# Main Agent Entry Point
# ---------------------------------------------------------------------------

def plan_interview_roadmap(resume_parsed: dict, jd_parsed: dict, match_analysis: dict,
                           config: Optional[GeminiConfig] = None) -> dict:
    """
    Plan the distribution of questions across categories for an interview.

    Args:
        resume_parsed: Parsed resume profile.
        jd_parsed: Parsed job description blueprint.
        match_analysis: Gap match analysis results.
        config: Optional GeminiConfig settings.

    Returns:
        Dict mapping question categories to count values.
    """
    if config is None:
        config = get_default_config()

    if not config.api_key:
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
        return call_gemini_json(prompt, config)
    except Exception as e:
        logger.warning(
            f"Interview Planner Agent Gemini call failed: {e}. "
            f"Falling back to programmatic roadmap planner."
        )
        return _plan_interview_roadmap_local(resume_parsed, jd_parsed, match_analysis)
