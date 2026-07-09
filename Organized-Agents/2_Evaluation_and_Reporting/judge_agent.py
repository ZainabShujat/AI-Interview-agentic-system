"""
HireIntel — Judge Agent
========================
Evaluates candidate answers on 6 dimensions (accuracy, depth, communication,
practicality, problem-solving, and business thinking), detects STAR framework
elements, and provides pacing/filler feedback based on telemetry signals.

Standalone usage:
    from agents.judge_agent import judge_answer
    from agents.gemini_core import GeminiConfig

    config = GeminiConfig(api_key="your-key")
    result = judge_answer(
        question="How do you handle scaling bottlenecks?",
        answer="I implement a read replica and vertical caching using Redis...",
        signals={"fillerCount": 2, "wordsPerMinute": 115},
        config=config
    )
    print(result["depth"])  # 80

Works without API key (degrades gracefully to rule-based heuristic scoring).
"""

import json
import logging
from typing import Optional

from .gemini_core import GeminiConfig, get_default_config, call_gemini_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Heuristic Rule-Based Evaluator (Local Fallback)
# ---------------------------------------------------------------------------

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
    tech_keywords = [
        "trade-off", "performance", "bottleneck", "scaling", "cache", "latency",
        "index", "database", "concurrency", "architecture", "design pattern",
        "refactor", "complexity", "big o"
    ]
    matched_tech = sum(1 for kw in tech_keywords if kw in ans_lower)
    depth += min(20, matched_tech * 4)

    # Practicality / execution indicators
    practical_keywords = [
        "implement", "testing", "deploy", "ci/cd", "docker", "kubernetes",
        "script", "migration", "production", "monitoring", "git", "log", "metrics"
    ]
    matched_prac = sum(1 for kw in practical_keywords if kw in ans_lower)
    practicality += min(20, matched_prac * 4)

    # Business / Product alignment indicators
    business_keywords = [
        "cost", "user experience", "ux", "revenue", "priority", "roi", "sla",
        "business requirement", "client", "stakeholder", "budget", "deliverable"
    ]
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
        communication -= 10  # Extremely slow pacing
    elif 15 <= latency <= 50:
        communication += 10  # Ideal conversational pacing

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


# ---------------------------------------------------------------------------
# Mock Evaluation Generator
# ---------------------------------------------------------------------------

def get_mock_evaluation(question: str, answer: str, signals: dict) -> dict:
    """Generate a clean mock answer evaluation for local development."""
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


# ---------------------------------------------------------------------------
# Main Agent Entry Point
# ---------------------------------------------------------------------------

def judge_answer(question: str, answer: str, signals: dict,
                 config: Optional[GeminiConfig] = None) -> dict:
    """
    Evaluate a candidate's answer to an interview question.

    Args:
        question: The question asked.
        answer: The candidate's response.
        signals: Telemetry pacing/delivery signals (latency, fillerCount, etc.).
        config: Optional GeminiConfig settings.

    Returns:
        Evaluation dictionary with scores, feedback, and STAR framework details.
    """
    if config is None:
        config = get_default_config()

    if not config.api_key:
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
        return call_gemini_json(prompt, config)
    except Exception as e:
        logger.warning(
            f"Judge Agent Gemini call failed: {e}. "
            f"Degrading gracefully to heuristic rule-based evaluator."
        )
        return judge_answer_heuristics(question, answer, signals)
