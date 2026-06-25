import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini: API Key loaded and configured successfully")
else:
    print("Gemini: API Key missing. Running in Mock Agent fallback mode.")

def call_gemini_json(prompt: str) -> dict:
    """Helper to query Gemini 1.5 Flash and request a JSON response."""
    if not GEMINI_API_KEY:
        raise ValueError("API Key missing")
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini API call failed: {e}. Falling back to simulation logic.")
        raise e

# --- 1. Resume Parser Agent ---
def parse_resume(raw_text: str) -> dict:
    if not GEMINI_API_KEY:
        return get_mock_resume_parsed()
        
    prompt = f"""
    You are an expert recruiter parsing a candidate resume.
    Extract the following fields from the raw text:
    - Skills (list of tech & soft skills)
    - Projects (list of projects with description and tools used)
    - Experience (roles, company, duration, achievements)
    - Education (degrees, school, graduation year)
    - Certifications (list of certificates)

    Resume Raw Text:
    {raw_text}

    Return JSON matching this schema:
    {{
      "skills": ["skill1", "skill2"],
      "projects": [{{"title": "", "description": "", "tools": []}}],
      "experience": [{{"title": "", "company": "", "duration": "", "summary": ""}}],
      "education": [{{"degree": "", "school": "", "year": ""}}],
      "certifications": ["cert1"]
    }}
    """
    try:
        return call_gemini_json(prompt)
    except Exception:
        return get_mock_resume_parsed()

# --- 2. JD Parser Agent ---
def parse_jd(raw_text: str) -> dict:
    if not GEMINI_API_KEY:
        return get_mock_jd_parsed()
        
    prompt = f"""
    You are an expert recruiter parsing a Job Description.
    Extract the following details from the text:
    - Target Job Title
    - Required Skills (must have)
    - Preferred Skills (nice to have)
    - Target Industry
    - Seniority Level (Junior, Mid, Senior, Lead, Director)

    Job Description Raw Text:
    {raw_text}

    Return JSON matching this schema:
    {{
      "title": "Software Engineer",
      "required_skills": ["skill1", "skill2"],
      "preferred_skills": ["skill1"],
      "industry": "Finance / SaaS",
      "seniority": "Senior"
    }}
    """
    try:
        return call_gemini_json(prompt)
    except Exception:
        return get_mock_jd_parsed()

# --- 3. Match Agent ---
def match_resume_and_jd(resume_parsed: dict, jd_parsed: dict) -> dict:
    if not GEMINI_API_KEY:
        return get_mock_match_analysis(resume_parsed, jd_parsed)
        
    prompt = f"""
    Compare the candidate's parsed Resume against the parsed Job Description (JD).
    
    Candidate Resume Data:
    {json.dumps(resume_parsed, indent=2)}
    
    Job Description Data:
    {json.dumps(jd_parsed, indent=2)}
    
    Evaluate the following:
    1. Overall Match Score (0 to 100). Be realistic.
    2. Strengths: 3-4 key alignment items showing where the candidate matches requirements well.
    3. Gaps: 2-3 development gaps where candidate lacks specified required or preferred skills. Include specific descriptions of the gaps.
    4. Readiness Details: A breakdown score (0-100) for 5 dimensions:
       - Core Coding & Architecture
       - System Design & Scalability
       - Team Leadership & Culture
       - Domain Experience
       - Tooling & CI/CD Pipelines
    5. Matched Skills: list of core skills matched from requirements.
    6. Missing Skills: list of required/preferred skills missing in the resume.
    7. Evidence: list of mappings, showing which skills were found in which projects/experience, or explicitly not found.
       
    Return JSON matching this schema:
    {{
      "matchScore": 82,
      "roleInfo": {{
        "title": "Target Role Title",
        "industry": "Target Industry",
        "seniority": "Target Seniority"
      }},
      "readinessDetails": [
        {{"name": "Core Coding & Architecture", "score": 80}},
        {{"name": "System Design & Scalability", "score": 75}},
        {{"name": "Team Leadership & Culture", "score": 90}},
        {{"name": "Domain Experience", "score": 70}},
        {{"name": "Tooling & CI/CD Pipelines", "score": 85}}
      ],
      "strengths": ["Strength 1 text", "Strength 2 text"],
      "gaps": [
        {{"skill": "Skill Name", "description": "Why it is a gap and what is missing"}}
      ],
      "matched_skills": ["SkillA", "SkillB"],
      "missing_skills": ["SkillC"],
      "evidence": [
        {{"skill": "SkillA", "status": "Found", "source": "Found in Experience: Software Engineer at Stripe"}},
        {{"skill": "SkillC", "status": "Not Found", "source": "Not found in resume"}}
      ]
    }}
    """
    try:
        return call_gemini_json(prompt)
    except Exception:
        return get_mock_match_analysis(resume_parsed, jd_parsed)

