from utils.logger import get_logger

log = get_logger("compliance_mapper")

OWASP_TOP10_2021 = {
    "A01:2021": {"name": "Broken Access Control", "keywords": ["access control", "authorization", "privilege", "directory traversal", "idor", "path traversal", "bypass"]},
    "A02:2021": {"name": "Cryptographic Failures", "keywords": ["plaintext", "weak encryption", "md5", "sha1", "ssl", "tls", "certificate", "crypto"]},
    "A03:2021": {"name": "Injection", "keywords": ["sql injection", "sqli", "xss", "command injection", "ldap injection", "xpath", "ssti", "rce"]},
    "A04:2021": {"name": "Insecure Design", "keywords": ["design flaw", "logic bypass", "business logic", "rate limit", "throttling"]},
    "A05:2021": {"name": "Security Misconfiguration", "keywords": ["default password", "misconfiguration", "verbose error", "debug", "directory listing", "exposed"]},
    "A06:2021": {"name": "Vulnerable and Outdated Components", "keywords": ["outdated", "vulnerable version", "cve", "unpatched", "deprecated", "end of life"]},
    "A07:2021": {"name": "Identification and Authentication Failures", "keywords": ["authentication", "brute force", "credential", "session", "password", "weak auth", "default cred"]},
    "A08:2021": {"name": "Software and Data Integrity Failures", "keywords": ["deserialization", "insecure deserialization", "supply chain", "integrity", "unsigned"]},
    "A09:2021": {"name": "Security Logging and Monitoring Failures", "keywords": ["logging", "monitoring", "audit", "detection", "alert"]},
    "A10:2021": {"name": "Server-Side Request Forgery", "keywords": ["ssrf", "server-side request", "url fetch", "internal request", "proxy"]},
}

MITRE_ATTACK = {
    "T1190": {"name": "Exploit Public-Facing Application", "tactic": "Initial Access", "keywords": ["cve", "exploit", "rce", "vulnerability", "public-facing"]},
    "T1078": {"name": "Valid Accounts", "tactic": "Initial Access", "keywords": ["credential", "password", "login", "brute force", "valid account"]},
    "T1133": {"name": "External Remote Services", "tactic": "Initial Access", "keywords": ["vpn", "rdp", "ssh", "remote access", "external"]},
    "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution", "keywords": ["shell", "powershell", "bash", "command", "script"]},
    "T1053": {"name": "Scheduled Task/Job", "tactic": "Persistence", "keywords": ["cron", "scheduled task", "at job", "systemd", "persistence"]},
    "T1547": {"name": "Boot or Logon Autostart Execution", "tactic": "Persistence", "keywords": ["registry run", "startup", "autostart", "boot"]},
    "T1071": {"name": "Application Layer Protocol", "tactic": "Command and Control", "keywords": ["http", "dns", "protocol", "c2", "beacon"]},
    "T1048": {"name": "Exfiltration Over Alternative Protocol", "tactic": "Exfiltration", "keywords": ["exfil", "ftp", "http upload", "dns exfil"]},
    "T1005": {"name": "Data from Local System", "tactic": "Collection", "keywords": ["local data", "file", "config", "credential", "hash"]},
    "T1021": {"name": "Remote Services", "tactic": "Lateral Movement", "keywords": ["smb", "rdp", "ssh", "winrm", "lateral", "psexec"]},
    "T1068": {"name": "Exploitation for Privilege Escalation", "tactic": "Privilege Escalation", "keywords": ["privilege escalation", "privesc", "kernel exploit", "sudo", "suid"]},
    "T1003": {"name": "OS Credential Dumping", "tactic": "Credential Access", "keywords": ["lsass", "sam", "shadow", "hash dump", "credential dump", "mimikatz"]},
    "T1082": {"name": "System Information Discovery", "tactic": "Discovery", "keywords": ["systeminfo", "uname", "enumerate", "discovery", "recon"]},
    "T1046": {"name": "Network Service Discovery", "tactic": "Discovery", "keywords": ["nmap", "port scan", "service discovery", "network scan"]},
    "T1110": {"name": "Brute Force", "tactic": "Credential Access", "keywords": ["brute force", "hydra", "password spray", "dictionary", "credential stuffing"]},
}

NIST_CSF = {
    "PR.AC": {"name": "Access Control", "keywords": ["authentication", "authorization", "access control", "privilege", "rbac"]},
    "PR.DS": {"name": "Data Security", "keywords": ["encryption", "data protection", "data leak", "sensitive data"]},
    "PR.IP": {"name": "Information Protection", "keywords": ["patch", "vulnerability", "baseline", "configuration"]},
    "PR.PT": {"name": "Protective Technology", "keywords": ["firewall", "ids", "ips", "segmentation", "network security"]},
    "DE.CM": {"name": "Security Continuous Monitoring", "keywords": ["monitoring", "logging", "detection", "alert", "siem"]},
    "DE.AE": {"name": "Anomalies and Events", "keywords": ["anomaly", "event", "incident", "unusual", "suspicious"]},
    "RS.RP": {"name": "Response Planning", "keywords": ["response", "incident response", "playbook", "remediation"]},
    "RC.RP": {"name": "Risk Management", "keywords": ["risk", "assessment", "compliance", "policy", "governance"]},
}

