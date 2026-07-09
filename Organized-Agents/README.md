# Standalone AI Hiring Agents

This folder contains the complete, self-contained suite of HireIntel's AI hiring and evaluation agents. They are designed as simple Python modules that can be plugged directly into other applications, scripts, or orchestrator workflows.

## ⚙️ Quick Install

```bash
pip install google-generativeai pymupdf
```

*Note: If you do not have an API key or prefer offline testing, the agents will automatically run using local heuristic rules.*

## 🚀 How to Run (Quickstart)

```python
from agents.gemini_core import GeminiConfig
from agents.resume_agent import parse_resume
from agents.jd_agent import parse_jd
from agents.match_agent import match_resume_and_jd

# 1. Initialize Configuration (Provide API key if available, otherwise leaves empty for offline rules)
config = GeminiConfig(api_key="YOUR_GEMINI_API_KEY") 

# 2. Parse a resume text
resume_data = parse_resume("Candidate Name: Jane Doe. Skill: React, Python, AWS...", config=config)
print("Candidate Name:", resume_data.get("candidate_name"))

# 3. Parse a job description text
jd_data = parse_jd("Looking for a Developer with experience in React and AWS...", config=config)
print("Target Role:", jd_data.get("title"))

# 4. Perform a deterministic skill-gap analysis
match_analysis = match_resume_and_jd(resume_data, jd_data)
print("Match Score:", match_analysis["matchScore"])
print("Strengths:", match_analysis["strengths"])
print("Gaps:", [gap["skill"] for gap in match_analysis["gaps"]])
```

## 🌐 Website Workflow Integration (e.g. FastAPI / Flask / Django)

If you are integrating these agents into a larger website or web application (such as an API backend server), follow this standard workflow:

### 1. Placement
Copy the entire `agents/` folder into your backend's source directory (e.g., alongside your route handlers or services).
```
my-website-backend/
├── app.py           (or main.py)
├── requirements.txt
└── agents/          <-- (Drop the folder here)
    ├── __init__.py
    ├── gemini_core.py
    └── ...
```

### 2. Initialization & Configuration
In your web application's startup code or dependency injection logic, create a `GeminiConfig` instance loaded with your environment variables (like `GEMINI_API_KEY`). Pass this config to the agents when you call them.

```python
# app.py (FastAPI Example)
import os
from fastapi import FastAPI
from pydantic import BaseModel
from agents.gemini_core import GeminiConfig
from agents.resume_agent import parse_resume

app = FastAPI()
# Load key from .env file or environment variables
api_key = os.getenv("GEMINI_API_KEY", "")
gemini_config = GeminiConfig(api_key=api_key)

class ResumeUpload(BaseModel):
    resume_text: str

@app.post("/api/parse-resume")
async def api_parse_resume(payload: ResumeUpload):
    # Call the agent directly within your route
    result = parse_resume(payload.resume_text, config=gemini_config)
    return {"status": "success", "data": result}
```

### 3. Frontend Communication
Your frontend (React, Vue, HTML/JS) can now make standard HTTP requests to these endpoints. The agents simply take strings as input and return Python dictionaries, which automatically serialize into JSON for your frontend to consume.

## 📂 File Summary
* `__init__.py` — Package exports.
* `gemini_core.py` — Config & Model parameters.
* `resume_agent.py` — Resume parser.
* `jd_agent.py` — Job description parser.
* `match_agent.py` — Local match analyzer (zero LLM calls).
* `planner_agent.py` — Interview questions distributor.
* `interview_agent.py` — Question generator.
* `judge_agent.py` — Answer scorer & evaluator.
* `memory_agent.py` — Session history tracker.
* `report_agent.py` — Final assessment compiler.
* `roadmap_agent.py` — Career roadmap & training recommendations.
