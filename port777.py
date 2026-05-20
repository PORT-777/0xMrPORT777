#!/usr/bin/env python3
"""
PORT-777 V1 — Hunting Loop + AI + Approval
Every command requires y/n approval, unless input ends with -y.
Usage: python port777.py
"""
import sys, os, re, signal, json, time
from pathlib import Path
sys.path.append(os.path.dirname(__file__))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt

console = Console()

_is_windows = os.name == "nt"
if _is_windows:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BANNER = """[bold red]
  ██████╗  ██████╗ ██████╗ ████████╗    ███████╗███████╗███████╗
  ██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝    ╚════██║╚════██║╚════██║
  ██████╔╝██║   ██║██████╔╝   ██║           ██╔╝    ██╔╝    ██╔╝
  ██╔═══╝ ██║   ██║██╔══██╗   ██║          ██╔╝    ██╔╝    ██╔╝
  ██║     ╚██████╔╝██║  ██║   ██║          ██║     ██║     ██║
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝          ╚═╝     ╚═╝     ╚═╝[/bold red]
  [bold cyan]PORT-777 V1 — Kali Linux AI Assistant[/bold cyan]
  [dim]Every command needs approval. Add -y to auto-approve all.[/dim]
  [dim]By 0xMr.PORT 777[/dim]"""


def box_style():
    return box.ASCII if _is_windows else box.SIMPLE


