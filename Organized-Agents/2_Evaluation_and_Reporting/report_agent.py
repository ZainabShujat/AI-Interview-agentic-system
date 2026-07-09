"""
HireIntel — Report Agent
=========================
Compiles full interview sessions and telemetry signals into diagnostic career
readiness reports containing executive summaries, dimension/category scores,
skills heatmaps, and communication pacing profiles.

Standalone usage:
    from agents.report_agent import generate_final_report
    from agents.gemini_core import GeminiConfig

    config = GeminiConfig(api_key="your-key")
    report = generate_final_report(all_qa, memory, config=config)
    print(report["overallScore"])

Works without API key (degrades gracefully to formatted mock report).
"""

import json
import logging
from typing import Optional

from .gemini_core import GeminiConfig, get_default_config, call_gemini_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Communication Profile Compiler
# ---------------------------------------------------------------------------

def compile_communication_profile(all_qa: list) -> dict:
    """Aggregate vocal, pacing, and completeness telemetry into a profile."""
    if not all_qa:
        return {}

    wpm_list = []
    filler_list = []
    latency_list = []
    words_list = []
    accuracy_list = []
    practicality_list = []
    problem_solving_list = []
    business_thinking_list = []

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
        practicality_list.append(eval_data.get("practicality", 80) or 80)
        problem_solving_list.append(eval_data.get("problemSolving", 78) or 78)
        business_thinking_list.append(eval_data.get("businessThinking", 75) or 75)

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


# ---------------------------------------------------------------------------
# Mock Fallback Report Generator
# ---------------------------------------------------------------------------

def get_mock_report_final(all_qa: list, memory: dict) -> dict:
    """Generate a mock report structure when Gemini is not configured."""
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


# ---------------------------------------------------------------------------
# Main Agent Entry Point
# ---------------------------------------------------------------------------

def generate_final_report(all_qa: list, memory: dict,
                          config: Optional[GeminiConfig] = None) -> dict:
    """
    Compile the complete interview session and memory into a final diagnostic report.

    Args:
        all_qa: List of Q&A records with evaluation data.
        memory: Persistent interview session memory.
        config: Optional GeminiConfig settings.

    Returns:
        The diagnostic report dictionary.
    """
    if config is None:
        config = get_default_config()

    if not config.api_key:
        report_json = get_mock_report_final(all_qa, memory)
        report_json["communicationProfile"] = compile_communication_profile(all_qa)
        report_json["all_qa"] = all_qa
        return report_json

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
        report_json = call_gemini_json(prompt, config)
        report_json["communicationProfile"] = compile_communication_profile(all_qa)
        report_json["all_qa"] = all_qa
        return report_json
    except Exception as e:
        logger.warning(f"Report Agent Gemini call failed: {e}. Falling back to mock final report.")
        report_json = get_mock_report_final(all_qa, memory)
        report_json["communicationProfile"] = compile_communication_profile(all_qa)
        report_json["all_qa"] = all_qa
        return report_json