# --- 4. Interview Planner Agent ---
def plan_interview_roadmap(resume_parsed: dict, jd_parsed: dict, match_analysis: dict) -> dict:
    if not GEMINI_API_KEY:
        seniority = jd_parsed.get("seniority", "Mid")
        role = jd_parsed.get("title", "Software Engineer")
        industry = jd_parsed.get("industry", "Technology")
        gaps = match_analysis.get("gaps", [])
        
        roadmap = {"Technical": 1, "Scenario": 1, "Behavioral": 1}
        
        # Adjust programmatically based on gaps
        has_behavioral_gap = False
        for gap in gaps:
            desc = gap.get("description", "").lower()
            if any(k in desc for k in ["compliance", "soc2", "audit", "leadership", "mentoring", "team"]):
                has_behavioral_gap = True
                
        if seniority in ["Senior", "Lead", "Director"]:
            roadmap["Scenario"] = 2
            if has_behavioral_gap:
                roadmap["Leadership"] = 2
            else:
                roadmap["Technical"] = 2
        elif seniority in ["Junior", "Intern"]:
            # Juniors focus heavily on technical fundamentals
            roadmap["Technical"] = 3
            roadmap["Scenario"] = 1
            roadmap["Behavioral"] = 1
        else:
            if has_behavioral_gap:
                roadmap["Behavioral"] = 2
            else:
                roadmap["Technical"] = 2
                
        return roadmap
        
    prompt = f"""
    You are the Interview Planner Agent. Based on the candidate's parsed Resume, target Job Description (JD), and match analysis (including gaps, seniority, role title, and industry), formulate a custom question distribution roadmap.
    
    Candidate Resume:
    {json.dumps(resume_parsed, indent=2)}
    
    Job Description:
    {json.dumps(jd_parsed, indent=2)}
    
    Match Analysis:
    {json.dumps(match_analysis, indent=2)}
    
    Guidelines:
    - Allocate a question count (integer from 1 to 3) for categories: "Technical", "Scenario", "Behavioral", "Leadership".
    - Total questions must be between 3 and 6.
    - Tailor the roadmap structure based on the candidate's seniority:
      - Juniors: Focus on foundational fundamentals ("Technical": 2-3).
      - Seniors: Focus on design, scaling, and architectural decisions ("Scenario": 2-3).
      - Managers/Leads: Focus on alignment, mentoring, and conflict resolution ("Leadership": 2-3).
    - Tailor the questions to the industry and role (e.g. Fintech needs compliance/security, healthcare needs HIPAA/privacy).
    - Target match weaknesses. If gaps exist in technical tools like Kafka, allocate more Scenario/Technical. If gaps exist in compliance or mentoring, allocate Leadership/Behavioral.
    
    Return JSON matching this schema:
    {{
      "Technical": 2,
      "Scenario": 2,
      "Behavioral": 1,
      "Leadership": 1
    }}
    """
    try:
        return call_gemini_json(prompt)
    except Exception:
        return {
          "Technical": 2,
          "Scenario": 1,
          "Behavioral": 1
        }

