import os
import json
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
import google.generativeai as genai
from scheduling_agent import SchedulingAgent
from urllib.parse import urlparse, parse_qs
from agent_core import build_timeline, create_mock_meeting, generate_mock_email, meetings_registry, parse_iso_datetime, schedule_from_payload

# Try to load from backend .env if not in environment
if not os.getenv("GEMINI_API_KEY"):
    env_paths = [
        ".env", 
        "../.env", 
        "../backend/.env"
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        os.environ["GEMINI_API_KEY"] = line.split("=", 1)[1].strip()
                        break

# Ensure API key is set
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY not set. Please run: set GEMINI_API_KEY=your_key")
else:
    genai.configure(api_key=api_key)


# In-memory chat sessions
sessions = {}

# Store booking results globally for the demo so we can easily fetch them
booking_results = {}

def book_interview(name: str, email: str, availability_slots: list[str], preferences: str = "") -> dict:
    """
    Book the interview once all details are collected from the candidate.
    
    Args:
        name: Full name of candidate
        email: Email address of candidate
        availability_slots: List of ISO 8601 datetimes the candidate is available. Examples: ['2026-07-16T10:00:00Z']
        preferences: Any scheduling preferences the candidate mentioned
    """
    print(f"Executing book_interview tool for {name} ({email})")
    agent = SchedulingAgent(api_key=api_key)
    
    result = agent.schedule(
        recruiter_slots=RECRUITER_SLOTS,
        candidate_slots=availability_slots,
        existing_meetings=[], 
        duration_minutes=30,
        buffer_minutes=15,
        recruiter_preferences=RECRUITER_PREFS,
        candidate_preferences=preferences
    )
    
    # Store the result so the frontend can retrieve it and show the fancy card
    booking_results[email] = result
    
    return {
        "status": result.get("status", "unknown"),
        "selected_slot": result.get("selected_slot", "none"),
        "reasoning": result.get("reasoning", [])
    }

class ChatHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/' or parsed.path == '/chat.html':
            self.path = '/chat.html'
            return super().do_GET()

        if parsed.path == '/api/schedule/meetings':
            query = parse_qs(parsed.query)
            email_filter = query.get('email', [None])[0]
            status_filter = query.get('status', [None])[0]
            meetings = meetings_registry
            if email_filter:
                meetings = [m for m in meetings if m.get('recruiter_email') == email_filter or m.get('candidate_email') == email_filter]
            if status_filter:
                meetings = [m for m in meetings if m.get('status') == status_filter]

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(meetings).encode('utf-8'))
            return

        if parsed.path.startswith('/api/schedule/'):
            meeting_id = parsed.path.rsplit('/', 1)[-1]
            meeting = next((m for m in meetings_registry if m.get('meeting_id') == meeting_id), None)
            if meeting:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(meeting).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Meeting not found"}).encode('utf-8'))
            return

        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/schedule':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode('utf-8'))

            try:
                result = schedule_from_payload(req)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

        elif self.path in ('/api/chat', '/api/schedule/chat'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode('utf-8'))

            if self.path == '/api/schedule/chat':
                try:
                    result = schedule_from_payload(req)
                    conversation_reply = (
                        f"Your interview is scheduled for {result['selected_slot']}. "
                        f"I created a mock Zoom link and sent mock emails to both participants."
                        if result.get('status') == 'scheduled'
                        else "I could not find an overlapping time slot for both participants."
                    )

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "response": conversation_reply,
                        "status": result.get('status'),
                        "timeline": result.get('timeline', []),
                        "selected_slot": result.get('selected_slot'),
                        "meeting_url": result.get('meeting_url'),
                        "meeting_id": result.get('meeting_id'),
                        "meeting_password": result.get('meeting_password'),
                        "emails_sent": result.get('emails_sent', False),
                        "emails": result.get('emails', []),
                        "job_title": result.get('job_title'),
                        "interviewer_name": result.get('interviewer_name'),
                        "resume_name": result.get('resume_name'),
                    }).encode('utf-8'))
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

            elif self.path == '/api/chat':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"reply": "Use /api/schedule/chat for scheduling."}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=ChatHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print("="*50)
    print(f"🚀 Chat Server running on http://localhost:{port}")
    print("="*50)
    httpd.serve_forever()

if __name__ == "__main__":
    run()
