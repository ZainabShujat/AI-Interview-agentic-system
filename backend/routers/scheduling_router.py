"""
Scheduling Router — Orchestration layer for the Scheduling Agent.

The agent makes decisions. This router executes them:
  Agent → Decision → Router → Zoom + Email + DB
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import ScheduledMeeting
from schemas import (
    ScheduleRequest,
    ScheduleAgentResponse,
    CancelResponse,
    RescheduleRequest,
)
from services.zoom_service import ZoomService
from services.email_service import EmailService

# Import the pure-intelligence agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "Scheduling-Agent"))
from scheduling_agent import SchedulingAgent  # type: ignore

router = APIRouter(prefix="/api/schedule", tags=["scheduling-agent"])

agent = SchedulingAgent()


def _meetings_to_dicts(meetings: list) -> list:
    """Convert ScheduledMeeting ORM objects to plain dicts for the agent."""
    return [
        {
            "recruiter_email": m.recruiter_email,
            "candidate_email": m.candidate_email,
            "start_time": m.start_time.isoformat() if m.start_time else "",
            "end_time": m.end_time.isoformat() if m.end_time else "",
            "status": m.status,
        }
        for m in meetings
    ]


def _meeting_to_response(m: ScheduledMeeting) -> dict:
    """Serialize a ScheduledMeeting to a JSON-safe dict."""
    return {
        "id": m.id,
        "recruiter_name": m.recruiter_name,
        "recruiter_email": m.recruiter_email,
        "candidate_name": m.candidate_name,
        "candidate_email": m.candidate_email,
        "meeting_id": m.meeting_id,
        "join_url": m.join_url,
        "password": m.password,
        "start_time": m.start_time.isoformat() if m.start_time else None,
        "end_time": m.end_time.isoformat() if m.end_time else None,
        "duration_minutes": m.duration_minutes,
        "buffer_minutes": m.buffer_minutes,
        "status": m.status,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


@router.post("", response_model=ScheduleAgentResponse)
def schedule_meeting(request: ScheduleRequest, db: Session = Depends(get_db)):
    """
    Full Scheduling Agent pipeline:
    1. Agent decides best slot (pure intelligence)
    2. Router checks for duplicates
    3. Router creates Zoom meeting
    4. Router sends emails
    5. Router stores meeting
    """
    timeline = []

    # Step 1: Gather existing meetings for conflict detection
    timeline.append({"step": "Loading existing meetings", "status": "running"})
    existing = db.query(ScheduledMeeting).filter(
        ScheduledMeeting.status == "scheduled"
    ).all()
    existing_dicts = _meetings_to_dicts(existing)
    timeline[-1]["status"] = "done"
    timeline[-1]["detail"] = f"{len(existing)} active meetings loaded"

    # Step 2: Ask the agent to decide
    timeline.append({"step": "Running Scheduling Agent", "status": "running"})
    decision = agent.schedule(
        recruiter_slots=request.recruiter.availability,
        candidate_slots=request.candidate.availability,
        existing_meetings=existing_dicts,
        duration_minutes=request.duration_minutes,
        buffer_minutes=request.buffer_minutes,
        recruiter_preferences=request.recruiter.preferences or "",
        candidate_preferences=request.candidate.preferences or ""
    )
    timeline[-1]["status"] = "done"
    timeline[-1]["detail"] = f"Agent returned: {decision['status']}"

    # If agent couldn't find a slot, return immediately
    if decision["status"] != "scheduled":
        return ScheduleAgentResponse(
            status=decision["status"],
            reasoning=decision["reasoning"],
            timeline=timeline,
        )

    selected_start = datetime.fromisoformat(decision["selected_slot"])
    selected_end = datetime.fromisoformat(decision["end_time"])

    # Step 3: Duplicate detection
    timeline.append({"step": "Checking for duplicate meetings", "status": "running"})
    duplicate_window = timedelta(minutes=30)
    duplicate = db.query(ScheduledMeeting).filter(
        ScheduledMeeting.status == "scheduled",
        ScheduledMeeting.recruiter_email == request.recruiter.email,
        ScheduledMeeting.candidate_email == request.candidate.email,
        ScheduledMeeting.start_time >= selected_start - duplicate_window,
        ScheduledMeeting.start_time <= selected_start + duplicate_window,
    ).first()

    if duplicate:
        timeline[-1]["status"] = "warning"
        timeline[-1]["detail"] = "Similar meeting already exists"
        decision["reasoning"].append(
            f"Duplicate detected — meeting {duplicate.meeting_id} already exists at "
            f"{duplicate.start_time.strftime('%A %I:%M %p')}"
        )
        return ScheduleAgentResponse(
            status="duplicate",
            selected_slot=decision["selected_slot"],
            meeting_url=duplicate.join_url,
            meeting_id=duplicate.meeting_id,
            meeting_password=duplicate.password,
            reasoning=decision["reasoning"],
            timeline=timeline,
        )
    timeline[-1]["status"] = "done"
    timeline[-1]["detail"] = "No duplicates found"

    # Step 4: Create Zoom meeting
    timeline.append({"step": "Creating Zoom meeting", "status": "running"})
    topic = f"Interview: {request.recruiter.name} ↔ {request.candidate.name}"
    zoom = ZoomService.create_meeting(topic, selected_start, request.duration_minutes)

    if not zoom:
        timeline[-1]["status"] = "error"
        timeline[-1]["detail"] = "Zoom meeting creation failed"
        decision["reasoning"].append("Zoom meeting creation failed")
        return ScheduleAgentResponse(
            status="error",
            selected_slot=decision["selected_slot"],
            reasoning=decision["reasoning"],
            timeline=timeline,
        )

    timeline[-1]["status"] = "done"
    timeline[-1]["detail"] = f"Meeting {zoom['meeting_id']} created"

    # Step 5: Send emails
    date_str = selected_start.strftime("%B %d, %Y")
    time_str = selected_start.strftime("%I:%M %p")
    role_label = "Scheduled Interview"

    timeline.append({"step": "Sending recruiter email", "status": "running"})
    EmailService.send_recruiter_notification(
        recruiter_email=request.recruiter.email,
        candidate_name=request.candidate.name,
        candidate_email=request.candidate.email,
        role=role_label,
        date_str=date_str,
        time_str=time_str,
        meet_link=zoom["join_url"],
    )
    timeline[-1]["status"] = "done"
    timeline[-1]["detail"] = f"Sent to {request.recruiter.email}"

    timeline.append({"step": "Sending candidate email", "status": "running"})
    EmailService.send_candidate_confirmation(
        candidate_name=request.candidate.name,
        candidate_email=request.candidate.email,
        role=role_label,
        date_str=date_str,
        time_str=time_str,
        meet_link=zoom["join_url"],
    )
    timeline[-1]["status"] = "done"
    timeline[-1]["detail"] = f"Sent to {request.candidate.email}"

    # Step 6: Store the meeting
    timeline.append({"step": "Storing meeting record", "status": "running"})
    meeting = ScheduledMeeting(
        recruiter_name=request.recruiter.name,
        recruiter_email=request.recruiter.email,
        candidate_name=request.candidate.name,
        candidate_email=request.candidate.email,
        meeting_id=zoom["meeting_id"],
        join_url=zoom["join_url"],
        password=zoom.get("password"),
        start_time=selected_start,
        end_time=selected_end,
        duration_minutes=request.duration_minutes,
        buffer_minutes=request.buffer_minutes,
        status="scheduled",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    timeline[-1]["status"] = "done"
    timeline[-1]["detail"] = f"Meeting {meeting.id} stored"

    decision["reasoning"].append("Zoom meeting created")
    decision["reasoning"].append("Emails sent to both participants")
    decision["reasoning"].append("Meeting stored in registry")

    return ScheduleAgentResponse(
        status="scheduled",
        selected_slot=decision["selected_slot"],
        meeting_url=zoom["join_url"],
        meeting_id=zoom["meeting_id"],
        meeting_password=zoom.get("password"),
        emails_sent=True,
        reasoning=decision["reasoning"],
        timeline=timeline,
    )


@router.post("/chat", response_model=ChatResponse)
def schedule_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Conversational ReAct loop using Gemini.
    """
    timeline = []
    
    # 1. Initialize Gemini with function calling tools
    import google.generativeai as genai
    import json
    
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    def trigger_scheduling(candidate_email: str) -> str:
        """Call this to automatically schedule a new meeting between the recruiter and candidate based on their availability."""
        # Use existing pipeline
        try:
            # We just create a standard ScheduleRequest and call our own function
            req = ScheduleRequest(
                recruiter=request.recruiter,
                candidate=request.candidate,
                duration_minutes=request.duration_minutes,
                buffer_minutes=request.buffer_minutes
            )
            res = schedule_meeting(req, db)
            timeline.extend(res.timeline)
            
            if res.status == "scheduled":
                return f"Successfully scheduled meeting {res.meeting_id} at {res.selected_slot}. Join URL: {res.meeting_url}"
            else:
                return f"Scheduling failed. Status: {res.status}. Reasoning: {', '.join(res.reasoning)}"
        except Exception as e:
            return f"Error scheduling: {str(e)}"

    def resend_emails(candidate_email: str) -> str:
        """Call this to resend the meeting invitation emails to both participants."""
        timeline.append({"step": "Checking existing meetings to resend email", "status": "running"})
        meeting = db.query(ScheduledMeeting).filter(
            ScheduledMeeting.candidate_email == request.candidate.email,
            ScheduledMeeting.status == "scheduled"
        ).order_by(ScheduledMeeting.created_at.desc()).first()
        
        if not meeting:
            timeline[-1]["status"] = "error"
            timeline[-1]["detail"] = "No active meeting found"
            return "No active meeting found for this candidate."
            
        timeline[-1]["status"] = "done"
        timeline[-1]["detail"] = "Meeting found"
        
        timeline.append({"step": "Resending emails", "status": "running"})
        date_str = meeting.start_time.strftime("%B %d, %Y") if meeting.start_time else "TBD"
        time_str = meeting.start_time.strftime("%I:%M %p") if meeting.start_time else "TBD"
        
        EmailService.send_candidate_confirmation(
            candidate_name=request.candidate.name,
            candidate_email=request.candidate.email,
            role="Scheduled Interview",
            date_str=date_str,
            time_str=time_str,
            meet_link=meeting.join_url
        )
        
        EmailService.send_recruiter_notification(
            recruiter_email=request.recruiter.email,
            candidate_name=request.candidate.name,
            candidate_email=request.candidate.email,
            role="Scheduled Interview",
            date_str=date_str,
            time_str=time_str,
            meet_link=meeting.join_url
        )
        
        timeline[-1]["status"] = "done"
        timeline[-1]["detail"] = "Emails resent"
        
        return "Emails successfully resent to both the recruiter and the candidate."

    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=[trigger_scheduling, resend_emails],
        system_instruction="You are a helpful AI scheduling assistant for a recruiter. You manage meetings. You can invoke tools to schedule meetings or resend emails. Answer the user naturally based on the tool results. Keep your responses concise."
    )
    
    # Format history for Gemini
    formatted_history = []
    for msg in request.history[:-1]:
        # Gemini expects role to be "user" or "model"
        role = "model" if msg.role in ("agent", "model") else "user"
        formatted_history.append({"role": role, "parts": [msg.content]})
        
    chat = model.start_chat(history=formatted_history)
    
    # Send the latest user message
    user_msg = request.history[-1].content if request.history else "Hello"
    response = chat.send_message(user_msg)
    
    # Process function calls if any
    agent_text = ""
    for part in response.parts:
        if fn := part.function_call:
            if fn.name == "trigger_scheduling":
                result = trigger_scheduling(fn.args.get("candidate_email", request.candidate.email))
                # Send result back to model using standard dict format
                response = chat.send_message({
                    "function_response": {
                        "name": "trigger_scheduling",
                        "response": {"result": result}
                    }
                })
                agent_text = response.text
            elif fn.name == "resend_emails":
                result = resend_emails(fn.args.get("candidate_email", request.candidate.email))
                response = chat.send_message({
                    "function_response": {
                        "name": "resend_emails",
                        "response": {"result": result}
                    }
                })
                agent_text = response.text
        elif part.text:
            agent_text += part.text

    if not agent_text:
        agent_text = response.text

    return ChatResponse(
        response=agent_text,
        timeline=timeline,
        status="success"
    )

