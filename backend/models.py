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
    current_question_index = Column(Integer, default=0)
    difficulty_level = Column(String(20), default="Medium") # Easy, Medium, Hard
    category_roadmap = Column(JSON, nullable=True) # Question distribution
    memory_json = Column(JSON, nullable=True) # strong areas, weak areas, asked questions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    resume = relationship("Resume", back_populates="interviews")
    jd = relationship("JobDescription", back_populates="interviews")
    answers = relationship("Answer", back_populates="interview", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="interview", uselist=False, cascade="all, delete-orphan")

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