def slash_command(cmd, args, assistant=None):
    if cmd in ("exit", "quit", "bye"):
        console.print("[yellow]Peace. ✌[/yellow]")
        return False

    if cmd in ("help", "h", "?"):
        help_table = Table(show_header=True, header_style="bold cyan", box=box_style())
        help_table.add_column("Command", style="bold yellow")
        help_table.add_column("Description")
        help_table.add_row("/help or /h", "show this help")
        help_table.add_row("/sessions", "list past sessions")
        help_table.add_row("/session <id>", "view session details")
        help_table.add_row("/findings", "show findings database")
        help_table.add_row("/reports", "list reports")
        help_table.add_row("/brain", "view current session brain state")
        help_table.add_row("/about", "developer info & links")
        help_table.add_row("/model <openrouter|ollama> [model_name]", "switch AI provider/model")
        help_table.add_row("/models", "list available Ollama models")
        help_table.add_row("/reset", "start fresh session")
        help_table.add_row("/exit or /quit", "exit PORT-777")
        help_table.add_row("", "")
        help_table.add_row("Any text", "AI picks tools and runs them")
        help_table.add_row("-y at end", "auto-approve all commands")
        console.print(help_table)
        return True

    if cmd == "sessions":
        try:
            from core.session_manager import SessionManager
            sm = SessionManager()
            sessions = sm.list_sessions()
            if not sessions:
                console.print("[yellow]No saved sessions.[/yellow]")
                return True
            t = Table(title="Sessions", header_style="bold cyan", box=box_style())
            t.add_column("ID", style="dim")
            t.add_column("Objective")
            t.add_column("Status")
            t.add_column("Date")
            for s in sessions[:20]:
                t.add_row(s["id"], s["objective"][:50], s["status"],
                          s["timestamp"][:19] if s["timestamp"] else "N/A")
            console.print(t)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        return True

    if cmd == "session" and args:
        try:
            from core.session_manager import SessionManager
            sm = SessionManager()
            data = sm.load(args[0])
            if not data:
                console.print(f"[red]Session '{args[0]}' not found.[/red]")
                return True
            console.print(Panel(f"[bold]Objective:[/bold] {data.get('objective', 'N/A')}"))
            console.print(f"[dim]Status:[/dim] {data.get('status', 'N/A')}")
            targets = data.get("targets", [])
            if targets:
                console.print(f"[dim]Targets:[/dim] {', '.join(targets[:5])}")
            cmds = data.get("commands", [])
            if cmds:
                console.print(f"\n[bold]Commands ({len(cmds)}):[/bold]")
                for c in cmds[:10]:
                    console.print(f"  [{c.get('step','?')}] {c.get('command','')[:120]}")
            if data.get("summary"):
                console.print(f"\n[bold]Summary:[/bold] {data['summary'][:500]}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        return True

    if cmd == "reports":
        reports_dir = Path(__file__).parent / "outputs"
        if not reports_dir.exists():
            console.print("[yellow]No reports.[/yellow]")
            return True
        files = sorted(reports_dir.glob("*"), key=os.path.getmtime, reverse=True)
        if not files:
            console.print("[yellow]No reports.[/yellow]")
            return True
        t = Table(title="Reports", header_style="bold cyan", box=box_style())
        t.add_column("File")
        t.add_column("Size")
        t.add_column("Date")
        for f in files[:15]:
            size = f.stat().st_size
            from datetime import datetime
            t.add_row(f.name, f"{size}B" if size < 1024 else f"{size//1024}KB",
                      datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M"))
        console.print(t)
        return True

    if cmd == "findings":
        try:
            from core.findings_db import FindingsDB
            db = FindingsDB()
            targets = db.get_target_summary()
            if not targets:
                console.print("[yellow]No findings yet.[/yellow]")
                return True
            console.print("[bold]Targets:[/bold]")
            t = Table(header_style="bold cyan", box=box_style())
            t.add_column("IP")
            t.add_column("Hostname")
            t.add_column("OS")
            t.add_column("Ports")
            t.add_column("Creds")
            t.add_column("Vulns")
            for tg in targets:
                t.add_row(tg.get("ip", ""), str(tg.get("hostname", ""))[:20],
                          str(tg.get("os", ""))[:15], str(tg.get("port_count", 0)),
                          str(tg.get("cred_count", 0)), str(tg.get("vuln_count", 0)))
            console.print(t)
            creds = db.get_all_credentials()
            if creds:
                console.print("\n[bold]Credentials:[/bold]")
                c = Table(header_style="bold cyan", box=box_style())
                c.add_column("Target")
                c.add_column("Service")
                c.add_column("Username")
                c.add_column("Password")
                for cr in creds[:10]:
                    c.add_row(cr.get("ip", ""), cr.get("service", ""),
                              cr.get("username", ""), cr.get("password", ""))
                console.print(c)
            vulns = db.get_all_vulnerabilities()
            if vulns:
                console.print("\n[bold]Vulnerabilities:[/bold]")
                v = Table(header_style="bold cyan", box=box_style())
                v.add_column("Target")
                v.add_column("CVE")
                v.add_column("Severity")
                for vu in vulns[:10]:
                    v.add_row(vu.get("ip", ""), vu.get("cve", ""), vu.get("severity", ""))
                console.print(v)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        return True

    if cmd == "brain":
        try:
            from core.brain import SessionBrain
            brain = SessionBrain()
            console.print(Panel(brain.get_state_summary(), title="Session Brain"))
            console.print(f"\n[bold]Targets & Ports:[/bold]")
            console.print(brain.get_open_ports_summary() or "No data")
            console.print(f"\n[bold]Priority Queue:[/bold]")
            console.print(brain.get_priority_summary() or "No priorities")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        return True

    if cmd == "about":
        console.print(Panel(
            "[bold]PORT-777 V1 — Kali Linux AI Assistant[/bold]\n\n"
            "[bold]Developer:[/bold] 0xMr.PORT 777\n"
            "[bold]Telegram:[/bold] https://t.me/PB_9B\n"
            "[bold]WhatsApp:[/bold] https://wa.me/+201026778601\n"
            "[bold]Instagram:[/bold] https://www.instagram.com/i_c.n\n"
            "[bold]YouTube:[/bold] https://youtube.com/@ahmed-yasser-777\n"
            "[bold]GitHub:[/bold] https://github.com/PORT-777\n"
            "[bold]TikTok:[/bold] https://www.tiktok.com/@i_c.n1\n"
            "[bold]Telegram Channel:[/bold] https://t.me/f_c_o_6\n\n"
            "[dim]Open-source AI penetration testing assistant.[/dim]",
            title="ℹ About", box=box_style()
        ))
        return True

    if cmd == "models":
        if not assistant:
            console.print("[red]No active session.[/red]")
            return True
        models = assistant.ai.list_local_models()
        if not models:
            console.print("[yellow]Ollama not running or no models found. Start Ollama first.[/yellow]")
            return True
        console.print("[bold]Available Ollama models:[/bold]")
        for m in models:
            console.print(f"  {m}")
        return True

    if cmd == "model" and args:
        provider = args[0].lower()
        model_name = args[1] if len(args) > 1 else None
        if not assistant:
            console.print("[red]No active session.[/red]")
            return True
        ok, msg = assistant.switch_model(provider, model_name)
        if ok:
            console.print(f"[green]{msg}[/green]")
        else:
            console.print(f"[red]{msg}[/red]")
        return True

    if cmd == "plugins":
        from core.plugin_manager import get_plugin_manager
        pm = get_plugin_manager()
        cat = args[0] if args else None
        plugins = pm.list_plugins(category=cat)
        if not plugins:
            console.print("[yellow]No plugins found.[/yellow]")
            return True
        console.print(f"[bold]Plugins ({len(plugins)}):[/bold]")
        for p in plugins:
            console.print(f"  {p['category']}/{p['name']} v{p['version']} — {p['description']}")
        return True

    if cmd == "cve":
        from core.cve_updater import get_cve_updater
        updater = get_cve_updater()
        action = args[0].lower() if args else "stats"
        if action == "fetch":
            console.print("[yellow]Fetching CVEs from NVD API...[/yellow]")
            cves = updater.fetch_recent()
            console.print(f"[green]Fetched {len(cves)} CVEs.[/green]")
            for c in cves[:10]:
                console.print(f"  [{c['severity'].upper()}] {c['cve']} — {c['desc'][:80]}")
        elif action == "stats":
            stats = updater.get_stats()
            console.print(f"[bold]CVE Cache:[/bold] {stats['total']} entries")
            console.print(f"[bold]Last updated:[/bold] {stats['last_updated']}")
            console.print(f"[bold]By severity:[/bold] {stats['by_severity']}")
        elif action == "schedule":
            from core.cve_scheduler import get_cve_scheduler
            scheduler = get_cve_scheduler()
            sub = args[1].lower() if len(args) > 1 else "status"
            if sub == "start":
                interval = int(args[2]) if len(args) > 2 else 24
                scheduler.interval_hours = interval
                ok = scheduler.start()
                console.print(f"[green]CVE scheduler started (every {interval}h)[/green]" if ok else "[yellow]Already running[/yellow]")
            elif sub == "stop":
                scheduler.stop()
                console.print("[yellow]CVE scheduler stopped[/yellow]")
            elif sub == "run":
                result = scheduler.run_once()
                if result.get("success"):
                    console.print(f"[green]Fetched {result['count']} CVEs[/green]")
                else:
                    console.print(f"[red]Error: {result.get('error')}[/red]")
            else:
                status = scheduler.get_status()
                console.print(f"[bold]CVE Scheduler Status:[/bold]")
                console.print(f"  Running: {'Yes' if status['running'] else 'No'}")
                console.print(f"  Interval: {status['interval_hours']}h")
                console.print(f"  Last run: {status['last_run'] or 'never'}")
                console.print(f"  Runs: {status['run_count']}")
                if status['recent_errors']:
                    console.print(f"  Errors: {len(status['recent_errors'])}")
        return True

    if cmd == "reset" and assistant:
        assistant.__init__()
        console.print("[green]Session reset.[/green]")
        return True

    console.print(f"[red]Unknown: /{cmd}[/red]")
    return True


def main():
    console.print(Panel(BANNER, box=box_style()))
    console.print("[dim]Write anything. Add [bold]-y[/bold] at end to auto-approve all commands. /help for commands.[/dim]\n")

    from core.assistant import KaliAssistant
    assistant = KaliAssistant()

    hunting = True
    phase_names = ["Reconnaissance", "Vulnerability Scan", "Exploitation", "AI Attack", "Reporting"]
    current_phase = 0

    while True:
        try:
            if hunting:
                phase_name = phase_names[current_phase % len(phase_names)]
                console.print(f"[dim]Phase {current_phase + 1}: {phase_name} | Iteration {current_phase // len(phase_names) + 1}[/dim]")

            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")

        except (EOFError, KeyboardInterrupt):
            print()
            if hunting:
                console.print("[yellow]Hunting paused. Type anything to resume or /exit to quit.[/yellow]")
                hunting = False
                continue
            console.print("[yellow]Peace. ✌[/yellow]")
            break

        if not user_input or not user_input.strip():
            continue

        hunting = True

        # Handle slash commands
        if user_input.startswith("/"):
            parts = user_input[1:].strip().split(None, 1)
            cmd = parts[0].lower()
            args = parts[1].split() if len(parts) > 1 else []
            if cmd in ("exit", "quit", "bye"):
                console.print("[yellow]Peace. ✌[/yellow]")
                break
            slash_command(cmd, args, assistant)
            continue

        # Check for -y flag (auto-approve)
        words = user_input.strip().split()
        auto_approve = words[-1] == "-y" if words else False
        if auto_approve:
            user_input = " ".join(words[:-1])

        # Process through hunting loop
        iteration = 0
        max_iter = 20
        current_input = user_input

        while iteration <= max_iter:
            try:
                resp_type, data = assistant.chat(current_input, auto_approve=auto_approve)
            except KeyboardInterrupt:
                print()
                console.print("[red]Cancelled.[/red]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                import traceback; traceback.print_exc()
                break

            if resp_type == "answer":
                content = data.get("content", "")
                console.print(f"[bold green]PORT-777[/bold green] {content[:800]}")
                current_phase += 1
                break

            elif resp_type == "pending":
                cmd = data.get("command", "")
                reason = data.get("reason", "")
                if reason:
                    console.print(f"[bold]AI:[/bold] {reason}")
                console.print(f"[bold yellow]Command:[/bold yellow] {cmd}")

                if auto_approve:
                    approved = True
                else:
                    ans = Prompt.assemble(
                        ("[cyan]Execute? (Y/n): [/cyan]", ""),
                        default="y"
                    )
                    approved = ans.lower() in ("y", "yes", "")

                if approved:
                    resp_type, data = assistant.execute_from_pending(data)

                    if resp_type == "command":
                        output = data.get("output", "")
                        cmd = data.get("command", "")
                        if output:
                            out_text = output[:800]
                            lines = out_text.split('\n')
                            if len(lines) > 12:
                                out_text = '\n'.join(lines[:12]) + f"\n... ({len(lines)-12} more lines)"
                            console.print(Panel(out_text, title="Output", box=box_style()))
                        if cmd:
                            console.print(f"[dim]{cmd[:100]}[/dim]")
                        current_phase += 1
                        # Auto-continue
                        iteration += 1
                        current_input = "continue"
                        time.sleep(2)
                        continue
                    elif resp_type == "answer":
                        console.print(f"[bold green]PORT-777[/bold green] {data.get('content', '')[:800]}")
                        break
                    elif resp_type == "summary":
                        console.print(f"[bold green]✓ {data['summary']}[/bold green]")
                        hunting = False
                        break
                else:
                    console.print("[yellow]Skipped.[/yellow]")
                    current_phase += 1
                    # Still continue to get next command
                    iteration += 1
                    current_input = "continue"
                    time.sleep(2)
                    continue

            elif resp_type == "summary":
                console.print(f"[bold green]✓ {data['summary']}[/bold green]")
                console.print("[dim]Objective complete. Type something new to start again.[/dim]")
                hunting = False
                break

            else:
                break

        print()


if __name__ == "__main__":
    if _is_windows:
        signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    main()
