import pytest
from core.exploit_engine import ExploitEngine
from core.post_exploit import PostExploitEngine
from core.payload_generator import PayloadGenerator
from core.compliance_mapper import ComplianceMapper
from core.attack_timeline import AttackTimeline
from core.network_discovery import NetworkDiscovery
from core.wordlist_generator import WordlistGenerator
from core.brain import SessionBrain
from core.safety import SafetyShield
from core.context_compressor import ContextCompressor


class TestPostExploitEngine:
    def test_suggest_not_empty(self):
        engine = PostExploitEngine()
        results = engine.suggest("linux")
        assert len(results) > 0

    def test_suggest_by_category(self):
        engine = PostExploitEngine()
        results = engine.suggest("linux", "privesc")
        assert all(r["category"] == "privesc" for r in results)

    def test_suggest_windows(self):
        engine = PostExploitEngine()
        results = engine.suggest("windows")
        assert len(results) > 0

    def test_get_command(self):
        engine = PostExploitEngine()
        cmd = engine.get_command("linpeas")
        assert cmd is not None
        assert cmd["id"] == "linpeas"

    def test_mark_executed(self):
        engine = PostExploitEngine()
        engine.mark_executed("linpeas")
        results = engine.suggest("linux")
        linpeas = [r for r in results if r["id"] == "linpeas"]
        assert len(linpeas) > 0
        assert linpeas[0]["executed"] is True

    def test_get_stats(self):
        engine = PostExploitEngine()
        stats = engine.get_stats()
        assert stats["total_modules"] > 0
        assert stats["privesc"] > 0
        assert stats["persistence"] > 0

    def test_format_for_prompt(self):
        engine = PostExploitEngine()
        output = engine.format_for_prompt("linux")
        assert "Post-Exploitation Modules" in output


class TestPayloadGenerator:
    def test_generate_bash(self):
        gen = PayloadGenerator()
        payloads = gen.generate("10.0.0.1", 4444, "bash")
        assert len(payloads) > 0
        assert "10.0.0.1" in payloads[0]["payload"]
        assert "4444" in payloads[0]["payload"]

    def test_generate_python(self):
        gen = PayloadGenerator()
        payloads = gen.generate("10.0.0.1", 5555, "python")
        assert len(payloads) > 0

    def test_generate_powershell(self):
        gen = PayloadGenerator()
        payloads = gen.generate("10.0.0.1", 4444, "powershell")
        assert len(payloads) > 0

    def test_generate_all(self):
        gen = PayloadGenerator()
        payloads = gen.generate_all("10.0.0.1", 4444)
        assert len(payloads) > 10

    def test_generate_meterpreter(self):
        gen = PayloadGenerator()
        payload = gen.generate_meterpreter("10.0.0.1", 4444, "elf")
        assert "msfvenom" in payload["command"]
        assert "10.0.0.1" in payload["command"]

    def test_generate_with_encoding(self):
        gen = PayloadGenerator()
        payloads = gen.generate("10.0.0.1", 4444, "bash", encoding="base64")
        assert payloads[0]["encoded"] is not None

    def test_generate_with_obfuscation(self):
        gen = PayloadGenerator()
        payloads = gen.generate("10.0.0.1", 4444, "bash", obfuscate=True)
        assert payloads[0]["obfuscated"] is not None

    def test_format_for_prompt(self):
        gen = PayloadGenerator()
        output = gen.format_for_prompt("10.0.0.1", 4444)
        assert "Payload Generator" in output


