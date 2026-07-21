"""
Voice AI Interviewer — Local Server
====================================
Exposes the complete Voice AI Interviewer via FastAPI.
Run:  python voice_server.py
"""

import os
import io
import logging

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import json

from orchestrator_agent import VoiceInterviewOrchestrator
from speech_service import transcribe_audio, analyze_voice_features

logger = logging.getLogger(__name__)

app = FastAPI(title="Voice AI Interviewer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("GEMINI_API_KEY", "")
orchestrator = VoiceInterviewOrchestrator(api_key=API_KEY)

class StartRequest(BaseModel):
    jd_text: str
    resume_text: str

@app.get("/health")
def health():
    return {"status": "ok", "agent": "Voice Interviewer"}

@app.post("/api/start")
async def start_interview(payload: StartRequest):
    """Initializes the agent's internal state and returns the first question."""
    try:
        data = orchestrator.start_interview(payload.jd_text, payload.resume_text)
        return data
    except Exception as e:
        logger.exception("Init failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/speak")
async def process_speech(
    audio_file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """The only endpoint the frontend needs during the interview."""
    try:
        raw_bytes = await audio_file.read()

        # 1. Transcribe audio (Deepgram)
        transcription_data = await transcribe_audio(raw_bytes)
        transcript = transcription_data.get("transcript", "")
        
        # 2. Extract acoustic telemetry
        signals = analyze_voice_features(raw_bytes)
        
        # 3. Agent handles everything internally (judge, memory, next question)
        result = orchestrator.process_turn(
            session_id=session_id,
            transcript=transcript,
            signals=signals
        )
        
        return {
            "transcript": transcript,
            "acoustic_signals": signals,
            "evaluation": result["evaluation"],
            "next_question": result["next_question"]
        }
    except Exception as e:
        logger.exception("Audio processing failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def serve_playground():
    html_path = os.path.join(os.path.dirname(__file__), "playground.html")
    return FileResponse(html_path, media_type="text/html")

if __name__ == "__main__":
    print("\n  Voice AI Interviewer")
    print("  http://localhost:5004\n")
    uvicorn.run(app, host="0.0.0.0", port=5004)
