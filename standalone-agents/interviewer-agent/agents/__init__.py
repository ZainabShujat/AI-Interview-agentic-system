"""
HireIntel Independent Agent Package
===================================
A self-contained collection of AI agents and deterministic logic.
This module specifically exports the Interview Agent and core configuration.

Example:
    from agents.interview_agent import generate_question
    from agents.gemini_core import GeminiConfig

    config = GeminiConfig(api_key="your-api-key")
    question = generate_question(resume={}, jd={}, history=[], category="Technical", difficulty="Medium", config=config)
"""

from .gemini_core import GeminiConfig, call_gemini_json, get_default_config
from .interview_agent import generate_question
