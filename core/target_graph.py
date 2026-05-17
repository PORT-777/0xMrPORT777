from core.findings_db import FindingsDB
from utils.logger import get_logger

log = get_logger("target_graph")


class TargetGraph:
    def __init__(self, brain_state=None):
        self.db = FindingsDB()
        self.brain_state = brain_state or {}
        self.nodes = []
        self.edges = []

    def build(self, brain_state=None):
        if brain_state:
            self.brain_state = brain_state
        self.nodes = []
        self.edges = []
        added_ips = set()

        targets_info = self.brain_state.get("targets", {})
        for ip, info in targets_info.items():
            services = info.get("services", {})
            os_info = info.get("os", "")
            hostname = info.get("hostname", "")
            port_list = list(services.keys())
            is_gateway = any("router" in str(os_info).lower() or "gateway" in str(hostname).lower()
                             for _ in [0])
            self.nodes.append({
                "id": ip,
                "label": hostname or ip,
                "ip": ip,
                "hostname": hostname,
                "os": os_info,
                "ports": port_list,
                "is_gateway": is_gateway or ip.endswith(".1") or ip.endswith(".254"),
                "service_count": len(services),
                "credentials_found": bool(info.get("credentials", [])),
                "vulnerabilities_found": bool(info.get("vulnerabilities", []))
            })
            added_ips.add(ip)

            for port_key, svc in services.items():
                connected_ip = svc.get("connected_to", "")
                if connected_ip and connected_ip not in added_ips:
                    self.nodes.append({
                        "id": connected_ip,
                        "label": connected_ip,
                        "ip": connected_ip,
                        "os": "",
                        "ports": [],
                        "is_gateway": False,
                        "service_count": 0,
                        "credentials_found": False,
                        "vulnerabilities_found": False
                    })
                    added_ips.add(connected_ip)
                if connected_ip:
                    self.edges.append({
                        "from": ip,
                        "to": connected_ip,
                        "label": port_key,
                        "service": svc.get("name", ""),
                        "port": port_key
                    })

        for ip in added_ips:
            if ip not in targets_info:
                db_info = self.db.get_target(ip)
                if db_info:
                    self._update_node(ip, db_info)

        self._add_internal_edges()
        self._mark_lateral_paths()

        log.info(f"Graph built: {len(self.nodes)} nodes, {len(self.edges)} edges")
        return {"nodes": self.nodes, "edges": self.edges}

    def to_dict(self):
        if not self.nodes:
            self.build()
        return {"nodes": self.nodes, "edges": self.edges}

    def find_weakest_path(self, target_ip=None):
        if not self.nodes:
            self.build()
        if not target_ip:
            gateways = [n for n in self.nodes if n.get("is_gateway")]
            if not gateways:
                return []
            entry = gateways[0]
            high_value = sorted(
                [n for n in self.nodes if n.get("vulnerabilities_found") or n.get("credentials_found")],
                key=lambda x: x.get("service_count", 0), reverse=True
            )
            target_ip = high_value[0]["id"] if high_value else self.nodes[-1]["id"]
        else:
            entry = next((n for n in self.nodes if n.get("is_gateway")), self.nodes[0])

        path = self._shortest_path(entry["id"], target_ip)
        if not path:
            path = self._shortest_path(self.nodes[0]["id"], target_ip)
        return path

    def format_for_prompt(self):
        if not self.nodes:
            return ""
        summary = self.to_dict()
        lines = [f"**Target Graph: {len(summary['nodes'])} hosts, {len(summary['edges'])} connections**"]
        for n in summary["nodes"]:
            ports = ", ".join(n.get("ports", [])[:5])
            creds = " 🔑" if n.get("credentials_found") else ""
            vulns = " 💥" if n.get("vulnerabilities_found") else ""
            lines.append(f"  {n['id']}{' (gateway)' if n['is_gateway'] else ''}{creds}{vulns} — ports: {ports}")
        for e in summary["edges"][:10]:
            lines.append(f"  {e['from']} → {e['to']} ({e['label']})")
        path = self.find_weakest_path()
        if path and len(path) > 1:
            lines.append(f"**Weakest attack path:** {' → '.join(path)}")
        return "\n".join(lines)

    def _update_node(self, ip, info):
        for n in self.nodes:
            if n["id"] == ip:
                n["os"] = info.get("os", n["os"])
                n["hostname"] = info.get("hostname", n["hostname"])
                break

    def _add_internal_edges(self):
        for i, n1 in enumerate(self.nodes):
            for n2 in self.nodes[i+1:]:
                ip1_parts = n1["id"].split(".")
                ip2_parts = n2["id"].split(".")
                if len(ip1_parts) == 4 and len(ip2_parts) == 4:
                    if ip1_parts[:3] == ip2_parts[:3]:
                        edge_id = f"{n1['id']}-{n2['id']}"
                        if not any(e["from"] == n1["id"] and e["to"] == n2["id"]
                                   or e["from"] == n2["id"] and e["to"] == n1["id"]
                                   for e in self.edges):
                            self.edges.append({
                                "from": n1["id"],
                                "to": n2["id"],
                                "label": "same subnet",
                                "service": "subnet",
                                "port": ""
                            })

    def _mark_lateral_paths(self):
        cred_targets = [n["id"] for n in self.nodes if n.get("credentials_found")]
        vuln_targets = [n["id"] for n in self.nodes if n.get("vulnerabilities_found")]
        for e in self.edges:
            if e["from"] in cred_targets or e["to"] in cred_targets:
                e["label"] += " 🔑"
            if e["from"] in vuln_targets or e["to"] in vuln_targets:
                e["label"] += " 💥"

    def _shortest_path(self, start, end):
        if start == end:
            return [start]
        adj = {}
        for e in self.edges:
            adj.setdefault(e["from"], set()).add(e["to"])
            adj.setdefault(e["to"], set()).add(e["from"])
        visited = {start}
        queue = [[start]]
        while queue:
            path = queue.pop(0)
            node = path[-1]
            for neighbor in adj.get(node, []):
                if neighbor == end:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return []
