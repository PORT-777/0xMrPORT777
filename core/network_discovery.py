import ipaddress
import re
from utils.logger import get_logger

log = get_logger("network_discovery")

DISCOVERY_COMMANDS = {
    "arp_scan": {
        "command": "arp-scan --localnet 2>/dev/null",
        "fallback": "nmap -sn 192.168.1.0/24",
        "desc": "ARP scan for local network discovery",
    },
    "nmap_ping": {
        "command": "nmap -sn {SUBNET}",
        "desc": "ICMP ping sweep of subnet",
    },
    "nmap_top_ports": {
        "command": "nmap --top-ports 1000 -T4 {SUBNET}",
        "desc": "Scan top 1000 ports on all hosts in subnet",
    },
    "nmap_quick": {
        "command": "nmap -F -T4 {SUBNET}",
        "desc": "Fast scan of common ports on subnet",
    },
    "nmap_udp": {
        "command": "nmap -sU --top-ports 20 -T4 {SUBNET}",
        "desc": "UDP scan for common services",
    },
    "nmap_os": {
        "command": "nmap -O -T4 {TARGETS}",
        "desc": "OS detection on discovered hosts",
    },
    "nmap_scripts": {
        "command": "nmap -sV --script vuln -T4 {TARGETS}",
        "desc": "Vulnerability scripts on discovered hosts",
    },
    "nmap_smb": {
        "command": "nmap -p 445 --script smb-enum-shares,smb-enum-users,smb-os-discovery {SUBNET}",
        "desc": "SMB enumeration across subnet",
    },
    "nmap_snmp": {
        "command": "nmap -p 161 --script snmp-brute,snmp-info {SUBNET}",
        "desc": "SNMP discovery and enumeration",
    },
    "nmap_mssql": {
        "command": "nmap -p 1433 --script ms-sql-info,ms-sql-empty-password {SUBNET}",
        "desc": "MSSQL discovery across subnet",
    },
    "nmap_rdp": {
        "command": "nmap -p 3389 --script rdp-enum-encryption,rdp-vuln-ms12-020 {SUBNET}",
        "desc": "RDP discovery and vulnerability check",
    },
    "nmap_ssh": {
        "command": "nmap -p 22 --script ssh-hostkey,ssh-auth-methods {SUBNET}",
        "desc": "SSH enumeration across subnet",
    },
    "discover_subnets": {
        "command": "ip route | grep -E '^[0-9]' | awk '{{print $1}}'",
        "desc": "Discover local subnets from routing table",
    },
    "dns_zone": {
        "command": "dig axfr {DOMAIN} @{DNS_SERVER} 2>/dev/null",
        "desc": "DNS zone transfer attempt",
    },
    "subdomain_enum": {
        "command": "subfinder -d {DOMAIN} -silent 2>/dev/null || amass enum -d {DOMAIN} 2>/dev/null",
        "desc": "Subdomain enumeration",
    },
}


class NetworkDiscovery:
    """Automated network discovery and adjacent network scanning."""

    def __init__(self):
        self.commands = DISCOVERY_COMMANDS
        self._discovered_hosts = set()
        self._discovered_subnets = set()

    def get_subnet_from_ip(self, ip, cidr=24):
        try:
            network = ipaddress.ip_network(f"{ip}/{cidr}", strict=False)
            return str(network)
        except ValueError:
            return None

    def get_adjacent_subnets(self, ip, cidr=24):
        try:
            network = ipaddress.ip_network(f"{ip}/{cidr}", strict=False)
            subnets = []
            net_addr = int(network.network_address)
            mask = network.prefixlen
            block_size = 2 ** (32 - mask)
            for offset in [-block_size, block_size]:
                adj_addr = net_addr + offset
                if 0 <= adj_addr < 2**32:
                    adj_net = ipaddress.ip_network(f"{ipaddress.ip_address(adj_addr)}/{mask}", strict=False)
                    subnets.append(str(adj_net))
            return subnets
        except (ValueError, TypeError):
            return []

    def generate_discovery_plan(self, target_ip, depth="basic"):
        subnet = self.get_subnet_from_ip(target_ip)
        adjacent = self.get_adjacent_subnets(target_ip)
        plan = {"target": target_ip, "subnet": subnet, "adjacent_subnets": adjacent, "commands": []}

        if depth in ["basic", "full"]:
            plan["commands"].append({
                "step": 1,
                "phase": "discovery",
                "command": self.commands["nmap_ping"]["command"].format(SUBNET=subnet),
                "desc": self.commands["nmap_ping"]["desc"],
            })
            plan["commands"].append({
                "step": 2,
                "phase": "service_scan",
                "command": self.commands["nmap_top_ports"]["command"].format(SUBNET=subnet),
                "desc": self.commands["nmap_top_ports"]["desc"],
            })

        if depth == "full":
            plan["commands"].append({
                "step": 3,
                "phase": "vulnerability",
                "command": self.commands["nmap_scripts"]["command"].format(TARGETS=subnet),
                "desc": self.commands["nmap_scripts"]["desc"],
            })
            plan["commands"].append({
                "step": 4,
                "phase": "smb_enum",
                "command": self.commands["nmap_smb"]["command"].format(SUBNET=subnet),
                "desc": self.commands["nmap_smb"]["desc"],
            })
            plan["commands"].append({
                "step": 5,
                "phase": "adjacent_scan",
                "command": self.commands["nmap_ping"]["command"].format(SUBNET=adjacent[0]) if adjacent else "",
                "desc": f"Scan adjacent subnet: {adjacent[0] if adjacent else 'N/A'}",
            })

        return plan

    def parse_discovery_output(self, output):
        hosts = []
        if not output:
            return hosts
        for line in output.split("\n"):
            match = re.search(r'Nmap scan report for\s+(\S+).*\(([\d.]+)\)', line)
            if match:
                hosts.append({"hostname": match.group(1), "ip": match.group(2)})
            else:
                ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                if ip_match and "open" in line.lower():
                    hosts.append({"ip": ip_match.group(1), "raw": line.strip()[:100]})
        return hosts

    def register_discovered(self, ip):
        self._discovered_hosts.add(ip)

    def get_discovered(self):
        return list(self._discovered_hosts)

    def format_for_prompt(self, target_ip):
        plan = self.generate_discovery_plan(target_ip, "basic")
        lines = ["**Network Discovery Plan:**"]
        lines.append(f"  Target: {plan['target']}")
        lines.append(f"  Subnet: {plan['subnet']}")
        if plan["adjacent_subnets"]:
            lines.append(f"  Adjacent: {', '.join(plan['adjacent_subnets'])}")
        lines.append(f"  Discovery commands: {len(plan['commands'])}")
        for cmd in plan["commands"]:
            lines.append(f"    [{cmd['phase']}] {cmd['desc']}")
        return "\n".join(lines)
