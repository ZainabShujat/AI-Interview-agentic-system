from sqlalchemy.orm import Session
from models import AuditLog

class AuditService:
    @staticmethod
    def log_action(db: Session, interview_id: str, action: str, details: str = None):
        """
        Logs an automation step to generate beautiful timelines for recruiters.
        """
        audit = AuditLog(
            interview_id=interview_id,
            action=action,
            details=details
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        return audit
