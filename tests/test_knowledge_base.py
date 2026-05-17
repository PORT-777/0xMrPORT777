import pytest
from core.knowledge_base import KaliKnowledge, TOOL_KNOWLEDGE


class TestKaliKnowledge:
    def test_get_all_tools_not_empty(self):
        tools = KaliKnowledge.get_all_tools()
        assert len(tools) > 0

    def test_get_tool_by_name(self):
        tool = KaliKnowledge.get_tool("nmap")
        assert tool is not None
        assert "description" in tool
        assert "examples" in tool

    def test_get_tool_not_found(self):
        tool = KaliKnowledge.get_tool("nonexistent_tool_xyz")
        assert tool is None

    def test_search_tools_by_name(self):
        results = KaliKnowledge.search_tools("nmap")
        assert len(results) > 0
        assert results[0]["name"] == "nmap"

    def test_search_tools_by_description(self):
        results = KaliKnowledge.search_tools("scanner")
        assert len(results) > 0

    def test_get_tools_by_category(self):
        tools = KaliKnowledge.get_tools_by_category("recon")
        assert len(tools) > 0
        assert "nmap" in tools

    def test_get_tools_by_category_empty(self):
        tools = KaliKnowledge.get_tools_by_category("nonexistent_category")
        assert tools == {}

    def test_get_tools_by_purpose_scan(self):
        tools = KaliKnowledge.get_tools_by_purpose("scan")
        assert len(tools) > 0
        names = [t["name"] for t in tools]
        assert "nmap" in names

    def test_get_tools_by_purpose_web(self):
        tools = KaliKnowledge.get_tools_by_purpose("web")
        assert len(tools) > 0
        names = [t["name"] for t in tools]
        assert "gobuster" in names

    def test_get_tools_by_purpose_brute(self):
        tools = KaliKnowledge.get_tools_by_purpose("brute")
        assert len(tools) > 0
        names = [t["name"] for t in tools]
        assert "hydra" in names

    def test_get_tools_by_purpose_exploit(self):
        tools = KaliKnowledge.get_tools_by_purpose("exploit")
        assert len(tools) > 0
        names = [t["name"] for t in tools]
        assert "metasploit" in names

    def test_get_tools_by_purpose_osint(self):
        tools = KaliKnowledge.get_tools_by_purpose("osint")
        assert len(tools) > 0

    def test_get_tools_by_purpose_privesc(self):
        tools = KaliKnowledge.get_tools_by_purpose("privesc")
        assert len(tools) > 0

    def test_get_tools_by_purpose_unknown(self):
        tools = KaliKnowledge.get_tools_by_purpose("unknown_purpose_xyz")
        assert tools == []

    def test_format_for_prompt_not_empty(self):
        prompt = KaliKnowledge.format_for_prompt(max_tools=20)
        assert len(prompt) > 0
        assert "Kali Linux Tools Available" in prompt

    def test_tool_entries_have_required_fields(self):
        required = {"description", "syntax", "examples", "category"}
        for category, tools in TOOL_KNOWLEDGE.items():
            for name, data in tools.items():
                for field in required:
                    assert field in data, f"Missing {field} in {name}"
