import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from utils.logger import get_logger
from server.bridge import chat_sync, confirm_and_execute, list_sessions, create_session, switch_session, close_session

log = get_logger("ws")


async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    log.info("WebSocket connected")
    current_session_id = None

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            msg = data.get("message", "")
            decision = data.get("decision")
            cmd = data.get("cmd", "")
            session_id = data.get("session_id", current_session_id)
            args = data.get("args", {})

            if cmd == "session":
                sub = args.get("action", "list")
                if sub == "new":
                    sid = create_session(args.get("objective", ""))
                    current_session_id = sid
                    await websocket.send_text(json.dumps({"type": "session_created", "session_id": sid}))
                elif sub == "list":
                    sessions = list_sessions()
                    await websocket.send_text(json.dumps({"type": "session_list", "sessions": sessions}))
                elif sub == "switch":
                    target = args.get("id", "")
                    ok = switch_session(target)
                    if ok:
                        current_session_id = target
                    await websocket.send_text(json.dumps({"type": "session_switched", "ok": ok, "session_id": target}))
                elif sub == "close":
                    target = args.get("id", "")
                    ok = close_session(target)
                    if ok and current_session_id == target:
                        current_session_id = None
                    await websocket.send_text(json.dumps({"type": "session_closed", "ok": ok}))
                await websocket.send_text(json.dumps({"type": "stream_end"}))
                continue

            if decision:
                result, sid = await asyncio.to_thread(confirm_and_execute, decision, session_id)
                current_session_id = sid
                result["session_id"] = sid
                await websocket.send_text(json.dumps(result))
                if result.get("type") == "done":
                    await websocket.send_text(json.dumps({"type": "stream_end"}))
                continue

            if not msg:
                continue

            result, sid = await asyncio.to_thread(chat_sync, msg, session_id)
            current_session_id = sid
            resp_type = result.get("type")

            if resp_type == "answer":
                await websocket.send_text(json.dumps({"type": "answer", "content": result.get("content", ""), "session_id": sid}))
                await websocket.send_text(json.dumps({"type": "stream_end"}))

            elif resp_type == "command_pending":
                await websocket.send_text(json.dumps({
                    "type": "command_pending",
                    "command": result.get("command", ""),
                    "reason": result.get("reason", ""),
                    "decision": result.get("decision"),
                    "session_id": sid
                }))

            elif resp_type == "command_done":
                await websocket.send_text(json.dumps({
                    "type": "command_start",
                    "command": result.get("command", ""),
                    "reason": result.get("reason", ""),
                    "session_id": sid
                }))
                output = result.get("output", "")
                if output:
                    await websocket.send_text(json.dumps({"type": "command_output", "output": output[:500], "session_id": sid}))
                await websocket.send_text(json.dumps({"type": "command_done", "command": result.get("command", ""), "session_id": sid}))
                await websocket.send_text(json.dumps({"type": "stream_end"}))

            elif resp_type == "done":
                await websocket.send_text(json.dumps({"type": "done", "content": result.get("content", ""), "session_id": sid}))
                await websocket.send_text(json.dumps({"type": "stream_end"}))

    except WebSocketDisconnect:
        log.info("WebSocket disconnected")
    except Exception as e:
        log.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))
        except Exception:
            pass
