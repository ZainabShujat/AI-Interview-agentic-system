import os
import shutil

def organize_agents():
    base_dir = "agents"
    target_dir = "Organized-Agents"
    
    folders = {
        "1_Pre_Interview_Screening": ["resume_agent.py", "jd_agent.py", "match_agent.py"],
        "2_Evaluation_and_Reporting": ["judge_agent.py", "report_agent.py"],
        "3_Planning_and_Roadmap": ["planner_agent.py", "roadmap_agent.py"],
        "4_Full_Automated_Interviewer": ["interview_agent.py", "memory_agent.py", "gemini_core.py"]
    }
    
    # Create the main directory
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    for folder, files in folders.items():
        folder_path = os.path.join(target_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        for file in files:
            src = os.path.join(base_dir, file)
            dst = os.path.join(folder_path, file)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"Copied {file} to {folder}")
            else:
                print(f"Warning: {file} not found in {base_dir}")
                
    # Copy root files
    root_files = ["__init__.py", "requirements.txt", "README.md"]
    for file in root_files:
        src = os.path.join(base_dir, file)
        dst = os.path.join(target_dir, file)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {file} to root of {target_dir}")
            
    print("Done organizing agents!")

if __name__ == "__main__":
    organize_agents()
