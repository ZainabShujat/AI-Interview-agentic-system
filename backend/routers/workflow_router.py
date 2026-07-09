from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import InterviewSlot, Interview, AuditLog
from schemas import SlotSubmitRequest, SchedulingResponse
from services.workflow_orchestrator import WorkflowOrchestrator
from datetime import datetime

router = APIRouter(prefix="/workflow", tags=["workflow"])

@router.post("/submit-slots", response_model=SchedulingResponse)
def submit_slots(request: SlotSubmitRequest, db: Session = Depends(get_db)):
    """
    Candidate or Recruiter submits available slots.
    """
    interview = db.query(Interview).filter(Interview.id == request.interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    for slot_data in request.slots:
        # Expecting ISO strings
        try:
            start_time = datetime.fromisoformat(slot_data["start_time"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(slot_data["end_time"].replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Expected ISO 8601 string.")
            
        slot = InterviewSlot(
            interview_id=request.interview_id,
            role=request.role,
            start_time=start_time,
            end_time=end_time
        )
        db.add(slot)
    
    db.commit()
    
    # Try scheduling if both parties might have submitted slots
    success, message = WorkflowOrchestrator.try_schedule(db, request.interview_id)
    
    if success:
        # Refresh to get meeting details
        db.refresh(interview)
        if interview.meeting:
            return SchedulingResponse(
                success=True,
                message=message,
                meeting_id=interview.meeting.meeting_id,
                join_url=interview.meeting.join_url,
                start_time=interview.meeting.start_time.isoformat()
            )
            
    return SchedulingResponse(
        success=False,
        message="Slots submitted successfully, waiting for overlap or other party."
    )

@router.get("/status/{interview_id}")
def get_workflow_status(interview_id: str, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    logs = db.query(AuditLog).filter(AuditLog.interview_id == interview_id).order_by(AuditLog.created_at).all()
    
    return {
        "workflow_state": interview.workflow_state,
        "audit_logs": [
            {
                "action": log.action,
                "details": log.details,
                "created_at": log.created_at.isoformat()
            } for log in logs
        ]
    }

from pydantic import BaseModel
class TestOrchestratorRequest(BaseModel):
    recruiter_email: str
    candidate_email: str

@router.post("/test-orchestrator")
def test_orchestrator(request: TestOrchestratorRequest, db: Session = Depends(get_db)):
    """
    Used by the Agent Playground to force a real End-to-End test of the Orchestrator (Zoom + Email)
    without needing to complete a full 30-minute AI interview first.
    """
    from models import JobDescription, Resume
    
    # 1. Create dummy JD and Resume just to satisfy DB constraints
    dummy_jd = JobDescription(raw_text="Dummy JD", parsed_json={"title": "Software Engineer"})
    dummy_resume = Resume(raw_text="Dummy Resume", parsed_json={"candidate_name": "Test Candidate"})
    db.add(dummy_jd)
    db.add(dummy_resume)
    db.commit()
    
    # 2. Create the dummy Interview ready for scheduling
    interview = Interview(
        resume_id=dummy_resume.id,
        jd_id=dummy_jd.id,
        candidate_name="Test Candidate",
        candidate_email=request.candidate_email,
        recruiter_id=request.recruiter_email,
        status="active",
        workflow_state="SCHEDULING"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    # 3. Add a mock slot for tomorrow
    from datetime import timedelta
    tomorrow = datetime.utcnow() + timedelta(days=1)
    slot = InterviewSlot(
        interview_id=interview.id,
        role="candidate",
        start_time=tomorrow,
        end_time=tomorrow + timedelta(hours=1)
    )
    db.add(slot)
    
    recruiter_slot = InterviewSlot(
        interview_id=interview.id,
        role="recruiter",
        start_time=tomorrow,
        end_time=tomorrow + timedelta(hours=1)
    )
    db.add(recruiter_slot)
    db.commit()
    
    # 4. Trigger the real Orchestrator!
    success, message = WorkflowOrchestrator.try_schedule(db, str(interview.id))
    
    # 5. Fetch the result
    db.refresh(interview)
    zoom_url = interview.meeting.join_url if interview.meeting else "No Zoom link generated"
    
    return {
        "success": success,
        "message": message,
        "zoom_url": zoom_url,
        "emails_sent_to": [request.candidate_email, request.recruiter_email]
    }

