import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Body
from server.bridge import chat_sync, confirm_and_execute, reset_assistant, list_sessions, create_session, switch_session, close_session

router = APIRouter(prefix="/api")

BASE = Path(__file__).parent.parent


@router.get("/status")
def get_status():
    sessions = list_sessions()
    return {
        "status": "online",
        "version": "v5",
        "active_sessions": len(sessions),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/models")
def api_list_models():
    from utils.ai_client import AIClient
    client = AIClient(provider="ollama")
    local = client.list_local_models()
    return {"providers": ["openrouter", "ollama"], "ollama_models": local, "current_provider": "openrouter"}


@router.post("/models/switch")
def api_switch_model(body: dict):
    provider = body.get("provider", "openrouter")
    model = body.get("model")
    from server.bridge import switch_model as bridge_switch
    ok, msg = bridge_switch(provider, model)
    return {"ok": ok, "message": msg}


@router.post("/chat")
def chat_api(body: dict = Body(...)):
    message = body.get("message", "")
    session_id = body.get("session_id")
    decision = body.get("decision")
    if decision:
        result, sid = confirm_and_execute(decision, session_id)
        return result
    if not message:
        raise HTTPException(400, "message required")
    result, sid = chat_sync(message, session_id)
    return result


@router.post("/sessions/create")
def api_create_session(body: dict = Body(...)):
    objective = body.get("objective", "")
    sid = create_session(objective)
    return {"session_id": sid, "objective": objective}


@router.get("/sessions/active")
def api_list_active_sessions():
    return list_sessions()


@router.post("/sessions/{session_id}/switch")
def api_switch_session(session_id: str):
    ok = switch_session(session_id)
    return {"ok": ok}


@router.post("/sessions/{session_id}/close")
def api_close_session(session_id: str):
    ok = close_session(session_id)
    return {"ok": ok}


@router.post("/reset")
def reset():
    reset_assistant()
    return {"status": "reset"}


@router.get("/sessions")
def list_sessions():
    try:
        from core.session_manager import SessionManager
        sm = SessionManager()
        sessions = sm.list_sessions()
        return [{"id": s["id"], "objective": s["objective"][:80],
                 "status": s["status"], "timestamp": s.get("timestamp", "")[:19]}
                for s in sessions[:30]]
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    try:
        from core.session_manager import SessionManager
        sm = SessionManager()
        data = sm.load(session_id)
        if not data:
            raise HTTPException(404, "Session not found")
        cmds = data.get("commands", [])
        return {
            "id": session_id,
            "objective": data.get("objective", ""),
            "status": data.get("status", ""),
            "timestamp": data.get("timestamp", ""),
            "summary": (data.get("summary") or "")[:500],
            "targets": list(data.get("targets", []))[:10],
            "commands": [{"step": c.get("step"), "command": c.get("command", "")[:120],
                          "tool": c.get("tool", ""), "reason": (c.get("reason") or "")[:80]}
                         for c in cmds[:30]],
            "cred_count": data.get("credentials_count", 0),
            "vuln_count": data.get("vulnerabilities_count", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/findings/targets")
def get_targets():
    try:
        from core.findings_db import FindingsDB
        db = FindingsDB()
        return db.get_target_summary() or []
    except Exception as e:
        return {"error": str(e)}


@router.get("/findings/credentials")
def get_credentials():
    try:
        from core.findings_db import FindingsDB
        db = FindingsDB()
        return db.get_all_credentials()[:30] or []
    except Exception as e:
        return {"error": str(e)}


@router.get("/findings/vulnerabilities")
def get_vulnerabilities():
    try:
        from core.findings_db import FindingsDB
        db = FindingsDB()
        return db.get_all_vulnerabilities()[:30] or []
    except Exception as e:
        return {"error": str(e)}


@router.get("/reports")
def list_reports():
    reports_dir = BASE / "outputs"
    if not reports_dir.exists():
        return []
    files = sorted(reports_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [{"name": f.name, "size": f.stat().st_size,
             "date": datetime.fromtimestamp(f.stat().st_mtime).isoformat()}
            for f in files[:20]]


@router.get("/exploits/suggest")
def suggest_exploits(target: str = Query(""), port: int = Query(0)):
    try:
        from core.exploit_engine import ExploitEngine
        ee = ExploitEngine()
        from core.brain import SessionBrain
        brain = SessionBrain()
        suggestions = ee.match_from_brain(brain.state)
        if target:
            suggestions = [s for s in suggestions if s.get("target_ip") == target]
        if port:
            suggestions = [s for s in suggestions if s.get("port") == port]
        results = []
        for s in suggestions[:10]:
            results.append({
                "cve": s["cve"],
                "target": s.get("target_ip", ""),
                "port": s.get("port", 0),
                "severity": s.get("severity", ""),
                "type": s.get("type", ""),
                "description": s.get("desc", ""),
                "metasploit": s.get("metasploit", ""),
                "match_score": s.get("match_score", 0)
            })
        return results
    except Exception as e:
        return {"error": str(e)}


@router.get("/graph/targets")
def get_target_graph():
    try:
        from core.target_graph import TargetGraph
        from core.brain import SessionBrain
        brain = SessionBrain()
        tg = TargetGraph(brain.state)
        return tg.build(brain.state)
    except Exception as e:
        return {"error": str(e)}


@router.get("/brain")
def get_brain():
    try:
        from core.brain import SessionBrain
        brain = SessionBrain()
        state = brain.state
        return {
            "phase": state.get("phase", ""),
            "objective": state.get("objective", ""),
            "targets": {ip: {"hostname": t.get("hostname", ""), "os": t.get("os", ""),
                             "services": t.get("services", {})}
                        for ip, t in state.get("targets", {}).items()},
            "credentials": len(state.get("credentials", [])),
            "vulnerabilities": len(state.get("vulnerabilities", [])),
            "ports": {ip: list(t.get("services", {}).keys()) for ip, t in state.get("targets", {}).items()}
        }
    except Exception as e:
        return {"error": str(e)}
