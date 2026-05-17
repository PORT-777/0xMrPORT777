import pytest
from core.context_compressor import ContextCompressor


class TestContextCompressor:
    def test_compress_short_output_unchanged(self):
        output = "line1\nline2\nline3"
        result = ContextCompressor.compress(output, max_lines=15)
        assert result == output

    def test_compress_long_output_reduces_lines(self):
        lines = [f"line {i}" for i in range(100)]
        output = "\n".join(lines)
        result = ContextCompressor.compress(output, max_lines=15)
        result_lines = result.split("\n")
        assert len(result_lines) <= 20

    def test_compress_empty_output(self):
        result = ContextCompressor.compress("")
        assert result == "[empty]"

    def test_compress_none_output(self):
        result = ContextCompressor.compress(None)
        assert result == "[empty]"

    def test_extract_nmap_header(self):
        output = "Starting Nmap 7.94\nNmap scan report for 192.168.1.1\nPORT   STATE SERVICE"
        header = ContextCompressor._extract_header(output)
        assert "Nmap scan report" in header or "Starting Nmap" in header

    def test_stats_open_ports(self):
        output = "80/tcp open  http\n443/tcp open  https\n22/tcp closed ssh"
        stats = ContextCompressor._get_stats(output)
        assert "OpenPorts:2" in stats

    def test_stats_cves(self):
        output = "Found CVE-2021-41773 and CVE-2023-44487"
        stats = ContextCompressor._get_stats(output)
        assert "CVEs:2" in stats

    def test_stats_credentials(self):
        output = "[22][ssh] host: 192.168.1.1 login: admin password: secret"
        stats = ContextCompressor._get_stats(output)
        assert "Credentials:1" in stats

    def test_important_line_open_port(self):
        assert ContextCompressor._is_important_line("80/tcp open  http") is True

    def test_important_line_cve(self):
        assert ContextCompressor._is_important_line("CVE-2021-41773 found") is True

    def test_important_line_login(self):
        assert ContextCompressor._is_important_line("login: admin password: secret") is True

    def test_important_line_banner(self):
        assert ContextCompressor._is_important_line("Banner: Apache/2.4.49") is True

    def test_important_line_noise(self):
        assert ContextCompressor._is_important_line("just some random text") is False

    def test_extract_structured_ips(self):
        output = "Scanning 192.168.1.1 and 10.0.0.5"
        data = ContextCompressor.extract_structured(output)
        assert "192.168.1.1" in data["ips"]
        assert "10.0.0.5" in data["ips"]

    def test_extract_structured_excludes_localhost(self):
        output = "Scanning 127.0.0.1 and 192.168.1.1"
        data = ContextCompressor.extract_structured(output)
        assert "127.0.0.1" not in data["ips"]
        assert "192.168.1.1" in data["ips"]

    def test_extract_structured_cves(self):
        output = "CVE-2021-41773 CVE-2023-44487"
        data = ContextCompressor.extract_structured(output)
        assert len(data["cves"]) == 2

    def test_extract_structured_urls(self):
        output = "Visit http://example.com and https://test.com/path"
        data = ContextCompressor.extract_structured(output)
        assert len(data["urls"]) == 2
