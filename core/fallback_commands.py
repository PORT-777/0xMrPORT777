import re


KNOWN_TOOLS = [
    "nmap", "masscan", "rustscan", "nikto", "whatweb", "wpscan",
    "gobuster", "dirb", "ffuf", "sqlmap", "hydra", "medusa",
    "john", "hashcat", "msfconsole", "msfvenom", "searchsploit",
    "theharvester", "sherlock", "holehe", "whois", "dnsrecon",
    "dig", "nslookup", "tcpdump", "tshark", "netcat", "nc",
    "curl", "wget", "python3", "python", "ping", "traceroute",
    "ls", "whoami", "id", "ifconfig", "ip", "ss", "ps",
    "df", "uname", "cat", "grep", "find", "apt", "systemctl",
    "chmod", "mkdir", "touch", "rm", "cp", "mv", "echo",
    "sudo", "docker", "ssh", "scp", "nuclei", "wafw00f",
    "dmitry", "recon-ng", "sublist3r", "amass", "enum4linux",
    "smbclient", "smbmap", "rdp-sec-check", "ike-scan",
    "snmpwalk", "onesixtyone", "dnsenum", "fierce", "lbd",
    "wafw00f", "xsstrike", "commix", "jwt_tool",
]


def is_direct_command(text):
    first_word = text.strip().split()[0].lower() if text.strip() else ""
    return first_word in KNOWN_TOOLS


PHASES = {
    0: {
        "name": "Reconnaissance",
        "commands": [
            {"cmd": "whatweb {target}", "desc": "Web tech reconnaissance"},
            {"cmd": "curl -sI {target}", "desc": "HTTP headers"},
            {"cmd": "dig {target} ANY +short", "desc": "DNS records"},
            {"cmd": "whois {target} 2>/dev/null | head -20", "desc": "WHOIS lookup"},
        ]
    },
    1: {
        "name": "Port Scanning",
        "commands": [
            {"cmd": "nmap -sV --top-ports 1000 {target}", "desc": "Port scan (top 1000)"},
            {"cmd": "nmap -sV -p- {target}", "desc": "Full port scan (may be slow)"},
        ]
    },
    2: {
        "name": "Vulnerability Scanning",
        "commands": [
            {"cmd": "nikto -h {target} -C all", "desc": "Nikto web scanner"},
            {"cmd": "nmap --script vuln -p 80,443,8080 {target}", "desc": "Nmap vulnerability scripts"},
        ]
    },
    3: {
        "name": "Exploitation Research",
        "commands": [
            {"cmd": "searchsploit {service} 2>/dev/null | head -20", "desc": "Search exploit-db"},
        ]
    },
    4: {
        "name": "Report",
        "commands": []
    }
}


class FallbackEngine:
    """Smart fallback with 4 phases when AI is unavailable.
    Runs deterministic scanning workflow without AI."""

    def __init__(self):
        self.queue = []
        self.done = False
        self.target = ""
        self.current_phase = -1
        self.found_vulns = []
        self.found_ports = []
        self.found_services = []
        self.services_discovered = []
        self.all_outputs = []

    def parse(self, user_input):
        self.queue = []
        self.done = False
        text = user_input.strip()
        if is_direct_command(text):
            self.queue.append({
                "command": text,
                "reason": "Direct command execution",
                "phase": -1
            })
            return True
        targets = self._extract_targets(text)
        if targets:
            self.target = targets[0]
            self._build_phase_queue()
            return True
        return False

    def _extract_targets(self, text):
        ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        domain_pattern = re.compile(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b')
        ips = ip_pattern.findall(text)
        domains = [d for d in domain_pattern.findall(text) if "openrouter" not in d and "github" not in d and d.count(".") >= 1]
        return ips + domains

    def _build_phase_queue(self):
        t = self.target
        for phase_id in sorted(PHASES.keys()):
            phase = PHASES[phase_id]
            for cmd_info in phase["commands"]:
                cmd = cmd_info["cmd"].replace("{target}", t).replace("{service}", "")
                self.queue.append({
                    "command": cmd,
                    "reason": f"[Phase {phase_id+1}/5: {phase['name']}] {cmd_info['desc']}",
                    "phase": phase_id
                })

    def next_command(self):
        if self.done or not self.queue:
            self.done = True
            return None
        item = self.queue.pop(0)
        phase = item.get("phase", -1)
        if phase != self.current_phase:
            self.current_phase = phase
        return item

    def add_finding(self, finding_type, value, detail=""):
        if finding_type == "vuln":
            self.found_vulns.append(value)
        elif finding_type == "port":
            self.found_ports.append(value)
        elif finding_type == "service":
            self.found_services.append(value)

    def has_more(self):
        return len(self.queue) > 0

    def summary(self):
        lines = ["=== Smart Fallback Summary ==="]
        if self.found_vulns:
            lines.append(f"Vulnerabilities: {', '.join(self.found_vulns[:10])}")
        if self.found_ports:
            lines.append(f"Ports: {', '.join(self.found_ports[:20])}")
        if self.found_services:
            lines.append(f"Services: {', '.join(self.found_services[:10])}")
        phases_run = sorted(set(item.get("phase", -1) for item in self.queue if item.get("phase") >= 0))
        if phases_run:
            lines.append(f"Phases completed: {len(phases_run)}/5")
        return "\n".join(lines)
