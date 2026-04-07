"""
Enhanced port scanner — python-nmap wrapper with:
  • Scan types:  SYN (-sS), Connect (-sT), Aggressive (-A), UDP (-sU), SYN+UDP
  • OS detection (-O --osscan-guess) with multiple match candidates
  • NSE scripts: default | banner | vuln | safe | discovery | http-headers | ssl-*
  • Configurable timing T0-T5
  • -Pn skip-ping option for firewalled hosts
  • Per-port: proto, state, product, version, extrainfo, CPE, confidence, script output
  • Host-level: hostname, MAC, vendor, traceroute hops
"""
import nmap
from typing import Optional

# ── Presets ───────────────────────────────────────────────────────────────────

RANGE_PRESETS: dict[str, tuple[str, Optional[str]]] = {
    "top-100":  ("--top-ports 100",  None),
    "top-1000": ("--top-ports 1000", None),
    "top-5000": ("--top-ports 5000", None),
    "full":     ("",                 "1-65535"),
}

SCAN_TYPE_FLAGS: dict[str, str] = {
    "connect":    "-sT",
    "syn":        "-sS",
    "udp":        "-sU",
    "syn_udp":    "-sS -sU",
    "aggressive": "-A",
}

SCRIPT_PRESETS: dict[str, str] = {
    "":            "",
    "default":     "--script=default",
    "banner":      "--script=banner",
    "vuln":        "--script=vuln",
    "safe":        "--script=safe",
    "discovery":   "--script=discovery",
    "http":        "--script=http-headers,http-title,http-methods,http-robots.txt",
    "ssl":         "--script=ssl-cert,ssl-enum-ciphers,ssl-dh-params",
    "smb":         "--script=smb-os-discovery,smb-security-mode,smb-vuln-ms17-010",
    "ftp":         "--script=ftp-anon,ftp-banner,ftp-syst",
    "ssh":         "--script=ssh-auth-methods,ssh-hostkey,ssh2-enum-algos",
    "dns":         "--script=dns-recursion,dns-zone-transfer",
    "smtp":        "--script=smtp-open-relay,smtp-commands,smtp-ntlm-info",
}


class PortScanner:
    def __init__(
        self,
        target: str,
        port_range: str = "top-1000",
        version_detect: bool = False,
        scan_type: str = "connect",
        os_detect: bool = False,
        script: str = "",
        timing: int = 4,
        skip_ping: bool = False,
        extra_flags: str = "",
    ):
        self.target       = target
        self.port_range   = port_range
        self.version_detect = version_detect
        self.scan_type    = scan_type
        self.os_detect    = os_detect
        self.script       = script
        self.timing       = max(0, min(5, int(timing)))
        self.skip_ping    = skip_ping
        self.extra_flags  = extra_flags.strip()

    def _build_args(self) -> tuple[str, Optional[str]]:
        parts: list[str] = [f"-T{self.timing}", "--open -n"]

        is_aggressive = self.scan_type == "aggressive"
        type_flag = SCAN_TYPE_FLAGS.get(self.scan_type, "-sT")
        parts.append(type_flag)

        if self.skip_ping:
            parts.append("-Pn")

        if is_aggressive:
            # -A already includes -sV, -sC, -O, --traceroute
            parts.append("--osscan-guess --version-intensity 7")
        else:
            if self.version_detect:
                parts.append("-sV --version-intensity 7")
            if self.os_detect:
                parts.append("-O --osscan-guess")
            script_flag = SCRIPT_PRESETS.get(self.script, "")
            if script_flag:
                parts.append(script_flag)

        if self.extra_flags:
            parts.append(self.extra_flags)

        args = " ".join(parts)

        if self.port_range in RANGE_PRESETS:
            extra_arg, ports_arg = RANGE_PRESETS[self.port_range]
            if extra_arg:
                args += " " + extra_arg
            return args, ports_arg

        return args, self.port_range if self.port_range else None

    def run(self) -> dict:
        nm = nmap.PortScanner()
        args, ports_arg = self._build_args()
        nm.scan(self.target, ports_arg, arguments=args)

        open_ports: list[dict] = []
        os_info:    dict       = {}
        host_info:  dict       = {}
        traceroute: list[dict] = []

        for host in nm.all_hosts():
            h = nm[host]

            # ── Host info ──────────────────────────────────────────────────────
            vendor_map = h.get("vendor", {})
            mac = h.get("addresses", {}).get("mac", "")
            host_info = {
                "ip":       host,
                "hostname": h.hostname() or "",
                "state":    h.state(),
                "mac":      mac,
                "vendor":   vendor_map.get(mac, "") if mac else "",
            }

            # ── OS detection ───────────────────────────────────────────────────
            if h.get("osmatch"):
                best = h["osmatch"][0]
                os_classes = best.get("osclass", [])
                cpe_str = ""
                if os_classes:
                    cpes = os_classes[0].get("cpe", [])
                    cpe_str = cpes[0] if cpes else ""
                os_info = {
                    "name":        best.get("name", ""),
                    "accuracy":    int(best.get("accuracy", 0)),
                    "cpe":         cpe_str,
                    "type":        os_classes[0].get("type", "") if os_classes else "",
                    "osfamily":    os_classes[0].get("osfamily", "") if os_classes else "",
                    "osgen":       os_classes[0].get("osgen", "") if os_classes else "",
                    "all_matches": [
                        {"name": m.get("name", ""), "accuracy": int(m.get("accuracy", 0))}
                        for m in h["osmatch"][:5]
                    ],
                }

            # ── Traceroute ─────────────────────────────────────────────────────
            if "tcp" in h and hasattr(h, "get"):
                tr = h.get("trace", {})
                if tr:
                    traceroute = [
                        {"hop": int(t.get("ttl", i + 1)), "ip": t.get("ipaddr", ""), "rtt": t.get("rtt", "")}
                        for i, t in enumerate(tr.get("hops", []))
                    ]

            # ── Ports ──────────────────────────────────────────────────────────
            for proto in h.all_protocols():
                for port in sorted(h[proto].keys()):
                    s = h[proto][port]
                    if s.get("state") not in ("open", "open|filtered"):
                        continue

                    scripts: dict[str, str] = {
                        sid: out.strip()
                        for sid, out in s.get("script", {}).items()
                    }

                    open_ports.append({
                        "port":      port,
                        "proto":     proto.upper(),
                        "state":     s.get("state", "open"),
                        "service":   s.get("name", ""),
                        "product":   s.get("product", ""),
                        "version":   s.get("version", ""),
                        "extrainfo": s.get("extrainfo", ""),
                        "cpe":       s.get("cpe", ""),
                        "conf":      int(s.get("conf", 0)),
                        "scripts":   scripts,
                    })

        return {
            "target":     self.target,
            "host_info":  host_info,
            "os_info":    os_info,
            "open_ports": open_ports,
            "traceroute": traceroute,
            "scan_args":  args,
        }
