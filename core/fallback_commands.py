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
    "sudo", "docker", "ssh", "scp",
]


def is_direct_command(text):
    first_word = text.strip().split()[0].lower() if text.strip() else ""
    return first_word in KNOWN_TOOLS


class FallbackEngine:
    """Direct command pass-through when AI is unavailable.
    Does NOT interpret natural language — only runs direct commands."""

    def __init__(self):
        self.queue = []
        self.done = False

    def parse(self, user_input):
        self.queue = []
        self.done = False
        text = user_input.strip()
        if is_direct_command(text):
            self.queue.append({
                "command": text,
                "reason": f"Direct command execution"
            })
        return len(self.queue) > 0

    def next_command(self):
        if self.done or not self.queue:
            self.done = True
            return None
        return self.queue.pop(0)

    def has_more(self):
        return len(self.queue) > 0

    def summary(self):
        return "Done."
