from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class JDRequest(BaseModel):
    text: str
    passing_score: Optional[int] = 60
    available_slots: Optional[List[str]] = []

class BlueprintUpdateRequest(BaseModel):
    blueprint: Dict[str, Any]

class MatchRequest(BaseModel):
    resume_id: str
    jd_id: str

class InterviewStartRequest(BaseModel):
    resume_id: str
    jd_id: str

class ConfidenceSignals(BaseModel):
    responseTime: int
    latencySeconds: float
    wordCount: int
    wordsPerMinute: int
    fillerCount: int
    speakingRate: Optional[float] = None
    energy: Optional[float] = None
    intensity: Optional[float] = None
    pitchVariance: Optional[float] = None
    jitter: Optional[float] = None
    shimmer: Optional[float] = None

class AnswerSubmitRequest(BaseModel):
    interview_id: str
    question_text: str
    category: str
    answer_text: str
    signals: ConfidenceSignals

class QuestionResponse(BaseModel):
    question: str
    category: str
    finished: bool

class ProjectSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    github: Optional[str] = None
    demo: Optional[str] = None
    contributions: List[str] = Field(default_factory=list)

class ExperienceSchema(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    employment_type: Optional[str] = None
    duration: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)

class EducationSchema(BaseModel):
    degree: Optional[str] = None
    branch: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None
    cgpa: Optional[str] = None

class InternshipSchema(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    duration: Optional[str] = None
    summary: Optional[str] = None

class LinkSchema(BaseModel):
    url: Optional[str] = None
    type: Optional[str] = None
    verified: Optional[bool] = True
    summary: Optional[str] = None
    skills_found: List[str] = Field(default_factory=list)
    projects_found: List[str] = Field(default_factory=list)

class ResumeAnalysisSchema(BaseModel):
    candidate_name: Optional[str] = None
    headline: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    website: Optional[str] = None

    summary: Optional[str] = None

    career_level: Optional[str] = None
    estimated_experience_years: Optional[float] = 0.0
    primary_domain: Optional[str] = None

    skills: List[str] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    cloud_platforms: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)

    projects: List[ProjectSchema] = Field(default_factory=list)
    experience: List[ExperienceSchema] = Field(default_factory=list)
    education: List[EducationSchema] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    internships: List[InternshipSchema] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    domain_experience: List[str] = Field(default_factory=list)
    top_strengths: List[str] = Field(default_factory=list)
    potential_concerns: List[str] = Field(default_factory=list)
    links: List[LinkSchema] = Field(default_factory=list)

class ResumeTelemetry(BaseModel):
    cached: bool
    model: str
    cost: float
    mode: str
    fallback: bool

class ResumeResponse(BaseModel):
    id: str
    filename: str
    parsed: Optional[ResumeAnalysisSchema] = None
    raw_resume_text: Optional[str] = None
    telemetry: Optional[ResumeTelemetry] = None

class RoadmapRequest(BaseModel):
    resume: Dict[str, Any]
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    target_jd: Optional[Dict[str, Any]] = None

class SlotSubmitRequest(BaseModel):
    interview_id: str
    role: str # 'candidate' or 'recruiter'
    slots: List[Dict[str, str]] # [{'start_time': 'iso_string', 'end_time': 'iso_string'}]

class SchedulingResponse(BaseModel):
    success: bool
    message: str
    meeting_id: Optional[str] = None
    join_url: Optional[str] = None
    start_time: Optional[str] = None

# --- Scheduling Agent Schemas ---

class PersonInfo(BaseModel):
    name: str
    email: str
    availability: List[str]  # ISO 8601 datetime strings
    preferences: Optional[str] = None  # e.g., "Prefers mornings", "Avoid Friday afternoons"

class ScheduleRequest(BaseModel):
    recruiter: PersonInfo
    candidate: PersonInfo
    duration_minutes: Optional[int] = 30
    buffer_minutes: Optional[int] = 15

class ScheduleAgentResponse(BaseModel):
    status: str  # "scheduled" | "no_overlap" | "all_conflicts" | "duplicate" | "error"
    selected_slot: Optional[str] = None
    meeting_url: Optional[str] = None
    meeting_id: Optional[str] = None
    meeting_password: Optional[str] = None
    emails_sent: bool = False
    reasoning: List[str] = []
    timeline: List[Dict[str, str]] = []

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    history: List[ChatMessage]
    recruiter: PersonInfo
    candidate: PersonInfo
    duration_minutes: int = 30
    buffer_minutes: int = 15

class ChatResponse(BaseModel):
    response: str
    timeline: List[dict] = []
    status: Optional[str] = None

class CancelResponse(BaseModel):
    status: str
    message: str

class RescheduleRequest(BaseModel):
    recruiter: PersonInfo
    candidate: PersonInfo
    duration_minutes: Optional[int] = 30
    buffer_minutes: Optional[int] = 15
