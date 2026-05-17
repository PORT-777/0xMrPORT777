import subprocess
import threading
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.config import get_config
from utils.logger import get_logger

log = get_logger("parallel")


class ParallelExecutor:
    """Execute multiple compatible commands simultaneously."""

    def __init__(self, max_workers=3):
        self.max_workers = max_workers

    def run_group(self, commands: list) -> list:
        """Run multiple independent commands in parallel.
        Returns list of (command, output) tuples."""
        if not commands:
            return []

        log.info(f"Parallel: running {len(commands)} commands with {self.max_workers} workers")
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {executor.submit(self._run_one, cmd): cmd for cmd in commands}
            for future in as_completed(future_map):
                cmd = future_map[future]
                try:
                    output = future.result()
                    results.append((cmd, output))
                except Exception as e:
                    results.append((cmd, f"[-] Error: {e}"))

        return results

    def _run_one(self, command: str) -> str:
        timeout = get_config("executor", "default_timeout") or 120
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout or result.stderr or ""
            return output.strip()
        except subprocess.TimeoutExpired:
            return f"[-] Timed out after {timeout}s"
        except Exception as e:
            return f"[-] Error: {e}"

    @staticmethod
    def is_compatible_group(commands: list) -> bool:
        """Check if commands can run in parallel (no target conflicts)."""
        if len(commands) <= 1:
            return False

        write_commands = {"nmap -o", "wget", "curl -o", ">", "tee"}
        has_write = False
        for cmd in commands:
            for wc in write_commands:
                if wc in cmd:
                    has_write = True
                    break
        if has_write:
            return False

        return True

    @staticmethod
    def suggest_parallel(objective: str, target: str) -> list:
        """Suggest commands that can run in parallel for common objectives."""
        suggestions = {
            "recon": [
                f"ping -c 2 {target}",
                f"nslookup {target}",
                f"whois {target} 2>/dev/null | head -20",
            ],
            "web_quick": [
                f"curl -s -I http://{target}",
                f"whatweb {target} --aggression 1 2>/dev/null",
                f"dig {target} ANY +short",
            ],
            "dns": [
                f"dig {target} A +short",
                f"dig {target} MX +short",
                f"dig {target} NS +short",
            ]
        }

        obj_lower = objective.lower()
        if "recon" in obj_lower or "scan" in obj_lower or "اكتشف" in obj_lower:
            return suggestions["recon"]
        if "web" in obj_lower or "site" in obj_lower or "موقع" in obj_lower:
            return suggestions["web_quick"]
        if "dns" in obj_lower:
            return suggestions["dns"]

        return []
