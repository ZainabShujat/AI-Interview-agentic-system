"""
HireIntel — Career Roadmap Agent
=================================
Generates personalized, actionable learning roadmaps and resume checkpoints
to help candidates bridge their gaps for target roles/companies.

Standalone usage:
    from agents.roadmap_agent import generate_career_roadmap
    from agents.gemini_core import GeminiConfig

    config = GeminiConfig(api_key="your-key")
    roadmap = generate_career_roadmap(resume, target_role="Senior Dev", config=config)
    print(roadmap["current_readiness"])

Works without API key (degrades gracefully to mock career roadmap).
"""

import json
import logging
from typing import Optional

from .gemini_core import GeminiConfig, get_default_config, call_gemini_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mock Fallback Roadmap Generator
# ---------------------------------------------------------------------------

def get_mock_career_roadmap(resume_parsed: dict, target_role: str,
                            target_company: str, target_jd: dict) -> dict:
    """Generate a high-quality mock career roadmap."""
    return {
        "current_readiness": 68,
        "estimated_time": "4 Months",
        "success_probability": "High",
        "missing_skills": ["Docker", "Kubernetes", "CI/CD Platforms", "Apache Kafka"],
        "weekly_milestones": [
            {
                "week": "Weeks 1-2",
                "focus": "Foundations & Docker containerization",
                "tasks": [
                    "Learn containerization basics: Dockerfile, volumes, and networks.",
                    "Containerize the local python interview microservices application.",
                    "Deploy the container locally and practice mapping environment variables."
                ]
            },
            {
                "week": "Weeks 3-4",
                "focus": "Kubernetes orchestration basics",
                "tasks": [
                    "Understand Kubernetes Pods, Deployments, and Services schemas.",
                    "Write basic YAML manifests to run the containerized python application.",
                    "Deploy onto a local minikube cluster and verify logs."
                ]
            },
            {
                "week": "Weeks 5-8",
                "focus": "CI/CD & AWS Deployment pipelines",
                "tasks": [
                    "Set up a GitHub Actions workflow to build and test code on every push.",
                    "Integrate Docker build and push to Amazon ECR.",
                    "Deploy to Amazon ECS (Fargate) using GitHub Actions secrets."
                ]
            },
            {
                "week": "Weeks 9-12",
                "focus": "High-throughput messaging & system design",
                "tasks": [
                    "Familiarize with Apache Kafka topics, producers, and consumer-groups.",
                    "Implement a test producer and consumer inside python to process mock logs.",
                    "Draft a multi-region scalable system design blueprint for high-frequency hiring data."
                ]
            }
        ],
        "projects_to_build": [
            {
                "title": "Scalable Containerized Interview Simulator",
                "spec": "FastAPI + Docker + minikube + GitHub Actions",
                "tasks": [
                    "Write a multi-stage Dockerfile to shrink image size.",
                    "Configure a local minikube cluster to run backend nodes behind a LoadBalancer service.",
                    "Create a GitHub Actions CI pipeline mapping secrets to build clean images."
                ]
            },
            {
                "title": "Event-Driven Log Analytics Queue",
                "spec": "FastAPI + Kafka + Docker Compose",
                "tasks": [
                    "Set up a single-node Kafka broker using Docker Compose.",
                    "Develop a background publisher node sending interview evaluations data.",
                    "Run multiple consumer nodes executing log processing in parallel."
                ]
            }
        ],
        "learning_resources": [
            {
                "name": "Docker and Kubernetes: The Complete Guide",
                "type": "Course / Reference",
                "link": "https://www.udemy.com/"
            },
            {
                "name": "Confluent Kafka Developer Tutorials",
                "type": "Documentation",
                "link": "https://developer.confluent.io/"
            }
        ],
        "resume_checkpoint_upgrades": [
            {
                "milestone": "Month 1",
                "checkpoints": [
                    "Add the 'Containerized Interview Simulator' project description to the projects section.",
                    "List 'Docker' and 'Kubernetes' under technical skills list."
                ]
            },
            {
                "milestone": "Month 2",
                "checkpoints": [
                    "Update the 'Work Experience' or 'Projects' sections to highlight GitHub Actions CI/CD automation pipelines.",
                    "Add 'AWS ECR/ECS' to the tools section."
                ]
            },
            {
                "milestone": "Month 3",
                "checkpoints": [
                    "Highlight event-driven architecture experience with 'Apache Kafka' inside the projects section.",
                    "Re-run readiness analysis on HireIntel to verify name scores."
                ]
            }
        ]
    }


