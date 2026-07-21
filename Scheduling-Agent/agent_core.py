import json
import uuid
from datetime import datetime, timedelta


meetings_registry: list[dict] = []


def parse_iso_datetime(value: str):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def format_mock_zoom_url(meeting_id: str) -> str:
    return f"https://zoom.example.com/j/{meeting_id}"


def generate_mock_email(display_name: str) -> str:
    slug = "".join(character.lower() for character in display_name if character.isalnum())
    slug = slug or "interviewer"
    return f"{slug}@company.com"


def format_mock_email(recipient_name: str, recipient_email: str, meeting: dict, role: str) -> dict:
    return {
        "to": {"name": recipient_name, "email": recipient_email},
        "subject": f"Interview scheduled for {meeting['selected_slot']}",
        "body": (
            f"Hi {recipient_name},\n\n"
            f"Your interview has been scheduled for {meeting['selected_slot']} (UTC).\n"
            f"Join link: {meeting['meeting_url']}\n"
            f"Meeting ID: {meeting['meeting_id']}\n"
            f"Password: {meeting['meeting_password']}\n\n"
            f"Job title: {meeting.get('job_title', 'Interview role')}\n"
            f"Interviewer: {meeting.get('interviewer_name', 'Recruiter')}\n"
            f"Resume: {meeting.get('resume_name', 'not provided')}\n\n"
            f"Role: {role}\n"
            f"Status: {meeting['status']}\n"
        ),
    }


def choose_slot(recruiter_availability: list[str], candidate_availability: list[str], duration_minutes: int) -> tuple[str | None, list[str]]:
    reasoning = []

    recruiter_times = []
    candidate_times = []
    for value in recruiter_availability:
        parsed = parse_iso_datetime(value)
        if parsed:
            recruiter_times.append(parsed)
    for value in candidate_availability:
        parsed = parse_iso_datetime(value)
        if parsed:
            candidate_times.append(parsed)

    reasoning.append(f"Recruiter provided {len(recruiter_times)} availability slots")
    reasoning.append(f"Candidate provided {len(candidate_times)} availability slots")

    overlapping = sorted(set(recruiter_times).intersection(candidate_times))
    reasoning.append(f"{len(overlapping)} overlapping slots found")

    if not overlapping:
        return None, reasoning + ["No overlap between recruiter and candidate availability"]

    selected = overlapping[0]
    reasoning.append(f"Selected earliest conflict-free slot: {selected.isoformat()}")
    reasoning.append(f"Meeting duration: {duration_minutes} minutes")
    return selected.isoformat(), reasoning


def build_timeline(meeting: dict) -> list[dict]:
    return [
        {"step": "Loading meeting request", "status": "done", "detail": "Request received"},
        {"step": "Finding matching slot", "status": "done", "detail": meeting["selected_slot"]},
        {"step": "Creating mock Zoom meeting", "status": "done", "detail": meeting["meeting_url"]},
        {"step": "Sending recruiter email", "status": "done", "detail": meeting["recruiter_email"]},
        {"step": "Sending candidate email", "status": "done", "detail": meeting["candidate_email"]},
        {"step": "Storing meeting", "status": "done", "detail": meeting["meeting_id"]},
    ]


def create_mock_meeting(recruiter: dict, candidate: dict, selected_slot: str, duration_minutes: int, buffer_minutes: int, reasoning: list[str]) -> dict:
    meeting_id = uuid.uuid4().hex[:10]
    meeting_password = uuid.uuid4().hex[:6]
    meeting_url = format_mock_zoom_url(meeting_id)
    end_time = None
    parsed_start = parse_iso_datetime(selected_slot)
    if parsed_start:
        end_time = (parsed_start + timedelta(minutes=duration_minutes)).isoformat()

    meeting = {
        "meeting_id": meeting_id,
        "meeting_url": meeting_url,
        "meeting_password": meeting_password,
        "status": "scheduled",
        "selected_slot": selected_slot,
        "end_time": end_time,
        "duration_minutes": duration_minutes,
        "buffer_minutes": buffer_minutes,
        "recruiter_name": recruiter.get("name", "Recruiter"),
        "recruiter_email": recruiter.get("email", ""),
        "candidate_name": candidate.get("name", "Candidate"),
        "candidate_email": candidate.get("email", ""),
        "job_title": recruiter.get("job_title", "Interview role"),
        "interviewer_name": recruiter.get("interviewer_name", recruiter.get("name", "Recruiter")),
        "resume_name": candidate.get("resume_name", "not provided"),
        "reasoning": reasoning + ["Mock Zoom meeting created", "Mock emails prepared for recruiter and candidate"],
    }
    meetings_registry.append(meeting)
    return meeting


def schedule_from_payload(req: dict) -> dict:
    recruiter = req.get("recruiter", {}) or {}
    candidate = req.get("candidate", {}) or {}
    duration_minutes = int(req.get("duration_minutes", 30) or 30)
    buffer_minutes = int(req.get("buffer_minutes", 15) or 15)

    recruiter["job_title"] = req.get("job_title") or recruiter.get("job_title") or "Interview role"
    recruiter["interviewer_name"] = req.get("interviewer_name") or recruiter.get("interviewer_name") or recruiter.get("name", "Recruiter")
    candidate["resume_name"] = req.get("resume_name") or candidate.get("resume_name") or "not provided"
    recruiter["email"] = recruiter.get("email") or generate_mock_email(recruiter["interviewer_name"])

    selected_slot, reasoning = choose_slot(
        recruiter.get("availability", []) or [],
        candidate.get("availability", []) or [],
        duration_minutes,
    )

    if not selected_slot:
        return {
            "status": "no_overlap",
            "selected_slot": None,
            "meeting_url": None,
            "meeting_id": None,
            "meeting_password": None,
            "emails_sent": False,
            "reasoning": reasoning,
            "timeline": build_timeline({
                "selected_slot": "No slot available",
                "meeting_url": "",
                "recruiter_email": recruiter.get("email", ""),
                "candidate_email": candidate.get("email", ""),
                "meeting_id": "",
            }),
            "emails": [],
            "job_title": recruiter["job_title"],
            "interviewer_name": recruiter["interviewer_name"],
            "resume_name": candidate["resume_name"],
        }

    meeting = create_mock_meeting(recruiter, candidate, selected_slot, duration_minutes, buffer_minutes, reasoning)
    recruiter_email = format_mock_email(recruiter.get("name", "Recruiter"), recruiter.get("email", ""), meeting, "recruiter")
    candidate_email = format_mock_email(candidate.get("name", "Candidate"), candidate.get("email", ""), meeting, "candidate")

    return {
        "status": "scheduled",
        "selected_slot": meeting["selected_slot"],
        "meeting_url": meeting["meeting_url"],
        "meeting_id": meeting["meeting_id"],
        "meeting_password": meeting["meeting_password"],
        "emails_sent": True,
        "reasoning": meeting["reasoning"],
        "timeline": build_timeline(meeting),
        "emails": [recruiter_email, candidate_email],
        "job_title": meeting["job_title"],
        "interviewer_name": meeting["interviewer_name"],
        "resume_name": meeting["resume_name"],
    }


def meetings_as_json() -> str:
    return json.dumps(meetings_registry)