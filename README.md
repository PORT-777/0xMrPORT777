# PORT-777 v5.3 🎯

**Kali Linux Superhuman AI — Penetration Testing Assistant**

[![CI/CD](https://github.com/PORT-777/0xMrPORT777/actions/workflows/ci.yml/badge.svg)](https://github.com/PORT-777/0xMrPORT777/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-169%20passed-brightgreen)](https://github.com/PORT-777/0xMrPORT777)
[![CVEs](https://img.shields.io/badge/cves-118-orange)](https://github.com/PORT-777/0xMrPORT777)
[![Modules](https://img.shields.io/badge/metasploit-65%2B-blue)](https://github.com/PORT-777/0xMrPORT777)

> By **0xMr.PORT 777** | [Telegram](https://t.me/PB_9B) | [WhatsApp](https://wa.me/+201026778601) | [Instagram](https://www.instagram.com/i_c.n)

---

## Overview

PORT-777 is an AI-powered penetration testing assistant that runs on Kali Linux. Talk to it in **Arabic or English** — it understands your intent, executes real commands, discovers vulnerabilities, exploits them, and generates professional reports.

**No flags. No menus. Just talk.**

```bash
python port777.py
```

Then type anything:
- `"افحص 192.168.1.5"` — Scan a target
- `"Find vulnerabilities on example.com"` — Web pentest
- `"What did we find on port 80?"` — Ask about results
- `"Try to exploit CVE-2021-41773"` — Auto-exploit

---

## Features

### 🧠 AI-Powered Intelligence
- **Conversational REPL** — ChatGPT-style interface, type anything naturally
- **Intent Detection** — AI understands scan, exploit, question, system admin
- **3-Step Lookahead Planning** — Plans ahead, not just the next command
- **Learn from Failure** — Auto-fallback when commands fail
- **Parallel Execution** — Runs compatible commands simultaneously
- **Command Chaining** — If-condition-then automated execution
- **Context Compression** — 5000-line output → 20-line summary

### 💣 Exploit Engine (118 CVEs)
- **48 services covered**: Apache, Nginx, Tomcat, MySQL, PostgreSQL, Redis, WordPress, Drupal, SMB, RDP, Exchange, Docker, Kubernetes, WebLogic, and more
- **65+ Metasploit modules** ready to execute — **100% coverage for major services**
- **Auto-exploit** — AI suggests and runs exploits directly via `msfconsole`
- Matches by: port, service name, version, brand

### 🕸️ Target Graph
- Network topology visualization
- Gateway detection, lateral path marking
- Weakest path analysis (BFS shortest path)
- Interactive hover tooltips in web dashboard

### 🔧 Auto-Heal
- Auto-detects missing tools before execution
- Installs via `apt` (Linux), `pip` (Python), `brew` (macOS)
- Retries automatically after installation

### 🧵 Multi-Session Parallel
- Run multiple pentest sessions simultaneously
- Each session has independent brain, executor, history
- `/session new`, `/session switch`, `/session close`

### 🧠 Dual AI Provider
| Provider | API Key | Models | Arabic | Offline |
|----------|---------|--------|--------|---------|
| **OpenRouter** | Required | 300+ | ✅ | ❌ |
| **Ollama** | Not needed | qwen2.5, deepseek-r1, llama3.2 | ✅ (qwen2.5) | ✅ |

Switch at runtime: `/model openrouter` or `/model ollama qwen2.5:7b`

### 🖥️ Web Dashboard
- **FastAPI backend** with 29 REST API routes
- **WebSocket** live streaming — real-time AI responses
- **React SPA** with Chat, Sessions, Findings, Graph pages
- **Swagger docs** at `http://localhost:7777/docs`

### 📄 Export Reports
- **Markdown** (.md) — Comprehensive pentest report
- **HTML** (.html) — Styled dark theme with badges & timeline
- **CSV** (.csv) — Structured data for spreadsheets
- **PDF** (.pdf) — Professional printable report
- **Plain Text** (.txt) — Fallback format

### 🐳 Docker Support
```bash
docker compose up -d
# App runs at http://localhost:7777
# Volumes: outputs, sessions, logs, DB files
```

### 🔌 Plugin System
- Auto-discovers plugins from `plugins/` directory
- Categories: `scanners/`, `exploits/`, `post_exploit/`
- `/plugins` command to list, `/api/plugins` REST endpoint
- Community can add custom scanners/exploits as Python files

### 🎯 Post-Exploitation Automation
- **26 modules** across 4 categories: privesc, persistence, lateral movement, data exfiltration
- LinPEAS, sudo check, SSH persistence, PsExec, hash dump, and more
- AI-aware — modules feed into system prompt for smart suggestions

### 💣 Smart Payload Generator
- **12 shell types**: bash, python, perl, php, ruby, nc, ncat, powershell, java, nodejs, golang, lua
- **4 encoding methods**: base64, base64_url, hex, URL encoding
- **Meterpreter**: msfvenom commands for elf, exe, py, php, aspx, war, jar
- Obfuscation support for evasion

### 📋 Compliance Mapping
- **OWASP Top 10 2021** — all 10 categories
- **MITRE ATT&CK** — 15 techniques across multiple tactics
- **NIST CSF** — 8 categories
- **PTES** — all 7 penetration testing phases
- Auto-mapped in reports and AI context

### ⏱️ Attack Timeline
- Automatic phase detection from commands
- **10 phases**: recon → scanning → enumeration → vuln analysis → exploitation → post-exploit → lateral → exfil → persistence → reporting
- Visual timeline in executive reports

### 🌐 Network Discovery
- Automated subnet scanning and adjacent network discovery
- **15 discovery commands**: ARP, ping sweep, port scans, SMB, SNMP, MSSQL, RDP, SSH, DNS, subdomain enum
- Smart discovery plans (basic or full depth)

### 📝 Smart Wordlist Generator
- Context-aware wordlists from target info (company name, domain, year)
- Username generation from personal info
- Mutation engine: leet speak, symbols, suffixes
- 35+ common passwords, 27 common usernames built-in

### 🤝 Collaborative Sessions
- Shared findings across parallel sessions
- Persistent state for targets, credentials, vulnerabilities
- User tracking per session

### 🔄 CVE Auto-Update
- Fetches latest CVEs from NVD API
- `/cve fetch` to download, `/cve stats` to view cache
- `/api/cve/stats` and `/api/cve/fetch` REST endpoints

### 🧬 Long-Term Memory (RAG)
- Remembers findings from all past sessions
- Keyword-based retrieval before each chat
- Avoids re-scanning known targets

### 🛡️ Safety Shield
- Blocks destructive commands (`rm -rf`, `dd if=`, etc.)
- Confirms before running scanning/exploit commands
- Safe commands (whoami, ls, ping) auto-execute

---

## Quick Start

### 1. Install

**Option A: One-Liner (Recommended for Kali)**
```bash
curl -sSL https://raw.githubusercontent.com/PORT-777/0xMrPORT777/main/install.sh | bash
```

**Option B: Manual Install**
```bash
git clone https://github.com/PORT-777/0xMrPORT777.git
cd 0xMrPORT777
chmod +x install.sh && ./install.sh
```

> 💡 **Auto-Update**: The installer checks for updates on every run and pulls the latest version automatically.

### 2. Setup API Key

```bash
cp .env.example .env
# Edit .env → add your OpenRouter API key
# Get one free at: https://openrouter.ai/keys
```

### 3. Run

```bash
# Conversational REPL
python port777.py

# Web Dashboard
python port777.py --serve

# Or with Docker
docker compose up -d
```

---

## Usage Examples

### REPL Mode
```
$ python port777.py

You: افحص 192.168.1.10
PORT-777: جاري الفحص...
[>] nmap -sV -sC 192.168.1.10
[*] Found: Port 22 (OpenSSH), Port 80 (Apache 2.4.49)
[*] Exploit suggestion: CVE-2021-41773 → msf exploit

You: جرب تدخل عليه
PORT-777: ⚡ Run: msfconsole -q -x "use exploit/multi/http/apache_normalize_path; set RHOSTS 192.168.1.10; run"
Execute? [y/n]: y
[>] Executing...
[*] Output: Session opened...
```

### Web Dashboard
```bash
python port777.py --serve
# Opens at http://localhost:7777
# Chat tab → type naturally
# Sessions tab → view past sessions
# Findings tab → targets, creds, vulns
# Graph tab → network topology with hover tooltips
```

### Slash Commands
```
/help                      → Show all commands
/sessions                  → List past sessions
/session new "recon X"     → Create parallel session
/session switch <id>       → Switch active session
/findings                  → Show findings database
/reports                   → List generated reports
/brain                     → View session brain state
/model openrouter          → Switch AI provider
/model ollama qwen2.5:7b   → Use local Ollama
/models                    → List available Ollama models
/plugins [category]        → List available plugins
/cve [fetch|stats]         → CVE auto-update from NVD
/post-exploit [category]   → Post-exploitation modules
/payload <type> <lhost>    → Generate reverse shell payload
/wordlist [target]         → Generate smart wordlist
/network-discover <ip>     → Network discovery plan
/about                     → Developer info
/reset                     → Start fresh session
/exit                      → Exit
```

---

## Architecture

```
PORT-777/
├── port777.py              # CLI entry point (REPL + --serve)
├── config.yaml             # Configuration
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── .gitignore
├── README.md
├── PROJECT_MAP.md
│
├── core/                   # Core engine (23 modules)
│   ├── assistant.py        # Conversational AI agent
│   ├── brain.py            # Session state machine
│   ├── auto_planner.py     # 3-step-ahead planning
│   ├── executor.py         # Command execution + auto-heal
│   ├── exploit_engine.py   # 118 CVE database + matching
│   ├── target_graph.py     # Network topology builder
│   ├── session_router.py   # Multi-session manager + collaboration
│   ├── memory_store.py     # Long-term memory (RAG)
│   ├── reporter.py         # Multi-format report generator
│   ├── safety.py           # Safety shield
│   ├── findings_db.py      # SQLite findings database
│   ├── knowledge_base.py   # 25+ Kali tools encyclopedia
│   ├── workflow_engine.py  # 6 pentest workflows
│   ├── parallel_executor.py # Multi-command parallelism
│   ├── context_compressor.py # Output compression
│   ├── session_manager.py  # Session save/load
│   ├── memory.py           # Session context
│   ├── plugin_manager.py   # Plugin system
│   ├── cve_updater.py      # CVE auto-update from NVD
│   ├── cve_scheduler.py    # CVE scheduler (persistent)
│   ├── post_exploit.py     # Post-exploitation automation
│   ├── payload_generator.py # Smart payload generator
│   ├── compliance_mapper.py # Compliance framework mapping
│   ├── attack_timeline.py  # Attack timeline builder
│   ├── network_discovery.py # Network discovery automation
│   └── wordlist_generator.py # Smart wordlist generator
│
├── plugins/                # Community plugins
│   ├── scanners/           # nmap_enhanced, etc.
│   ├── exploits/           # msf_exploit, etc.
│   └── post_exploit/       # enum_system, etc.
│
├── server/                 # Web UI backend (6 modules)
│   ├── main.py             # FastAPI app
│   ├── api.py              # REST endpoints (33 routes)
│   ├── ws.py               # WebSocket handler
│   ├── bridge.py           # AI session bridge
│   ├── models.py           # Pydantic schemas
│   └── ui/                 # React SPA source
│       ├── src/            # React components
│       └── vite.config.js
│
├── utils/                  # Utilities (5 modules)
│   ├── ai_client.py        # OpenRouter + Ollama client
│   ├── prompts.py          # AI system prompts
│   ├── config.py           # YAML config loader
│   ├── logger.py           # Rotating file logger
│   └── output_parser.py    # nmap/hydra/gobuster parser
│
├── templates/              # Report templates
│   └── report.html         # HTML report template
│
├── outputs/                # Generated reports
├── sessions/               # Saved sessions
├── logs/                   # Log files
└── findings.db             # SQLite database
```

---

## Configuration

### `config.yaml`
```yaml
ai:
  provider: "openrouter"      # or "ollama"
  model: "openrouter/auto"    # OpenRouter model
  ollama_url: "http://localhost:11434"
  ollama_model: "qwen2.5:7b"  # Recommended for Arabic

executor:
  default_timeout: 120
  long_running_timeout: 600

safety:
  enabled: true
  confirm_destructive: true

reporting:
  formats: ["markdown", "txt", "html", "csv"]
```

### `.env`
```
OPENROUTER_API_KEY=your_key_here
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System health |
| `/api/chat` | POST | Send message to AI |
| `/api/sessions` | GET | List saved sessions |
| `/api/sessions/{id}` | GET | Session details |
| `/api/sessions/create` | POST | Create parallel session |
| `/api/sessions/active` | GET | List active sessions |
| `/api/findings/targets` | GET | Target summary |
| `/api/findings/credentials` | GET | Discovered credentials |
| `/api/findings/vulnerabilities` | GET | Found vulnerabilities |
| `/api/reports` | GET | List reports |
| `/api/exploits/suggest` | GET | CVE suggestions |
| `/api/graph/targets` | GET | Network topology |
| `/api/brain` | GET | Session brain state |
| `/api/models` | GET | Available AI models |
| `/api/models/switch` | POST | Switch AI provider |
| `/api/plugins` | GET | List available plugins |
| `/api/plugins/{name}/run` | POST | Run a plugin |
| `/api/cve/stats` | GET | CVE cache statistics |
| `/api/cve/fetch` | POST | Fetch CVEs from NVD |
| `/api/cve/scheduler/status` | GET | Scheduler status |
| `/api/cve/scheduler/start` | POST | Start scheduler |
| `/api/cve/scheduler/stop` | POST | Stop scheduler |
| `/api/cve/scheduler/run` | POST | Run scheduler now |
| `/api/post-exploit/suggest` | GET | Post-exploit module suggestions |
| `/api/post-exploit/stats` | GET | Post-exploit statistics |
| `/api/payload/generate` | POST | Generate reverse shell payload |
| `/api/payload/generate-all` | POST | Generate all payload types |
| `/api/payload/meterpreter` | POST | Generate Meterpreter payload |
| `/api/compliance/map` | POST | Map finding to frameworks |
| `/api/compliance/report` | GET | Full compliance report |
| `/api/timeline` | GET | Attack timeline |
| `/api/network-discovery/plan` | POST | Generate discovery plan |
| `/api/network-discovery/parse` | POST | Parse discovery output |
| `/api/wordlist/generate` | POST | Generate smart wordlist |
| `/api/wordlist/usernames` | POST | Generate username list |
| `/api/sessions/{id}/share` | POST | Share finding across sessions |
| `/api/sessions/shared` | GET | Get shared findings |
| `/api/sessions/{id}/user` | POST | Set session user |
| `/ws/chat` | WebSocket | Live chat streaming |

Full Swagger docs: `http://localhost:7777/docs`

---

## Requirements

| Requirement | Version |
|-------------|---------|
| **OS** | Kali Linux (recommended) / Linux / macOS |
| **Python** | 3.10+ |
| **AI** | OpenRouter API key or Ollama (local) |
| **Node.js** | 18+ (for building React SPA) |

### Python Dependencies
```
python-dotenv>=1.0.0
requests>=2.31.0
rich>=13.0.0
pyyaml>=6.0
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
pydantic>=2.10.0
websockets>=14.0
weasyprint>=62.0
```

### Test Dependencies
```
pytest>=7.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
```

### Optional: Ollama (Local AI)
```bash
# Install Ollama: https://ollama.ai
ollama pull qwen2.5:7b    # Best for Arabic
ollama pull deepseek-r1:8b # Best for reasoning
```

---

## Exploit Coverage

| Service | CVEs | Metasploit |
|---------|------|------------|
| Apache | 4 | ✅ |
| Nginx | 6 | ✅ |
| Tomcat | 4 | ✅ |
| OpenSSH | 3 | ✅ |
| Samba/SMB | 6 | ✅ |
| MySQL | 2 | ✅ |
| PostgreSQL | 7 | ✅ |
| Redis | 2 | ✅ |
| WordPress | 11 | ✅ |
| Drupal | 2 | ✅ |
| Jenkins | 3 | ✅ |
| Docker | 5 | ✅ |
| Kubernetes | 5 | ✅ |
| Exchange | 2 | ✅ |
| WebLogic | 5 | ✅ |
| + 25 more services | 48 total | 65+ modules |

---

## License

MIT

---

## Developer

**0xMr.PORT 777**
- 📱 [Telegram](https://t.me/PB_9B)
- 💬 [WhatsApp](https://wa.me/+201026778601)
- 📸 [Instagram](https://www.instagram.com/i_c.n)

---

> ⚠️ **Disclaimer**: This tool is for authorized penetration testing only. Always obtain proper authorization before testing any system. The developer is not responsible for misuse.
