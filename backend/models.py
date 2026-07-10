import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=True)
    raw_text = Column(Text, nullable=False)
    parsed_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interviews = relationship("Interview", back_populates="resume")

class JobDescription(Base):
    __tablename__ = "jds"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=True)
    recruiter_id = Column(String(100), nullable=True) # Tracks which recruiter created this role
    department = Column(String(100), nullable=True) # For recruiter department filters
    passing_score = Column(Integer, default=60) # Recruiter-defined passing threshold
    available_slots = Column(JSON, default=list) # Recruiter available slots for interviews
    raw_text = Column(Text, nullable=False)
    parsed_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interviews = relationship("Interview", back_populates="jd")

class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=True)
    candidate_name = Column(String(255), nullable=True) # Candidate display name for recruiter lists
    candidate_email = Column(String(255), nullable=True) # For candidate tracking & invitation notifications
    invitation_token = Column(String(100), nullable=True) # Token validation for invited candidate sessions
    recruiter_id = Column(String(100), nullable=True) # Linking evaluations to specific recruiter ownership
    hiring_decision = Column(String(50), default="Pending") # Pipeline tracking: Pending, Shortlisted, Rejected, Offered
    resume_id = Column(String(36), ForeignKey("resumes.id"), nullable=False)
    jd_id = Column(String(36), ForeignKey("jds.id"), nullable=False)
    status = Column(String(20), default="active") # active, completed
    workflow_state = Column(String(50), default="PENDING") # PENDING, MATCHED, INTERVIEWING, JUDGED, QUALIFIED, SCHEDULING, SCHEDULED, COMPLETED
    current_question_index = Column(Integer, default=0)
    difficulty_level = Column(String(20), default="Medium") # Easy, Medium, Hard
    category_roadmap = Column(JSON, nullable=True) # Question distribution
    memory_json = Column(JSON, nullable=True) # strong areas, weak areas, asked questions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    resume = relationship("Resume", back_populates="interviews")
    jd = relationship("JobDescription", back_populates="interviews")
    answers = relationship("Answer", back_populates="interview", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    slots = relationship("InterviewSlot", back_populates="interview", cascade="all, delete-orphan")
    meeting = relationship("Meeting", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="interview", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False)
    category = Column(String(50), nullable=False) # Technical, Scenario, Behavioral, Leadership
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    evaluation_json = Column(JSON, nullable=True) # accuracy, communication, depth, confidence
    confidence_metrics = Column(JSON, nullable=True) # wpm, fillerCount, latencySeconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interview = relationship("Interview", back_populates="answers")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False)
    report_json = Column(JSON, nullable=False) # Recharts structure + summary
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interview = relationship("Interview", back_populates="report")

class ResumeCache(Base):
    __tablename__ = "resume_caches"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    raw_text_hash = Column(String(64), unique=True, index=True, nullable=False)
    parsed_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class InterviewSlot(Base):
    __tablename__ = "interview_slots"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False)
    role = Column(String(20), nullable=False) # 'candidate' or 'recruiter'
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interview = relationship("Interview", back_populates="slots")

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False, unique=True)
    meeting_id = Column(String(100), nullable=False)
    join_url = Column(Text, nullable=False)
    password = Column(String(100), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interview = relationship("Interview", back_populates="meeting")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interview = relationship("Interview", back_populates="audit_logs")

class ScheduledMeeting(Base):
    """
    Standalone meeting registry for the Scheduling Agent.
    Independent from the interview-pipeline Meeting model.
    Used for conflict detection, duplicate prevention, and meeting lifecycle.
    """
    __tablename__ = "scheduled_meetings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recruiter_name = Column(String(255), nullable=False)
    recruiter_email = Column(String(255), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False)
    meeting_id = Column(String(100), nullable=False)
    join_url = Column(Text, nullable=False)
    password = Column(String(100), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30)
    buffer_minutes = Column(Integer, default=15)
    status = Column(String(20), default="scheduled")  # scheduled | cancelled | completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

