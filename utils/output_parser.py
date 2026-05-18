import re
import json


class OutputParser:
    """Parses structured data from common pentesting tool outputs."""

    @staticmethod
    def parse_nmap(output: str) -> dict:
        data = {
            "hosts": [],
            "ports": [],
            "services": [],
            "os_detections": [],
            "raw": output[:2000]
        }
        host_pattern = re.compile(r'Nmap scan report for ([^\n]+)')
        port_pattern = re.compile(r'(\d+)/(tcp|udp)\s+(open|filtered|closed)\s+(\S+)\s*(.*)')
        os_pattern = re.compile(r'OS details:\s*(.+)')

        for match in host_pattern.finditer(output):
            data["hosts"].append(match.group(1).strip())

        for match in port_pattern.finditer(output):
            port_info = {
                "port": match.group(1),
                "protocol": match.group(2),
                "state": match.group(3),
                "service": match.group(4),
                "version": match.group(5).strip() if match.group(5) else ""
            }
            data["ports"].append(port_info)
            data["services"].append(match.group(4))

        for match in os_pattern.finditer(output):
            data["os_detections"].append(match.group(1).strip())

        return data

    @staticmethod
    def parse_gobuster(output: str) -> list:
        urls = []
        for line in output.splitlines():
            parts = line.split()
            for p in parts:
                if p.startswith("http://") or p.startswith("https://"):
                    urls.append(p.strip())
                    break
        return urls

    @staticmethod
    def parse_hydra(output: str) -> list:
        credentials = []
        pattern = re.compile(r'\[(\d+)\]\[(\w+)\]\s+host:\s+(\S+)\s+login:\s+(\S+)\s+password:\s+(\S+)')
        for match in pattern.finditer(output):
            credentials.append({
                "port": match.group(1),
                "service": match.group(2),
                "host": match.group(3),
                "username": match.group(4),
                "password": match.group(5)
            })
        return credentials

    @staticmethod
    def extract_ips(output: str) -> list:
        return re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)

    @staticmethod
    def parse_dig(output: str) -> dict:
        data = {"ips": [], "domain": "", "raw": output[:500]}
        for line in output.splitlines():
            line = line.strip()
            if line.startswith(";; ANSWER SECTION:"):
                continue
            parts = line.split()
            if len(parts) >= 5 and parts[2] in ("A", "AAAA"):
                data["ips"].append(parts[4].rstrip("."))
            elif "->" in line:
                for ip in re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line):
                    if ip not in data["ips"]:
                        data["ips"].append(ip)
        for ip in re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output):
            if ip not in data["ips"] and not ip.startswith("0."):
                data["ips"].append(ip)
        return data

    @staticmethod
    def extract_hashes(output: str) -> list:
        md5_pattern = re.findall(r'\b[a-fA-F0-9]{32}\b', output)
        sha1_pattern = re.findall(r'\b[a-fA-F0-9]{40}\b', output)
        sha256_pattern = re.findall(r'\b[a-fA-F0-9]{64}\b', output)
        ntlm_pattern = re.findall(r'\b[a-fA-F0-9]{32}:[a-fA-F0-9]{32}\b', output)
        return {
            "md5": md5_pattern,
            "sha1": sha1_pattern,
            "sha256": sha256_pattern,
            "ntlm": ntlm_pattern
        }
