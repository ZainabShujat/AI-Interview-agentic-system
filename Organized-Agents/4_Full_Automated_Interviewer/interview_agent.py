"""
HireIntel — Adaptive Interview Agent
====================================
Generates contextual interview questions that adapt dynamically based on 
the candidate's background, target job description, conversation history, 
and session memory status (such as weaknesses or follow-up needs).

Standalone usage:
    from agents.interview_agent import generate_question
    from agents.gemini_core import GeminiConfig

    config = GeminiConfig(api_key="your-key")
    result = generate_question(resume, jd, history=[], category="Technical", 
                               difficulty="Medium", config=config)
    print(result)

Works without API key (degrades gracefully to a static mock question pool).
"""

import json
import logging
from typing import Optional

from .gemini_core import GeminiConfig, get_default_config, call_gemini_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mock Questions Pool & Fallback Generator
# ---------------------------------------------------------------------------

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
    """Select a mock question based on category and current question offset."""
    pool = MOCK_QUESTIONS_POOL.get(category, MOCK_QUESTIONS_POOL["Technical"])
    idx = offset % len(pool)
    return pool[idx]


# ---------------------------------------------------------------------------
# Main Agent Entry Point
# ---------------------------------------------------------------------------

def generate_question(resume: dict, jd: dict, history: list, category: str, difficulty: str,
                      memory: Optional[dict] = None, config: Optional[GeminiConfig] = None) -> str:
    """
    Generate the next interview question.

    Supports memory guidelines (like skill-gap targets or follow-up probes)
    to adjust question targets dynamically.

    Args:
        resume: Parsed resume profile.
        jd: Parsed job description blueprint.
        history: Current conversation history.
        category: Targeted category (Technical, Scenario, Behavioral, Leadership).
        difficulty: Targeted difficulty level (Easy, Medium, Hard).
        memory: Optional persistent session memory.
        config: Optional GeminiConfig settings.

    Returns:
        The generated question text.
    """
    if config is None:
        config = get_default_config()

    if not config.api_key:
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
        res = call_gemini_json(prompt, config)
        question = res.get("question")
        if not question:
            raise RuntimeError("Gemini response did not include a question field.")
        return question
    except Exception as e:
        logger.warning(
            f"Question Generator Agent Gemini call failed: {e}. "
            f"Falling back to mock question generator."
        )
        return get_mock_question(category, difficulty, offset=len(history) if history else 0)
