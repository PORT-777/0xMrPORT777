# PROJECT MAP - PORT-777 v5 — Kali Linux Superhuman AI

## Overview
Conversational AI assistant for Kali Linux. ChatGPT-style REPL + Web Dashboard.
Speaks Arabic/English. Understands ANY input — scan, exploit, question, system admin.

## Architecture
```
APP/
├── port777.py              # ChatGPT-style REPL + --serve flag for Web UI
├── config.yaml             # v5 config
├── core/
│   ├── assistant.py        # Conversational agent: chat() → answer | command | done
│   ├── brain.py            # Session state machine (targets, ports, priorities)
│   ├── auto_planner.py     # 3-step-ahead planning + failure fallback
│   ├── context_compressor.py # Long output → structured summary
│   ├── executor.py         # Command execution + **auto-heal (ensure_tool)**
│   ├── session_router.py   # **Multi-session manager (parallel targets)**
│   ├── safety.py           # Safety shield
│   ├── memory.py           # Session context
│   ├── session_manager.py  # Save/load sessions
│   ├── reporter.py         # Reports with findings DB
│   ├── knowledge_base.py   # 25+ Kali tools encyclopedia
│   ├── findings_db.py      # SQLite findings DB
│   ├── workflow_engine.py  # 6 pentest workflows
│   ├── parallel_executor.py # Multi-command parallelism
│   ├── exploit_engine.py   # CVE matching + Metasploit suggestions
│   └── target_graph.py     # Network topology graph builder
├── server/                 # Web UI backend
│   ├── main.py             # FastAPI app (uvicorn)
│   ├── api.py              # REST endpoints
│   ├── ws.py               # WebSocket handler (live chat)
│   ├── models.py           # Pydantic schemas
│   ├── bridge.py           # KaliAssistant wrapper
│   ├── ui/                 # React SPA source (Vite)
│   └── static/             # Built frontend
├── utils/
│   ├── ai_client.py        # OpenRouter API (retry + fallback)
│   ├── prompts.py          # CONVERSATIONAL_PROMPT — answer | command | done
│   ├── config.py           # YAML loader
│   ├── logger.py           # Rotating file logger
│   └── output_parser.py    # Parse nmap, hydra, gobuster
├── outputs/                # Reports + findings export
├── sessions/               # Saved sessions
├── logs/                   # Logs
├── findings.db             # SQLite database
├── brain_state.json        # Live brain state
├── .env / .env.example
├── requirements.txt
└── PROJECT_MAP.md
```

## Features

### Conversational REPL
- No flags. No menu. `python port777.py` → ready to chat
- AI auto-detects intent: scan, exploit, question, system, chat
- Three response types: **answer** (chat), **command** (execute), **done** (finish)
- Auto-confirmation for safe commands (ls, whoami), prompt for destructive (nmap, hydra)
- Slash commands: /help, /sessions, /findings, /reports, /workflows, /brain, /reset, /exit
- Continuous session — context persists across all messages
- Multi-session: `/session new "objective"` creates parallel sessions; `/session switch <id>` to swap
- **Model switching**: `/model openrouter` or `/model ollama qwen2.5:7b` — switch AI provider at runtime

### Web Dashboard (v5)
- `python port777.py --serve` → opens FastAPI server on port 7777
- WebSocket live streaming — type in browser, AI replies in real-time
- REST APIs: sessions, findings, reports, brain state, exploit suggestions, target graph
- React SPA with Chat, Sessions, Findings, Graph pages
- Graph page: **hover tooltips** (IP, OS, ports, creds/vulns), highlight on hover, click to select
- Swagger docs at http://localhost:7777/docs

