import pytest
import json
from core.memory_store import MemoryStore


@pytest.fixture
def memory(tmp_path):
    mem_file = tmp_path / "test_memory.json"
    mem = MemoryStore()
    mem.filepath = mem_file
    mem._store = {"sessions": [], "findings": [], "credentials": [], "targets": {}}
    return mem


class TestMemoryStore:
    def test_add_session(self, memory):
        memory.add_session("s1", "Scan target", "Found 3 open ports", targets=["192.168.1.1"])
        assert len(memory._store["sessions"]) == 1
        assert memory._store["sessions"][0]["id"] == "s1"

    def test_add_finding(self, memory):
        memory.add_finding("port", "80/tcp open http", "192.168.1.1")
        assert len(memory._store["findings"]) == 1

    def test_add_target(self, memory):
        memory.add_target("192.168.1.1", {"hostname": "target", "os": "Linux", "services": {"80": "http"}})
        assert "192.168.1.1" in memory._store["targets"]

    def test_add_credential(self, memory):
        memory.add_credential("192.168.1.1", "ssh", "admin", "secret")
        assert len(memory._store["credentials"]) == 1

    def test_query_relevant_by_ip(self, memory):
        memory.add_session("s1", "Scan 192.168.1.1", "Found open ports on 192.168.1.1")
        result = memory.query_relevant("Check 192.168.1.1")
        assert "192.168.1.1" in result or "session" in result.lower()

    def test_query_relevant_no_match(self, memory):
        memory.add_session("s1", "Scan example.com", "Web scan results")
        result = memory.query_relevant("192.168.99.99")
        assert result == ""

    def test_max_sessions_capped(self, memory):
        for i in range(60):
            memory.add_session(f"s{i}", f"Objective {i}", f"Summary {i}")
        assert len(memory._store["sessions"]) <= 50

    def test_max_findings_capped(self, memory):
        for i in range(250):
            memory.add_finding("type", f"Finding {i}")
        assert len(memory._store["findings"]) <= 200

    def test_max_credentials_capped(self, memory):
        for i in range(120):
            memory.add_credential("10.0.0.1", "ssh", f"user{i}", f"pass{i}")
        assert len(memory._store["credentials"]) <= 100

    def test_format_for_prompt(self, memory):
        memory.add_session("s1", "Scan 192.168.1.1", "Found services")
        prompt = memory.format_for_prompt("Scan 192.168.1.1")
        assert len(prompt) > 0

    def test_extract_keywords(self, memory):
        keywords = memory._extract_keywords("Scan 192.168.1.1 for vulnerabilities")
        assert "192.168.1.1" in keywords

    def test_match_keywords(self, memory):
        score = memory._match_keywords("scan target 192.168.1.1", ["192.168.1.1", "target"])
        assert score > 0

    def test_get_all_targets_summary_empty(self, memory):
        summary = memory.get_all_targets_summary()
        assert summary == ""

    def test_save_and_load(self, memory, tmp_path):
        mem_file = tmp_path / "persist_memory.json"
        memory.filepath = mem_file
        memory.add_session("s1", "Test", "Summary")
        memory._save()
        assert mem_file.exists()

        mem2 = MemoryStore()
        mem2.filepath = mem_file
        mem2._store = mem2._load()
        assert len(mem2._store["sessions"]) == 1