PTES_PHASES = {
    "Pre-engagement": {"keywords": ["scope", "rules of engagement", "authorization", "target", "objective"]},
    "Intelligence Gathering": {"keywords": ["recon", "osint", "whois", "dns", "subdomain", "enumeration", "discovery"]},
    "Threat Modeling": {"keywords": ["threat", "attack vector", "risk", "vulnerability", "attack surface"]},
    "Vulnerability Analysis": {"keywords": ["vulnerability", "scan", "cve", "weakness", "misconfiguration", "outdated"]},
    "Exploitation": {"keywords": ["exploit", "rce", "injection", "bypass", "metasploit", "payload", "shell"]},
    "Post-Exploitation": {"keywords": ["post-exploit", "privilege escalation", "persistence", "lateral", "dump", "exfil"]},
    "Reporting": {"keywords": ["report", "finding", "recommendation", "remediation", "summary", "executive"]},
}


class ComplianceMapper:
    """Maps findings to compliance frameworks."""

    def __init__(self):
        self.owasp = OWASP_TOP10_2021
        self.mitre = MITRE_ATTACK
        self.nist = NIST_CSF
        self.ptes = PTES_PHASES

    def map_finding(self, finding_text):
        text = finding_text.lower()
        results = {
            "owasp": [],
            "mitre": [],
            "nist": [],
            "ptes": []
        }

        for cid, info in self.owasp.items():
            if any(kw in text for kw in info["keywords"]):
                results["owasp"].append({"id": cid, "name": info["name"]})

        for tid, info in self.mitre.items():
            if any(kw in text for kw in info["keywords"]):
                results["mitre"].append({"id": tid, "name": info["name"], "tactic": info["tactic"]})

        for cid, info in self.nist.items():
            if any(kw in text for kw in info["keywords"]):
                results["nist"].append({"id": cid, "name": info["name"]})

        for phase, info in self.ptes.items():
            if any(kw in text for kw in info["keywords"]):
                results["ptes"].append({"phase": phase})

        return results

    def map_cve(self, cve_entry):
        desc = cve_entry.get("desc", "").lower()
        severity = cve_entry.get("severity", "").lower()
        vuln_type = cve_entry.get("type", "").lower()

        mapping = self.map_finding(f"{desc} {vuln_type} {severity}")

        if severity in ["critical", "high"]:
            if not mapping["owasp"]:
                mapping["owasp"].append({"id": "A06:2021", "name": "Vulnerable and Outdated Components"})

        return mapping

    def map_session_findings(self, commands):
        all_findings = []
        for cmd in commands:
            output = cmd.get("output", "").lower()
            command = cmd.get("command", "").lower()
            text = f"{command} {output}"
            if text.strip():
                mapping = self.map_finding(text)
                if any(mapping.values()):
                    all_findings.append({
                        "command": cmd.get("command", "")[:80],
                        "mapping": mapping
                    })
        return all_findings

    def format_for_prompt(self, commands=None):
        if not commands:
            return ""

        findings = self.map_session_findings(commands)
        if not findings:
            return ""

        lines = ["**Compliance Mapping:**"]
        owasp_seen = set()
        mitre_seen = set()

        for f in findings:
            for o in f["mapping"]["owasp"]:
                if o["id"] not in owasp_seen:
                    lines.append(f"  OWASP: {o['id']} — {o['name']}")
                    owasp_seen.add(o["id"])
            for m in f["mapping"]["mitre"]:
                if m["id"] not in mitre_seen:
                    lines.append(f"  MITRE ATT&CK: {m['id']} ({m['tactic']}) — {m['name']}")
                    mitre_seen.add(m["id"])

        return "\n".join(lines)

    def get_report_section(self, commands):
        findings = self.map_session_findings(commands)
        if not findings:
            return {"owasp": [], "mitre": [], "nist": [], "ptes": []}

        aggregated = {"owasp": {}, "mitre": {}, "nist": {}, "ptes": {}}
        for f in findings:
            for framework in ["owasp", "mitre", "nist", "ptes"]:
                for item in f["mapping"][framework]:
                    key = item.get("id", item.get("phase", ""))
                    if key not in aggregated[framework]:
                        aggregated[framework][key] = item
                        aggregated[framework][key]["count"] = 0
                    aggregated[framework][key]["count"] += 1

        return {
            "owasp": list(aggregated["owasp"].values()),
            "mitre": list(aggregated["mitre"].values()),
            "nist": list(aggregated["nist"].values()),
            "ptes": list(aggregated["ptes"].values()),
        }
