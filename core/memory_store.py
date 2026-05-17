import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter
from utils.logger import get_logger

log = get_logger("memory_store")

MEMORY_FILE = Path(__file__).parent.parent / "memory_store.json"


class MemoryStore:
    def __init__(self):
        self.filepath = MEMORY_FILE
        self._store = self._load()

    def _load(self):
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.warning(f"Memory load error: {e}")
        return {"sessions": [], "findings": [], "credentials": [], "targets": {}}

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self._store, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.warning(f"Memory save error: {e}")

    def add_session(self, session_id, objective, summary, targets=None, commands=None):
        entry = {
            "id": session_id,
            "objective": objective[:200],
            "summary": (summary or "")[:500],
            "targets": list(targets)[:10] if targets else [],
            "command_count": len(commands) if commands else 0,
            "timestamp": datetime.now().isoformat()
        }
        self._store["sessions"].insert(0, entry)
        self._store["sessions"] = self._store["sessions"][:50]
        self._save()

    def add_finding(self, finding_type, content, target=""):
        entry = {"type": finding_type, "content": content[:300], "target": target, "timestamp": datetime.now().isoformat()}
        self._store["findings"].insert(0, entry)
        self._store["findings"] = self._store["findings"][:200]
        self._save()

    def add_target(self, ip, info):
        self._store["targets"][ip] = {
            "hostname": info.get("hostname", ""),
            "os": info.get("os", ""),
            "services": info.get("services", {}),
            "last_seen": datetime.now().isoformat()
        }
        self._store["targets"] = {k: v for k, v in list(self._store["targets"].items())[:100]}
        self._save()

    def add_credential(self, ip, service, username, password):
        entry = {"ip": ip, "service": service, "username": username, "password": password, "timestamp": datetime.now().isoformat()}
        self._store["credentials"].insert(0, entry)
        self._store["credentials"] = self._store["credentials"][:100]
        self._save()

    def query_relevant(self, text, max_results=5):
        keywords = self._extract_keywords(text)
        if not keywords:
            return ""

        scored = []
        for session in self._store["sessions"]:
            score = self._match_keywords(session.get("objective", "") + " " + session.get("summary", ""), keywords)
            if score > 0:
                scored.append((score, "session", session))

        for finding in self._store["findings"]:
            score = self._match_keywords(finding.get("content", ""), keywords)
            if score > 0:
                scored.append((score, "finding", finding))

        scored.sort(key=lambda x: x[0], reverse=True)
        scored = scored[:max_results]

        if not scored:
            return ""

        lines = ["**Previous session memory (relevant):**"]
        for score, typ, item in scored:
            if typ == "session":
                lines.append(f"  • [{item.get('objective','')[:60]}] {item.get('summary','')[:150]}")
            elif typ == "finding":
                lines.append(f"  • {item.get('content','')[:150]} (target: {item.get('target','')})")
        return "\n".join(lines)

    def get_all_targets_summary(self):
        if not self._store["targets"]:
            return ""
        lines = ["**Known targets from all sessions:**"]
        for ip, info in self._store["targets"].items():
            services = ", ".join(info.get("services", {}).keys()) or "?"
            lines.append(f"  • {ip} ({info.get('os','?')}) — services: {services}")
        return "\n".join(lines)

    def format_for_prompt(self, user_input):
        relevant = self.query_relevant(user_input)
        targets = self.get_all_targets_summary()
        parts = [p for p in [relevant, targets] if p.strip()]
        return "\n\n".join(parts)

    def _extract_keywords(self, text):
        text = text.lower()
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
        domains = re.findall(r'\b[\w.-]+\.[a-z]{2,}\b', text)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
        stopwords = {"this", "that", "what", "with", "from", "have", "been", "will", "would", "could",
                     "should", "their", "there", "which", "about", "also", "into", "than", "then",
                     "scan", "check", "show", "list", "tell", "find", "run", "use"}
        words = [w for w in words if w not in stopwords]
        return list(set(ips + domains + words))

    def _match_keywords(self, text, keywords):
        text = text.lower()
        score = 0
        for kw in keywords:
            if kw in text:
                score += len(kw)
        return score


_global_memory = None


def get_memory():
    global _global_memory
    if _global_memory is None:
        _global_memory = MemoryStore()
    return _global_memory
