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
│   ├── target_graph.py     # Network topology graph builder
│   ├── plugin_manager.py   # **Plugin system (scanners/exploits)**
│   ├── cve_updater.py      # **CVE auto-update from NVD API**
│   └── cve_scheduler.py    # **CVE scheduler (24h auto-fetch)**
├── server/                 # Web UI backend
│   ├── main.py             # FastAPI app (uvicorn)
│   ├── api.py              # REST endpoints (33 routes)
│   ├── ws.py               # WebSocket handler (live chat)
│   ├── models.py           # Pydantic schemas
│   ├── bridge.py           # KaliAssistant wrapper
│   ├── ui/                 # React SPA source (Vite)
│   │   ├── src/
│   │   │   ├── App.jsx             # Main app with 7 tabs
│   │   │   ├── DashboardPage.jsx   # **Overview dashboard**
│   │   │   ├── ChatPage.jsx        # **Enhanced chat**
│   │   │   ├── CVEPage.jsx         # **CVE viewer + scheduler**
│   │   │   ├── PluginsPage.jsx     # **Plugin browser + runner**
│   │   │   ├── SessionsPage.jsx    # Session history
│   │   │   ├── FindingsPage.jsx    # Findings tables
│   │   │   ├── GraphPage.jsx       # Network graph
│   │   │   └── api.js              # API client
│   │   └── vite.config.js
│   └── static/             # Built frontend
├── plugins/                # **Community plugins**
│   ├── scanners/           # Scanner plugins (nmap_enhanced, etc.)
│   ├── exploits/           # Exploit plugins (msf_exploit, etc.)
│   └── post_exploit/       # Post-exploitation plugins
├── tests/                  # **Unit/Integration tests (118 tests)**
│   ├── conftest.py
│   ├── test_safety.py
│   ├── test_exploit_engine.py
│   ├── test_context_compressor.py
│   ├── test_output_parser.py
│   ├── test_knowledge_base.py
│   ├── test_brain.py
│   ├── test_memory_store.py
│   ├── test_workflow_engine.py
│   └── test_cve_scheduler.py
├── templates/              # Report templates
│   └── report.html         # HTML report template
├── Dockerfile              # **Docker container**
├── docker-compose.yml      # **Docker Compose**
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
├── requirements-dev.txt    # **Test dependencies**
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
  /plugins [category]       → List available plugins
  /cve [fetch|stats|schedule] → CVE auto-update + scheduler
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
- **PDF** (.pdf) — professional printable report via weasyprint
- **Plain Text** (.txt) — fallback format
- All generated automatically on session completion to `outputs/`

### Docker Support
- `Dockerfile` — Python 3.13 slim base
- `docker-compose.yml` — app + optional Ollama service
- Volumes for outputs, sessions, logs, DB files
- `docker compose up` to start

### Plugin System
- `core/plugin_manager.py` — auto-discovers plugins from `plugins/` directory
- Categories: `scanners/`, `exploits/`, `post_exploit/`
- Standard interface: `name`, `description`, `category`, `run(target, **kwargs)`
- 3 example plugins included: nmap_enhanced, msf_exploit, enum_system
- `/plugins` command in REPL, `/api/plugins` REST endpoint
- Community can add custom scanners/exploits as Python files

### CVE Auto-Update
- `core/cve_updater.py` — fetches latest CVEs from NVD API
- `/cve fetch` — download recent CVEs (default: last 30 days)
- `/cve stats` — view cache statistics
- Cached in `cve_cache.json`
- `/api/cve/stats` and `/api/cve/fetch` REST endpoints

### CVE Scheduler (v5.2)
- `core/cve_scheduler.py` — automatic CVE updates every 24 hours (configurable)
- Background daemon thread, non-blocking
- `/cve schedule start [hours]` — start auto-fetch
- `/cve schedule stop` — stop scheduler
- `/cve schedule run` — manual trigger
- `/cve schedule status` — view scheduler state
- REST: `/api/cve/scheduler/status|start|stop|run`
- Error tracking with recent error history

### Unit/Integration Tests (v5.2)
- `tests/` directory with pytest suite
- 118 tests across 8 modules:
  - `test_safety.py` — SafetyShield command validation
  - `test_exploit_engine.py` — CVE matching, Metasploit suggestions
  - `test_context_compressor.py` — Output compression, structured extraction
  - `test_output_parser.py` — nmap, hydra, gobuster parsing
  - `test_knowledge_base.py` — Tool knowledge, search, categories
  - `test_brain.py` — SessionBrain state machine, phase transitions
  - `test_memory_store.py` — Long-term memory, keyword matching
  - `test_workflow_engine.py` — Workflow definitions, phase prompts
  - `test_cve_scheduler.py` — Scheduler lifecycle, run_once
- `requirements-dev.txt` — pytest, pytest-asyncio, pytest-cov, apscheduler
- Run: `python -m pytest tests/ -v`

### UI Enhancements (v5.2)
- **Dashboard Page** (`DashboardPage.jsx`) — overview with stat cards, severity bar chart, session info, target table
- **CVE Page** (`CVEPage.jsx`) — CVE database viewer, fetch from NVD, scheduler controls (start/stop/run/interval)
- **Plugins Page** (`PluginsPage.jsx`) — plugin browser, category filter, run plugins with target input, result viewer
- **Chat Improvements** — typing indicator, clear chat button, better status colors, improved empty state
- **New Nav Tabs** — Dashboard (default), CVEs, Plugins (7 tabs total)
- **API Extensions** — 4 new CVE scheduler endpoints, plugin run endpoint

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
- Telegram Bot
- Multi-target parallel sessions
- Advanced PDF report styling
- CVE auto-update scheduling persistence (save interval to config)
- Integration tests for full API + WebSocket flow