@router.get("/meetings")
def list_meetings(
    email: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all meetings. Supports ?email= and ?status= filters."""
    query = db.query(ScheduledMeeting).order_by(ScheduledMeeting.start_time.desc())

    if email:
        query = query.filter(
            (ScheduledMeeting.recruiter_email == email)
            | (ScheduledMeeting.candidate_email == email)
        )
    if status:
        query = query.filter(ScheduledMeeting.status == status)

    meetings = query.all()
    return [_meeting_to_response(m) for m in meetings]


@router.get("/{meeting_id}")
def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """Single meeting lookup."""
    meeting = db.query(ScheduledMeeting).filter(
        ScheduledMeeting.id == meeting_id
    ).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return _meeting_to_response(meeting)


@router.delete("/{meeting_id}", response_model=CancelResponse)
def cancel_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """Cancel a meeting. Sets status to 'cancelled'."""
    meeting = db.query(ScheduledMeeting).filter(
        ScheduledMeeting.id == meeting_id
    ).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.status == "cancelled":
        return CancelResponse(status="already_cancelled", message="Meeting was already cancelled.")

    meeting.status = "cancelled"
    db.commit()

    return CancelResponse(status="cancelled", message=f"Meeting {meeting.meeting_id} has been cancelled.")


@router.post("/{meeting_id}/reschedule", response_model=ScheduleAgentResponse)
def reschedule_meeting(
    meeting_id: str,
    request: RescheduleRequest,
    db: Session = Depends(get_db),
):
    """
    Reschedule an existing meeting:
    1. Cancel the old meeting
    2. Schedule a new one with fresh availability
    3. Send reschedule notification emails
    """
    # Cancel old meeting
    old_meeting = db.query(ScheduledMeeting).filter(
        ScheduledMeeting.id == meeting_id
    ).first()
    if not old_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    old_meeting.status = "cancelled"
    db.commit()

    # Schedule new meeting using the same pipeline
    schedule_request = ScheduleRequest(
        recruiter=request.recruiter,
        candidate=request.candidate,
        duration_minutes=request.duration_minutes,
        buffer_minutes=request.buffer_minutes,
    )
    result = schedule_meeting(schedule_request, db)

    # Add reschedule context to reasoning
    if hasattr(result, "reasoning"):
        result.reasoning.insert(
            0, f"Rescheduling — previous meeting {old_meeting.meeting_id} cancelled"
        )

    return result
