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
