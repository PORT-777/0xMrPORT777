import os
import re
from utils.config import get_config


class SafetyShield:
    """Validates commands before execution to prevent accidental damage."""

    def __init__(self):
        self.enabled = get_config("safety", "enabled")
        self.destructive_cmds = get_config("safety", "destructive_commands")
        self.targets_used = []

    def check_command(self, command: str) -> tuple:
        """
        Returns (allowed: bool, message: str).
        If allowed is False, the command should not be executed.
        """
        if not self.enabled:
            return True, ""

        command_lower = command.strip().lower()

        for pattern in self.destructive_cmds:
            if pattern in command_lower:
                return False, (
                    f"Command blocked: '{command[:80]}...' matches destructive "
                    f"pattern '{pattern}'. Use --force to override."
                )

        if ">/dev/sd" in command_lower or ">/dev/mmc" in command_lower:
            return False, "Blocked: direct disk write detected."

        if "wget" in command_lower and "| bash" in command_lower:
            return False, "Blocked: pipe-from-web to shell detected."

        if "curl" in command_lower and "| bash" in command_lower:
            return False, "Blocked: pipe-from-web to shell detected."

        if "chmod -r" in command_lower or "chmod 0" in command_lower:
            return False, "Blocked: permission removal on files."

        return True, ""

    def extract_targets(self, command: str) -> list:
        """Extract potential IP targets from a command."""
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        domain_pattern = r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'
        ips = re.findall(ip_pattern, command)
        domains = re.findall(domain_pattern, command)
        return ips + [d for d in domains if d not in ["localhost", "local"]]

    def confirm_command(self, command: str, reason: str) -> bool:
        """Prompt user to confirm a command before execution."""
        targets = self.extract_targets(command)
        new_targets = [t for t in targets if t not in self.targets_used]

        if new_targets and get_config("safety", "require_target_confirmation"):
            print(f"\n[!] New target(s) detected: {', '.join(new_targets)}")
            resp = input("    Proceed? [Y/n]: ").strip().lower()
            if resp not in ("", "y", "yes"):
                return False
            self.targets_used.extend(new_targets)

        return True
