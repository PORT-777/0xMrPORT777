import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

log = get_logger("findings")


class FindingsDB:
    """SQLite database for storing penetration testing findings."""

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "findings.db"
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT NOT NULL,
                    hostname TEXT,
                    domain TEXT,
                    os TEXT,
                    first_seen TEXT,
                    last_seen TEXT,
                    notes TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER,
                    port INTEGER,
                    protocol TEXT DEFAULT 'tcp',
                    state TEXT,
                    service TEXT,
                    version TEXT,
                    banner TEXT,
                    first_seen TEXT,
                    FOREIGN KEY(target_id) REFERENCES targets(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER,
                    service TEXT,
                    username TEXT,
                    password TEXT,
                    hash TEXT,
                    hash_type TEXT,
                    source TEXT,
                    found_at TEXT,
                    notes TEXT,
                    FOREIGN KEY(target_id) REFERENCES targets(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vulnerabilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER,
                    cve TEXT,
                    severity TEXT,
                    description TEXT,
                    tool TEXT,
                    found_at TEXT,
                    proof TEXT,
                    FOREIGN KEY(target_id) REFERENCES targets(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    objective TEXT,
                    started_at TEXT,
                    ended_at TEXT,
                    summary TEXT
                )
            """)
            conn.commit()

    def add_target(self, ip, hostname=None, domain=None, os_name=None):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT id FROM targets WHERE ip=?", (ip,))
            existing = cur.fetchone()
            now = datetime.now().isoformat()
            if existing:
                conn.execute(
                    "UPDATE targets SET last_seen=?, hostname=COALESCE(?,hostname) WHERE id=?",
                    (now, hostname, existing[0])
                )
                return existing[0]
            else:
                cur = conn.execute(
                    "INSERT INTO targets (ip, hostname, domain, os, first_seen, last_seen) VALUES (?,?,?,?,?,?)",
                    (ip, hostname, domain, os_name, now, now)
                )
                return cur.lastrowid

    def add_port(self, target_id, port, protocol="tcp", state="open", service="", version="", banner=""):
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            conn.execute(
                "INSERT INTO ports (target_id, port, protocol, state, service, version, banner, first_seen) VALUES (?,?,?,?,?,?,?,?)",
                (target_id, port, protocol, state, service, version, banner, now)
            )

    def add_credential(self, target_id, service, username="", password="", hash_val="", hash_type="", source=""):
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            conn.execute(
                "INSERT INTO credentials (target_id, service, username, password, hash, hash_type, source, found_at) VALUES (?,?,?,?,?,?,?,?)",
                (target_id, service, username, password, hash_val, hash_type, source, now)
            )

    def add_vulnerability(self, target_id, cve="", severity="medium", description="", tool="", proof=""):
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            conn.execute(
                "INSERT INTO vulnerabilities (target_id, cve, severity, description, tool, found_at, proof) VALUES (?,?,?,?,?,?,?)",
                (target_id, cve, severity, description, tool, now, proof)
            )

    def get_target_id(self, ip):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT id FROM targets WHERE ip=?", (ip,))
            row = cur.fetchone()
            return row[0] if row else None

    def get_target_summary(self, target_id=None):
        with sqlite3.connect(self.db_path) as conn:
            if target_id:
                cur = conn.execute("SELECT ip, hostname, os, first_seen, last_seen FROM targets WHERE id=?", (target_id,))
            else:
                cur = conn.execute("SELECT ip, hostname, os, first_seen, last_seen FROM targets ORDER BY last_seen DESC LIMIT 20")
            targets = [{"ip": r[0], "hostname": r[1], "os": r[2], "first_seen": r[3], "last_seen": r[4]} for r in cur.fetchall()]

            for t in targets:
                tid = self.get_target_id(t["ip"])
                if tid:
                    cur = conn.execute("SELECT COUNT(*), GROUP_CONCAT(DISTINCT service) FROM ports WHERE target_id=?", (tid,))
                    row = cur.fetchone()
                    t["port_count"] = row[0]
                    t["services"] = row[1].split(",") if row[1] else []

                    cur = conn.execute("SELECT COUNT(*) FROM credentials WHERE target_id=?", (tid,))
                    t["cred_count"] = cur.fetchone()[0]

                    cur = conn.execute("SELECT COUNT(*) FROM vulnerabilities WHERE target_id=?", (tid,))
                    t["vuln_count"] = cur.fetchone()[0]
            return targets

    def get_all_ports(self, target_ip=None):
        with sqlite3.connect(self.db_path) as conn:
            if target_ip:
                tid = self.get_target_id(target_ip)
                if not tid:
                    return []
                cur = conn.execute("SELECT port, protocol, state, service, version FROM ports WHERE target_id=?", (tid,))
            else:
                cur = conn.execute(
                    "SELECT t.ip, p.port, p.protocol, p.state, p.service, p.version "
                    "FROM ports p JOIN targets t ON p.target_id=t.id ORDER BY t.ip, p.port"
                )
            return [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    def get_all_credentials(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT t.ip, c.service, c.username, c.password, c.hash, c.hash_type, c.source, c.found_at "
                "FROM credentials c JOIN targets t ON c.target_id=t.id ORDER BY t.ip"
            )
            return [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    def get_all_vulnerabilities(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT t.ip, v.cve, v.severity, v.description, v.tool, v.found_at "
                "FROM vulnerabilities v JOIN targets t ON v.target_id=t.id ORDER BY v.severity, t.ip"
            )
            return [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    def parse_and_store_nmap(self, output, target_ip):
        import re
        tid = self.get_target_id(target_ip)
        if not tid:
            tid = self.add_target(target_ip)

        host_pattern = re.compile(r'Nmap scan report for ([^\n]+)')
        port_pattern = re.compile(r'(\d+)/(tcp|udp)\s+(open|filtered|closed)\s+(\S+)\s*(.*)')
        os_pattern = re.compile(r'OS details:\s*(.+)')

        for match in host_pattern.finditer(output):
            host = match.group(1).strip()
            if host != target_ip:
                self.add_target(host)

        for match in port_pattern.finditer(output):
            self.add_port(
                tid,
                int(match.group(1)),
                match.group(2),
                match.group(3),
                match.group(4),
                match.group(5).strip() if match.group(5) else ""
            )

        for match in os_pattern.finditer(output):
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE targets SET os=? WHERE id=?", (match.group(1).strip(), tid))

    def export_json(self, filepath=None):
        data = {
            "targets": self.get_target_summary(),
            "ports": self.get_all_ports(),
            "credentials": self.get_all_credentials(),
            "vulnerabilities": self.get_all_vulnerabilities(),
            "exported_at": datetime.now().isoformat()
        }
        if filepath is None:
            filepath = Path(__file__).parent.parent / "outputs" / "findings_export.json"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return filepath
