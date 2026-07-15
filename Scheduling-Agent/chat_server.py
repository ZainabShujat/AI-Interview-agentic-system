import os
import json
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
import google.generativeai as genai
from scheduling_agent import SchedulingAgent
from datetime import datetime, timedelta, timezone

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

# Mock recruiter data for the demo
RECRUITER_SLOTS = [
    (datetime.now(timezone.utc) + timedelta(days=1, hours=10)).isoformat(),
    (datetime.now(timezone.utc) + timedelta(days=1, hours=14)).isoformat(),
    (datetime.now(timezone.utc) + timedelta(days=2, hours=11)).isoformat(),
]
RECRUITER_PREFS = "Prefers afternoon slots if possible. Avoid Fridays."

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
        if self.path == '/' or self.path == '/chat.html':
            self.path = '/chat.html'
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode('utf-8'))
            
            session_id = req.get('session_id', 'default')
            user_message = req.get('message', '')
            
            if session_id not in sessions:
                system_instruction = (
                    "You are a friendly, conversational AI Interview Scheduler for our company. "
                    "Your goal is to collect: Name, Email, and Preferred Dates/Times for an interview. "
                    "Always be polite and conversational. Do not output markdown, keep it like a text message. "
                    "If they provide partial info, acknowledge it and ask for the rest. "
                    "Once you have Name, Email, and at least one or two Date/Time slots they are available, "
                    "convert their times into ISO 8601 strings and call the book_interview function."
                    "After booking, congratulate them and tell them the final time!"
                )
                
                chat_model = genai.GenerativeModel(
                    "gemini-1.5-flash",
                    system_instruction=system_instruction,
                    tools=[book_interview]
                )
                sessions[session_id] = chat_model.start_chat(enable_automatic_function_calling=True)
                
            chat = sessions[session_id]
            
            try:
                response = chat.send_message(user_message)
                reply_text = response.text
                
                # Check if a booking was made recently in this conversation
                # We can check our global booking_results or just let the LLM's text suffice.
                # To show the rich card, we'll return all recent booking results just in case.
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Find the most recent booking result to send to the UI
                latest_booking = None
                if booking_results:
                    latest_booking = list(booking_results.values())[-1]
                
                res = {
                    "reply": reply_text,
                    "booking_data": latest_booking
                }
                
                # Clear booking_results so we don't send it again
                booking_results.clear()
                
                self.wfile.write(json.dumps(res).encode('utf-8'))
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
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