### Exploit Engine (v5)
- Bundled CVE database (**102 entries across 42 services**)
- Match by: port, service name, version, brand
- Metasploit module suggestion per CVE (**30 modules**)
- **Auto-execute**: exploit suggestions feed into AI prompt context — AI can run Metasploit exploits directly via msfconsole
- Prompt updated with msfconsole command format for exploit execution
- `/api/exploits/suggest?target=X&port=Y` endpoint
- Services covered: Apache, Nginx, Tomcat, MySQL, PostgreSQL, Redis, WordPress (10+), Drupal, Joomla, Jenkins, Elasticsearch, MongoDB, ProFTPD, vsFTPd, OpenSSH, Samba, SMB, RDP, Exchange, WebLogic, JBoss, Docker, Kubernetes, Grafana, Confluence, Jira, Fortinet, Citrix, Palo Alto, BIND, Exim, GlassFish, SNMP, NFS + more

### Target Graph (v5)
- Builds network topology from brain state + findings DB
- Nodes: targets with IP, OS, ports, credentials/vulnerabilities flags
- Edges: service connections + same-subnet links
- Weakest path analysis (BFS shortest path to high-value targets)
- `/api/graph/targets` returns nodes + edges JSON for frontend visualization

### Auto-Heal (v5)
- `executor.ensure_tool(tool_name)` — auto-detect missing tools
- Supports apt (Linux), pip (Python tools), brew (macOS)
- Hooked into `executor.run()` — installs missing tools silently before execution
- Logs installation status

### Multi-Session Parallel (v5)
- `core/session_router.py` — manages multiple KaliAssistant instances
- Each session has independent brain, executor, history
- REPL: `/session new "recon target A"` → `/session switch <id>` → `/session close <id>`
- API: `POST /api/sessions/create`, `GET /api/sessions/active`, `POST /api/sessions/{id}/switch|close`
- WebSocket supports multi-session with session_id tracking

## Core Flow
1. User types ANYTHING naturally (Arabic/English)
2. Brain initializes on first message
3. AI receives CONVERSATIONAL_PROMPT + tool knowledge + brain state + exploit suggestions + target graph
4. AI decides: answer | command (confirm?) | done
5. If command → executor auto-installs missing tools if needed
6. Output analyzed → brain updated → exploit engine re-matches → graph rebuilds
7. Loop indefinitely until /exit

## Commands
```
python port777.py            → Start conversational REPL
python port777.py --serve    → Start Web UI server (port 7777)
  /help                     → Show slash commands
  /sessions                 → List past sessions
  /session <id>             → View session details
  /session new <objective>  → Create new parallel session
  /session switch <id>      → Switch active session
  /session close <id>       → Close session
  /findings                 → Show findings database
  /reports                  → List reports
  /workflows                → List available workflows
  /brain                    → View current session brain state
  /model <provider> [model] → Switch AI provider (openrouter/ollama)
  /models                   → List available Ollama models
  /about                    → Developer info & links
  /reset                    → Start fresh session
  /exit                     → Exit
```

## Features (Complete v5)

### Developer Info
- Banner shows "By 0xMr.PORT 777"
- `/about` command: Telegram, WhatsApp, Instagram links
- Web dashboard root shows developer info
- Reports footer includes credits

### Export Reports
- **Markdown** (.md) — comprehensive pentest report
- **HTML** (.html) — styled dark theme, badges, timeline
- **CSV** (.csv) — structured data for spreadsheets
- **Plain Text** (.txt) — fallback format
- All generated automatically on session completion to `outputs/`

### Long-Term Memory (RAG)
- `memory_store.json` stores sessions, findings, targets, credentials
- Before each AI chat, relevant past sessions are queried via keyword matching
- AI sees "Previous session memory" in system context
- Targets discovered in past sessions are remembered
- Helps avoid re-scanning the same targets

### Auto-Heal
- `executor.ensure_tool(tool_name)` — auto-detect missing tools
- Supports apt (Linux), pip (Python tools), brew (macOS)
- Hooked into `executor.run()` — installs missing tools before execution
- Uses direct subprocess for tool checks (no recursion)

## Pending / Future
- Docker support (docker-compose)
- Plugin system for community scanners
