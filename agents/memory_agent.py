"""
HireIntel — Session Memory Agent
=================================
Manages persistent session memory throughout an interview loop. Tracks:
- Tested skills.
- Untested skills from the JD.
- Weak areas (scores < 70).
- Follow-up prompts needed if the candidate had a weak answer.

Standalone usage:
    from agents.memory_agent import update_memory
    from agents.gemini_core import GeminiConfig

    config = GeminiConfig(api_key="your-key")
    session_memory = update_memory(None, question, answer, evaluation, jd)

Works without API key (degrades gracefully to programmatic session logic).
"""

import json
import logging
from typing import Optional

from .gemini_core import GeminiConfig, get_default_config, call_gemini_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Programmatic Session Memory (Local Fallback)
# ---------------------------------------------------------------------------

def _update_memory_programmatic(current_memory: Optional[dict], question: str,
                                answer: str, evaluation: dict, jd_parsed: dict) -> dict:
    """Fallback memory agent to structure tested/untested lists dynamically without API key."""
    if not current_memory or not isinstance(current_memory, dict):
        current_memory = {
            "tested_skills": [],
            "untested_skills": list(jd_parsed.get("required_skills", []) or []),
            "weak_skills": [],
            "strengths": [],
            "needs_followup": False,
            "followup_context": None
        }

    q_lower = question.lower()
    a_lower = answer.lower()

    # Detect what skills from JD were mentioned/tested
    jd_skills = list(jd_parsed.get("required_skills", []) or []) + list(jd_parsed.get("preferred_skills", []) or [])
    detected = []
    for skill in jd_skills:
        skill_lower = skill.lower()
        if skill_lower in q_lower or skill_lower in a_lower:
            detected.append(skill)

    # Move from untested to tested
    tested_set = set(current_memory.get("tested_skills", []) or [])
    untested_set = set(current_memory.get("untested_skills", []) or [])

    for skill in detected:
        tested_set.add(skill)
        if skill in untested_set:
            untested_set.remove(skill)

    current_memory["tested_skills"] = list(tested_set)
    current_memory["untested_skills"] = list(untested_set)

    # Check for weakness (Score under 70 in accuracy or depth)
    accuracy = evaluation.get("accuracy", 80)
    depth = evaluation.get("depth", 80)

    if accuracy < 70 or depth < 70:
        current_memory["needs_followup"] = True
        current_memory["followup_context"] = {
            "question": question,
            "answer": answer,
            "weak_score": min(accuracy, depth)
        }
        # Associate weakness with detected skills, or overall topic
        for skill in detected:
            if skill not in current_memory["weak_skills"]:
                current_memory["weak_skills"].append(skill)
    else:
        current_memory["needs_followup"] = False
        current_memory["followup_context"] = None
        for skill in detected:
            if skill in current_memory["weak_skills"]:
                current_memory["weak_skills"].remove(skill)

    return current_memory


# ---------------------------------------------------------------------------
# Main Agent Entry Point
# ---------------------------------------------------------------------------

def update_memory(current_memory: Optional[dict], question: str, answer: str,
                  evaluation: dict, jd_parsed: dict, config: Optional[GeminiConfig] = None) -> dict:
    """
    Update the interview session memory profile based on the latest QA turn.

    Tracks tested/untested required skills, notes candidates' weak spots,
    and flags if the interviewer needs to follow up on the next turn.

    Args:
        current_memory: Dict containing previous state (or None/empty for first turn).
        question: Question asked this turn.
        answer: Answer provided this turn.
        evaluation: Score evaluations and feedback from Judge Agent.
        jd_parsed: Parsed Job Description blueprint.
        config: Optional GeminiConfig settings.

    Returns:
        Updated session memory dictionary.
    """
    if config is None:
        config = get_default_config()

    if not config.api_key:
        return _update_memory_programmatic(current_memory, question, answer, evaluation, jd_parsed)

    # Format previous history
    mem_context = current_memory if (current_memory and isinstance(current_memory, dict)) else {}

    prompt = f"""
    You are the Interview Memory Tracker Agent. Your task is to update the running interview session memory profile based on the latest question, answer, and evaluation.
    
    Previous Session Memory:
    {json.dumps(mem_context, indent=2)}
    
    Current Turn details:
    - Question: "{question}"
    - Answer: "{answer}"
    - Evaluation details: {json.dumps(evaluation, indent=2)}
    
    Job Description Requirements:
    {json.dumps(jd_parsed, indent=2)}
    
    Update:
    1. "tested_skills": Skills/competencies explicitly targeted or verified in this or previous turns.
    2. "untested_skills": Key skills from the Job Description that have NOT been targeted or demonstrated yet.
    3. "weak_skills": Skills/areas where the candidate's scores or answers demonstrated low proficiency (scores < 70).
    4. "needs_followup": Set to true if the candidate's latest response was incomplete, evasive, or scored poorly, indicating the next question should probe or clarify this specific answer rather than changing topics.
    5. "followup_context": If needs_followup is true, save the question, answer, and context. Otherwise set to null.
    
    Return JSON matching exactly this schema:
    {{
      "tested_skills": ["React", "TypeScript"],
      "untested_skills": ["Kafka", "AWS"],
      "weak_skills": [],
      "strengths": ["Clean state architecture description"],
      "needs_followup": false,
      "followup_context": null
    }}
    """
    try:
        return call_gemini_json(prompt, config)
    except Exception as e:
        logger.warning(
            f"Memory Agent Gemini call failed: {e}. "
            f"Falling back to local programmatic session memory updater."
        )
        return _update_memory_programmatic(current_memory, question, answer, evaluation, jd_parsed)
