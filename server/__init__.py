from pathlib import Path
from datetime import datetime

from utils.logger import get_logger

log = get_logger("server")


SESSION_STORE = {}


class SessionStore:
    def __init__(self, session_id):
        self.session_id = session_id
        self.messages = []
        self.created_at = datetime.now().isoformat()

    def add_user(self, text):
        self.messages.append({"role": "user", "content": text, "time": datetime.now().isoformat()})

    def add_assistant(self, text):
        self.messages.append({"role": "assistant", "content": text, "time": datetime.now().isoformat()})

    def to_dict(self):
        return {"id": self.session_id, "created": self.created_at, "messages": self.messages}
