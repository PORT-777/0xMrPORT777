import subprocess
import os
import signal
import time
from utils.config import get_config
from utils.logger import get_logger

log = get_logger("executor")


class CommandExecutor:
    def __init__(self):
        self.default_timeout = get_config("executor", "default_timeout") or 120
        self.long_timeout = get_config("executor", "long_running_timeout") or 600
        self.history = []

    def run(self, command):
        self.history.append(command)

        if os.name == "nt":
            return self._run_windows(command)

        tool_hint = command.split()[0] if command.split() else ""
        if tool_hint and not self._check_tool_raw(tool_hint) and self.ensure_tool(tool_hint):
            log.info(f"Installed missing tool: {tool_hint}")

        timeout = self.long_timeout if self._is_long_running(command) else self.default_timeout

        try:
            log.info(f"Executing: {command[:200]}")
            print(f"\n[>] Executing ({timeout}s timeout): {command[:200]}{'...' if len(command) > 200 else ''}")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"

            log.info(f"Command finished (rc={result.returncode}, {len(output)} chars)")
            return output.strip()

        except subprocess.TimeoutExpired:
            log.warning(f"Command timed out after {timeout}s: {command[:80]}")
            return f"[-] Command timed out after {timeout} seconds."
        except FileNotFoundError:
            log.warning(f"Command not found: {command.split()[0] if command.split() else command}")
            return f"[-] Command not found: '{command.split()[0] if command.split() else command}'. Try installing it."
        except PermissionError:
            log.warning(f"Permission denied: {command[:80]}")
            return "[-] Permission denied. Try with sudo."
        except Exception as e:
            log.error(f"Execution error: {e}")
            return f"[-] Execution error: {str(e)}"

    def run_with_live_output(self, command):
        """Execute and show output live (for long-running commands)."""
        self.history.append(command)

        try:
            log.info(f"Executing (live): {command[:200]}")
            print(f"\n[>] Executing (live): {command[:200]}")

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            output_lines = []
            for line in iter(process.stdout.readline, ""):
                print(line, end="", flush=True)
                output_lines.append(line)

            process.wait()
            output = "".join(output_lines)
            log.info(f"Live command finished (rc={process.returncode})")
            return output

        except Exception as e:
            log.error(f"Live execution error: {e}")
            return f"[-] Error: {str(e)}"

    def _check_tool_raw(self, tool_name):
        try:
            result = subprocess.run(
                f"command -v {tool_name} 2>/dev/null",
                shell=True, capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def check_tool(self, tool_name):
        return self._check_tool_raw(tool_name)

    def ensure_tool(self, tool_name):
        if self._check_tool_raw(tool_name):
            return True
        log.info(f"Tool missing: {tool_name}. Attempting install...")
        print(f"[*] {tool_name} not found. Installing...")
        return self.install_tool(tool_name)

    def install_tool(self, tool_name):
        python_tools = ["requests", "beautifulsoup4", "python-nmap", "colorama", "rich"]
        if tool_name in python_tools:
            result = self.run(f"pip install {tool_name} 2>&1")
        elif os.path.exists("/usr/bin/apt"):
            result = self.run(f"apt-get install -y {tool_name} 2>&1")
        elif os.path.exists("/opt/homebrew/bin/brew") or os.path.exists("/usr/local/bin/brew"):
            result = self.run(f"brew install {tool_name} 2>&1")
        else:
            log.warning(f"Cannot auto-install {tool_name}: no package manager found")
            return False
        success = "error" not in result.lower() or "already" in result.lower()
        if success:
            print(f"[+] {tool_name} installed")
            log.info(f"Installed {tool_name}")
        else:
            print(f"[-] Failed to install {tool_name}")
        return success

    def _is_long_running(self, command):
        cmd_lower = command.lower()
        if "masscan" in cmd_lower or "gobuster dir" in cmd_lower or "dirb" in cmd_lower or "sqlmap" in cmd_lower or "hydra" in cmd_lower or "hashcat" in cmd_lower or "john" in cmd_lower:
            return True
        if "nmap" in cmd_lower and "-p-" in cmd_lower:
            return True
        return False

    def _run_windows(self, command):
        safe_commands = ["whoami", "ipconfig", "ping", "nslookup", "netstat", "systeminfo", "echo", "tracert", "pathping"]
        cmd_base = command.split()[0] if command.split() else ""

        if cmd_base not in safe_commands:
            return f"[-] Windows mode: command '{cmd_base}' not in safe list. Run on Kali Linux."

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return (result.stdout + result.stderr).strip()
        except Exception as e:
            return f"[-] Error: {str(e)}"
