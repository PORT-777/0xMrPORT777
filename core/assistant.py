import re
from datetime import datetime

from utils.ai_client import AIClient
from utils.prompts import CONVERSATIONAL_PROMPT
from utils.config import get_config
from utils.logger import get_logger
from utils.output_parser import OutputParser
from core.executor import CommandExecutor
from core.memory import SessionMemory
from core.safety import SafetyShield
from core.session_manager import SessionManager
from core.reporter import ReportGenerator
from core.knowledge_base import KaliKnowledge
from core.findings_db import FindingsDB
from core.workflow_engine import WorkflowEngine
from core.parallel_executor import ParallelExecutor
from core.brain import SessionBrain
from core.auto_planner import AutoPlanner
from core.context_compressor import ContextCompressor
from core.exploit_engine import ExploitEngine
from core.memory_store import get_memory
from core.post_exploit import PostExploitEngine
from core.payload_generator import PayloadGenerator
from core.compliance_mapper import ComplianceMapper
from core.attack_timeline import AttackTimeline
from core.network_discovery import NetworkDiscovery
from core.wordlist_generator import WordlistGenerator
from core.fallback_commands import FallbackEngine, is_direct_command

log = get_logger("assistant")


class KaliAssistant:
    """
    Conversational Kali Linux AI assistant.
    AI responds with TEXT. Commands extracted from ```bash code blocks.
    Returns ("pending", data) — caller must approve then call execute_from_pending().
    """

    def __init__(self):
        self.ai = AIClient()
        self.executor = CommandExecutor()
        self.session_mgr = SessionManager()
        self.reporter = ReportGenerator()
        self.parser = OutputParser()
        self.safety = SafetyShield()
        self.knowledge = KaliKnowledge()
        self.findings = FindingsDB()
        self.workflow_engine = WorkflowEngine()
        self.parallel = ParallelExecutor()
        self.brain = SessionBrain()
        self.planner = AutoPlanner(self.brain)
        self.exploit_engine = ExploitEngine()
        self.compressor = ContextCompressor()
        self.memory = SessionMemory()
        self.post_exploit = PostExploitEngine()
        self.payload_gen = PayloadGenerator()
        self.compliance = ComplianceMapper()
        self.timeline = AttackTimeline()
        self.network_disc = NetworkDiscovery()
        self.wordlist_gen = WordlistGenerator()
        self.max_iterations = get_config("app", "max_iterations") or 35
        self.session_id = self.session_mgr.generate_id()
        self.conversation_history = []
        self.all_commands = []
        self.step_count = 0
        self.consecutive_failures = 0
        self.context_loaded = False
        self._fallback = FallbackEngine()
        self._fallback_active = False
        self._pending_data = None

    def chat(self, user_input, auto_approve=False):
        """
        Process user input. Returns (response_type, data).
        response_type: "answer", "pending", "summary"
          - "pending": data = {"command": str, "reason": str, "output": "",
                               "ai_reply": str, "user_message": str, "is_fallback": bool}
            Caller must show command to user, get approval, then call execute_from_pending(data).
          - "answer": data = {"content": str} — AI replied without command.
          - "summary": data = {"summary": str} — objective complete.
        If auto_approve=True, skips pending and executes immediately (returns "command").
        """
        self.step_count += 1

        if not self.context_loaded:
            self._init_context(user_input)
            self.context_loaded = True

        system_prompt = self._build_system_prompt()
        user_message = self._build_user_message(user_input)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in self.conversation_history[-20:]:
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})

        ai_reply = self.ai.ask(messages)

        if not ai_reply or "AI unavailable" in ai_reply or "All 6 OpenRouter models failed" in ai_reply:
            log.warning("AI unavailable, using deterministic fallback")
            self._fallback_active = True
            if not self._fallback.has_more():
                self._fallback.parse(user_input)
            return self._handle_fallback(user_input, auto_approve)

        self._fallback_active = False

        command = self._extract_command(ai_reply)

        if command:
            allowed, block_msg = self.safety.check_command(command)
            if not allowed:
                return ("answer", {"content": f"⚠️ {block_msg}"})

            reason_match = re.search(r'⚡\s*(.*?):', ai_reply)
            reason = reason_match.group(1).strip() if reason_match else ""

            pending_data = {
                "command": command,
                "reason": reason,
                "output": "",
                "ai_reply": ai_reply,
                "user_message": user_message,
                "is_fallback": False
            }

            if auto_approve:
                return self.execute_from_pending(pending_data)

            self._pending_data = pending_data
            return ("pending", pending_data)
        else:
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": ai_reply})
            return ("answer", {"content": ai_reply})

    def execute_from_pending(self, pending_data):
        """Execute a pending command after user approval. Returns ("command", data)."""
        command = pending_data["command"]
        ai_reply = pending_data.get("ai_reply", "")
        user_message = pending_data.get("user_message", "")
        is_fallback = pending_data.get("is_fallback", False)

        if is_fallback:
            reason = pending_data.get("reason", "")
            print(f"[>] {command}")
            output = self.executor.run(command, timeout=300 if "nmap -p-" in command else 120)
            print(f"[*] Output ({len(output or '')} chars):")
            print((output or "")[:600])
            self.brain.update_after_command(command, output)
            self.memory.add_message("command", command)
            self.timeline.add_event(command, output or "", command.split()[0] if command else "")
            return ("command", {"command": command, "reason": reason, "output": (output or "")[:2000]})

        print(f"[>] {command[:200]}")

        output = self.executor.run(command)

        self.brain.update_after_command(command, output)
        self.memory.add_message("command", command)
        self.timeline.add_event(command, output or "", command.split()[0] if command else "")

        is_failure = not output or "error" in output.lower() or "timed out" in output.lower()
        self.consecutive_failures = (self.consecutive_failures + 1) if is_failure else 0

        self.all_commands.append({
            "step": self.step_count,
            "command": command,
            "tool": command.split()[0] if command else "",
            "output": (output or "")[:2000],
            "timestamp": datetime.now().isoformat()
        })

        compressed = self.compressor.compress(output) if output else "[empty]"
        print(f"[*] Output ({len(output or '')} chars):")
        print(compressed[:600])

        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": ai_reply})

        if is_failure and self.consecutive_failures > 1:
            fallbacks = self.planner.get_fallback(command)
            if fallbacks:
                return ("answer", {
                    "content": f"⚠️ Command failed. Try: {', '.join(fallbacks[:3])}"
                })

        reason_match = re.search(r'⚡\s*(.*?):', ai_reply)
        reason = reason_match.group(1).strip() if reason_match else ""

        return ("command", {
            "command": command,
            "reason": reason,
            "output": compressed[:500]
        })

    def _extract_command(self, text):
        """Extract bash command from AI response.
        Looks for ```bash ... ``` blocks, then lines starting with tool names."""
        if not text:
            return ""

        code_blocks = re.findall(r'```(?:bash)?\s*\n(.*?)```', text, re.DOTALL)
        for block in code_blocks:
            cmd = block.strip().split('\n')[0].strip()
            if cmd and not cmd.startswith('#') and not cmd.startswith('//'):
                return cmd

        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('⚡ '):
                cmd = line[2:].strip()
                if cmd and is_direct_command(cmd):
                    return cmd
            first_word = line.split()[0].lower() if line.split() else ""
            if first_word in ("nmap", "whatweb", "nikto", "curl", "dig",
                              "whois", "sqlmap", "hydra", "nuclei", "gobuster",
                              "ffuf", "wpscan", "searchsploit", "msfconsole",
                              "msfvenom", "python3", "python", "sudo",
                              "ping", "traceroute", "wget", "ls", "cat",
                              "grep", "find", "chmod", "mkdir", "echo",
                              "nslookup", "wafw00f"):
                return line

        return ""

    def _handle_fallback(self, user_input, auto_approve=False):
        """Smart fallback when AI unavailable."""
        if user_input != "continue":
            if not self._fallback.has_more() and not self._fallback.parse(user_input):
                return ("answer", {"content": "⚠️ AI (OpenRouter) unreachable.\n"
                    "Type a direct command, or fix internet:\n"
                    "  sudo sh -c 'echo \"nameserver 8.8.8.8\" > /etc/resolv.conf'\n"
                    "  ping -c 1 openrouter.ai"})

        cmd_info = self._fallback.next_command()
        if not cmd_info:
            return ("summary", {"summary": self._fallback.summary()})

        command = cmd_info["command"]
        reason = cmd_info["reason"]

        pending_data = {
            "command": command,
            "reason": reason,
            "output": "",
            "ai_reply": "",
            "user_message": user_input,
            "is_fallback": True
        }

        if auto_approve:
            return self.execute_from_pending(pending_data)

        self._pending_data = pending_data
        return ("pending", pending_data)

    def switch_model(self, provider, model=None):
        providers = self.ai.list_providers()
        if provider not in providers:
            return False, f"Provider must be one of: {', '.join(providers)}"
        self.ai.switch_provider(provider, model)
        return True, f"Switched to {provider} ({self.ai.model})"

    def _init_context(self, user_input):
        self.brain.start(self.session_id, user_input)
        self.memory.start_session(user_input)
        log.info(f"Session {self.session_id}: {user_input[:100]}")

    def _build_system_prompt(self):
        base = CONVERSATIONAL_PROMPT
        tools = self.knowledge.format_for_prompt(max_tools=20)
        brain_state = self.brain.format_for_prompt() if self.context_loaded else ""
        planner_suggestions = self.planner.format_suggestions_for_prompt() if self.context_loaded else ""
        exploit_suggestions = self.exploit_engine.format_for_prompt(self.brain.state) if self.context_loaded else ""
        long_term_memory = get_memory().format_for_prompt(self.brain.state.get("objective", "")) if self.context_loaded else ""
        post_exploit_ctx = self.post_exploit.format_for_prompt("linux") if self.context_loaded else ""
        payload_ctx = self.payload_gen.format_for_prompt("0.0.0.0", 4444) if self.context_loaded else ""
        compliance_ctx = self.compliance.format_for_prompt(self.all_commands) if self.context_loaded else ""
        timeline_ctx = self.timeline.format_for_prompt() if self.context_loaded else ""
        fail_note = (
            f"\nNote: {self.consecutive_failures} consecutive failures. Try a different approach.\n"
            if self.consecutive_failures > 1 else ""
        )
        extra = [t for t in [tools, brain_state, planner_suggestions, exploit_suggestions, long_term_memory, post_exploit_ctx, payload_ctx, compliance_ctx, timeline_ctx, fail_note] if t.strip()]
        extra_block = "\n\n".join(extra)
        return f"{base}\n\n{extra_block}" if extra_block else base

    def _build_user_message(self, user_input):
        parts = [f"User: {user_input}"]
        if self.step_count > 1:
            parts.append(f"\nSession context: {self.brain.get_state_summary()}")
            queue = self.brain.get_priority_summary()
            if queue and queue != "No pending high-priority actions.":
                parts.append(f"\nPriorities:\n{queue}")
        parts.append("\nCommands so far: " + str(len(self.all_commands)))
        return "\n".join(parts)

    def _finish(self, summary):
        try:
            data = {
                "objective": self.brain.state.get("objective", "Chat session"),
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "commands": self.all_commands,
                "summary": summary[:500] if summary else "",
                "targets": list(self.brain.state["targets"].keys()),
                "credentials_count": len(self.brain.state["credentials"]),
                "vulnerabilities_count": len(self.brain.state["vulnerabilities"])
            }
            self.session_mgr.save(self.session_id, data)

            extra = {
                "targets": self.findings.get_target_summary(),
                "ports": self.findings.get_all_ports(),
                "credentials": self.findings.get_all_credentials(),
                "vulnerabilities": self.findings.get_all_vulnerabilities()
            }
            self.reporter.generate(
                self.session_id, data["objective"],
                self.all_commands, summary or "", extra_data=extra
            )
            self.findings.export_json()
            self.brain.save_as()
            get_memory().add_session(
                self.session_id, data["objective"], summary,
                targets=self.brain.state["targets"].keys(),
                commands=self.all_commands
            )
        except Exception as e:
            log.warning(f"Session finalize error: {e}")
