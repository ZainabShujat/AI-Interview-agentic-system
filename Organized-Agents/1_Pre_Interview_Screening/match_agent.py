"""
HireIntel — Deterministic Match Agent
======================================
Performs reproducible, explainable skill-gap analysis between a parsed resume
and a parsed job description. **No LLM calls** — purely deterministic.

Standalone usage:
    from agents.match_agent import match_resume_and_jd

    result = match_resume_and_jd(resume_parsed, jd_parsed)
    print(result["matchScore"])        # 82
    print(result["justifications"])    # [{type: "success", text: "..."}]

No API key needed. This agent never calls the LLM.
"""

import re
from typing import Optional

from .gemini_core import normalize_skill, display_skill


# ---------------------------------------------------------------------------
# Skill Collection Helpers
# ---------------------------------------------------------------------------

def _collect_resume_skills(resume_parsed: dict) -> set:
    """Collect and normalize all skills from a parsed resume across all sources."""
    skills = set()

    # 1. Direct skills lists
    skill_fields = [
        "skills", "technical_skills", "programming_languages",
        "frameworks", "databases", "cloud_platforms", "tools", "certifications"
    ]
    for field in skill_fields:
        for val in resume_parsed.get(field, []) or []:
            skills.add(normalize_skill(val))

    # 2. Experience technologies
    for exp in resume_parsed.get("experience", []) or []:
        for tech in exp.get("technologies", []) or []:
            skills.add(normalize_skill(tech))

    # 3. Project technologies
    for proj in resume_parsed.get("projects", []) or []:
        for tech in (proj.get("technologies") or proj.get("tools") or []):
            skills.add(normalize_skill(tech))

    # 4. Link skills
    for link in resume_parsed.get("links", []) or []:
        for skill in link.get("skills_found", []) or []:
            skills.add(normalize_skill(skill))

    return {skill for skill in skills if skill}


def _collect_jd_required(jd_parsed: dict) -> set:
    return {normalize_skill(skill) for skill in (jd_parsed.get("required_skills", []) or []) if skill}


def _collect_jd_preferred(jd_parsed: dict) -> set:
    return {normalize_skill(skill) for skill in (jd_parsed.get("preferred_skills", []) or []) if skill}


# ---------------------------------------------------------------------------
# Main Agent Entry Points
# ---------------------------------------------------------------------------

def match_resume_and_jd(resume_parsed: dict, jd_parsed: dict) -> dict:
    """Alias for deterministic_match_resume_and_jd."""
    return deterministic_match_resume_and_jd(resume_parsed, jd_parsed)


def deterministic_match_resume_and_jd(resume_parsed: dict, jd_parsed: dict) -> dict:
    """
    Transparent, deterministic match model: no LLM scoring, only structured comparison.

    Scoring formula:
        matchScore = (required_coverage × 70) + (preferred_coverage × 20) + (domain_alignment × 10)

    Args:
        resume_parsed: Structured resume dict (from Resume Agent).
        jd_parsed: Structured JD dict (from JD Agent).

    Returns:
        Dict with matchScore, justifications, gaps, strengths, evidence, readiness details.
    """
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
            "skill": display_skill(skill),
            "status": "Found" if found else "Not Found",
            "source": "Detected in structured resume skills, project tools, or certifications." if found else "Not present in structured resume profile."
        })

    gaps = [
        {
            "skill": display_skill(skill),
            "description": "Required capability missing from the structured resume profile."
        }
        for skill in sorted(missing_required)
    ] + [
        {
            "skill": display_skill(skill),
            "description": "Preferred capability not found; validate during assessment if relevant."
        }
        for skill in sorted(missing_preferred)
    ]

    strengths = [
        f"Matches {len(matched_required)} of {len(required)} required skills."
    ]
    if matched_preferred:
        strengths.append(f"Also covers preferred skills: {', '.join(display_skill(s) for s in sorted(matched_preferred))}.")
    if additional:
        strengths.append(f"Brings adjacent capabilities: {', '.join(display_skill(s) for s in sorted(additional)[:6])}.")

    readiness_details = [
        {"name": "Required Skill Coverage", "score": round(len(matched_required) / len(required) * 100) if required else 100},
        {"name": "Preferred Skill Coverage", "score": round(len(matched_preferred) / len(preferred) * 100) if preferred else 100},
        {"name": "Domain Alignment", "score": 100 if domain_score else 55},
        {"name": "Ramp Risk", "score": max(35, 100 - (len(missing_required) * 18) - (len(missing_preferred) * 7))},
        {"name": "Assessment Priority", "score": min(100, 55 + (len(missing_required) * 12) + (len(missing_preferred) * 5))}
    ]

    # Generate explainable matching justifications
    justifications = []

    total_req = len(required)
    match_req = len(matched_required)
    if total_req > 0:
        justifications.append({
            "type": "success" if match_req >= total_req * 0.7 else "warning",
            "text": f"Matches {match_req}/{total_req} required skills ({', '.join(display_skill(s) for s in sorted(matched_required)[:5])}{' and more' if len(matched_required) > 5 else ''})"
        })
    else:
        justifications.append({
            "type": "success",
            "text": "No required skills specified in Job Description."
        })

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

    for s in sorted(missing_required)[:3]:
        justifications.append({
            "type": "warning",
            "text": f"Missing required skill: {display_skill(s)}"
        })

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
        "matched_skills": [display_skill(skill) for skill in sorted(matched_required | matched_preferred)],
        "missing_skills": [display_skill(skill) for skill in sorted(missing_required | missing_preferred)],
        "additional_skills": [display_skill(skill) for skill in sorted(additional)],
        "evidence": evidence
    }


def generate_assessment_blueprint(jd_parsed: dict, match_analysis: dict) -> dict:
    """Generate interview module plan from JD and match gaps."""
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


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

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
            "Deep expertise in React, TypeScript, and state management architectures.",
            "Proven track record of designing REST and GraphQL APIs.",
            "Strong deployment and operations expertise using Docker, Kubernetes, and AWS."
        ],
        "gaps": [
            {"skill": "High-Frequency Messaging Networks", "description": "Familiarity with Apache Kafka or RabbitMQ missing."},
            {"skill": "Fintech Security Compliance", "description": "PCI-DSS or SOC2 compliance experience not found."}
        ],
        "matched_skills": ["React", "TypeScript", "Python", "FastAPI", "Docker", "AWS"],
        "missing_skills": ["Kafka", "SOC2 Compliance"],
        "evidence": [
            {"skill": "React", "status": "Found", "source": "Found in Experience"},
            {"skill": "Kafka", "status": "Not Found", "source": "Not found in resume text"}
        ]
    }
