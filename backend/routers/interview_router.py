from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from services import gemini_service, pdf_service

router = APIRouter(prefix="/api/interview", tags=["interview"])

@router.post("/start")
async def start_interview(payload: schemas.InterviewStartRequest, db: Session = Depends(get_db)):
    # Verify inputs
    resume = db.query(models.Resume).filter(models.Resume.id == payload.resume_id).first()
    jd = db.query(models.JobDescription).filter(models.JobDescription.id == payload.jd_id).first()
    if not resume or not jd:
        raise HTTPException(status_code=404, detail="Resume or Job Description record not found.")
        
    try:
        # Match analysis to extract initial alignment profiles
        match_analysis = gemini_service.match_resume_and_jd(resume.parsed_json, jd.parsed_json)
        
        # Plan interview roadmap
        roadmap = gemini_service.plan_interview_roadmap(resume.parsed_json, jd.parsed_json, match_analysis)
        
        # Compile category distribution into a sequential category routing queue
        category_queue = []
        for cat in ["Technical", "Scenario", "Behavioral", "Leadership"]:
            count = roadmap.get(cat, 0)
            category_queue.extend([cat] * count)
        
        if not category_queue:
            category_queue = ["Technical", "Scenario", "Behavioral"]
            
        first_category = category_queue[0]
        first_difficulty = "Medium"
        question_text = gemini_service.generate_question(
            resume=resume.parsed_json,
            jd=jd.parsed_json,
            history=[],
            category=first_category,
            difficulty=first_difficulty,
            memory=None
        )
        
        # Extract candidate name and email from parsed resume details
        parsed_resume = resume.parsed_json or {}
        cand_name = parsed_resume.get("candidate_name") or "Candidate"
        cand_email = parsed_resume.get("email") or "candidate@email.com"

        # Create Interview record
        db_interview = models.Interview(
            resume_id=resume.id,
            jd_id=jd.id,
            candidate_name=cand_name,
            candidate_email=cand_email,
            status="active",
            current_question_index=0,
            difficulty_level=first_difficulty,
            category_roadmap={"roadmap": roadmap, "queue": category_queue},
            memory_json={
                "demonstrated_skills": [],
                "weak_skills": [],
                "topics_covered": [],
                "confidence_by_skill": {},
                "questions_asked": [],
                "followup_count": 0,
                "needs_followup": False,
                "followup_context": None
            }
        )
        db.add(db_interview)
        db.commit()
        db.refresh(db_interview)
        
        return {
            "interview_id": db_interview.id,
            "question": question_text,
            "category": first_category,
            "finished": False
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error starting simulation session: {str(e)}")

@router.post("/answer")
async def submit_answer(payload: schemas.AnswerSubmitRequest, db: Session = Depends(get_db)):
    # Retrieve active interview
    interview = db.query(models.Interview).filter(models.Interview.id == payload.interview_id).first()
    if not interview or interview.status == "completed":
        raise HTTPException(status_code=404, detail="Active interview session not found.")
        
    try:
        # Run Judge Agent on user response
        evaluation = gemini_service.judge_answer(
            question=payload.question_text,
            answer=payload.answer_text,
            signals=payload.signals.model_dump()
        )
        
        # Save Answer record
        db_answer = models.Answer(
            interview_id=interview.id,
            category=payload.category,
            question_text=payload.question_text,
            answer_text=payload.answer_text,
            evaluation_json=evaluation,
            confidence_metrics=payload.signals.model_dump()
        )
        db.add(db_answer)
        
        # Update Memory Agent
        updated_memory = gemini_service.update_memory(
            current_memory=interview.memory_json,
            question=payload.question_text,
            answer=payload.answer_text,
            evaluation=evaluation,
            jd_parsed=interview.jd.parsed_json if interview.jd else None
        )
        
        # --- ADAPTIVE ENGINE DIFFICULTY LOGIC ---
        # Compute difficulty trends checking a weighted average of the last two answers.
        history_answers = db.query(models.Answer).filter(models.Answer.interview_id == interview.id).all()
        last_answers = history_answers[-2:] if len(history_answers) >= 2 else history_answers
        if last_answers:
            avg_score = 0.0
            for ans in last_answers:
                ev = ans.evaluation_json or {}
                acc = ev.get("accuracy", 75)
                dep = ev.get("depth", 75)
                comm = ev.get("communication", 75)
                prob = ev.get("problemSolving", 75)
                weighted = (acc * 0.40) + (dep * 0.30) + (comm * 0.15) + (prob * 0.15)
                avg_score += weighted
            avg_score /= len(last_answers)
            
            if avg_score > 85:
                interview.difficulty_level = "Hard"
            elif avg_score < 70:
                interview.difficulty_level = "Easy"
            else:
                interview.difficulty_level = "Medium"
        else:
            interview.difficulty_level = "Medium"

        # --- FOLLOW-UP STATE MACHINE LOGIC ---
        depth = evaluation.get("depth", 75)
        communication = evaluation.get("communication", 75)
        
        current_memory = updated_memory or {}
        followup_count = current_memory.get("followup_count", 0)
        
        if (depth < 60 or communication < 50) and followup_count < 2:
            # Trigger follow-up
            current_memory["needs_followup"] = True
            current_memory["followup_context"] = {
                "question": payload.question_text,
                "answer": payload.answer_text
            }
            current_memory["followup_count"] = followup_count + 1
            interview.memory_json = current_memory
            # Do NOT increment current_question_index
            next_idx = interview.current_question_index
        else:
            # Advance to next category
            current_memory["needs_followup"] = False
            current_memory["followup_context"] = None
            current_memory["followup_count"] = 0
            interview.memory_json = current_memory
            # Increment current_question_index
            next_idx = interview.current_question_index + 1
            interview.current_question_index = next_idx

        # Get category sequence
        category_queue = []
        if isinstance(interview.category_roadmap, dict):
            category_queue = interview.category_roadmap.get("queue", [])
        else:
            category_queue = ["Technical", "Scenario", "Behavioral"]
            
        if next_idx >= len(category_queue):
            # Simulation is complete
            interview.status = "completed"
            db.commit()
            return {
                "question": "",
                "category": "",
                "finished": True
            }
            
        next_category = category_queue[next_idx]
        
        # Retrieve previous Q&A history to feed back to prompt context
        history = [
            {"question": ans.question_text, "answer": ans.answer_text, "evaluation": ans.evaluation_json}
            for ans in history_answers
        ]
        
        # Generate next adaptive question
        next_question = gemini_service.generate_question(
            resume=interview.resume.parsed_json,
            jd=interview.jd.parsed_json,
            history=history,
            category=next_category,
            difficulty=interview.difficulty_level,
            memory=current_memory
        )
        
        db.commit()
        
        return {
            "question": next_question,
            "category": next_category,
            "finished": False
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting response: {str(e)}")

@router.get("/report")
async def get_report(interview_id: str, db: Session = Depends(get_db)):
    # Check if report already generated
    report = db.query(models.Report).filter(models.Report.interview_id == interview_id).first()
    if report:
        return report.report_json
        
    # Generate report
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found.")
        
    try:
        answers = db.query(models.Answer).filter(models.Answer.interview_id == interview_id).all()
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
        report_json = gemini_service.generate_final_report(
            all_qa=history,
            memory=interview.memory_json
        )
        
        # Save Report
        db_report = models.Report(
            interview_id=interview_id,
            report_json=report_json
        )
        db.add(db_report)
        db.commit()
        
        return report_json
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error compiling performance insights: {str(e)}")

@router.get("/report/pdf")
async def download_report_pdf(interview_id: str, db: Session = Depends(get_db)):
    # Retrieve or generate report JSON
    report_json = None
    report = db.query(models.Report).filter(models.Report.interview_id == interview_id).first()
    if report:
        report_json = report.report_json
    else:
        # Generate on the fly
        report_json = await get_report(interview_id, db)
        
    try:
        # Generate PDF binary
        pdf_bytes = pdf_service.generate_report_pdf(report_json)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=readiness-report-{interview_id[:8]}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error compiling PDF: {str(e)}")

@router.get("/reports")
async def list_reports(jd_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Interview)
    if jd_id:
        query = query.filter(models.Interview.jd_id == jd_id)
    interviews = query.order_by(models.Interview.created_at.desc()).all()
    
    results = []
    for interview in interviews:
        report = db.query(models.Report).filter(models.Report.interview_id == interview.id).first()
        resume = db.query(models.Resume).filter(models.Resume.id == interview.resume_id).first()
        jd = db.query(models.JobDescription).filter(models.JobDescription.id == interview.jd_id).first()
        
        parsed_resume = resume.parsed_json if resume else {}
        parsed_jd = jd.parsed_json if jd else {}
        
        report_data = report.report_json if report else {}
        overall_score = report_data.get("overallScore", 0)
        recommendation = report_data.get("recommendation", "Pending")
        
        if not overall_score and parsed_resume and parsed_jd:
            try:
                match = gemini_service.match_resume_and_jd(parsed_resume, parsed_jd)
                overall_score = match.get("matchScore", 60)
            except Exception:
                overall_score = 60
                
        results.append({
            "interview_id": interview.id,
            "candidate_name": parsed_resume.get("candidate_name") or interview.candidate_name or "Candidate",
            "candidate_email": parsed_resume.get("email") or interview.candidate_email or "candidate@email.com",
            "job_title": parsed_jd.get("title") or "Software Engineer",
            "jd_id": interview.jd_id,
            "score": overall_score,
            "recommendation": recommendation,
            "status": "Completed" if interview.status == "completed" else "In Progress",
            "date": interview.created_at.strftime("%Y-%m-%d") if interview.created_at else None
        })
    return results

class JudgeRequest(BaseModel):
    question: str
    answer: str
    signals: schemas.ConfidenceSignals

@router.post("/judge")
async def judge_answer_endpoint(payload: JudgeRequest):
    try:
        evaluation = gemini_service.judge_answer(
            question=payload.question,
            answer=payload.answer,
            signals=payload.signals.model_dump()
        )
        return evaluation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating response: {str(e)}")

from typing import List

class RawReportRequest(BaseModel):
    all_qa: List[Dict[str, Any]]
    memory: Dict[str, Any]

@router.post("/report/raw")
async def generate_raw_report(payload: RawReportRequest):
    try:
        report = gemini_service.generate_final_report(
            all_qa=payload.all_qa,
            memory=payload.memory
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error compiling report: {str(e)}")