# ---------------------------------------------------------------------------
# Main Agent Entry Point
# ---------------------------------------------------------------------------

def generate_career_roadmap(resume: dict, target_role: Optional[str] = None,
                            target_company: Optional[str] = None,
                            target_jd: Optional[dict] = None,
                            config: Optional[GeminiConfig] = None) -> dict:
    """
    Generate a personalized career readiness roadmap and resume upgrades list.

    Args:
        resume: Parsed resume profile.
        target_role: Name of target job role.
        target_company: Target company name.
        target_jd: Target job description parsed JSON context.
        config: Optional GeminiConfig settings.

    Returns:
        Personalized roadmap details mapping readiness, timeline, milestones, etc.
    """
    if config is None:
        config = get_default_config()

    if not config.api_key:
        return get_mock_career_roadmap(resume, target_role or "", target_company or "", target_jd or {})

    prompt = f"""
    You are a Senior Career Mentor & Coach Agent. Your job is to create a realistic, personalized, and highly actionable learning roadmap and resume upgrade checkpoint list.
    
    Candidate Resume:
    {json.dumps(resume, indent=2)}
    
    Target Role: {target_role or "N/A"}
    Target Company: {target_company or "N/A"}
    Target Job Description (JD):
    {json.dumps(target_jd, indent=2) if target_jd else "N/A"}
    
    Analyze:
    - Current strengths vs Gaps (Skills, Projects, Experience, Certifications).
    - Map readiness percentage score (integer 0 to 100) and Success Probability ("Low", "Medium", "High").
    - Estimate the timeline in months (e.g. "3 Months", "4 Months").
    
    Formulate:
    1. A list of specific "missing_skills".
    2. A week-by-week or phase-by-phase learning "weekly_milestones" plan. Include containerized, specific action tasks (e.g. instead of "Learn React", say "Week 3: Learn React routing -> Implement navigation -> Deploy page").
    3. Specific personalized "projects_to_build" (with title, target technical specs, and subtasks) tailored to bridge their project/experience gaps.
    4. Relevant "learning_resources" links or course topics.
    5. Actionable "resume_checkpoint_upgrades" mapped to monthly milestones (telling the candidate exactly what projects or certifications to add to their resume over time).
    
    Guidelines:
    - Tailor the plan dynamically to what the candidate *already knows* (e.g. if they already know React, do NOT tell them to learn basic React; focus on advanced optimizations or gaps).
    - Return ONLY valid JSON format.
    
    Return JSON matching exactly this schema:
    {{
      "current_readiness": 72,
      "estimated_time": "4 Months",
      "success_probability": "High",
      "missing_skills": ["Docker", "Kubernetes"],
      "weekly_milestones": [
        {{
          "week": "Weeks 1-2",
          "focus": "Topic details",
          "tasks": ["Task 1 description", "Task 2 description"]
        }}
      ],
      "projects_to_build": [
        {{
          "title": "Project Title",
          "spec": "Tech stack details",
          "tasks": ["Subtask 1", "Subtask 2"]
        }}
      ],
      "learning_resources": [
        {{
          "name": "Resource Name",
          "type": "Type description",
          "link": "URL link (if known, or placeholder)"
        }}
      ],
      "resume_checkpoint_upgrades": [
        {{
          "milestone": "Month 1",
          "checkpoints": ["Action 1 details", "Action 2 details"]
        }}
      ]
    }}
    """
    try:
        return call_gemini_json(prompt, config)
    except Exception as e:
        logger.warning(
            f"Career Intelligence Agent Gemini call failed: {e}. "
            f"Falling back to mock career roadmap."
        )
        return get_mock_career_roadmap(resume, target_role or "", target_company or "", target_jd or {})