# --- 5. Interview Agent (Adaptive Question Formulation) ---
def generate_question(resume: dict, jd: dict, history: list, category: str, difficulty: str, memory: dict = None) -> str:
    if not GEMINI_API_KEY:
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
    - Do NOT mention "AI", "Agent", or structural instructions. Make it sound like a human peer interviewer.
    - Return ONLY the question text in JSON format.
    
    Return JSON matching this schema:
    {{
      "question": "The question text goes here."
    }}
    """
    try:
        res = call_gemini_json(prompt)
        return res.get("question", get_mock_question(category, difficulty, offset=len(history) if history else 0))
    except Exception:
        return get_mock_question(category, difficulty, offset=len(history) if history else 0)

# --- 6. Judge Agent ---
def judge_answer(question: str, answer: str, signals: dict) -> dict:
    if not GEMINI_API_KEY:
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
        return call_gemini_json(prompt)
    except Exception:
        return get_mock_evaluation(question, answer, signals)

# --- 7. Memory Agent ---
def update_memory(current_memory: dict, question: str, answer: str, evaluation: dict, jd_parsed: dict = None) -> dict:
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
    if GEMINI_API_KEY:
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
            extracted = call_gemini_json(prompt)
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
        except Exception:
            pass  # Fall back to programmatic parsing

    # Programmatic Fallback/Mock Memory Parser
    accuracy = evaluation.get("accuracy", 75)
    depth = evaluation.get("depth", 75)
    score = int((accuracy + depth) / 2)
    
    # Expanded fallback skill list
    skills_list = ["React", "TypeScript", "Python", "FastAPI", "SQL", "Docker", "AWS", "Kafka", "RabbitMQ", "Kubernetes", "Compliance", "SOC2", "Redis", "PostgreSQL", "CI/CD", "Terraform", "GraphQL", "NoSQL", "Microservices"]
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
            "evidence": f"Candidate demonstrated { 'solid' if score >= 75 else 'basic' } familiarity with {skill} during the response."
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

def compile_communication_profile(all_qa: list) -> dict:
    wpm_list = []
    filler_list = []
    latency_list = []
    words_list = []
    accuracy_list = []
    
    # Executive scores lists
    practicality_list = []
    problem_solving_list = []
    business_thinking_list = []
    
    # STAR Framework counts
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
        
        # Collect new executive scores
        practicality_list.append(eval_data.get("practicality", 80) or 80)
        problem_solving_list.append(eval_data.get("problemSolving", 78) or 78)
        business_thinking_list.append(eval_data.get("businessThinking", 75) or 75)
        
        # Collect STAR indicators
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

# --- 8. Report Agent ---
def generate_final_report(all_qa: list, memory: dict) -> dict:
    if not GEMINI_API_KEY:
        return get_mock_report_final(all_qa, memory)
        
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
        report_json = call_gemini_json(prompt)
        report_json["communicationProfile"] = compile_communication_profile(all_qa)
        report_json["all_qa"] = all_qa
        return report_json
    except Exception:
        return get_mock_report_final(all_qa, memory)

# --- MOCK FALLBACKS ---

def get_mock_resume_parsed() -> dict:
    return {
      "skills": ["React", "TypeScript", "JavaScript", "Python", "FastAPI", "SQL", "Docker", "Git", "AWS"],
      "projects": [
        {
          "title": "E-Commerce Microservices",
          "description": "Designed custom order dispatch queue processing 10k orders/day.",
          "tools": ["Python", "FastAPI", "PostgreSQL", "Docker"]
        }
      ],
      "experience": [
        {
          "title": "Software Engineer",
          "company": "SaaS Ventures Ltd",
          "duration": "2024 - Present",
          "summary": "Maintained frontends in React and TypeScript while supporting python microservice features."
        }
      ],
      "education": [
        {
          "degree": "B.S. Computer Science",
          "school": "State Tech University",
          "year": "2023"
        }
      ],
      "certifications": ["AWS Certified Solutions Architect"]
    }

def get_mock_jd_parsed() -> dict:
    return {
      "title": "Senior Software Engineer",
      "required_skills": ["React", "TypeScript", "Python", "Kafka", "Distributed Systems", "PCI-DSS Security Compliance"],
      "preferred_skills": ["Kubernetes", "AWS", "FastAPI"],
      "industry": "Financial Technology",
      "seniority": "Senior"
    }

def get_mock_match_analysis(resume_parsed: dict, jd_parsed: dict) -> dict:
    return {
      "matchScore": 82,
      "roleInfo": {
        "title": jd_parsed.get("title", "Senior Software Engineer"),
        "industry": jd_parsed.get("industry", "Financial Technology"),
        "seniority": jd_parsed.get("seniority", "Senior")
      },
      "readinessDetails": [
        {"name": "Core Coding & Architecture", "score": 85},
        {"name": "System Design & Scalability", "score": 75},
        {"name": "Team Leadership & Culture", "score": 90},
        {"name": "Domain Experience (Fintech)", "score": 70},
        {"name": "Tooling & CI/CD Pipelines", "score": 90}
      ],
      "strengths": [
        "Deep expertise in React, TypeScript, and state management architectures (Redux, Zustand).",
        "Proven track record of designing REST and GraphQL APIs with Python-based microservices.",
        "Strong deployment and operations expertise using Docker, Kubernetes, and AWS Cloud services."
      ],
      "gaps": [
        {
          "skill": "High-Frequency Messaging Networks",
          "description": "The job requires familiarity with Apache Kafka or RabbitMQ. Your profile highlights database caching but lacks message queue orchestration."
        },
        {
          "skill": "Fintech Security Compliance",
          "description": "The description emphasizes PCI-DSS or SOC2 compliance experience. Your background is primarily in consumer product SaaS without direct audit exposure."
        }
      ],
      "matched_skills": ["React", "TypeScript", "Python", "FastAPI", "Docker", "AWS"],
      "missing_skills": ["Kafka", "SOC2 Compliance"],
      "evidence": [
        {"skill": "React", "status": "Found", "source": "Found in Experience: Software Engineer at SaaS Ventures Ltd"},
        {"skill": "TypeScript", "status": "Found", "source": "Found in Experience: Software Engineer at SaaS Ventures Ltd"},
        {"skill": "Python", "status": "Found", "source": "Found in Project: E-Commerce Microservices"},
        {"skill": "FastAPI", "status": "Found", "source": "Found in Project: E-Commerce Microservices"},
        {"skill": "Docker", "status": "Found", "source": "Found in Project: E-Commerce Microservices"},
        {"skill": "AWS", "status": "Found", "source": "Found in Certifications: AWS Certified Solutions Architect"},
        {"skill": "Kafka", "status": "Not Found", "source": "Not found in resume text"},
        {"skill": "SOC2 Compliance", "status": "Not Found", "source": "Not found in resume text"}
      ]
    }

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
    pool = MOCK_QUESTIONS_POOL.get(category, MOCK_QUESTIONS_POOL["Technical"])
    idx = offset % len(pool)
    return pool[idx]

def get_mock_evaluation(question: str, answer: str, signals: dict) -> dict:
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

def get_mock_report_final(all_qa: list, memory: dict) -> dict:
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
