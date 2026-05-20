from core.plugin_manager import Plugin

plugin = Plugin(
    name="nmap_enhanced",
    description="Enhanced nmap scan with OS detection, version detection, and script scanning",
    category="scanner",
    version="1.0.0",
    author="0xMr.PORT 777"
)


def run(target, **kwargs):
    import subprocess
    import shlex
    timeout = kwargs.get("timeout", 300)
    ports = kwargs.get("ports", "-p-")
    cmd = f"nmap -sV -sC -O {ports} {target}"
    try:
        result = subprocess.run(shlex.split(cmd), shell=False, capture_output=True, text=True, timeout=timeout)
        return {
            "status": "success" if result.returncode == 0 else "error",
            "command": cmd,
            "output": (result.stdout + result.stderr)[:5000],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "command": cmd, "output": f"Timed out after {timeout}s"}
    except Exception as e:
        return {"status": "error", "command": cmd, "output": str(e)}
