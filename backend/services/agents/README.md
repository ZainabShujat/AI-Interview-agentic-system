# HireIntel — Standalone Agent Package

This folder contains the complete, self-contained suite of HireIntel's AI hiring and evaluation agents. They are designed as zero-dependency Python modules that can be plugged directly into other applications, websites, scripts, or orchestrator workflows.

---

## 📂 Package Structure

*   `__init__.py` — Clean entry-point exposing the public API.
*   `gemini_core.py` — Shared configuration (`GeminiConfig`), API client, local skill definitions, and fallback helpers.
*   `resume_agent.py` — Raw resume text parser.
*   `jd_agent.py` — Job description parser.
*   `match_agent.py` — Deterministic matching engine & skill gap analyzer (**reproducible, zero LLM calls**).
*   `planner_agent.py` — Custom interview question distribution planner.
*   `interview_agent.py` — Adaptive question generator.
*   `judge_agent.py` — Candidate response evaluator (scores accuracy, depth, STAR structure, pacing, and filler words).
*   `memory_agent.py` — Persistent session state manager.
*   `report_agent.py` — Speech profiling and career readiness report compiler.
*   `roadmap_agent.py` — Actionable transition learning path and monthly resume upgrade checkpoint compiler.

---

## ⚙️ Installation

All agents run using standard **Python 3**. 

### Dependencies
To install the required libraries for full LLM support and PDF document processing, run:

```bash
pip install google-generativeai pymupdf
```

*Note: If you do not have an API key or prefer local execution, the agents will automatically degrade gracefully to local rules, heuristics, and mock data generators with zero external dependencies.*

---

## 🚀 Quick Run-through Code Examples

Below are standard examples demonstrating how to import and run the core agents.

### 1. Initialize Configuration
```python
from agents.gemini_core import GeminiConfig

# Using LLM capabilities:
config = GeminiConfig(api_key="YOUR_GEMINI_API_KEY")

# For testing local rules/heuristics only (no API key needed):
# config = GeminiConfig(api_key="")
```

### 2. Resume & Job Description Parsing
Extract unstructured text into unified structured blueprints:
```python
from agents.resume_agent import parse_resume
from agents.jd_agent import parse_jd

# Parse a resume (will extract name, email, skills, and work timeline)
resume_data = parse_resume("John Doe. Email: john@example.com. Skills: Python, Docker, AWS Solutions Architect Certified...", config=config)
print("Candidate Name:", resume_data["candidate_name"])

# Parse a target job description
jd_data = parse_jd("Seeking a Senior Backend Engineer with 5+ years of experience. Required skills: Python, SQL, Kafka, Docker...", config=config)
print("Target Role Title:", jd_data["title"])
```

### 3. Deterministic Matching (No LLM Calls)
Performs reproducible skill-gap and domain overlap analysis between the parsed resume and JD:
```python
from agents.match_agent import match_resume_and_jd

match_analysis = match_resume_and_jd(resume_data, jd_data)
print("Match Score:", match_analysis["matchScore"])
print("Strengths:", match_analysis["strengths"])
print("Identified Gaps:", [gap["skill"] for gap in match_analysis["gaps"]])
```

### 4. Interactive Interview Loop & Evaluation
Simulate a live adaptive screening interview:
```python
from agents.interview_agent import generate_question
from agents.judge_agent import judge_answer
from agents.memory_agent import update_memory

# A. Generate the first adaptive question
first_question = generate_question(
    resume=resume_data,
    jd=jd_data,
    history=[],
    category="Technical",
    difficulty="Medium",
    config=config
)
print("Q1:", first_question)

# B. Evaluate the candidate's answer and pacing signals
candidate_answer = "I containerize the app using multi-stage Dockerfiles and write compose specs."
telemetry_signals = {"fillerCount": 1, "wordsPerMinute": 130, "latencySeconds": 2.5}

q1_evaluation = judge_answer(
    question=first_question,
    answer=candidate_answer,
    signals=telemetry_signals,
    config=config
)
print("Evaluated Depth Score:", q1_evaluation["depth"])
print("STAR Structure Found:", q1_evaluation["starFramework"])

# C. Update the persistent session memory (tracks weak areas and untested skills)
session_memory = update_memory(
    current_memory=None,  # First turn
    question=first_question,
    answer=candidate_answer,
    evaluation=q1_evaluation,
    jd_parsed=jd_data,
    config=config
)
```

### 5. Final Reporting & Career Roadmap
Compile final diagnostics and actionable steps:
```python
from agents.report_agent import generate_final_report
from agents.roadmap_agent import generate_career_roadmap

# Compile evaluation history and session memory into a final report card
completed_qas = [{"question": first_question, "answer": candidate_answer, "evaluation": q1_evaluation}]
hiring_report = generate_final_report(completed_qas, session_memory, config=config)
print("Overall Hiring Score:", hiring_report["overallScore"])
print("Hiring Recommendation:", hiring_report["recommendation"])

# Compile an actionable learning path roadmap to bridge identified gaps
roadmap = generate_career_roadmap(resume_data, target_role=jd_data["title"], target_jd=jd_data, config=config)
print("Actionable Weekly Milestones:")
for phase in roadmap["weekly_milestones"]:
    print(f"- {phase['week']} ({phase['focus']}): {phase['tasks']}")
```
