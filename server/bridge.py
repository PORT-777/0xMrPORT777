from utils.logger import get_logger
from core.session_router import get_router

log = get_logger("bridge")


def get_or_create_assistant(session_id=None):
    router = get_router()
    if session_id:
        asst = router.get(session_id)
        if asst:
            return asst, session_id
    active = router.get_active_id()
    if active:
        asst = router.get(active)
        if asst:
            return asst, active
    sid = router.create("default web session")
    return router.get(sid), sid


def chat_sync(message, session_id=None):
    asst, sid = get_or_create_assistant(session_id)
    try:
        resp_type, data = asst.chat(message)
    except Exception as e:
        log.error(f"chat_sync error: {e}")
        return {"type": "answer", "content": f"Error: {str(e)}"}, sid

    result = _format_response(resp_type, data)
    result["session_id"] = sid
    return result, sid


def confirm_and_execute(decision, session_id=None):
    asst, sid = get_or_create_assistant(session_id)
    try:
        resp_type, data = asst.confirm_and_execute(decision)
    except Exception as e:
        log.error(f"confirm error: {e}")
        return {"type": "answer", "content": f"Error: {str(e)}"}, sid

    result = _format_response(resp_type, data)
    result["session_id"] = sid
    return result, sid


def _format_response(resp_type, data):
    if resp_type == "answer":
        return {"type": "answer", "content": data["content"]}
    elif resp_type == "command":
        pending = data.get("pending_approval", False)
        cmd = data.get("command", "")
        reason = data.get("reason", "")
        output = data.get("output", "")
        if pending:
            return {"type": "command_pending", "command": cmd, "reason": reason, "decision": data.get("decision")}
        return {"type": "command_done", "command": cmd, "reason": reason, "output": output[:500]}
    elif resp_type == "summary":
        return {"type": "done", "content": data["summary"]}
    return {"type": "answer", "content": "..."}


def reset_assistant():
    from core.session_router import reset_router
    reset_router()
    log.info("Router reset")


def list_sessions():
    return get_router().list_sessions()


def create_session(objective=""):
    return get_router().create(objective)


def switch_session(session_id):
    return get_router().switch(session_id)


def close_session(session_id):
    return get_router().close(session_id)


def switch_model(provider, model=None):
    router = get_router()
    active = router.get_active_id()
    if not active:
        asst, sid = get_or_create_assistant()
    else:
        asst = router.get(active)
    if not asst:
        return False, "No active session"
    return asst.switch_model(provider, model)
