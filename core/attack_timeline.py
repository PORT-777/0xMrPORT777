import json
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

log = get_logger("attack_timeline")

PHASE_ORDER = [
    "reconnaissance",
    "scanning",
    "enumeration",
    "vulnerability_analysis",
    "exploitation",
    "post_exploitation",
    "lateral_movement",
    "data_exfiltration",
    "persistence",
    "reporting"
]

PHASE_INDICATORS = {
    "reconnaissance": ["whois", "dns", "subfinder", "amass", "theharvester", "shodan", "osint", "recon"],
    "scanning": ["nmap", "masscan", "rustscan", "scan", "port", "service"],
    "enumeration": ["enum", "gobuster", "dirb", "dirbuster", "nikto", "wfuzz", "ffuf", "smbclient", "snmp"],
    "vulnerability_analysis": ["vuln", "cve", "nessus", "openvas", "nuclei", "vulnerability"],
    "exploitation": ["exploit", "metasploit", "msfconsole", "payload", "shell", "rce", "injection", "bypass"],
    "post_exploitation": ["privilege", "escalation", "privesc", "sudo", "suid", "hash", "dump", "credential"],
    "lateral_movement": ["lateral", "pivot", "psexec", "ssh", "winrm", "smb", "pass-the-hash"],
    "data_exfiltration": ["exfil", "download", "upload", "transfer", "dump", "extract", "copy"],
    "persistence": ["cron", "systemd", "scheduled", "registry", "ssh key", "backdoor", "persistence"],
    "reporting": ["report", "export", "generate", "summary", "findings"],
}


class AttackTimeline:
    """Builds and manages attack timeline from session history."""

    def __init__(self):
        self.events = []
        self.phase_order = PHASE_ORDER
        self.indicators = PHASE_INDICATORS

    def add_event(self, command, output="", tool="", phase=None, timestamp=None, status="success"):
        if not phase:
            phase = self._detect_phase(command, output)

        event = {
            "id": len(self.events) + 1,
            "timestamp": timestamp or datetime.now().isoformat(),
            "phase": phase,
            "command": command[:200],
            "tool": tool or self._extract_tool(command),
            "output_summary": output[:100] if output else "",
            "status": status,
            "findings": self._extract_findings(output),
        }
        self.events.append(event)
        return event

    def add_events_from_commands(self, commands):
        for cmd in commands:
            self.add_event(
                command=cmd.get("command", ""),
                output=cmd.get("output", ""),
                tool=cmd.get("tool", ""),
                timestamp=cmd.get("timestamp"),
                status="success" if cmd.get("output") else "error"
            )

    def get_timeline(self):
        return sorted(self.events, key=lambda x: x["timestamp"])

    def get_phase_summary(self):
        summary = {}
        for event in self.events:
            phase = event["phase"]
            if phase not in summary:
                summary[phase] = {"count": 0, "tools": set(), "findings": 0, "first": event["timestamp"], "last": event["timestamp"]}
            summary[phase]["count"] += 1
            summary[phase]["tools"].add(event["tool"])
            summary[phase]["findings"] += len(event.get("findings", []))
            summary[phase]["last"] = event["timestamp"]
        for phase in summary:
            summary[phase]["tools"] = list(summary[phase]["tools"])
        return summary

    def get_attack_path(self):
        phases_seen = []
        for event in self.events:
            if event["phase"] not in phases_seen:
                phases_seen.append(event["phase"])
        ordered = [p for p in self.phase_order if p in phases_seen]
        return ordered

    def export_json(self, filepath=None):
        data = {
            "generated": datetime.now().isoformat(),
            "total_events": len(self.events),
            "phases": self.get_attack_path(),
            "events": self.get_timeline()
        }
        if filepath:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        return data

    def format_for_prompt(self):
        if not self.events:
            return ""
        summary = self.get_phase_summary()
        lines = ["**Attack Timeline:**"]
        for phase in self.phase_order:
            if phase in summary:
                s = summary[phase]
                lines.append(f"  [{phase.replace('_', ' ').title()}] {s['count']} events, tools: {', '.join(s['tools'][:3])}, findings: {s['findings']}")
        return "\n".join(lines)

    def _detect_phase(self, command, output):
        text = f"{command} {output}".lower()
        for phase in self.phase_order:
            indicators = self.indicators.get(phase, [])
            if any(ind in text for ind in indicators):
                return phase
        return "scanning"

    def _extract_tool(self, command):
        if not command:
            return "unknown"
        parts = command.split()
        return parts[0] if parts else "unknown"

    def _extract_findings(self, output):
        findings = []
        if not output:
            return findings
        import re
        cves = re.findall(r'CVE-\d{4}-\d{4,7}', output, re.IGNORECASE)
        findings.extend([{"type": "cve", "value": c.upper()} for c in cves])
        ports = re.findall(r'(\d+)/tcp\s+open', output)
        findings.extend([{"type": "open_port", "value": p} for p in ports])
        return findings
