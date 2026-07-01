"""
HireIntel — Session Memory Agent
================================
Maintains persistent session state across the interview loop.
Tracks tested vs. untested skills, demonstrated strengths, and weak areas.

Standalone usage:
    from agents.memory_agent import update_memory
    from agents.gemini_core import GeminiConfig

    config = GeminiConfig(api_key="your-key")
    memory = update_memory(
        current_memory=None,
        question="How do you handle schema migrations?",
        answer="I write SQL scripts and apply them during low traffic...",
        evaluation={"accuracy": 80, "depth": 70},
        config=config
    )
    print(memory["tested_skills"])

Works without API key (degrades gracefully to rule-based keyword matching).
"""

import json
import logging
from typing import Optional

from .gemini_core import GeminiConfig, get_default_config, call_gemini_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Main Agent Entry Point
# ---------------------------------------------------------------------------

def update_memory(current_memory: Optional[dict], question: str, answer: str,
                  evaluation: dict, jd_parsed: Optional[dict] = None,
                  config: Optional[GeminiConfig] = None) -> dict:
    """
    Update persistent session memory with the latest Q&A evaluation.

    Tracks demonstrated vs. weak skills, tested vs. untested JD skills, 
    and confidence-by-skill evidence.

    Args:
        current_memory: The current session memory dictionary, or None to initialize.
        question: The last interview question asked.
        answer: The candidate's response.
        evaluation: The Judge Agent evaluation results for the answer.
        jd_parsed: Optional parsed job description (used to initialize untested skills).
        config: Optional GeminiConfig settings.

    Returns:
        The updated session memory dictionary.
    """
    if config is None:
        config = get_default_config()

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
    if config.api_key:
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
            extracted = call_gemini_json(prompt, config)
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
        except Exception as e:
            logger.warning(f"Memory Agent Gemini call failed: {e}. Falling back to heuristics.")

    # Programmatic Fallback/Mock Memory Parser
    accuracy = evaluation.get("accuracy", 75)
    depth = evaluation.get("depth", 75)
    score = int((accuracy + depth) / 2)

    # Expanded fallback skill list
    skills_list = [
        "React", "TypeScript", "Python", "FastAPI", "SQL", "Docker", "AWS",
        "Kafka", "RabbitMQ", "Kubernetes", "Compliance", "SOC2", "Redis",
        "PostgreSQL", "CI/CD", "Terraform", "GraphQL", "NoSQL", "Microservices"
    ]
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
            "evidence": f"Candidate demonstrated {'solid' if score >= 75 else 'basic'} familiarity with {skill} during the response."
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
