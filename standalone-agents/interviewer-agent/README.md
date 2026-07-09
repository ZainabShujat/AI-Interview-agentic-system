# HireIntel Interviewer Agent

A standalone, plug-and-play AI Interview Agent extracted from the HireIntel Autonomous Hiring Pipeline. 

This agent is designed to be easily embedded into any Python backend. It generates contextual, dynamic interview questions that adapt based on a candidate's resume, the target job description, the ongoing conversation history, and an optional memory state (such as detected skill gaps).

## Features
- **Dynamic Context:** Fuses Resume, JD, and Conversation History to ask hyper-relevant questions.
- **Memory Integration:** Can accept "guidelines" from previous turns (e.g., "The candidate's last answer was weak, ask a follow-up").
- **Graceful Fallbacks:** If the API key is missing or the LLM times out, it seamlessly falls back to a curated pool of deterministic mock questions so your application never crashes.
- **Model Cascading:** Automatically retries across a fallback list of Gemini models if the primary one rate-limits.

## Installation

1. Copy the `agents/` folder into your project.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```python
from agents.interview_agent import generate_question
from agents.gemini_core import GeminiConfig

# 1. Setup Configuration (Or use defaults which read from os.environ["GEMINI_API_KEY"])
config = GeminiConfig(api_key="your-google-gemini-api-key")

# 2. Mock Data (Normally this comes from your database or parsing agents)
resume = {"name": "John Doe", "skills": ["Python", "React", "Docker"]}
jd = {"title": "Full Stack Engineer", "requirements": ["Microservices", "Python"]}
history = [
    {"question": "Tell me about your Python experience.", "answer": "I use it for backends."}
]

# 3. Generate the Next Question
question = generate_question(
    resume=resume,
    jd=jd,
    history=history,
    category="Technical",    # 'Technical', 'Behavioral', 'Scenario', 'Leadership'
    difficulty="Medium",     # 'Easy', 'Medium', 'Hard'
    config=config
)

print(question)
```
