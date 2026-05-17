import re
from utils.logger import get_logger

log = get_logger("planner")


class AutoPlanner:
    """
    Plans 3 steps ahead based on brain state.
    Generates priority-ordered action suggestions.
    Adapts on failure (if nmap fails -> try masscan).
    """

    PRIORITY_RULES = [
        {
            "condition": "no_targets",
            "priority": "highest",
            "suggestion": "Run network discovery first (arp-scan, nmap -sn, or ping sweep)"
        },
        {
            "condition": "targets_no_ports",
            "priority": "high",
            "suggestion": "Port scan discovered targets",
            "tools": ["nmap -sV", "masscan"]
        },
        {
            "condition": "web_services",
            "priority": "high",
            "suggestion": "Web services detected on {target} — run web recon",
            "tools": ["whatweb", "gobuster", "nikto"]
        },
        {
            "condition": "ssh_service",
            "priority": "medium",
            "suggestion": "SSH on {target} — try brute force or key auth",
            "tools": ["hydra -l root -P", "nmap --script ssh*"]
        },
        {
            "condition": "db_service",
            "priority": "high",
            "suggestion": "Database service on {target} — enumerate and test",
            "tools": ["nmap --script mysql*", "sqlmap"]
        },
        {
            "condition": "http_service",
            "priority": "high",
            "suggestion": "HTTP on {target} — directory fuzzing and vuln scan",
            "tools": ["gobuster dir", "nikto", "curl"]
        },
        {
            "condition": "has_credentials",
            "priority": "high",
            "suggestion": "Credentials found — try lateral movement or privilege escalation",
        },
        {
            "condition": "has_vulnerabilities",
            "priority": "high",
            "suggestion": "Vulnerabilities found — search for exploits",
            "tools": ["searchsploit"]
        }
    ]

    FAILURE_FALLBACKS = {
        "nmap": ["masscan", "rustscan"],
        "masscan": ["nmap"],
        "hydra": ["medusa"],
        "gobuster": ["ffuf", "dirb"],
        "nikto": ["whatweb", "curl -I"],
        "sqlmap": ["curl -v", "manual inspection"],
        "theharvester": ["whois", "dig"],
    }

    def __init__(self, brain):
        self.brain = brain

    def plan_next_actions(self, max_suggestions=3):
        """Generate next actions based on current brain state."""
        state = self.brain.state
        targets = state.get("targets", {})
        suggestions = []

        num_targets = len(targets)
        targets_with_ports = sum(1 for t in targets.values() if t["ports"])

        if num_targets == 0:
            suggestions.append(self.PRIORITY_RULES[0])
            return suggestions[:max_suggestions]

        if num_targets > 0 and targets_with_ports == 0:
            suggestions.append(self.PRIORITY_RULES[1])

        for ip, t in targets.items():
            open_ports = set(t["ports"].keys()) if t["ports"] else set()

            if open_ports & {80, 443, 8080, 8443, 3000, 5000}:
                s = self.PRIORITY_RULES[2].copy()
                s["target"] = ip
                s["suggestion"] = s["suggestion"].replace("{target}", ip)
                suggestions.append(s)

            if open_ports & {22}:
                s = self.PRIORITY_RULES[3].copy()
                s["target"] = ip
                s["suggestion"] = s["suggestion"].replace("{target}", ip)
                suggestions.append(s)

            if open_ports & {3306, 5432, 27017, 1433, 1521}:
                s = self.PRIORITY_RULES[4].copy()
                s["target"] = ip
                s["suggestion"] = s["suggestion"].replace("{target}", ip)
                suggestions.append(s)

            if open_ports & {80, 8080}:
                s = self.PRIORITY_RULES[5].copy()
                s["target"] = ip
                s["suggestion"] = s["suggestion"].replace("{target}", ip)
                suggestions.append(s)

        if state.get("credentials"):
            suggestions.append(self.PRIORITY_RULES[6])

        if state.get("vulnerabilities"):
            suggestions.append(self.PRIORITY_RULES[7])

        seen = []
        unique = []
        for s in suggestions:
            key = s.get("condition", s.get("suggestion", ""))
            if key not in seen:
                seen.append(key)
                unique.append(s)

        return unique[:max_suggestions]

    def get_fallback(self, failed_command):
        """Suggest alternative after a command failure."""
        cmd_base = failed_command.strip().split()[0] if failed_command.strip() else ""
        if cmd_base in self.FAILURE_FALLBACKS:
            fallbacks = self.FAILURE_FALLBACKS[cmd_base]
            log.info(f"Fallback for '{cmd_base}': {', '.join(fallbacks)}")
            return fallbacks
        return ["try a different approach or tool"]

    def format_suggestions_for_prompt(self):
        """Format planning suggestions for AI prompt injection."""
        suggestions = self.plan_next_actions(max_suggestions=3)
        if not suggestions:
            return ""
        lines = ["## Auto-Planner Suggestions", ""]
        for i, s in enumerate(suggestions, 1):
            lines.append(f"{i}. {s['suggestion']}")
            if s.get("tools"):
                lines.append(f"   Tools: {', '.join(s['tools'])}")
            lines.append("")
        return "\n".join(lines)

    def format_failures_for_prompt(self, last_command=None):
        """Format failure info for prompt."""
        if not last_command:
            return ""
        fallbacks = self.get_fallback(last_command)
        lines = [
            "## Previous Command Failed",
            f"Failed: {last_command[:100]}",
            f"Try: {', '.join(fallbacks)}",
            ""
        ]
        return "\n".join(lines)
