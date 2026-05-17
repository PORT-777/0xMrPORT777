import json
import os
from datetime import datetime
from utils.logger import get_logger

log = get_logger("memory")


class SessionMemory:
    def __init__(self):
        self.history = []
        self.objective = ""

    def start_session(self, objective):
        self.objective = objective
        self.history = [{
            "role": "user",
            "objective": objective,
            "timestamp": datetime.now().isoformat()
        }]

    def add_message(self, role, content):
        if not content:
            return
        entry = {
            "role": role,
            "content": content[:3000],
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(entry)

    def get_context(self, max_exchanges=8):
        lines = []
        for entry in self.history[-max_exchanges * 2:]:
            role = entry["role"]
            content = entry.get("content", entry.get("objective", ""))
            if not content:
                continue
            prefix = {
                "user": "User",
                "command": "Command",
                "output": "Output",
                "ai": "Decision"
            }.get(role, role)
            max_len = 1000 if role == "output" else 500
            lines.append(f"{prefix}: {content[:max_len]}")
        return "\n".join(lines)

    def get_full_history(self):
        return self.history
