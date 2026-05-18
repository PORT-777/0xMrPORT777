# PROJECT MAP - PORT-777 V1 — Kali Linux AI Assistant

## Overview
Conversational AI assistant for Kali Linux. Hunting Loop REPL.
AI responds in text, commands extracted from ```bash blocks.
Every command requires user approval (y/n) unless `-y` flag used.
Smart fallback with 4 phases when AI is unreachable.
Speaks Arabic/English.

## Architecture
```
APP/
├── port777.py              # Hunting Loop REPL + y/n approval system
├── install.sh              # One-command installer for Kali Linux
├── config.yaml             # V1 config
├── 777.py                  # Original Shadow Worm v5 (reference only)
├── core/
│   ├── assistant.py        # Text-based AI → extract_command() + execute_from_pending()
│   ├── brain.py            # Session state machine (targets, ports, priorities)
│   ├── auto_planner.py     # 3-step-ahead planning + failure fallback
│   ├── context_compressor.py # Long output → structured summary
│   ├── executor.py         # Command execution + auto-heal (ensure_tool)
│   ├── session_router.py   # Multi-session manager (parallel targets)
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
│   ├── plugin_manager.py   # Plugin system (scanners/exploits)
│   ├── cve_updater.py      # CVE auto-update from NVD API
│   ├── cve_scheduler.py    # CVE scheduler (24h auto-fetch + persistence)
│   ├── post_exploit.py     # Post-exploitation automation (26 modules)
│   ├── payload_generator.py # Smart payload generator (12 shell types)
│   ├── compliance_mapper.py # OWASP/MITRE/NIST/PTES compliance mapping
│   ├── attack_timeline.py  # Attack phase timeline builder
│   ├── network_discovery.py # Network discovery automation
│   ├── wordlist_generator.py # Smart wordlist generator
│   └── fallback_commands.py # Smart 4-phase fallback (AI unreachable)
├── utils/
│   ├── ai_client.py        # OpenRouter API (retry + fallback)
│   ├── prompts.py          # Ghost-style Arabic prompt — no JSON, no code
│   ├── config.py           # YAML loader
│   ├── logger.py           # Rotating file logger
│   └── output_parser.py    # Parse nmap, hydra, gobuster, dig
├── server/                 # Web UI backend (not loaded by default)
│   ├── main.py, api.py, ws.py, models.py, bridge.py
│   └── ui/                 # React SPA (Vite)
├── plugins/                # Community plugins
│   ├── scanners/
│   ├── exploits/
│   └── post_exploit/
├── tests/                  # 169 unit/integration tests
│   ├── test_safety.py, test_exploit_engine.py, test_context_compressor.py
│   ├── test_output_parser.py, test_knowledge_base.py, test_brain.py
│   ├── test_memory_store.py, test_workflow_engine.py
│   ├── test_cve_scheduler.py, test_integration.py
│   └── conftest.py
├── templates/              # Report templates
├── Dockerfile
├── docker-compose.yml
├── outputs/                # Reports + findings export
├── sessions/               # Saved sessions
├── logs/                   # Logs
├── findings.db             # SQLite database
├── brain_state.json        # Live brain state
├── .env / .env.example
├── requirements.txt
├── requirements-dev.txt
└── PROJECT_MAP.md
```

## Features

### Hunting Loop REPL
- No flags. No menu. `python port777.py` → ready to hunt
- AI auto-decides: answer (chat) or command (execute)
- Commands extracted from AI text response via ```bash blocks
- **y/n approval** before every command execution
- **-y flag**: add `-y` at end of input to auto-approve all commands
- Smart fallback with 4 phases when AI unreachable (Recon → Vuln → Exploit → Report)
- Phase tracking: "Phase 1: Reconnaissance | Iteration 1"
- Auto-continue: after each command, feeds "continue" to AI
- Slash commands: /help, /sessions, /findings, /reports, /brain, /about, /reset, /exit
- Model switching: `/model openrouter` or `/model ollama`

### Smart Fallback (No AI)
When OpenRouter is unreachable, runs deterministic phases:
1. **Reconnaissance**: whatweb, curl, dig, whois
2. **Port Scanning**: nmap -sV --top-ports 1000
3. **Vulnerability Scanning**: nikto, nmap --script vuln
4. **Exploitation Research**: searchsploit
Each phase shown to user for y/n approval.

### Exploit Engine (V1)
- Bundled CVE database (118 entries across 48 services)
- Match by port, service name, version, brand
- Metasploit module suggestion per CVE (65+ modules)
- Services: Apache, Nginx (6 CVEs), MySQL, PostgreSQL (7), Redis, WordPress (11), etc.

### Target Graph (V1)
- Network topology from brain state + findings DB
- Weakest path analysis (BFS shortest path)

### Auto-Heal (V1)
- auto-detect missing tools, auto-install via apt/pip

### Long-Term Memory (RAG)
- memory_store.json stores sessions, findings, targets
- AI sees "Previous session memory" in context

### Post-Exploitation (V1)
- 26 modules: privilege escalation, persistence, lateral movement, exfiltration

### Payload Generator (V1)
- 12 shell types, 4 encodings, Metasploit payloads

### Compliance Mapping (V1)
- OWASP Top 10, MITRE ATT&CK, NIST CSF, PTES

### Attack Timeline (V1)
- 10 phases, auto-detected from commands

### Network Discovery (V1)
- 15 discovery commands, smart subnet calculation

### Wordlist Generator (V1)
- Target-based wordlists, mutation engine

### CVE Auto-Update + Scheduler (V1)
- Fetch from NVD API, auto-schedule every 24h
- Persistent state across restarts

### GitHub Actions CI/CD
- Python 3.10-3.13 matrix, Bandit security scan
- Docker build, 169 tests

## Core Flow
1. User types anything (Arabic/English)
2. If input ends with `-y`: auto-approve mode ON
3. AI receives Ghost-style Arabic prompt + tool knowledge + brain state
4. AI responds with text: analysis + ```bash command
5. System extracts command from ```bash block
6. **y/n approval**: shown to user before execution (unless auto-approve)
7. If approved → executor runs command → brain updates
8. Auto-continue: feeds "continue" to AI for next action
9. If AI unreachable → Smart Fallback with 4 phases
10. Loop until /exit or objective complete

## Commands
```
python port777.py    → Start hunting loop REPL
  -y at end of text  → Auto-approve all commands
  /help              → Show commands
  /sessions          → List past sessions
  /session <id>      → View session
  /findings          → Show findings
  /reports           → List reports
  /brain             → View brain state
  /model <provider>  → Switch AI provider
  /about             → Developer info
  /plugins           → List plugins
  /cve [action]      → CVE operations
  /reset             → Fresh session
  /exit              → Exit
```

## Key Design Decisions
- **AI responds in plain TEXT** (not JSON) — extracted via ```bash blocks
- **y/n before every command** — user controls execution
- **-y flag** — auto-approve for power users
- **Smart Fallback** — 4 deterministic phases when AI is down
- **Ghost-style Arabic prompt** — AI must execute, not write code
- **No pre-defined tool chains** — AI decides everything
- **No web dashboard loaded** — CLI-only, server files preserved

## Pending / Future
- Fix Kali DNS for OpenRouter connectivity
- Telegram Bot integration
- Multi-user collaborative sessions
- Full API integration tests
