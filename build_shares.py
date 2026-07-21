import os
import shutil

base_dir = r"c:\Users\shuja\Desktop\agents\AI-Interview-agentic-system"
src_dir = os.path.join(base_dir, "agents")

shares = {
    "agentshare1": ["resume_agent.py"],
    "agentshare2": ["jd_agent.py", "match_agent.py"],
    "agentshare3": ["interview_agent.py", "judge_agent.py"],
    "agentshare4": ["memory_agent.py", "planner_agent.py"],
    "agentshare5": ["resume_agent.py", "jd_agent.py", "match_agent.py", "planner_agent.py", "interview_agent.py", "judge_agent.py", "memory_agent.py", "report_agent.py", "roadmap_agent.py", "orchestrator_agent.py", "voice_server_standalone.py", "playground.html"]
}

example_codes = {
    "agentshare1": """from gemini_core import GeminiConfig
from resume_agent import parse_resume

config = GeminiConfig(api_key="YOUR_API_KEY_HERE")
result = parse_resume("Jane Doe. Python Developer.", config=config)
print("Resume Parsing Result:", result)
""",
    "agentshare2": """from gemini_core import GeminiConfig
from jd_agent import parse_jd
from match_agent import match_resume_and_jd

config = GeminiConfig(api_key="YOUR_API_KEY_HERE")
jd_result = parse_jd("Looking for Python Developer.", config=config)
resume_data = {"candidate_name": "Jane", "skills": ["Python"]}
match = match_resume_and_jd(resume_data, jd_result)
print("Match Score:", match.get("matchScore"))
""",
    "agentshare3": """from gemini_core import GeminiConfig
from interview_agent import generate_interview_question
from judge_agent import evaluate_answer

config = GeminiConfig(api_key="YOUR_API_KEY_HERE")
question = generate_interview_question("Python", config=config)
print("Question:", question)

evaluation = evaluate_answer(question, "I use print statements.", config=config)
print("Evaluation:", evaluation)
""",
    "agentshare4": """from gemini_core import GeminiConfig
from planner_agent import generate_interview_plan
from memory_agent import SessionMemory

config = GeminiConfig(api_key="YOUR_API_KEY_HERE")
plan = generate_interview_plan([{"skill": "Python", "importance": "high"}], config=config)
print("Interview Plan:", plan)

memory = SessionMemory()
memory.add_interaction("Hello", "Hi there")
print("Memory History:", memory.get_history())
""",
    "agentshare5": """from orchestrator_agent import VoiceInterviewOrchestrator

# Initialize the orchestrator for the voice interview
orchestrator = VoiceInterviewOrchestrator(api_key="YOUR_API_KEY_HERE")
print("Orchestrator initialized. Run voice_server.py to start the voice agent API.")
"""
}

readme_texts = {
    "agentshare1": "# Agent Share 1: Resume Parser\n\nContains the resume parser and core configuration. Plug this into your API to parse candidate resumes into structured JSON.\n\n## Usage\n1. `pip install -r requirements.txt`\n2. Add your API key to `example.py`\n3. Run `python example.py`",
    "agentshare2": "# Agent Share 2: JD Parser & Matcher\n\nContains the Job Description parser and Match agent to calculate fit scores.\n\n## Usage\n1. `pip install -r requirements.txt`\n2. Add your API key to `example.py`\n3. Run `python example.py`",
    "agentshare3": "# Agent Share 3: Interview & Judge\n\nContains the agents to generate technical interview questions and score candidate answers.\n\n## Usage\n1. `pip install -r requirements.txt`\n2. Add your API key to `example.py`\n3. Run `python example.py`",
    "agentshare4": "# Agent Share 4: Memory & Planner\n\nContains the session memory tracker and the planner agent to create interview roadmaps.\n\n## Usage\n1. `pip install -r requirements.txt`\n2. Add your API key to `example.py`\n3. Run `python example.py`",
    "agentshare5": "# Voice AI Interviewer (Agent Share 5)\n\nContains the complete autonomous Voice Interview orchestrator integrating all sub-agents (Resume, JD, Planner, Memory, Interview, Judge) along with real STT and TTS.\n\n## Usage\n1. `pip install -r requirements.txt`\n2. Add your API keys (`GEMINI_API_KEY`, `DEEPGRAM_API_KEY`)\n3. Run `python voice_server.py`\n4. Open `playground.html` in your browser."
}

for share, files in shares.items():
    target_dir = os.path.join(base_dir, share)
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy common files (skip __init__.py — shares are standalone, not packages)
    shutil.copy2(os.path.join(src_dir, "gemini_core.py"), target_dir)
    
    if share == "agentshare5":
        speech_service_src = os.path.join(base_dir, "backend", "services", "speech_service.py")
        if os.path.exists(speech_service_src):
            shutil.copy2(speech_service_src, target_dir)
    
    # Copy specific agent files, converting relative imports to direct imports
    for f in files:
        src_path = os.path.join(src_dir, f)
        
        # Rename voice_server_standalone.py to voice_server.py
        dst_filename = "voice_server.py" if f == "voice_server_standalone.py" else f
        dst_path = os.path.join(target_dir, dst_filename)
        
        with open(src_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        # Convert relative imports (from .module) to direct imports (from module)
        content = content.replace("from .gemini_core", "from gemini_core")
        with open(dst_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        
    # Write requirements
    reqs = "google-generativeai\npydantic\nfastapi\nuvicorn\n"
    if share == "agentshare5":
        reqs += "python-multipart\nhttpx\nPyPDF2\n"
    with open(os.path.join(target_dir, "requirements.txt"), "w") as f:
        f.write(reqs)
        
    # Write example.py
    with open(os.path.join(target_dir, "example.py"), "w") as f:
        f.write(example_codes[share])
        
    # Write README.md
    with open(os.path.join(target_dir, "README.md"), "w") as f:
        f.write(readme_texts[share])
        
print("Shares created successfully.")
