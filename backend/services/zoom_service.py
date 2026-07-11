import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ZoomService:
    @staticmethod
    def _get_access_token():
        account_id = os.getenv("ZOOM_ACCOUNT_ID")
        client_id = os.getenv("ZOOM_CLIENT_ID")
        client_secret = os.getenv("ZOOM_CLIENT_SECRET")
        
        if not account_id or not client_id or not client_secret:
            return None

        url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}"
        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        
        response = requests.post(url, auth=auth)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Zoom Auth Error ({response.status_code}): {response.text}")
            return None

    @staticmethod
    def create_meeting(topic: str, start_time: datetime, duration: int = 30):
        """
        Creates a Zoom meeting using Server-to-Server OAuth.
        Returns meeting details.
        """
        token = ZoomService._get_access_token()
        if not token:
            print("Zoom credentials not configured. Returning mock meeting.")
            return {
                "meeting_id": "MOCK-12345",
                "join_url": "https://zoom.us/j/mock-meeting",
                "password": "mockpassword",
                "start_time": start_time
            }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "topic": topic,
            "type": 2, # Scheduled meeting
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration": duration,
            "timezone": "UTC",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "waiting_room": True
            }
        }
        
        response = requests.post("https://api.zoom.us/v2/users/me/meetings", headers=headers, json=payload)
        
        if response.status_code == 201:
            data = response.json()
            return {
                "meeting_id": str(data.get("id")),
                "join_url": data.get("join_url"),
                "password": data.get("password"),
                "start_time": start_time
            }
        else:
            print(f"Error creating Zoom meeting: {response.text}")
            return None
