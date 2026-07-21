import logging
import uuid
from typing import Dict, Any, List

from .gemini_core import GeminiConfig
from .jd_agent import parse_jd
from .resume_agent import parse_resume
from .match_agent import match_resume_and_jd
from .planner_agent import plan_interview_roadmap
from .interview_agent import generate_question
from .judge_agent import judge_answer
from .report_agent import generate_final_report

logger = logging.getLogger(__name__)

class VoiceInterviewOrchestrator:
    """
    Orchestrates the entire interview flow as a true autonomous agent.
    Maintains session state internally so the frontend remains completely dumb.
    """
    def __init__(self, api_key: str = ""):
        self.config = GeminiConfig(api_key=api_key) if api_key else GeminiConfig()
        # In-memory session store: session_id -> state
        self.sessions = {}

    def start_interview(self, jd_text: str, resume_text: str) -> Dict[str, Any]:
        """
        Parses context, generates blueprint, creates session, returns first question.
        """
        session_id = str(uuid.uuid4())
        
        logger.info("Parsing JD...")
        jd_parsed = parse_jd(jd_text, config=self.config)

        logger.info("Parsing Resume...")
        resume_parsed = parse_resume(resume_text, config=self.config)

        logger.info("Matching Resume and JD...")
        match_results = match_resume_and_jd(resume_parsed, jd_parsed)

        logger.info("Planning Interview Roadmap...")
        roadmap = plan_interview_roadmap(resume_parsed, jd_parsed, match_results, config=self.config)
        blueprint = roadmap.get("assessment_blueprint", {"title": "Candidate", "topics": []})

        # Generate first question based on the parsed documents
        first_question = generate_question(
            resume=resume_parsed,
            jd=jd_parsed,
            history=[],
            category="Technical",
            difficulty="Medium",
            config=self.config
        )
        
        self.sessions[session_id] = {
            "jd": jd_parsed,
            "resume": resume_parsed,
            "roadmap": roadmap,
            "blueprint": blueprint,
            "history": [{"role": "ai", "content": first_question}],
            "evaluations": []
        }

        return {
            "session_id": session_id,
            "first_question": first_question
        }

    def process_turn(self, session_id: str, transcript: str, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes candidate audio transcript, judges it, updates memory, generates next question.
        """
        if session_id not in self.sessions:
            raise ValueError("Invalid session_id")
            
        session = self.sessions[session_id]
        
        # 1. Record user's answer
        session["history"].append({"role": "user", "content": transcript})
        
        # 2. Judge answer based on the previous AI question
        last_question = ""
        for msg in reversed(session["history"]):
            if msg["role"] == "ai":
                last_question = msg["content"]
                break
                
        evaluation = judge_answer(last_question, transcript, signals, config=self.config)
        session["evaluations"].append(evaluation)
        
        # 3. Generate next adaptive question
        next_question = generate_question(
            resume=session["resume"],
            jd=session["jd"],
            history=session["history"],
            category="Technical",
            difficulty="Medium",
            config=self.config
        )
        
        # 4. Record AI's new question
        session["history"].append({"role": "ai", "content": next_question})
        
        return {
            "evaluation": evaluation,
            "next_question": next_question
        }
