import os
import json
from datetime import datetime
from pathlib import Path
from utils.config import get_config


class SessionManager:
    """Manages saving, loading, listing penetration testing sessions."""

    def __init__(self):
        storage = get_config("sessions", "storage_dir") or "sessions"
        self.storage_dir = Path(__file__).parent.parent / storage
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session_id: str, data: dict) -> str:
        filepath = self.storage_dir / f"{session_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return str(filepath)

    def load(self, session_id: str) -> dict:
        filepath = self.storage_dir / f"{session_id}.json"
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_sessions(self) -> list[dict]:
        sessions = []
        for fpath in sorted(self.storage_dir.glob("*.json"), key=os.path.getmtime, reverse=True):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "id": fpath.stem,
                    "objective": data.get("objective", "N/A"),
                    "timestamp": data.get("timestamp", "N/A"),
                    "command_count": len(data.get("commands", [])),
                    "status": data.get("status", "unknown"),
                    "file": str(fpath)
                })
            except Exception:
                continue
        return sessions

    def delete(self, session_id: str) -> bool:
        filepath = self.storage_dir / f"{session_id}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def generate_id(self) -> str:
        return datetime.now().strftime("session_%Y%m%d_%H%M%S")
