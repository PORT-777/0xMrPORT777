import json
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

log = get_logger("assistant")


class KaliAssistant:
    """
    Conversational Kali Linux AI assistant.
    User types ANYTHING — the AI understands and responds.
    Supports: commands, answers, multi-step tasks, questions.
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
        self.max_iterations = get_config("app", "max_iterations") or 35
        self.session_id = self.session_mgr.generate_id()
        self.conversation_history = []
        self.all_commands = []
        self.step_count = 0
        self.consecutive_failures = 0
        self.context_loaded = False
        self._pending_message = None

    def chat(self, user_input):
        """
        Process a single user message.
        Returns (response_type, data) where response_type is:
          - "answer": data = {"content": str}
          - "command": data = {"command": str, "reason": str, "output": str}
          - "summary": data = {"summary": str}
        """
        self.step_count += 1

        if not self.context_loaded:
            self._init_context(user_input)
            self.context_loaded = True

        system_prompt = self._build_system_prompt()
        user_message = self._build_user_message(user_input)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_message})

        ai_reply = self.ai.ask(messages)
        if not ai_reply:
            return ("answer", {"content": "[-] AI unavailable. Check your API key."})

        decision = self._parse_json(ai_reply)
        if not decision:
            self.conversation_history.append({"role": "user", "content": user_message})
            return ("answer", {"content": ai_reply})

        response_type = decision.get("type", "command")

        if response_type == "answer":
            content = decision.get("content", decision.get("reason", ""))
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": ai_reply})
            return ("answer", {"content": content})

        if response_type == "done":
            summary = decision.get("summary", "Done.")
            log.info(f"Session {self.session_id}: objective complete")
            self._finish(summary)
            return ("summary", {"summary": summary})

        command = decision.get("command", "").strip()
        reason = decision.get("reason", "")
        confirm = decision.get("confirm", True)

        if not command:
            self.conversation_history.append({"role": "user", "content": user_message})
            return ("answer", {"content": reason or "I don't understand. Can you rephrase?"})

        allowed, block_msg = self.safety.check_command(command)
        if not allowed:
            self.conversation_history.append({"role": "user", "content": user_message})
            return ("answer", {"content": f"⚠️ {block_msg}"})

        if confirm:
            self._pending_message = user_message
            return ("command", {
                "command": command,
                "reason": reason,
                "pending_approval": True,
                "decision": decision
            })

        return self._execute_and_respond(command, reason, decision, user_message, ai_reply)

    def confirm_and_execute(self, decision):
        """Execute a previously pending command."""
        command = decision.get("command", "")
        reason = decision.get("reason", "")
        user_message = self._pending_message or ""
        self._pending_message = None
        ai_reply = json.dumps(decision)
        return self._execute_and_respond(command, reason, decision, user_message, ai_reply)

    def _execute_and_respond(self, command, reason, decision, user_message, ai_reply):
        """Execute a command and return the result."""
        if reason:
            print(f"[💡] {reason}")
        print(f"[>] {command[:200]}")

        extras = decision.get("parallel", [])
        chains = decision.get("chain", [])

        if extras and self.parallel.is_compatible_group([command] + extras):
            all_cmds = [command] + extras[:2]
            print(f"[*] Parallel: {len(all_cmds)} commands")
            results = self.parallel.run_group(all_cmds)
            output_parts = []
            for cmd, out in results:
                print(f"  [{cmd[:60]}...] ({len(out)} chars)")
                output_parts.append(f"--- {cmd} ---\n{out}")
            output = "\n\n".join(output_parts)
        elif chains:
            output = self._execute_chain(command, chains)
        else:
            output = self.executor.run(command)

        self.brain.update_after_command(command, output)
        self.memory.add_message("command", command)

        is_failure = not output or "error" in output.lower() or "timed out" in output.lower()
        self.consecutive_failures = (self.consecutive_failures + 1) if is_failure else 0

        self.all_commands.append({
            "step": self.step_count,
            "command": command,
            "tool": command.split()[0] if command else "",
            "reason": reason,
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

        return ("command", {
            "command": command,
            "reason": reason,
            "output": compressed[:500],
            "pending_approval": False
        })

    def _execute_chain(self, command, chains):
        print(f"[>] Primary: {command[:150]}")
        primary_output = self.executor.run(command)
        combined = f"[PRIMARY] {command}\n{primary_output}\n"
        for i, chain in enumerate(chains):
            condition = chain.get("if", "")
            then_cmd = chain.get("then", "")
            if condition and then_cmd and condition in primary_output.lower():
                print(f"[>] Chain {i+1}: {condition} → {then_cmd[:100]}")
                chain_output = self.executor.run(then_cmd)
                combined += f"\n[CHAIN {i+1}] {then_cmd}\n{chain_output}\n"
        return combined

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
        fail_note = (
            f"\nNote: {self.consecutive_failures} consecutive failures. Try a different approach.\n"
            if self.consecutive_failures > 1 else ""
        )
        extra = [t for t in [tools, brain_state, planner_suggestions, exploit_suggestions, long_term_memory, fail_note] if t.strip()]
        extra_block = "\n\n".join(extra)
        return f"{base}\n\n{extra_block}" if extra_block else base

    def _build_user_message(self, user_input):
        parts = [f"User: {user_input}"]
        if self.step_count > 1:
            parts.append(f"\nSession context: {self.brain.get_state_summary()}")
            queue = self.brain.get_priority_summary()
            if queue and queue != "No pending high-priority actions.":
                parts.append(f"\nPriorities:\n{queue}")
        parts.append(
            "\n\nRespond with JSON:"
            '\n{"type": "answer", "content": "..."} — for replies, explanations, chat'
            '\n{"type": "command", "command": "...", "reason": "...", "confirm": true/false} — to execute'
            '\n{"type": "done", "summary": "..."} — if task is complete'
            '\nUse "parallel" and "chain" for advanced execution.'
        )
        return "\n".join(parts)

    def _parse_json(self, text):
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            for pattern in [
                r'```(?:json)?\s*\n?(.*?)\n?```',
                r'(\{(?:[^{}]|(?:\{[^{}]*\}))*})',
                r'\{[^{}]*\}'
            ]:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1) if match.lastindex else match.group())
                    except json.JSONDecodeError:
                        continue
            lower = text.lower()
            if "sorry" in lower or "cannot" in lower:
                return {"type": "answer", "content": text[:500]}
        return None

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
