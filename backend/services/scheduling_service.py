from sqlalchemy.orm import Session
from models import InterviewSlot
from datetime import timedelta

class SchedulingService:
    @staticmethod
    def find_earliest_overlap(db: Session, interview_id: str, duration_minutes: int = 30):
        """
        Finds the earliest overlapping time slot between recruiter and candidate slots.
        Uses deterministic Python logic (no LLM).
        """
        recruiter_slots = db.query(InterviewSlot).filter(
            InterviewSlot.interview_id == interview_id,
            InterviewSlot.role == "recruiter"
        ).order_by(InterviewSlot.start_time).all()
        
        candidate_slots = db.query(InterviewSlot).filter(
            InterviewSlot.interview_id == interview_id,
            InterviewSlot.role == "candidate"
        ).order_by(InterviewSlot.start_time).all()
        
        for c_slot in candidate_slots:
            for r_slot in recruiter_slots:
                # Calculate overlap
                latest_start = max(c_slot.start_time, r_slot.start_time)
                earliest_end = min(c_slot.end_time, r_slot.end_time)
                
                # Check if overlap is sufficient for the duration
                if (earliest_end - latest_start) >= timedelta(minutes=duration_minutes):
                    return latest_start
                    
        return None
