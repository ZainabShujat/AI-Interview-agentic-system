"""
Backward-compatibility shim.
All core agent logic now lives inside individual files in the services/agents/ package.
This module re-exports all agent functions and configurations to ensure that the
entire existing backend codebase, routers, and test cases function without modification.

For new code, prefer importing directly from services.agents:
    from services.agents.resume_agent import parse_resume
"""

import os
from services.agents.gemini_core import (
    GeminiConfig, call_gemini_json, get_default_config,
    _get_api_key, _get_model
)
from services.agents.resume_agent import (
    parse_resume, normalize_resume_parsed, get_mock_resume_parsed
)
from services.agents.jd_agent import (
    parse_jd, get_mock_jd_parsed
)
from services.agents.match_agent import (
    match_resume_and_jd, deterministic_match_resume_and_jd,
    generate_assessment_blueprint, get_mock_match_analysis
)
from services.agents.planner_agent import (
    plan_interview_roadmap
)
from services.agents.interview_agent import (
    generate_question, get_mock_question
)
from services.agents.judge_agent import (
    judge_answer, get_mock_evaluation
)
from services.agents.memory_agent import (
    update_memory
)
from services.agents.report_agent import (
    generate_final_report, compile_communication_profile, get_mock_report_final
)
from services.agents.roadmap_agent import (
    generate_career_roadmap, get_mock_career_roadmap
)

# Export legacy constants mapped to current config state
GEMINI_API_KEY = _get_api_key()
GEMINI_MODEL = _get_model()
