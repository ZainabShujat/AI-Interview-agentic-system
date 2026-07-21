from typing import Optional, List, Dict, Any
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Response, File, UploadFile, Form
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
from services import gemini_service, speech_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/voice", tags=["voice_interview"])


@router.post("/start")
async def start_voice_interview(
    jd_id: str = Form(...),
    resume_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Starts a new Voice Interview session. 
    Parses resume PDF, matches to JD, generates blueprint, and provides first question.
    """
    jd = db.query(models.JobDescription).filter(models.JobDescription.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job Description not found.")
        
    try:
        # Extract text from PDF
        pdf_bytes = await resume_file.read()
        import fitz
        raw_text = ""
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in pdf_doc:
            raw_text += page.get_text()
        pdf_doc.close()
        
        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Failed to extract text from Resume.")
            
        # Parse Resume
        parsed_resume = gemini_service.parse_resume(raw_text)
        db_resume = models.Resume(
            raw_text=raw_text,
            parsed_json=parsed_resume
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        
        # Match & Plan (Orchestrating agents)
        match_analysis = gemini_service.match_resume_and_jd(db_resume.parsed_json, jd.parsed_json)
        roadmap = gemini_service.plan_interview_roadmap(db_resume.parsed_json, jd.parsed_json, match_analysis)
        
        # Compile category queue
        category_queue = []
        for cat in ["Technical", "Scenario", "Behavioral", "Leadership"]:
            count = roadmap.get(cat, 0)
            category_queue.extend([cat] * count)
        if not category_queue:
            category_queue = ["Technical", "Scenario", "Behavioral"]
            
        first_category = category_queue[0]
        first_difficulty = "Medium"
        question_text = gemini_service.generate_question(
            resume=db_resume.parsed_json,
            jd=jd.parsed_json,
            history=[],
            category=first_category,
            difficulty=first_difficulty,
            memory=None
        )
        
        cand_name = parsed_resume.get("candidate_name") or "Candidate"
        cand_email = parsed_resume.get("email") or "candidate@email.com"

        # Create Interview record using UUID
        db_interview = models.Interview(
            resume_id=db_resume.id,
            jd_id=jd.id,
            candidate_name=cand_name,
            candidate_email=cand_email,
            status="active",
            workflow_state="INTERVIEWING",
            current_question_index=0,
            difficulty_level=first_difficulty,
            category_roadmap={"roadmap": roadmap, "queue": category_queue},
            memory_json={
                "demonstrated_skills": [],
                "weak_skills": [],
                "topics_covered": [],
                "confidence_by_skill": {},
                "questions_asked": [{"role": "ai", "content": question_text}],
                "followup_count": 0,
                "needs_followup": False,
                "followup_context": None
            }
        )
        db.add(db_interview)
        db.commit()
        db.refresh(db_interview)
        
        return {
            "session_uuid": db_interview.id,
            "resume_id": db_resume.id,
            "question": question_text,
            "category": first_category,
            "finished": False
        }
    except Exception as e:
        db.rollback()
        logger.exception("Voice Interview Start Failed")
        raise HTTPException(status_code=500, detail=f"Voice Start failed: {str(e)}")


@router.post("/speak")
async def process_voice_speech(
    session_uuid: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Main loop for voice interaction. 
    Transcribes audio, extracts metrics, evaluates, and generates next question.
    """
    # Retrieve active interview
    interview = db.query(models.Interview).filter(models.Interview.id == session_uuid).first()
    if not interview or interview.status == "completed":
        raise HTTPException(status_code=404, detail="Active session not found or already completed.")
        
    try:
        # Read audio bytes
        audio_bytes = await audio_file.read()
        
        # 1. Transcribe audio (Deepgram/mock)
        transcription_result = await speech_service.transcribe_audio(audio_bytes)
        transcript = transcription_result.get("transcript", "")
        
        if not transcript.strip():
             return {
                 "question": "I didn't quite catch that. Could you repeat?",
                 "category": "Retry",
                 "finished": False,
                 "evaluation": None,
                 "transcript": ""
             }
        
        # 2. Extract observable speech metrics (telemetry)
        observable_metrics = speech_service.analyze_voice_features(audio_bytes)
        
        # Get the question that was just asked
        memory = interview.memory_json or {}
        history_msgs = memory.get("questions_asked", [])
        last_question = ""
        for msg in reversed(history_msgs):
            if msg["role"] == "ai":
                last_question = msg["content"]
                break
        
        # 3. Orchestrate Judge
        evaluation = gemini_service.judge_answer(
            question=last_question,
            answer=transcript,
            signals=observable_metrics
        )
        
        # Append answer to history
        history_msgs.append({"role": "user", "content": transcript})
        
        # Retrieve category sequence
        category_queue = []
        if isinstance(interview.category_roadmap, dict):
            category_queue = interview.category_roadmap.get("queue", [])
        else:
            category_queue = ["Technical", "Scenario", "Behavioral"]
            
        current_idx = interview.current_question_index
        current_category = category_queue[current_idx] if current_idx < len(category_queue) else "General"
        
        # Save Answer record
        db_answer = models.Answer(
            interview_id=interview.id,
            category=current_category,
            question_text=last_question,
            answer_text=transcript,
            evaluation_json=evaluation,
            confidence_metrics=observable_metrics
        )
        db.add(db_answer)
        
        # 4. Update Memory Agent
        updated_memory = gemini_service.update_memory(
            current_memory=memory,
            question=last_question,
            answer=transcript,
            evaluation=evaluation,
            jd_parsed=interview.jd.parsed_json if interview.jd else None
        )
        
        # --- FOLLOW-UP STATE MACHINE LOGIC ---
        depth = evaluation.get("depth", 75)
        communication = evaluation.get("communication", 75)
        
        current_memory = updated_memory or {}
        followup_count = current_memory.get("followup_count", 0)
        
        if (depth < 60 or communication < 50) and followup_count < 2:
            current_memory["needs_followup"] = True
            current_memory["followup_context"] = {
                "question": last_question,
                "answer": transcript
            }
            current_memory["followup_count"] = followup_count + 1
            interview.memory_json = current_memory
            next_idx = interview.current_question_index
        else:
            current_memory["needs_followup"] = False
            current_memory["followup_context"] = None
            current_memory["followup_count"] = 0
            interview.memory_json = current_memory
            next_idx = interview.current_question_index + 1
            interview.current_question_index = next_idx
            
        if next_idx >= len(category_queue):
            # Session exhausted all questions in blueprint. Time to finish.
            db.commit()
            return {
                "question": "Thank you, that concludes our interview questions. I am finalizing the report now.",
                "category": "",
                "finished": True,
                "evaluation": evaluation,
                "transcript": transcript
            }
            
        next_category = category_queue[next_idx]
        
        # Gather QA history for generation context
        history_answers = db.query(models.Answer).filter(models.Answer.interview_id == interview.id).all()
        history = [
            {"question": ans.question_text, "answer": ans.answer_text, "evaluation": ans.evaluation_json}
            for ans in history_answers
        ]
        
        # 5. Generate Next Question
        next_question = gemini_service.generate_question(
            resume=interview.resume.parsed_json,
            jd=interview.jd.parsed_json,
            history=history,
            category=next_category,
            difficulty=interview.difficulty_level,
            memory=current_memory
        )
        
        current_memory["questions_asked"] = history_msgs
        current_memory["questions_asked"].append({"role": "ai", "content": next_question})
        interview.memory_json = current_memory
        
        db.commit()
        
        return {
            "question": next_question,
            "category": next_category,
            "finished": False,
            "evaluation": evaluation,
            "transcript": transcript
        }
        
    except Exception as e:
        db.rollback()
        logger.exception("Voice processing failed")
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")


@router.post("/finish")
async def finish_voice_interview(
    session_uuid: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Finalizes scores, generates the report, and marks interview as completed.
    """
    interview = db.query(models.Interview).filter(models.Interview.id == session_uuid).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    if interview.status == "completed":
        # Check if report already exists
        report = db.query(models.Report).filter(models.Report.interview_id == session_uuid).first()
        if report:
            return {"status": "success", "report": report.report_json}
            
    try:
        answers = db.query(models.Answer).filter(models.Answer.interview_id == session_uuid).all()
        history = [
            {
                "question": ans.question_text,
                "answer": ans.answer_text,
                "evaluation": ans.evaluation_json,
                "category": ans.category,
                "confidence_metrics": ans.confidence_metrics
            }
            for ans in answers
        ]
        
        # Run Report Agent
        passing_score = interview.jd.passing_score if interview.jd and interview.jd.passing_score is not None else 60
        report_json = gemini_service.generate_final_report(
            all_qa=history,
            memory=interview.memory_json,
            passing_score=passing_score
        )
        
        # Save Report
        db_report = models.Report(
            interview_id=session_uuid,
            report_json=report_json
        )
        db.add(db_report)
        
        interview.status = "completed"
        interview.workflow_state = "COMPLETED"
        db.commit()
        
        # Trigger Workflow Orchestrator 
        try:
            from services.workflow_orchestrator import WorkflowOrchestrator
            WorkflowOrchestrator.process_interview_completion(db, session_uuid)
        except ImportError:
            logger.warning("WorkflowOrchestrator not found, skipping workflow completion hook.")
        
        return {"status": "success", "report": report_json}
        
    except Exception as e:
        db.rollback()
        logger.exception("Voice Interview Finish Failed")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
