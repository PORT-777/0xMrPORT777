import pytest
import os
import json
from pathlib import Path
from core.brain import SessionBrain


@pytest.fixture
def brain(tmp_path):
    brain_path = tmp_path / "test_brain.json"
    return SessionBrain(brain_path=brain_path)


class TestSessionBrain:
    def test_default_state(self, brain):
        assert brain.state["phase"] == "initial"
        assert brain.state["targets"] == {}
        assert brain.state["credentials"] == []
        assert brain.state["vulnerabilities"] == []

    def test_start_session(self, brain):
        brain.start("test_123", "Scan target 192.168.1.1")
        assert brain.state["session_id"] == "test_123"
        assert brain.state["objective"] == "Scan target 192.168.1.1"
        assert brain.state["phase"] == "recon"

    def test_extract_ips_from_output(self, brain):
        brain.start("test_1", "recon")
        brain.update_after_command("nmap 192.168.1.1", "Nmap scan report for 192.168.1.1\nPORT   STATE SERVICE\n80/tcp open  http")
        assert "192.168.1.1" in brain.state["targets"]

    def test_extract_ports_from_nmap(self, brain):
        brain.start("test_1", "recon")
        output = "80/tcp open  http  Apache 2.4.49\n443/tcp open  https  nginx"
        brain.update_after_command("nmap -sV 192.168.1.1", output)
        brain.update_after_command("nmap -sV 192.168.1.1", "Nmap scan report for 192.168.1.1\n" + output)
        target = brain.state["targets"].get("192.168.1.1", {})
        assert len(target.get("ports", {})) > 0

    def test_extract_vulnerabilities(self, brain):
        brain.start("test_1", "recon")
        output = "Found CVE-2021-41773 on target"
        brain.update_after_command("searchsploit apache", output)
        assert len(brain.state["vulnerabilities"]) > 0
        assert brain.state["vulnerabilities"][0]["cve"] == "CVE-2021-41773"

    def test_phase_updates_to_enumeration(self, brain):
        brain.start("test_1", "recon")
        brain.update_after_command("nmap 192.168.1.1", "Nmap scan report for 192.168.1.1\n80/tcp open  http")
        assert brain.state["phase"] == "enumeration"

    def test_phase_updates_to_exploitation(self, brain):
        brain.start("test_1", "recon")
        brain.update_after_command("nmap 192.168.1.1", "Nmap scan report for 192.168.1.1\n80/tcp open  http")
        brain.update_after_command("searchsploit", "CVE-2021-41773 found")
        assert brain.state["phase"] == "exploitation"

    def test_get_state_summary(self, brain):
        brain.start("test_1", "recon")
        summary = brain.get_state_summary()
        assert "Phase:" in summary
        assert "Targets:" in summary

    def test_get_open_ports_summary_empty(self, brain):
        brain.start("test_1", "recon")
        summary = brain.get_open_ports_summary()
        assert "No open ports" in summary

    def test_get_priority_summary_empty(self, brain):
        brain.start("test_1", "recon")
        summary = brain.get_priority_summary()
        assert "No pending" in summary

    def test_format_for_prompt(self, brain):
        brain.start("test_1", "recon")
        prompt = brain.format_for_prompt()
        assert "Current Session State" in prompt

    def test_excludes_localhost(self, brain):
        brain.start("test_1", "recon")
        brain.update_after_command("ping 127.0.0.1", "127.0.0.1 is alive")
        assert "127.0.0.1" not in brain.state["targets"]

    def test_command_history_updated(self, brain):
        brain.start("test_1", "recon")
        brain.update_after_command("whoami", "root")
        assert len(brain.state["command_history"]) > 0
        assert brain.state["command_history"][0]["command"] == "whoami"

    def test_failed_action_tracked(self, brain):
        brain.start("test_1", "recon")
        brain.update_after_command("nmap", "")
        assert len(brain.state["failed_actions"]) > 0
