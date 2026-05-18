import os
import re
from datetime import datetime
from pathlib import Path
from utils.config import get_config


class ReportGenerator:
    def __init__(self):
        output_dir = get_config("reporting", "output_dir") or "outputs"
        self.output_dir = Path(__file__).parent.parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.include_raw = get_config("reporting", "include_raw_outputs")
        self.formats = get_config("reporting", "formats") or ["markdown", "txt"]

    def generate(self, session_id: str, objective: str, commands: list,
                 summary: str, extra_data: dict = None) -> list[str]:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename_base = f"report_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        files_created = []

        findings = self._extract_findings(commands)
        timeline = self._build_timeline(commands)
        ports = self._extract_ports(commands, extra_data)
        vulnerabilities = self._extract_vulnerabilities(commands, extra_data)
        credentials = extra_data.get("credentials", []) if extra_data else []
        targets = extra_data.get("targets", []) if extra_data else []

        from core.compliance_mapper import ComplianceMapper
        from core.attack_timeline import AttackTimeline
        compliance = ComplianceMapper().get_report_section(commands)
        attack_timeline = AttackTimeline()
        attack_timeline.add_events_from_commands(commands)

        context = {
            "timestamp": timestamp, "objective": objective, "summary": summary,
            "findings": findings, "timeline": timeline, "ports": ports,
            "vulnerabilities": vulnerabilities, "credentials": credentials,
            "targets": targets, "commands": commands,
            "session_id": session_id, "filename_base": filename_base,
            "compliance": compliance, "attack_timeline": attack_timeline
        }

        for fmt in self.formats:
            ext, content = self._render(fmt, context)
            if content is None:
                continue
            filepath = self.output_dir / f"{filename_base}{ext}"
            if isinstance(content, bytes):
                with open(filepath, "wb") as f:
                    f.write(content)
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
            files_created.append(str(filepath))

        return files_created

    def _render(self, fmt, ctx):
        if fmt == "markdown":
            return ".md", self._build_markdown(ctx)
        elif fmt == "txt":
            return ".txt", self._build_text(ctx)
        elif fmt == "html":
            return ".html", self._build_html(ctx)
        elif fmt == "csv":
            return ".csv", self._build_csv(ctx)
        elif fmt == "pdf":
            return ".pdf", self._build_pdf(ctx)
        return None, None

    def _build_pdf(self, ctx):
        html_content = self._build_html(ctx)
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes
        except ImportError:
            log.warning("weasyprint not installed. Install with: pip install weasyprint")
            return None
        except Exception as e:
            log.warning(f"PDF generation failed: {e}")
            return None

        return files_created

    def _extract_findings(self, commands):
        findings = []
        for cmd in commands:
            out = cmd.get("output", "")
            if not out:
                continue
            if "open" in out.lower() and ("port" in out.lower()):
                findings.append(("Open ports detected", out[:200]))
            if "vulnerability" in out.lower() or "cve-" in out.lower():
                findings.append(("Vulnerability found", out[:300]))
            if "password" in out.lower() or "credential" in out.lower():
                findings.append(("Credentials discovered", out[:200]))
            if "admin" in out.lower():
                findings.append(("Admin access detected", out[:200]))
        return findings

    def _build_timeline(self, commands):
        timeline = []
        for i, cmd in enumerate(commands, 1):
            timeline.append({
                "step": i,
                "command": cmd.get("command", "")[:100],
                "tool": cmd.get("tool", "unknown"),
                "status": "success" if cmd.get("output") else "error"
            })
        return timeline

    def _extract_ports(self, commands, extra_data=None):
        if extra_data and extra_data.get("ports"):
            return extra_data["ports"]
        ports = set()
        for cmd in commands:
            out = cmd.get("output", "")
            matches = re.findall(r'(\d+)/tcp\s+open', out)
            ports.update(matches)
        return sorted(ports, key=int) if ports else []

    def _extract_vulnerabilities(self, commands, extra_data=None):
        if extra_data and extra_data.get("vulnerabilities"):
            return [v.get("cve", "") for v in extra_data["vulnerabilities"] if v.get("cve")]
        vulns = []
        for cmd in commands:
            out = cmd.get("output", "")
            cves = re.findall(r'CVE-\d{4}-\d{4,7}', out, re.IGNORECASE)
            vulns.extend(cves)
        return list(set(v.upper() for v in vulns))

    def _build_markdown(self, ctx):
        timestamp, objective, summary = ctx["timestamp"], ctx["objective"], ctx["summary"]
        findings, timeline = ctx["findings"], ctx["timeline"]
        ports, vulnerabilities, credentials, targets = ctx["ports"], ctx["vulnerabilities"], ctx["credentials"], ctx["targets"]
        commands = ctx["commands"]
        lines = [
            f"# PORT-777 Penetration Test Report",
            f"",
            f"**Date:** {timestamp}",
            f"**Objective:** {objective}",
            f"**Status:** {'Completed' if summary else 'Incomplete'}",
            f"",
            f"---",
            f"",
            f"## Executive Summary",
            f"",
            f"{summary or 'No summary available.'}",
            f"",
        ]

        if targets:
            lines += ["", "## Targets", ""]
            lines.append("| IP | Hostname | OS | Ports | Credentials | Vulns |")
            lines.append("|---|---|---|---|---|---|")
            for t in targets:
                lines.append(
                    f"| {t.get('ip','')} | {t.get('hostname','')} | {t.get('os','')} "
                    f"| {t.get('port_count',0)} | {t.get('cred_count',0)} | {t.get('vuln_count',0)} |"
                )

        if ports:
            lines += ["", "## Open Ports", ""]
            if isinstance(ports[0], dict):
                lines.append("| Port | Protocol | State | Service | Version |")
                lines.append("|---|---|---|---|---|")
                for p in ports:
                    lines.append(f"| {p.get('port','')} | {p.get('protocol','tcp')} | {p.get('state','')} | {p.get('service','')} | {p.get('version','')} |")
            else:
                for p in ports:
                    lines.append(f"- Port {p}/tcp")

        if vulnerabilities:
            lines += ["", "## Vulnerabilities", ""]
            for v in vulnerabilities:
                lines.append(f"- {v}")

        if credentials:
            lines += ["", "## Discovered Credentials", ""]
            lines.append("| Target | Service | Username | Password |")
            lines.append("|---|---|---|---|")
            for c in credentials:
                lines.append(f"| {c.get('ip','')} | {c.get('service','')} | {c.get('username','')} | {c.get('password','')} |")

        if findings:
            lines += ["", "## Key Findings", ""]
            for title, detail in findings:
                lines.append(f"- **{title}**: {detail[:200]}")

        lines += ["", "## Execution Timeline", ""]
        lines.append("| Step | Tool | Command | Status |")
        lines.append("|------|------|---------|--------|")
        for t in timeline:
            lines.append(f"| {t['step']} | {t['tool']} | `{t['command']}` | {t['status']} |")

        if self.include_raw and commands:
            lines += ["", "## Raw Command Outputs", ""]
            for cmd in commands:
                lines.append(f"### `{cmd.get('command', '')}`")
                lines.append("```")
                lines.append((cmd.get("output", "") or "")[:500])
                lines.append("```")

        lines += ["", "---", "*Generated by PORT-777 AI Assistant — By 0xMr.PORT 777 | t.me/PB_9B | wa.me/+201026778601 | instagram.com/i_c.n | youtube.com/@ahmed-yasser-777 | github.com/PORT-777 | tiktok.com/@i_c.n1 | t.me/f_c_o_6*"]
        return "\n".join(lines)

    def _build_text(self, ctx):
        timestamp, objective, summary = ctx["timestamp"], ctx["objective"], ctx["summary"]
        findings, timeline = ctx["findings"], ctx["timeline"]
        ports, vulnerabilities, credentials, targets = ctx["ports"], ctx["vulnerabilities"], ctx["credentials"], ctx["targets"]
        lines = [
            "=" * 60,
            "PORT-777 PENETRATION TEST REPORT",
            "=" * 60,
            f"Date: {timestamp}",
            f"Objective: {objective}",
            "",
            "EXECUTIVE SUMMARY",
            summary or "No summary available.",
            "",
        ]

        if targets:
            lines += ["--- TARGETS ---"]
            for t in targets:
                lines.append(f"  {t.get('ip','')} ({t.get('hostname','')}) - "
                             f"Ports:{t.get('port_count',0)} Creds:{t.get('cred_count',0)} Vulns:{t.get('vuln_count',0)}")

        if ports:
            lines += ["--- OPEN PORTS ---"]
            for p in ports:
                if isinstance(p, dict):
                    lines.append(f"  {p.get('port','')}/{p.get('protocol','tcp')} {p.get('state','')} {p.get('service','')} {p.get('version','')}")
                else:
                    lines.append(f"  Port {p}/tcp")

        if vulnerabilities:
            lines += ["--- VULNERABILITIES ---"]
            for v in vulnerabilities:
                lines.append(f"  {v}")

        if credentials:
            lines += ["--- CREDENTIALS ---"]
            for c in credentials:
                lines.append(f"  {c.get('ip','')} | {c.get('service','')} | {c.get('username','')}:{c.get('password','')}")

        if findings:
            lines += ["--- FINDINGS ---"]
            for t, d in findings:
                lines.append(f"  [{t}] {d[:100]}")

        lines += ["", "--- TIMELINE ---"]
        for t in timeline:
            lines.append(f"  [{t['step']}] {t['tool']}: {t['command']} -> {t['status']}")

        lines += ["", "=" * 60, "Generated by PORT-777 AI Assistant — By 0xMr.PORT 777 | t.me/PB_9B | wa.me/+201026778601 | instagram.com/i_c.n | github.com/PORT-777 | youtube.com/@ahmed-yasser-777 | tiktok.com/@i_c.n1 | t.me/f_c_o_6"]
        return "\n".join(lines)

    def _build_html(self, ctx):
        template_path = Path(__file__).parent.parent / "templates" / "report.html"
        if not template_path.exists():
            return "<html><body><h1>PORT-777 Report</h1><p>Template not found.</p></body></html>"
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        def severity_badge(s):
            s = str(s).lower()
            if s == "critical": return '<span class="badge badge-open">CRITICAL</span>'
            if s == "high": return '<span class="badge badge-open">HIGH</span>'
            return f'<span class="badge badge-closed">{s}</span>'

        summary_box = f'<div class="summary-box">{self._esc(ctx["summary"]) or "No summary."}</div>' if ctx["summary"] else ""
        html = html.replace("{{SUMMARY_SECTION}}",
            f"<h2>Executive Summary</h2>{summary_box}" if summary_box else "")

        targets_html = ""
        if ctx["targets"]:
            rows = "".join(
                f"<tr><td>{t.get('ip','')}</td><td>{t.get('hostname','')}</td>"
                f"<td>{t.get('os','')}</td><td>{t.get('port_count',0)}</td>"
                f"<td>{t.get('cred_count',0)}</td><td>{t.get('vuln_count',0)}</td></tr>"
                for t in ctx["targets"]
            )
            targets_html = f"<h2>Targets</h2><table><thead><tr><th>IP</th><th>Hostname</th><th>OS</th><th>Ports</th><th>Creds</th><th>Vulns</th></tr></thead><tbody>{rows}</tbody></table>"
        html = html.replace("{{TARGETS_SECTION}}", targets_html)

        ports_html = ""
        if ctx["ports"]:
            if isinstance(ctx["ports"][0], dict):
                rows = "".join(
                    f"<tr><td>{p.get('port','')}/{p.get('protocol','tcp')}</td><td>{p.get('state','')}</td><td>{p.get('service','')}</td><td>{p.get('version','')}</td></tr>"
                    for p in ctx["ports"]
                )
                ports_html = f"<h2>Open Ports</h2><table><thead><tr><th>Port</th><th>State</th><th>Service</th><th>Version</th></tr></thead><tbody>{rows}</tbody></table>"
            else:
                rows = "".join(f"<tr><td>Port {p}/tcp</td></tr>" for p in ctx["ports"])
                ports_html = f"<h2>Open Ports</h2><table><thead><tr><th>Port</th></tr></thead><tbody>{rows}</tbody></table>"
        html = html.replace("{{PORTS_SECTION}}", ports_html)

        vulns_html = ""
        if ctx["vulnerabilities"]:
            rows = "".join(
                f"<tr><td>{v.get('ip','')}</td><td class='code'>{v.get('cve','')}</td><td>{severity_badge(v.get('severity',''))}</td><td>{v.get('port','-')}</td></tr>"
                if isinstance(v, dict) else
                f"<tr><td colspan='4' class='code'>{v}</td></tr>"
                for v in ctx["vulnerabilities"]
            )
            vulns_html = f"<h2>Vulnerabilities</h2><table><thead><tr><th>Target</th><th>CVE</th><th>Severity</th><th>Port</th></tr></thead><tbody>{rows}</tbody></table>"
        html = html.replace("{{VULNERABILITIES_SECTION}}", vulns_html)

        creds_html = ""
        if ctx["credentials"]:
            rows = "".join(
                f"<tr><td>{c.get('ip','')}</td><td>{c.get('service','')}</td><td class='code'>{c.get('username','')}</td><td class='code'>{c.get('password','')}</td></tr>"
                for c in ctx["credentials"]
            )
            creds_html = f"<h2>Discovered Credentials</h2><table><thead><tr><th>Target</th><th>Service</th><th>Username</th><th>Password</th></tr></thead><tbody>{rows}</tbody></table>"
        html = html.replace("{{CREDENTIALS_SECTION}}", creds_html)

        findings_html = ""
        if ctx["findings"]:
            items = "".join(
                f'<div class="finding-item"><strong>{self._esc(t)}</strong><br>{self._esc(d[:200])}</div>'
                for t, d in ctx["findings"]
            )
            findings_html = f"<h2>Key Findings</h2>{items}"
        html = html.replace("{{FINDINGS_SECTION}}", findings_html)

        timeline_html = "<h2>Execution Timeline</h2>"
        if ctx["timeline"]:
            steps = "".join(
                f'<div class="timeline-step"><span class="step-num">{t["step"]}</span>'
                f'<span class="code">{t["command"]}</span> '
                f'<span class="badge badge-{t["status"]}">{t["status"]}</span>'
                f'<span style="color:#666;margin-left:8px">{t["tool"]}</span></div>'
                for t in ctx["timeline"]
            )
            timeline_html += steps
        html = html.replace("{{TIMELINE_SECTION}}", timeline_html)

        html = html.replace("{{DATE}}", self._esc(ctx["timestamp"]))
        html = html.replace("{{OBJECTIVE}}", self._esc(ctx["objective"][:80]))
        duration = ""
        if ctx["commands"]:
            ts = ctx["commands"][0].get("timestamp", "")
            duration = f"{len(ctx['commands'])} commands"
        html = html.replace("{{DURATION}}", duration)
        return html

    def _build_csv(self, ctx):
        lines = ["PORT-777 Pentest Report", f"Date,{ctx['timestamp']}", f"Objective,{ctx['objective']}", "", "Targets,IP,Hostname,OS,Ports,Credentials,Vulns"]
        for t in ctx["targets"]:
            lines.append(f"Target,{t.get('ip','')},{t.get('hostname','')},{t.get('os','')},{t.get('port_count',0)},{t.get('cred_count',0)},{t.get('vuln_count',0)}")
        lines += ["", "Credentials,Target,Service,Username,Password"]
        for c in ctx["credentials"]:
            lines.append(f"Cred,{c.get('ip','')},{c.get('service','')},{c.get('username','')},{c.get('password','')}")
        lines += ["", "Vulnerabilities,Target,CVE,Severity,Port"]
        for v in ctx["vulnerabilities"]:
            if isinstance(v, dict):
                lines.append(f"Vuln,{v.get('ip','')},{v.get('cve','')},{v.get('severity','')},{v.get('port','')}")
            else:
                lines.append(f"Vuln,,{v},,")
        return "\n".join(lines)

    def _esc(self, text):
        if not text:
            return ""
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
