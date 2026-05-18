import re


INTENT_PATTERNS = [
    {
        "keywords": ["ثغرات", "vuln", "vulnerability", "cve", "exploit", "weakness"],
        "intent": "vuln_scan",
        "priority": 10,
    },
    {
        "keywords": ["افحص", "scan", "port", "مسح", "نقاط الضعف"],
        "intent": "full_scan",
        "priority": 9,
    },
    {
        "keywords": ["recon", "اكتشف", "discover", "تحقق", "subdomain"],
        "intent": "recon",
        "priority": 8,
    },
    {
        "keywords": ["whois", "dig", "dns", "nslookup"],
        "intent": "dns_lookup",
        "priority": 7,
    },
    {
        "keywords": ["whatweb", "what web", "web tech", "server", "تقنية"],
        "intent": "web_tech",
        "priority": 6,
    },
    {
        "keywords": ["nikto", "web scan", "http scan"],
        "intent": "web_vuln",
        "priority": 5,
    },
    {
        "keywords": ["exploit", "اختراق", "هجوم", "metasploit", "attack"],
        "intent": "exploit",
        "priority": 4,
    },
    {
        "keywords": ["password", "brute", "hydra", "login", "كلمة المرور", "تخمين"],
        "intent": "brute",
        "priority": 3,
    },
]

COMMAND_TEMPLATES = {
    "vuln_scan": [
        {"command": "whatweb {target}", "reason": "Detect web technologies"},
        {"command": "nmap -sV --script vuln {target}", "reason": "Vulnerability scan"},
        {"command": "nikto -h {target}", "reason": "Web vulnerability scan"},
        {"command": "curl -sI {target}", "reason": "HTTP headers inspection"},
    ],
    "full_scan": [
        {"command": "nmap -sV --top-ports 1000 {target}", "reason": "Quick port scan with service detection"},
        {"command": "nmap -sV --script vuln {target}", "reason": "Vulnerability scan on discovered ports"},
    ],
    "recon": [
        {"command": "whatweb {target}", "reason": "Fingerprint web technologies"},
        {"command": "dig {target}", "reason": "DNS resolution"},
        {"command": "whois {target}", "reason": "WHOIS lookup"},
    ],
    "dns_lookup": [
        {"command": "dig {target}", "reason": "DNS query"},
        {"command": "nslookup {target}", "reason": "DNS resolution"},
    ],
    "web_tech": [
        {"command": "whatweb {target}", "reason": "Web technology detection"},
        {"command": "curl -sI {target}", "reason": "HTTP headers inspection"},
    ],
    "web_vuln": [
        {"command": "nikto -h {target}", "reason": "Web server vulnerability scan"},
        {"command": "nmap -p 80,443 --script http-enum {target}", "reason": "Web enumeration"},
    ],
    "exploit": [
        {"command": "searchsploit {target}", "reason": "Search public exploits"},
    ],
    "brute": [
        {"command": "hydra -l admin -P /usr/share/wordlists/rockyou.txt {target}", "reason": "Brute force login"},
    ],
}


def extract_target(text):
    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text)
    domains = re.findall(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b', text)
    ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
    if urls:
        return urls[0]
    if ips:
        return ips[0]
    if domains:
        return domains[0]
    return None


def detect_intent(text):
    text_lower = text.lower()
    best_intent = None
    best_score = 0
    for pattern in INTENT_PATTERNS:
        score = sum(1 for kw in pattern["keywords"] if kw in text_lower)
        if score > best_score:
            best_score = score
            best_intent = pattern["intent"]
    return best_intent if best_score > 0 else "full_scan"


def build_commands(text):
    target = extract_target(text)
    intent = detect_intent(text)
    templates = COMMAND_TEMPLATES.get(intent, COMMAND_TEMPLATES["full_scan"])
    commands = []
    for t in templates:
        if target:
            cmd = t["command"].replace("{target}", target)
            commands.append({"command": cmd, "reason": t["reason"], "target": target})
    return commands


class FallbackEngine:
    """Deterministic command execution when AI is unavailable."""

    def __init__(self):
        self.queue = []
        self.target = ""
        self.intent = ""
        self.done = False

    def parse(self, user_input):
        self.queue = build_commands(user_input)
        self.target = extract_target(user_input) or ""
        self.intent = detect_intent(user_input)
        self.done = False
        return len(self.queue) > 0

    def next_command(self):
        if self.done:
            return None
        if self.queue:
            return self.queue.pop(0)
        self.done = True
        return None

    def has_more(self):
        return len(self.queue) > 0

    def summary(self):
        intent_names = {
            "vuln_scan": "Vulnerability scan",
            "full_scan": "Port and vulnerability scan",
            "recon": "Reconnaissance",
            "dns_lookup": "DNS lookup",
            "web_tech": "Web technology detection",
            "web_vuln": "Web vulnerability scan",
            "exploit": "Exploit search",
            "brute": "Brute force attack",
        }
        name = intent_names.get(self.intent, "Scan")
        return f"{name} on {self.target} complete."
