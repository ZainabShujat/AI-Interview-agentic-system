from sqlalchemy.orm import Session
from models import Interview, Meeting
from .decision_engine import DecisionEngine
from .scheduling_service import SchedulingService
from .zoom_service import ZoomService
from .email_service import EmailService
from .audit_service import AuditService

class WorkflowOrchestrator:
    @staticmethod
    def process_interview_completion(db: Session, interview_id: str):
        """
        Triggered when an interview is completed.
        Calls Decision Engine to evaluate.
        """
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return
            
        AuditService.log_action(db, interview_id, "Interview Completed")
        interview.workflow_state = "JUDGED"
        db.commit()
        
        decision = DecisionEngine.evaluate_candidate(db, interview_id)
        
        if decision == "Qualified":
            interview.workflow_state = "QUALIFIED"
            AuditService.log_action(db, interview_id, "Qualified", "Candidate passed threshold.")
            # Move to scheduling
            interview.workflow_state = "SCHEDULING"
        elif decision == "Recruiter Review":
            interview.workflow_state = "PENDING_REVIEW"
            AuditService.log_action(db, interview_id, "Recruiter Review", "Candidate needs manual review.")
        else:
            interview.workflow_state = "REJECTED"
            AuditService.log_action(db, interview_id, "Rejected", "Candidate did not meet threshold.")
        
        db.commit()
        
    @staticmethod
    def try_schedule(db: Session, interview_id: str):
        """
        Triggered when slots are submitted.
        Checks if we can schedule the interview.
        """
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview or interview.workflow_state != "SCHEDULING":
            return False, "Interview not ready for scheduling."
            
        overlap_time = SchedulingService.find_earliest_overlap(db, interview_id)
        
        if not overlap_time:
            return False, "No overlapping slots found."
            
        # We have an overlap, coordinate downstream!
        AuditService.log_action(db, interview_id, "Slots Matched", f"Found overlap at {overlap_time}")
        
        # 1. Zoom
        topic = f"Interview with {interview.candidate_name}"
        zoom_details = ZoomService.create_meeting(topic, overlap_time)
        
        if zoom_details:
            meeting = Meeting(
                interview_id=interview_id,
                meeting_id=zoom_details["meeting_id"],
                join_url=zoom_details["join_url"],
                password=zoom_details.get("password"),
                start_time=zoom_details["start_time"]
            )
            db.add(meeting)
            AuditService.log_action(db, interview_id, "Zoom Meeting Created", zoom_details["join_url"])
        else:
            AuditService.log_action(db, interview_id, "Zoom Creation Failed", "Failed to create Zoom meeting.")
            
        # 2. Email
        date_str = overlap_time.strftime("%B %d, %Y")
        time_str = overlap_time.strftime("%I:%M %p")
        
        role_title = "Candidate"
        if interview.jd:
            role_title = "Open Role"
            
        EmailService.send_candidate_confirmation(
            candidate_name=interview.candidate_name or "Candidate",
            candidate_email=interview.candidate_email or "test@example.com",
            role=role_title,
            date_str=date_str,
            time_str=time_str,
            meet_link=zoom_details["join_url"] if zoom_details else "#"
        )
        
        EmailService.send_recruiter_notification(
            recruiter_email=interview.recruiter_id or "recruiter@example.com",
            candidate_name=interview.candidate_name or "Candidate",
            candidate_email=interview.candidate_email or "test@example.com",
            role=role_title,
            date_str=date_str,
            time_str=time_str,
            meet_link=zoom_details["join_url"] if zoom_details else "#"
        )
        
        AuditService.log_action(db, interview_id, "Emails Sent")
        
        # 3. Update Status
        interview.workflow_state = "SCHEDULED"
        db.commit()
        
        return True, "Successfully scheduled."
