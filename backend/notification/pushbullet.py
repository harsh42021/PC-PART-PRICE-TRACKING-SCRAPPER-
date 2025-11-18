# backend/notifications/pushbullet.py
import os
import requests

PUSHBULLET_API_BASE = "https://api.pushbullet.com/v2"
DEFAULT_KEY = os.environ.get("PUSHBULLET_API_KEY")

class PushbulletClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or DEFAULT_KEY

    def send_note(self, title, body):
        if not self.api_key:
            return {"error": True, "message": "No Pushbullet API key configured"}
        headers = {"Access-Token": self.api_key, "Content-Type": "application/json"}
        payload = {"type": "note", "title": title, "body": body}
        try:
            r = requests.post(f"{PUSHBULLET_API_BASE}/pushes", json=payload, headers=headers, timeout=8)
            r.raise_for_status()
            return {"ok": True}
        except Exception as e:
            return {"error": True, "message": str(e)}
