import os
import shutil
from pathlib import Path

def create_structure():
    base_dir = Path(r"c:\Users\shuja\Desktop\agents\AI-Interview-agentic-system")
    github_dir = base_dir / "github"
    agents_src_dir = base_dir / "agents"
    
    # 1. Create directories
    directories = [
        "playground",
        "examples/screenshots",
        "docs",
        "assets",
        "Resume Parser Agent",
        "JD Parser Agent",
        "Readiness Match Agent",
        "Interview Agent",
        "Judge Agent",
        "Planner Agent",
        "Report Agent",
        "Memory Agent",
        "Roadmap Agent",
        "Shared Utilities"
    ]
    
    for d in directories:
        (github_dir / d).mkdir(parents=True, exist_ok=True)
        
    # 2. Copy and rename agent files
    agent_mappings = {
        "resume_agent.py": "Resume Parser Agent/resume_agent.py",
        "jd_agent.py": "JD Parser Agent/jd_agent.py",
        "match_agent.py": "Readiness Match Agent/match_agent.py",
        "interview_agent.py": "Interview Agent/interview_agent.py",
        "judge_agent.py": "Judge Agent/judge_agent.py",
        "planner_agent.py": "Planner Agent/planner_agent.py",
        "report_agent.py": "Report Agent/report_agent.py",
        "memory_agent.py": "Memory Agent/memory_agent.py",
        "roadmap_agent.py": "Roadmap Agent/roadmap_agent.py",
        "gemini_core.py": "Shared Utilities/gemini_core.py",
        "__init__.py": "Shared Utilities/__init__.py"
    }
    
    for src_file, dest_rel_path in agent_mappings.items():
        src_path = agents_src_dir / src_file
        dest_path = github_dir / dest_rel_path
        if src_path.exists():
            shutil.copy2(src_path, dest_path)
        else:
            print(f"Warning: Source file {src_path} does not exist.")
            
    # 3. Copy playground
    playground_src = base_dir / "agent-playground" / "index.html"
    playground_dest = github_dir / "playground" / "index.html"
    if playground_src.exists():
        shutil.copy2(playground_src, playground_dest)
        
    # 4. Create placeholders for examples, docs, assets
    (github_dir / "examples" / "sample_resume.pdf").touch()
    (github_dir / "examples" / "sample_jd.txt").touch()
    (github_dir / "examples" / "sample_report.pdf").touch()
    
    (github_dir / "docs" / "workflow.png").touch()
    (github_dir / "docs" / "architecture.png").touch()
    (github_dir / "docs" / "api-flow.png").touch()
    (github_dir / "docs" / "demo.gif").touch()
    
    (github_dir / "assets" / "logo.png").touch()
    (github_dir / "assets" / "banner.png").touch()

if __name__ == "__main__":
    create_structure()
    print("GitHub structure creation and file copying completed.")
