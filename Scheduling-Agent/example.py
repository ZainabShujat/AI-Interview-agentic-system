"""
Quick-start example for the Scheduling Agent.

Calls the live HireIntel backend to schedule a real interview.
Zoom meetings are created. Emails are sent.

Usage:
    pip install requests
    python example.py
"""

import requests
import json

# Point this at your running HireIntel backend
API_BASE = "https://hireintel-bv0v.onrender.com"


def main():
    print("=" * 60)
    print("  Scheduling Agent · Quick Start Example")
    print("  An AB Talks Open Agent")
    print("=" * 60)
    print()

    # 1. Schedule a meeting
    print("▶ Scheduling an interview...")
    print()

    payload = {
        "recruiter": {
            "name": "Sarah Chen",
            "email": "sarah@company.com",
            "availability": [
                "2025-07-15T10:00:00Z",
                "2025-07-15T11:00:00Z",
                "2025-07-15T14:00:00Z",
            ],
            "preferences": "Prefers afternoon slots if possible. Avoid Mondays."
        },
        "candidate": {
            "name": "Alex Johnson",
            "email": "alex@email.com",
            "availability": [
                "2025-07-15T09:00:00Z",
                "2025-07-15T10:00:00Z",
                "2025-07-15T15:00:00Z",
            ],
            "preferences": "I am a morning person, so earlier is better."
        },
        "duration_minutes": 30,
        "buffer_minutes": 15,
    }

    response = requests.post(f"{API_BASE}/api/schedule", json=payload)
    result = response.json()

    print(f"  Status: {result.get('status')}")
    print(f"  Selected Slot: {result.get('selected_slot')}")
    print(f"  Meeting URL: {result.get('meeting_url')}")
    print(f"  Emails Sent: {result.get('emails_sent')}")
    print()

    # 2. Show the Agent Decision Log
    print("▶ Agent Decision Log:")
    for reason in result.get("reasoning", []):
        print(f"  ✓ {reason}")
    print()

    # 3. Show the Execution Timeline
    print("▶ Execution Timeline:")
    for step in result.get("timeline", []):
        icon = "✓" if step["status"] == "done" else "✗" if step["status"] == "error" else "⚠"
        print(f"  {icon} {step['step']}  →  {step.get('detail', '')}")
    print()

    # 4. List all meetings
    print("▶ All Meetings:")
    meetings_res = requests.get(f"{API_BASE}/api/schedule/meetings")
    meetings = meetings_res.json()
    for m in meetings:
        status_icon = "🟢" if m["status"] == "scheduled" else "🔴" if m["status"] == "cancelled" else "🟡"
        print(f"  {status_icon} {m['recruiter_name']} ↔ {m['candidate_name']}  |  {m['start_time']}")
    print()

    print("=" * 60)
    print("  Done. Check your inbox for the meeting invitations.")
    print("=" * 60)


if __name__ == "__main__":
    main()