class TestComplianceMapper:
    def test_map_owasp_injection(self):
        mapper = ComplianceMapper()
        result = mapper.map_finding("SQL injection found on login form")
        assert len(result["owasp"]) > 0

    def test_map_owasp_xss(self):
        mapper = ComplianceMapper()
        result = mapper.map_finding("Reflected XSS vulnerability in search parameter")
        assert len(result["owasp"]) > 0

    def test_map_mitre_exploit(self):
        mapper = ComplianceMapper()
        result = mapper.map_finding("CVE-2021-41773 exploit successful RCE")
        assert len(result["mitre"]) > 0

    def test_map_mitre_brute_force(self):
        mapper = ComplianceMapper()
        result = mapper.map_finding("Brute force attack with hydra found valid credentials")
        assert len(result["mitre"]) > 0

    def test_map_nist(self):
        mapper = ComplianceMapper()
        result = mapper.map_finding("Authentication bypass on admin panel")
        assert len(result["nist"]) > 0

    def test_map_ptes(self):
        mapper = ComplianceMapper()
        result = mapper.map_finding("Exploitation of remote code execution vulnerability")
        assert len(result["ptes"]) > 0

    def test_map_cve(self):
        mapper = ComplianceMapper()
        cve = {"cve": "CVE-2021-41773", "desc": "Apache path traversal RCE", "severity": "critical", "type": "rce"}
        result = mapper.map_cve(cve)
        assert len(result["owasp"]) > 0 or len(result["mitre"]) > 0

    def test_format_for_prompt(self):
        mapper = ComplianceMapper()
        commands = [{"command": "nmap -sV target", "output": "port 80 open Apache 2.4.49 vulnerability"}]
        output = mapper.format_for_prompt(commands)
        assert "Compliance Mapping" in output

    def test_get_report_section(self):
        mapper = ComplianceMapper()
        commands = [{"command": "nmap -sV target", "output": "CVE-2021-41773 Apache RCE"}]
        section = mapper.get_report_section(commands)
        assert "owasp" in section
        assert "mitre" in section


class TestAttackTimeline:
    def test_add_event(self):
        timeline = AttackTimeline()
        event = timeline.add_event("nmap -sV 10.0.0.1", "port 80 open", "nmap")
        assert event["phase"] == "scanning"
        assert event["tool"] == "nmap"

    def test_add_event_exploit(self):
        timeline = AttackTimeline()
        event = timeline.add_event("msfconsole exploit", "session opened", "metasploit")
        assert event["phase"] == "exploitation"

    def test_add_events_from_commands(self):
        timeline = AttackTimeline()
        commands = [
            {"command": "nmap -sV target", "output": "port 80 open", "tool": "nmap"},
            {"command": "msfconsole -x exploit", "output": "session opened", "tool": "msfconsole"},
        ]
        timeline.add_events_from_commands(commands)
        assert len(timeline.events) == 2

    def test_get_phase_summary(self):
        timeline = AttackTimeline()
        timeline.add_event("nmap -sV target", "port 80 open", "nmap")
        timeline.add_event("gobuster dir", "admin found", "gobuster")
        summary = timeline.get_phase_summary()
        assert "scanning" in summary or "enumeration" in summary

    def test_get_attack_path(self):
        timeline = AttackTimeline()
        timeline.add_event("nmap -sV target", "port 80 open", "nmap")
        timeline.add_event("msfconsole exploit", "session opened", "metasploit")
        path = timeline.get_attack_path()
        assert len(path) >= 1

    def test_export_json(self):
        timeline = AttackTimeline()
        timeline.add_event("nmap -sV target", "port 80 open", "nmap")
        data = timeline.export_json()
        assert "events" in data
        assert "phases" in data

    def test_format_for_prompt(self):
        timeline = AttackTimeline()
        timeline.add_event("nmap -sV target", "port 80 open", "nmap")
        output = timeline.format_for_prompt()
        assert "Attack Timeline" in output


class TestNetworkDiscovery:
    def test_get_subnet(self):
        nd = NetworkDiscovery()
        subnet = nd.get_subnet_from_ip("192.168.1.100")
        assert subnet == "192.168.1.0/24"

    def test_get_adjacent_subnets(self):
        nd = NetworkDiscovery()
        adjacent = nd.get_adjacent_subnets("192.168.1.100")
        assert len(adjacent) == 2
        assert "192.168.0.0/24" in adjacent
        assert "192.168.2.0/24" in adjacent

    def test_generate_discovery_plan(self):
        nd = NetworkDiscovery()
        plan = nd.generate_discovery_plan("192.168.1.100", "basic")
        assert plan["target"] == "192.168.1.100"
        assert len(plan["commands"]) >= 2

    def test_generate_discovery_plan_full(self):
        nd = NetworkDiscovery()
        plan = nd.generate_discovery_plan("192.168.1.100", "full")
        assert len(plan["commands"]) >= 4

    def test_parse_discovery_output(self):
        nd = NetworkDiscovery()
        output = "Nmap scan report for host1 (192.168.1.1)\nNmap scan report for host2 (192.168.1.2)"
        hosts = nd.parse_discovery_output(output)
        assert len(hosts) == 2

    def test_format_for_prompt(self):
        nd = NetworkDiscovery()
        output = nd.format_for_prompt("192.168.1.100")
        assert "Network Discovery Plan" in output


