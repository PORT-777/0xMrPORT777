import json
import os
import re
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

log = get_logger("brain")


class SessionBrain:
    """
    Maintains structured state about the current penetration test session.
    Tracks targets, ports, credentials, vulnerabilities, and priority queue.
    Updates automatically after each command.
    """

    def __init__(self, brain_path=None):
        if brain_path is None:
            brain_path = Path(__file__).parent.parent / "brain_state.json"
        self.path = str(brain_path)
        self.state = self._default_state()
        self._load()

    def _default_state(self):
        return {
            "session_id": "",
            "objective": "",
            "targets": {},
            "credentials": [],
            "vulnerabilities": [],
            "priority_queue": [],
            "completed_actions": [],
            "failed_actions": [],
            "command_history": [],
            "phase": "initial",
            "started_at": "",
            "updated_at": ""
        }

    def start(self, session_id, objective):
        self.state = self._default_state()
        self.state["session_id"] = session_id
        self.state["objective"] = objective
        self.state["started_at"] = datetime.now().isoformat()
        self.state["phase"] = "recon"
        self._save()

    def update_after_command(self, command, output):
        now = datetime.now().isoformat()
        self.state["updated_at"] = now
        self.state["command_history"].append({
            "command": command[:200],
            "timestamp": now
        })

        if not output:
            self.state["failed_actions"].append(command[:100])
            return

        self.state["completed_actions"].append(command[:100])
        self._extract_targets(output)
        self._extract_ports(output)
        self._extract_credentials(output, command)
        self._extract_vulnerabilities(output)
        self._update_priority_queue(command, output)
        self._update_phase()
        self._save()

    def _extract_targets(self, output):
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        domains = re.findall(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b', output)
        for ip in ips:
            if ip.startswith("127.") or ip.startswith("0."):
                continue
            if ip not in self.state["targets"]:
                self.state["targets"][ip] = {
                    "ports": {},
                    "services": [],
                    "os": "",
                    "hostname": "",
                    "status": "discovered",
                    "first_seen": datetime.now().isoformat()
                }
        for d in domains:
            if d in ("localhost", "localdomain"):
                continue
            for ip in ips:
                if ip in self.state["targets"]:
                    if not self.state["targets"][ip].get("hostname"):
                        self.state["targets"][ip]["hostname"] = d

    def _extract_ports(self, output):
        port_pattern = re.compile(r'(\d+)/(tcp|udp)\s+(open|filtered|closed)\s+(\S+)\s*(.*)')
        for match in port_pattern.finditer(output):
            port_num = int(match.group(1))
            protocol = match.group(2)
            state = match.group(3)
            service = match.group(4)
            version = match.group(5).strip() if match.group(5) else ""

            if state != "open":
                continue

            for ip in self.state["targets"]:
                if port_num not in self.state["targets"][ip]["ports"]:
                    self.state["targets"][ip]["ports"][port_num] = {
                        "protocol": protocol,
                        "state": state,
                        "service": service,
                        "version": version,
                        "found_at": datetime.now().isoformat()
                    }
                    svc_str = f"{port_num}/{protocol} ({service})"
                    if svc_str not in self.state["targets"][ip]["services"]:
                        self.state["targets"][ip]["services"].append(svc_str)

    def _extract_credentials(self, output, command):
        hydra_pattern = re.compile(r'\[(\d+)\]\[(\w+)\]\s+host:\s+(\S+)\s+login:\s+(\S+)\s+password:\s+(\S+)')
        for match in hydra_pattern.finditer(output):
            self.state["credentials"].append({
                "host": match.group(3),
                "port": match.group(1),
                "service": match.group(2),
                "username": match.group(4),
                "password": match.group(5),
                "source": command[:50],
                "found_at": datetime.now().isoformat()
            })

    def _extract_vulnerabilities(self, output):
        cves = re.findall(r'CVE-\d{4}-\d{4,7}', output, re.IGNORECASE)
        for cve in cves:
            cve_upper = cve.upper()
            if not any(v["cve"] == cve_upper for v in self.state["vulnerabilities"]):
                self.state["vulnerabilities"].append({
                    "cve": cve_upper,
                    "severity": "unknown",
                    "source": "scan",
                    "found_at": datetime.now().isoformat()
                })

    def _update_priority_queue(self, command, output):
        self.state["priority_queue"] = []
        targets_with_ports = [ip for ip, t in self.state["targets"].items() if t["ports"]]
        targets_without_ports = [ip for ip, t in self.state["targets"].items() if not t["ports"]]

        web_services = {80, 443, 8080, 8443, 81, 3000, 5000, 8000, 8888}
        for ip, t in self.state["targets"].items():
            open_ports = set(t["ports"].keys())
            if open_ports & web_services:
                self.state["priority_queue"].append({
                    "target": ip,
                    "priority": "high",
                    "reason": f"Web services detected",
                    "ports": sorted(open_ports & web_services)
                })
            if any("ssh" in p.get("service", "").lower() for p in t["ports"].values()):
                self.state["priority_queue"].append({
                    "target": ip,
                    "priority": "medium",
                    "reason": "SSH service - potential brute force target",
                    "ports": [22]
                })

        for ip in targets_with_ports[:3]:
            ports = list(self.state["targets"][ip]["ports"].keys())[:5]
            svcs = [self.state["targets"][ip]["ports"][p].get("service", "") for p in ports]
            if svcs:
                self.state["priority_queue"].append({
                    "target": ip,
                    "priority": "medium",
                    "reason": f"Services: {', '.join(filter(None, svcs))}",
                    "ports": ports[:5]
                })

    def _update_phase(self):
        ports_found = sum(1 for t in self.state["targets"].values() if t["ports"])
        creds_found = len(self.state["credentials"])
        vulns_found = len(self.state["vulnerabilities"])

        if vulns_found > 0 or creds_found > 0:
            self.state["phase"] = "exploitation"
        elif ports_found > 0:
            self.state["phase"] = "enumeration"
        else:
            self.state["phase"] = "recon"

    def get_open_ports_summary(self):
        result = []
        for ip, t in self.state["targets"].items():
            if t["ports"]:
                ports_str = ", ".join(f"{p}/{t['ports'][p]['protocol']} ({t['ports'][p]['service']})"
                                      for p in sorted(t["ports"].keys()))
                result.append(f"{ip}: {ports_str}")
        return "\n".join(result) if result else "No open ports found yet."

    def get_priority_summary(self):
        if not self.state["priority_queue"]:
            return "No pending high-priority actions."
        lines = []
        for item in self.state["priority_queue"][:5]:
            lines.append(f"[{item['priority'].upper()}] {item['target']}: {item['reason']}")
        return "\n".join(lines)

    def get_state_summary(self):
        targets_count = len(self.state["targets"])
        ports_count = sum(len(t["ports"]) for t in self.state["targets"].values())
        creds_count = len(self.state["credentials"])
        vulns_count = len(self.state["vulnerabilities"])
        cmds_count = len(self.state["command_history"])
        return (
            f"Phase: {self.state['phase']} | "
            f"Targets: {targets_count} | Ports: {ports_count} | "
            f"Credentials: {creds_count} | Vulns: {vulns_count} | "
            f"Commands: {cmds_count}"
        )

    def format_for_prompt(self):
        """Format brain state as a compact prompt addition."""
        lines = ["## Current Session State", ""]
        lines.append(self.get_state_summary())
        lines.append("")
        if self.state["targets"]:
            lines.append("### Targets & Open Ports")
            for ip, t in self.state["targets"].items():
                if t["ports"]:
                    ports_str = ", ".join(
                        f"{p}/{d['protocol']}({d['service']})"
                        for p, d in sorted(t["ports"].items())
                    )
                    lines.append(f"- {ip}: {ports_str}")
                else:
                    lines.append(f"- {ip}: (no open ports yet)")
            lines.append("")
        if self.state["credentials"]:
            lines.append(f"### Credentials Found: {len(self.state['credentials'])}")
            for c in self.state["credentials"][-5:]:
                lines.append(f"- {c.get('host','')} | {c.get('username','')}:{c.get('password','')}")
            lines.append("")
        if self.state["vulnerabilities"]:
            lines.append(f"### Vulnerabilities: {len(self.state['vulnerabilities'])}")
            for v in self.state["vulnerabilities"][-5:]:
                lines.append(f"- {v['cve']}")
            lines.append("")
        if self.state["priority_queue"]:
            lines.append("### Recommended Next Actions")
            for p in self.state["priority_queue"][:3]:
                lines.append(f"- [{p['priority'].upper()}] {p['reason']} on {p['target']}")
            lines.append("")
        return "\n".join(lines)

    def save_as(self, filepath=None):
        p = filepath or self.path
        os.makedirs(os.path.dirname(p) if os.path.dirname(p) else ".", exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)
        log.info(f"Brain saved to {p}")

    def _save(self):
        try:
            self.save_as(self.path)
        except Exception as e:
            log.warning(f"Brain save failed: {e}")

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.state[k] = v
                log.info("Brain state loaded from disk")
            except Exception:
                pass
