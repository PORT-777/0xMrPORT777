import re
from utils.logger import get_logger

log = get_logger("compressor")


class ContextCompressor:
    """
    Compresses long command outputs into structured summaries.
    Preserves key data while reducing token count by 90%+.
    """

    @staticmethod
    def compress(output: str, max_lines=15) -> str:
        """Compress output to essential lines only."""
        if not output:
            return "[empty]"

        lines = output.strip().splitlines()
        if len(lines) <= max_lines:
            return output

        summary_lines = []
        shown = set()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if ContextCompressor._is_important_line(stripped):
                if stripped not in shown:
                    summary_lines.append(stripped)
                    shown.add(stripped)

        if len(summary_lines) > max_lines:
            summary_lines = summary_lines[:max_lines]

        header = ContextCompressor._extract_header(output)
        if header:
            summary_lines = [f"[HEADER] {header}"] + summary_lines

        stats = ContextCompressor._get_stats(output)
        if stats:
            if summary_lines:
                summary_lines.append(stats)

        original_lines = len(lines)
        summary_lines.append(f"[Original: {original_lines} lines, compressed to {len(summary_lines)}]")

        return "\n".join(summary_lines)

    @staticmethod
    def _extract_header(output: str) -> str:
        """Extract header line from tool output."""
        lines = output.strip().splitlines()
        for line in lines[:10]:
            if "Nmap scan report for" in line:
                return line.strip()
            if "Starting Nmap" in line:
                return line.strip()
            if "Gobuster" in line:
                return line.strip()
            if "Hydra" in line:
                return line.strip()
            if "sqlmap" in line.lower():
                return line.strip()[:100]
        return ""

    @staticmethod
    def _get_stats(output: str) -> str:
        """Generate statistics line about output content."""
        open_ports = len(re.findall(r'(\d+)/(tcp|udp)\s+open', output))
        ips = len(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output))
        cves = len(re.findall(r'CVE-\d{4}-\d{4,7}', output, re.IGNORECASE))
        creds = len(re.findall(r'login:\s*\S+\s+password:', output, re.IGNORECASE))
        errors = len(re.findall(r'error|fail|timeout', output, re.IGNORECASE))

        parts = []
        if open_ports:
            parts.append(f"OpenPorts:{open_ports}")
        if ips:
            parts.append(f"IPs:{ips}")
        if cves:
            parts.append(f"CVEs:{cves}")
        if creds:
            parts.append(f"Credentials:{creds}")
        if errors:
            parts.append(f"Errors:{errors}")

        return f"[Stats] {' '.join(parts)}" if parts else ""

    @staticmethod
    def _is_important_line(line: str) -> bool:
        """Check if a line contains important information."""
        important_patterns = [
            r'(open|filtered)\s+\S+',
            r'OS details',
            r'Service Info',
            r'http://',
            r'https://',
            r'login:\s+\S+',
            r'password:\s+\S+',
            r'CVE-\d{4}',
            r'[Vv]ulnerability',
            r'[Ee]xploit',
            r'[Aa]dmin',
            r'[Rr]oot',
            r'[Ff]lag',
            r'[Bb]anner',
            r'Discovered',
            r'[Mm]atch',
            r'200\s+OK',
            r'301\s+',
            r'403\s+',
            r'500\s+',
            r'Database',
            r'Table',
            r'Column',
            r'Username',
            r'Password',
            r'Hash',
            r'Token',
            r'Session',
            r'Cookie',
        ]
        return any(re.search(p, line, re.IGNORECASE) for p in important_patterns)

    @staticmethod
    def extract_structured(output: str) -> dict:
        """Extract all structured data from output at once."""
        data = {
            "ips": list(set(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output))),
            "ports": [],
            "cves": list(set(re.findall(r'CVE-\d{4}-\d{4,7}', output, re.IGNORECASE))),
            "urls": list(set(re.findall(r'https?://[^\s\'\"<>]+', output))),
            "credentials": [],
            "open_ports_count": 0,
        }

        data["ips"] = [ip for ip in data["ips"] if not ip.startswith("127.")]
        data["cves"] = [c.upper() for c in data["cves"]]

        port_pattern = re.compile(r'(\d+)/(tcp|udp)\s+(open)\s+(\S+)\s*(.*)')
        for match in port_pattern.finditer(output):
            data["ports"].append({
                "port": int(match.group(1)),
                "protocol": match.group(2),
                "service": match.group(4),
                "version": match.group(5).strip()
            })
            data["open_ports_count"] += 1

        cred_pattern = re.compile(r'login:\s*(\S+)\s+password:\s*(\S+)')
        for match in cred_pattern.finditer(output):
            data["credentials"].append({
                "username": match.group(1),
                "password": match.group(2)
            })

        return data