class TestWordlistGenerator:
    def test_generate_from_target(self):
        gen = WordlistGenerator()
        target = {"name": "TestCorp", "domain": "testcorp.com"}
        wordlist = gen.generate_from_target(target)
        assert len(wordlist) > 0
        assert "testcorp" in wordlist
        assert "Testcorp" in wordlist

    def test_generate_usernames(self):
        gen = WordlistGenerator()
        target = {"first_name": "john", "last_name": "doe", "domain": "testcorp.com"}
        usernames = gen.generate_usernames(target)
        assert len(usernames) > 0
        assert "john.doe" in usernames
        assert "johndoe" in usernames

    def test_generate_mutation(self):
        gen = WordlistGenerator()
        mutations = gen.generate_mutation("password")
        assert len(mutations) > 5
        assert "password" in mutations
        assert "Password" in mutations

    def test_generate_custom(self):
        gen = WordlistGenerator()
        wordlist = gen.generate_custom(["hello", "world"])
        assert len(wordlist) > 0

    def test_get_stats(self):
        gen = WordlistGenerator()
        stats = gen.get_stats()
        assert stats["common_passwords"] > 0
        assert stats["common_usernames"] > 0

    def test_format_for_prompt(self):
        gen = WordlistGenerator()
        output = gen.format_for_prompt({"name": "TestCorp", "domain": "testcorp.com"})
        assert "Smart Wordlist Generator" in output


class TestIntegration:
    def test_exploit_engine_with_post_exploit(self):
        ee = ExploitEngine()
        pe = PostExploitEngine()
        matches = ee.match(port=80, service="Apache")
        assert len(matches) > 0
        post_suggestions = pe.suggest("linux", "privesc")
        assert len(post_suggestions) > 0

    def test_compliance_with_exploit_engine(self):
        mapper = ComplianceMapper()
        ee = ExploitEngine()
        matches = ee.match(port=80, service="Apache")
        for m in matches:
            mapping = mapper.map_cve(m)
            assert isinstance(mapping, dict)

    def test_timeline_with_commands(self):
        timeline = AttackTimeline()
        commands = [
            {"command": "nmap -sV 10.0.0.1", "output": "port 80 open Apache 2.4.49", "tool": "nmap"},
            {"command": "msfconsole -x exploit", "output": "session opened", "tool": "msfconsole"},
        ]
        timeline.add_events_from_commands(commands)
        path = timeline.get_attack_path()
        assert len(path) >= 1

    def test_network_discovery_with_exploit_engine(self):
        nd = NetworkDiscovery()
        ee = ExploitEngine()
        plan = nd.generate_discovery_plan("192.168.1.100")
        assert plan["subnet"] is not None
        matches = ee.match(port=80)
        assert isinstance(matches, list)

    def test_full_pipeline(self):
        brain = SessionBrain()
        brain.start("test-session", "Test objective")
        brain.update_after_command("nmap -sV 10.0.0.1", "port 22 open ssh\nport 80 open Apache 2.4.49")

        ee = ExploitEngine()
        matches = ee.match_from_brain(brain.state)
        assert isinstance(matches, list)

        pe = PostExploitEngine()
        post = pe.suggest("linux")
        assert len(post) > 0

        mapper = ComplianceMapper()
        timeline = AttackTimeline()
        timeline.add_event("nmap -sV 10.0.0.1", "port 80 open Apache", "nmap")
        assert len(timeline.events) > 0

    def test_safety_with_payload_generator(self):
        shield = SafetyShield()
        gen = PayloadGenerator()
        payloads = gen.generate("10.0.0.1", 4444, "bash")
        for p in payloads:
            allowed, _ = shield.check_command(f"echo '{p['payload']}'")
            assert isinstance(allowed, bool)

    def test_compressor_with_timeline(self):
        compressor = ContextCompressor()
        timeline = AttackTimeline()
        timeline.add_event("nmap -sV target", "port 80 open Apache 2.4.49 CVE-2021-41773", "nmap")
        summary = timeline.format_for_prompt()
        compressed = compressor.compress(summary)
        assert len(compressed) > 0
