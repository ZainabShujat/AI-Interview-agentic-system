"""
HireIntel — Gemini Core
========================
Shared foundation for all HireIntel agents.

Provides:
- GeminiConfig: Injectable configuration for API key, model, and fallbacks.
- call_gemini_json(): LLM caller with model cascade and timeout.
- Hardcoded skill databases for local heuristic fallbacks.
- URL extraction, link verification, and text utility functions.

Standalone usage:
    from agents.gemini_core import GeminiConfig, call_gemini_json

    config = GeminiConfig(api_key="your-key")
    result = call_gemini_json("Return JSON: {\"hello\": \"world\"}", config)
"""

import os
import json
import re
import urllib.request
import urllib.error
import logging
import datetime
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class GeminiConfig:
    """Injectable configuration for Gemini API access.
    
    Pass an instance to any agent function to control which API key and model
    are used. When no config is passed, agents fall back to local heuristics.
    
    Example:
        config = GeminiConfig(api_key="AIza...")
        result = parse_resume(raw_text, config=config)
    """
    api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    fallbacks: List[str] = field(default_factory=lambda: [
        "gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"
    ])
    timeout: int = 30


def _build_default_config() -> GeminiConfig:
    """Build a default GeminiConfig from environment variables.
    
    This is used by the backward-compatibility shim so the existing backend
    continues working without passing config explicitly.
    """
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    fallbacks_raw = os.getenv(
        "GEMINI_MODEL_FALLBACKS",
        "gemini-2.5-flash,gemini-flash-latest,gemini-2.0-flash"
    )
    fallbacks = [m.strip() for m in fallbacks_raw.split(",") if m.strip()]

    return GeminiConfig(api_key=api_key, model=model, fallbacks=fallbacks)


# Module-level default config (loaded from env vars at import time).
# Used by the backward-compat shim and agents when no config is passed.
_default_config: Optional[GeminiConfig] = None


def get_default_config() -> GeminiConfig:
    """Lazily initialize and return the default config from env vars."""
    global _default_config
    if _default_config is None:
        _default_config = _build_default_config()
    return _default_config


# Expose legacy constants for backward compatibility
@property
def _api_key():
    return get_default_config().api_key

GEMINI_API_KEY = property(lambda self: get_default_config().api_key)

# Simple module-level accessors (used by the shim)
def _get_api_key():
    return get_default_config().api_key

def _get_model():
    return get_default_config().model


# ---------------------------------------------------------------------------
# LLM Client
# ---------------------------------------------------------------------------

def call_gemini_json(prompt: str, config: Optional[GeminiConfig] = None) -> dict:
    """Query Gemini and request a JSON response, with automatic model cascade.
    
    Args:
        prompt: The prompt text to send.
        config: Optional GeminiConfig. If None, uses env-var defaults.
        
    Returns:
        Parsed JSON dict from the model response.
        
    Raises:
        ValueError: If no API key is available.
        RuntimeError: If all model candidates fail.
    """
    if config is None:
        config = get_default_config()

    if not config.api_key:
        raise ValueError("Gemini API Key missing. Pass a GeminiConfig with api_key set.")

    import google.generativeai as genai
    genai.configure(api_key=config.api_key)

    # Inject temporal context to prevent date confusion
    now = datetime.datetime.now()
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    current_year = now.year
    context_prefix = (
        f"[SYSTEM NOTE: The current real-world date and time is {current_time_str}. "
        f"Do NOT treat dates from {current_year - 1}, {current_year}, or earlier as 'future' plans; "
        f"the current year is {current_year}. Any references to dates on or before {current_year} represent past or active current activities.]\n\n"
    )
    prompt = context_prefix + prompt

    # Build unique model candidate list
    model_candidates = []
    for model_name in [config.model, *config.fallbacks]:
        if model_name and model_name not in model_candidates:
            model_candidates.append(model_name)

    last_error = None
    for model_name in model_candidates:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"},
                request_options={"timeout": config.timeout}
            )
            return json.loads(response.text)
        except Exception as e:
            last_error = e
            logger.warning(f"Gemini API call failed with model {model_name}: {e}.")

    raise RuntimeError(
        f"Gemini API call failed for all configured models: {model_candidates}. "
        f"Last error: {last_error}"
    )


# ---------------------------------------------------------------------------
# URL Extraction & Link Verification
# ---------------------------------------------------------------------------

def extract_urls(text: str) -> list:
    """Extract up to 8 unique URLs from text."""
    urls = re.findall(r"https?://[^\s<>)\]]+", text or "")
    cleaned = []
    for url in urls:
        url = url.rstrip(".,;:'\"")
        if url not in cleaned:
            cleaned.append(url)
    return cleaned[:8]


