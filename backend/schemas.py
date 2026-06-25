from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class JDRequest(BaseModel):
    text: str

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
