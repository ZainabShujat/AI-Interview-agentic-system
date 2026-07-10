from sqlalchemy.orm import Session
from models import Interview

class DecisionEngine:
    @staticmethod
    def evaluate_candidate(db: Session, interview_id: str):
        """
        Determines qualification based on configurable thresholds.
        Returns: 'Qualified', 'Recruiter Review', or 'Reject'.
        """
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview or not interview.report:
            return "Reject"

        report_json = interview.report.report_json
        
        # Configurable threshold logic
        score = report_json.get("overall_score", 0)
        
        if score == 0 and "metrics" in report_json:
            metrics = report_json["metrics"]
            if isinstance(metrics, dict):
                total = sum(metrics.values())
                count = len(metrics)
                score = total / count if count > 0 else 0
            
        # Dynamic threshold logic
        passing_score = interview.jd.passing_score if interview.jd and interview.jd.passing_score else 80
        review_band = passing_score - 15
        
        if score >= passing_score:
            return "Qualified"
        elif score >= review_band:
            return "Recruiter Review"
        else:
            return "Reject"
