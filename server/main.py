import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from server.api import router as api_router
from server.ws import chat_websocket
from utils.logger import get_logger

log = get_logger("server")

app = FastAPI(title="PORT-777 V1", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket):
    await chat_websocket(websocket)


static_dir = Path(__file__).parent / "static"
if static_dir.exists() and (static_dir / "index.html").exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        index = static_dir / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"error": "Frontend not built"}
else:
    @app.get("/")
    def root():
        return {
            "app": "PORT-777 V1",
            "developer": "0xMr.PORT 777",
            "telegram": "https://t.me/PB_9B",
            "whatsapp": "https://wa.me/+201026778601",
            "instagram": "https://www.instagram.com/i_c.n",
            "status": "online",
            "frontend": "not built (run `cd server/ui && npm install && npm run build`)",
            "docs": "/docs"
        }


def start(host="0.0.0.0", port=7777):
    import uvicorn
    log.info(f"Starting PORT-777 server on http://{host}:{port}")
    print(f"\n[+] PORT-777 Dashboard: http://localhost:{port}")
    print(f"[+] By 0xMr.PORT 777")
    print(f"[+] API docs: http://localhost:{port}/docs\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")
