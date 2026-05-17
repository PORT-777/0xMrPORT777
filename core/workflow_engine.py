WORKFLOWS = {
    "quick_recon": {
        "name": "Quick Reconnaissance",
        "description": "Fast initial scan of a target IP/domain",
        "phases": [
            {"prompt": "Run initial ping sweep / ARP scan to check if target is alive",
             "suggested_tools": ["ping", "nmap -sn"]},
            {"prompt": "Quick port scan for top 1000 ports with service detection",
             "suggested_tools": ["nmap -sV", "rustscan"]},
            {"prompt": "Run web technology identification if port 80/443 is open",
             "suggested_tools": ["whatweb", "curl -I"]},
        ]
    },
    "full_scan": {
        "name": "Full Port & Service Scan",
        "description": "Comprehensive scan of all ports with detailed service detection",
        "phases": [
            {"prompt": "Full port scan (all 65535 ports) with fast rate",
             "suggested_tools": ["masscan -p1-65535", "nmap -p-"]},
            {"prompt": "Service version detection on discovered ports",
             "suggested_tools": ["nmap -sV -p<ports>"]},
            {"prompt": "Run default scripts and OS detection",
             "suggested_tools": ["nmap -sC -O -A -p<ports>"]},
        ]
    },
    "web_pentest": {
        "name": "Web Application Pentest",
        "description": "Full web application security assessment",
        "phases": [
            {"prompt": "Identify web technologies and framework",
             "suggested_tools": ["whatweb", "curl -I", "wafw00f"]},
            {"prompt": "Directory and file enumeration",
             "suggested_tools": ["gobuster dir", "ffuf", "dirb"]},
            {"prompt": "Check for information disclosure and backup files",
             "suggested_tools": ["curl", "gobuster dir -x bak,txt,old"]},
            {"prompt": "Web vulnerability scanning",
             "suggested_tools": ["nikto", "wpscan (if wordpress)"]},
            {"prompt": "Test for SQL injection if parameters exist",
             "suggested_tools": ["sqlmap"]},
        ]
    },
    "osint_gathering": {
        "name": "OSINT Information Gathering",
        "description": "Open-source intelligence collection on a target domain",
        "phases": [
            {"prompt": "DNS enumeration and subdomain discovery",
             "suggested_tools": ["dnsrecon", "dig", "nslookup"]},
            {"prompt": "WHOIS domain information lookup",
             "suggested_tools": ["whois"]},
            {"prompt": "Email and employee information gathering",
             "suggested_tools": ["theharvester"]},
            {"prompt": "Subdomain brute-forcing",
             "suggested_tools": ["gobuster dns", "ffuf"]},
        ]
    },
    "password_audit": {
        "name": "Password Security Audit",
        "description": "Test password strength and crack hashes",
        "phases": [
            {"prompt": "Identify hash type from captured hashes",
             "suggested_tools": ["hashid", "hash-identifier"]},
            {"prompt": "Run hashcat with rockyou wordlist",
             "suggested_tools": ["hashcat"]},
            {"prompt": "Try online brute-force on identified services",
             "suggested_tools": ["hydra", "medusa"]},
        ]
    },
    "network_pentest": {
        "name": "Network Infrastructure Pentest",
        "description": "Internal network penetration test",
        "phases": [
            {"prompt": "Discover live hosts on the network",
             "suggested_tools": ["nmap -sn", "netdiscover"]},
            {"prompt": "Port scan all discovered hosts",
             "suggested_tools": ["masscan", "nmap"]},
            {"prompt": "Service detection on all hosts",
             "suggested_tools": ["nmap -sV"]},
            {"prompt": "Check for default credentials on discovered services",
             "suggested_tools": ["hydra", "medusa"]},
            {"prompt": "Search for known vulnerabilities in discovered services",
             "suggested_tools": ["searchsploit"]},
        ]
    }
}


class WorkflowEngine:
    """Manages multi-phase penetration testing workflows."""

    @staticmethod
    def list_workflows() -> dict:
        return {k: {"name": v["name"], "description": v["description"]}
                for k, v in WORKFLOWS.items()}

    @staticmethod
    def get_workflow(name: str) -> dict:
        return WORKFLOWS.get(name)

    @staticmethod
    def get_phase_prompts(workflow_name: str) -> list:
        wf = WORKFLOWS.get(workflow_name)
        if not wf:
            return []
        return [p["prompt"] for p in wf["phases"]]

    @staticmethod
    def generate_system_prompt_extension(workflow_name: str = None) -> str:
        """Generate workflow-specific instructions for the AI prompt."""
        if workflow_name and workflow_name in WORKFLOWS:
            wf = WORKFLOWS[workflow_name]
            lines = [f"## Current Workflow: {wf['name']}", f"Objective: {wf['description']}", ""]
            for i, phase in enumerate(wf["phases"], 1):
                tools = ", ".join(phase["suggested_tools"])
                lines.append(f"Phase {i}: {phase['prompt']}")
                lines.append(f"  Suggested tools: {tools}")
            return "\n".join(lines)
        return ""
