import subprocess
import os
import signal
import time
import shlex
import shutil
from utils.config import get_config
from utils.logger import get_logger

log = get_logger("executor")

_KNOWN_BINARIES = {
    "nmap", "masscan", "rustscan", "nikto", "whatweb", "wpscan",
    "gobuster", "dirb", "ffuf", "sqlmap", "hydra", "medusa",
    "john", "hashcat", "msfconsole", "msfvenom", "searchsploit",
    "theharvester", "sherlock", "holehe", "whois", "dnsrecon",
    "dig", "nslookup", "tcpdump", "tshark", "netcat", "nc",
    "curl", "wget", "python3", "python", "ping", "traceroute",
    "ls", "whoami", "id", "ifconfig", "ip", "ss", "ps",
    "df", "uname", "cat", "grep", "find", "apt", "apt-get",
    "systemctl", "chmod", "mkdir", "touch", "rm", "cp", "mv",
    "echo", "sudo", "docker", "ssh", "scp", "nuclei", "nslookup",
    "wafw00f", "pip", "pip3", "gem", "npm",
}


class CommandExecutor:
    def __init__(self):
        self.default_timeout = get_config("executor", "default_timeout") or 120
        self.long_timeout = get_config("executor", "long_running_timeout") or 600
        self.history = []

    def _command_to_args(self, command):
        return shlex.split(command)

    def _needs_shell(self, command):
        operators = {"|", ";", "&", ">", "<", "$(", "`"}
        return any(op in command for op in operators)

    def run(self, command):
        self.history.append(command)

        if os.name == "nt":
            return self._run_windows(command)

        tool_hint = command.split()[0] if command.split() else ""
        if tool_hint and tool_hint in _KNOWN_BINARIES:
            if not shutil.which(tool_hint) and self.ensure_tool(tool_hint):
                log.info(f"Installed missing tool: {tool_hint}")

        timeout = self.long_timeout if self._is_long_running(command) else self.default_timeout

        try:
            log.info(f"Executing: {command[:200]}")
            print(f"\n[>] Executing ({timeout}s timeout): {command[:200]}{'...' if len(command) > 200 else ''}")

            if self._needs_shell(command):
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            else:
                args = self._command_to_args(command)
                result = subprocess.run(
                    args,
                    shell=False,
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

            args = self._command_to_args(command)
            process = subprocess.Popen(
                args,
                shell=False,
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
        return shutil.which(tool_name) is not None

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
        try:
            if tool_name in python_tools:
                result = subprocess.run(
                    ["pip", "install", tool_name],
                    capture_output=True, text=True, timeout=120
                )
            elif os.path.exists("/usr/bin/apt"):
                result = subprocess.run(
                    ["apt-get", "install", "-y", tool_name],
                    capture_output=True, text=True, timeout=300
                )
            elif os.path.exists("/opt/homebrew/bin/brew") or os.path.exists("/usr/local/bin/brew"):
                result = subprocess.run(
                    ["brew", "install", tool_name],
                    capture_output=True, text=True, timeout=300
                )
            else:
                log.warning(f"Cannot auto-install {tool_name}: no package manager found")
                return False
            output = (result.stdout + result.stderr).lower()
            success = result.returncode == 0
            if success:
                print(f"[+] {tool_name} installed")
                log.info(f"Installed {tool_name}")
            else:
                print(f"[-] Failed to install {tool_name}")
            return success
        except Exception as e:
            log.error(f"Install error for {tool_name}: {e}")
            return False

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
