import threading
import uuid
from datetime import datetime
from utils.logger import get_logger

log = get_logger("session_router")


class SessionRouter:
    """Manages multiple parallel KaliAssistant sessions."""

    def __init__(self):
        self._sessions = {}
        self._active_id = None
        self._lock = threading.Lock()

    def create(self, objective=""):
        session_id = uuid.uuid4().hex[:12]
        with self._lock:
            from core.assistant import KaliAssistant
            asst = KaliAssistant()
            self._sessions[session_id] = {
                "assistant": asst,
                "objective": objective[:200],
                "created": datetime.now().isoformat(),
                "status": "active",
                "message_count": 0
            }
            self._active_id = session_id
        log.info(f"Session created: {session_id}, objective: {objective[:80]}")
        return session_id

    def get(self, session_id):
        with self._lock:
            entry = self._sessions.get(session_id)
            if entry:
                return entry["assistant"]
            return None

    def chat(self, session_id, message):
        asst = self.get(session_id)
        if not asst:
            return None, None
        resp_type, data = asst.chat(message)
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["message_count"] += 1
                if resp_type == "summary":
                    self._sessions[session_id]["status"] = "completed"
        return resp_type, data

    def list_sessions(self):
        with self._lock:
            return {
                sid: {
                    "objective": info["objective"],
                    "created": info["created"],
                    "status": info["status"],
                    "messages": info["message_count"],
                    "active": sid == self._active_id
                }
                for sid, info in self._sessions.items()
            }

    def switch(self, session_id):
        with self._lock:
            if session_id in self._sessions:
                self._active_id = session_id
                log.info(f"Switched to session: {session_id}")
                return True
            return False

    def close(self, session_id):
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                if self._active_id == session_id:
                    keys = list(self._sessions.keys())
                    self._active_id = keys[0] if keys else None
                log.info(f"Session closed: {session_id}")
                return True
            return False

    def get_active_id(self):
        with self._lock:
            return self._active_id

    def broadcast_all(self):
        with self._lock:
            return {sid: info["status"] for sid, info in self._sessions.items()}


_global_router = SessionRouter()


def get_router():
    return _global_router


def reset_router():
    global _global_router
    _global_router = SessionRouter()