def fetch_public_link_evidence(urls: list) -> list:
    """Fetch and summarize content from public URLs for verification."""
    evidence = []
    for url in urls[:5]:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "HireIntelResumeVerifier/1.0",
                    "Accept": "text/html,text/plain,application/json;q=0.9,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                content_type = response.headers.get("content-type", "")
                raw = response.read(120000).decode("utf-8", errors="ignore")

            text = raw
            if "html" in content_type:
                text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
                text = re.sub(r"(?s)<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            evidence.append({
                "url": url,
                "status": "fetched",
                "content_type": content_type,
                "text_excerpt": text[:5000]
            })
        except Exception as e:
            evidence.append({
                "url": url,
                "status": "unavailable",
                "error": str(e)[:240]
            })
    return evidence


# ---------------------------------------------------------------------------
# Contact Extractors
# ---------------------------------------------------------------------------

def extract_email(text: str) -> Optional[str]:
    """Extract the first email address from text."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract the first phone number from text."""
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else None


# ---------------------------------------------------------------------------
# Hardcoded Skill Databases
# ---------------------------------------------------------------------------

PROGRAMMING_LANGUAGES = {
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "perl", "bash", "shell",
    "sql", "html", "css", "groovy", "elixir", "erlang", "clojure"
}

FRAMEWORKS = {
    "react", "angular", "vue", "svelte", "next.js", "nextjs", "gatsby", "nuxt",
    "express", "fastapi", "django", "flask", "spring", "spring boot", "asp.net",
    "rails", "laravel", "symfony", "graphql", "rest", "grpc"
}

DATABASES = {
    "postgres", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "firestore", "oracle", "mssql", "sqlite",
    "cockroachdb", "neo4j", "influxdb", "clickhouse", "bigquery"
}

CLOUD_PLATFORMS = {
    "aws", "amazon web services", "azure", "gcp", "google cloud", "heroku",
    "vercel", "netlify", "digitalocean", "linode", "cloudfoundry", "ibm cloud"
}

TOOLS_AND_PLATFORMS = {
    "docker", "kubernetes", "k8s", "jenkins", "gitlab", "github", "git", "circleci",
    "terraform", "ansible", "chef", "puppet", "grafana", "prometheus", "datadog",
    "slack", "jira", "confluence", "notion", "figma", "postman", "vscode", "vim",
    "emacs", "intellij", "pycharm", "vs code", "xcode", "android studio"
}

SOFT_SKILLS = {
    "leadership", "communication", "teamwork", "collaboration", "problem-solving",
    "critical thinking", "time management", "adaptability", "creativity", "mentoring",
    "negotiation", "presentation", "strategic thinking", "agile", "scrum"
}


# ---------------------------------------------------------------------------
# Skill Utility Functions
# ---------------------------------------------------------------------------

def categorize_skills(skills_text: str) -> dict:
    """Categorize skills from raw text using the hardcoded database (no LLM)."""
    all_skills = []
    skill_matches = re.findall(
        r'(?:^|\b|,\s*)([A-Z][A-Za-z0-9+\-.*#\s()]{1,30}?)(?:,|\s*$|\n)',
        skills_text
    )
    all_skills.extend([s.strip() for s in skill_matches if s.strip()])

    for delimiter in [',', '•', '|', '·', '-']:
        if delimiter in skills_text:
            parts = skills_text.split(delimiter)
            all_skills.extend([s.strip() for s in parts if 2 < len(s.strip()) < 50])

    categorized = {
        'programming_languages': [],
        'frameworks': [],
        'databases': [],
        'cloud_platforms': [],
        'tools': [],
        'soft_skills': []
    }

    seen = set()
    for skill in all_skills:
        skill_lower = skill.lower().strip()
        if skill_lower in seen or len(skill_lower) < 2:
            continue
        seen.add(skill_lower)

        if skill_lower in PROGRAMMING_LANGUAGES:
            categorized['programming_languages'].append(skill)
        elif any(fw.lower() in skill_lower or skill_lower in fw.lower() for fw in FRAMEWORKS):
            categorized['frameworks'].append(skill)
        elif any(db.lower() in skill_lower or skill_lower in db.lower() for db in DATABASES):
            categorized['databases'].append(skill)
        elif any(cp.lower() in skill_lower or skill_lower in cp.lower() for cp in CLOUD_PLATFORMS):
            categorized['cloud_platforms'].append(skill)
        elif any(tool.lower() in skill_lower or skill_lower in tool.lower() for tool in TOOLS_AND_PLATFORMS):
            categorized['tools'].append(skill)
        elif skill_lower in SOFT_SKILLS:
            categorized['soft_skills'].append(skill)
        else:
            categorized['tools'].append(skill)

    return categorized


def normalize_skill(skill: str) -> str:
    """Normalize a skill name for comparison (lowercase, strip separators)."""
    return " ".join(str(skill).lower().replace("-", " ").replace("_", " ").split())


def display_skill(skill: str) -> str:
    """Format a skill name for display."""
    cleaned = " ".join(str(skill).replace("_", " ").split())
    return cleaned.upper() if cleaned.lower() in {"aws", "sql", "ci/cd"} else cleaned
