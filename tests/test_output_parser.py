import pytest
from utils.output_parser import OutputParser


class TestOutputParser:
    def test_parse_nmap_ports(self):
        output = "Nmap scan report for 192.168.1.1\nPORT   STATE SERVICE\n22/tcp open  ssh\n80/tcp open  http\n443/tcp open  https"
        data = OutputParser.parse_nmap(output)
        assert len(data["ports"]) >= 2
        assert data["ports"][0]["port"] == "22"
        assert data["ports"][0]["service"] == "ssh"

    def test_parse_nmap_hosts(self):
        output = "Nmap scan report for 192.168.1.1\nNmap scan report for 10.0.0.5"
        data = OutputParser.parse_nmap(output)
        assert len(data["hosts"]) == 2
        assert "192.168.1.1" in data["hosts"]

    def test_parse_nmap_os(self):
        output = "OS details: Linux 5.4"
        data = OutputParser.parse_nmap(output)
        assert len(data["os_detections"]) == 1
        assert "Linux 5.4" in data["os_detections"][0]

    def test_parse_nmap_empty(self):
        data = OutputParser.parse_nmap("")
        assert data["ports"] == []
        assert data["hosts"] == []

    def test_parse_gobuster(self):
        output = """
/index.html (Status: 200)
/admin (Status: 301)
/login.php (Status: 200)
        """
        urls = OutputParser.parse_gobuster(output)
        assert len(urls) == 0

    def test_parse_hydra_credentials(self):
        output = "[22][ssh] host: 192.168.1.1   login: admin   password: secret123"
        creds = OutputParser.parse_hydra(output)
        assert len(creds) == 1
        assert creds[0]["username"] == "admin"
        assert creds[0]["password"] == "secret123"
        assert creds[0]["host"] == "192.168.1.1"

    def test_parse_hydra_multiple(self):
        output = """
[22][ssh] host: 192.168.1.1   login: root   password: toor
[22][ssh] host: 192.168.1.1   login: admin   password: admin
        """
        creds = OutputParser.parse_hydra(output)
        assert len(creds) == 2

    def test_extract_ips(self):
        output = "Scanning 192.168.1.1 and 10.0.0.5 and 172.16.0.1"
        ips = OutputParser.extract_ips(output)
        assert len(ips) == 3

    def test_extract_hashes_md5(self):
        output = "hash: d41d8cd98f00b204e9800998ecf8427e"
        hashes = OutputParser.extract_hashes(output)
        assert len(hashes["md5"]) == 1

    def test_extract_hashes_sha256(self):
        output = "hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        hashes = OutputParser.extract_hashes(output)
        assert len(hashes["sha256"]) == 1

    def test_extract_hashes_ntlm(self):
        output = "aad3b435b51404eeaad3b435b51404ee:5f4dcc3b5aa765d61d8327deb882cf99"
        hashes = OutputParser.extract_hashes(output)
        assert len(hashes["ntlm"]) == 1
