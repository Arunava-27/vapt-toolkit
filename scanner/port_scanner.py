"""
Enhanced port scanner — python-nmap wrapper with:
  • Scan types:  SYN (-sS), Connect (-sT), Aggressive (-A), UDP (-sU), SYN+UDP
  • OS detection (-O --osscan-guess) with multiple match candidates
  • NSE scripts: default | banner | vuln | safe | discovery | http-headers | ssl-*
  • Configurable timing T0-T5
  • -Pn skip-ping option for firewalled hosts
  • Per-port: proto, state, product, version, extrainfo, CPE, confidence, script output
  • Host-level: hostname, MAC, vendor, traceroute hops
  • WSL support: auto-detects and uses WSL nmap on Windows
"""
import nmap
import os
import signal
from typing import Optional
from wsl_config import wsl

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
        self._nm: Optional[nmap.PortScanner] = None
        self._stopped = False

    def stop(self):
        """Kill the running nmap process immediately."""
        self._stopped = True
        nm = self._nm
        if nm is None:
            return
        # python-nmap exposes the subprocess as nm._nm_proc_scanprocess
        proc = getattr(nm, "_nm_proc_scanprocess", None)
        if proc is None:
            return
        try:
            if os.name == "nt":
                import subprocess
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True)
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

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
    
    def _parse_nmap_xml(self, xml_str: str, args: str) -> dict:
        """Parse nmap XML output from WSL nmap scan."""
        import logging
        import xml.etree.ElementTree as ET
        logger = logging.getLogger(__name__)
        
        try:
            root = ET.fromstring(xml_str)
        except Exception as e:
            logger.error(f"[PORT_SCANNER] Failed to parse XML: {str(e)}")
            return {
                "target": self.target,
                "host_info": {},
                "os_info": {},
                "open_ports": [],
                "traceroute": [],
                "scan_args": args,
                "error": f"Failed to parse nmap XML: {str(e)}"
            }
        
        open_ports = []
        os_info = {}
        host_info = {}
        traceroute = []
        
        # Parse host information
        for host in root.findall('.//host'):
            status = host.find('status')
            if status is None or status.get('state') != 'up':
                continue
            
            addr = host.find('address[@addr]')
            target_ip = addr.get('addr') if addr is not None else self.target
            
            # Host name
            hostname_elem = host.find('hostnames/hostname[@name]')
            hostname = hostname_elem.get('name') if hostname_elem is not None else ""
            
            # Host state
            host_state = status.get('state', 'unknown')
            
            # MAC and vendor
            mac_addr = ""
            vendor = ""
            for addr in host.findall('address'):
                if addr.get('addrtype') == 'mac':
                    mac_addr = addr.get('addr', '')
                    vendor_elem = host.find(f"address[@vendor][@addr='{mac_addr}']")
                    if vendor_elem is not None:
                        vendor = vendor_elem.get('vendor', '')
            
            host_info = {
                "ip": target_ip,
                "hostname": hostname,
                "state": host_state,
                "mac": mac_addr,
                "vendor": vendor,
            }
            
            # OS detection
            osmatch = host.find('os/osmatch[@name]')
            if osmatch is not None:
                os_classes = osmatch.findall('osclass')
                cpe_str = ""
                if os_classes:
                    cpes = os_classes[0].findall('cpe')
                    cpe_str = cpes[0].text if cpes else ""
                
                os_info = {
                    "name": osmatch.get('name', ''),
                    "accuracy": int(osmatch.get('accuracy', 0)),
                    "cpe": cpe_str,
                    "type": os_classes[0].get('type', '') if os_classes else "",
                    "osfamily": os_classes[0].get('osfamily', '') if os_classes else "",
                    "osgen": os_classes[0].get('osgen', '') if os_classes else "",
                    "all_matches": []
                }
                
                # All OS matches
                for om in host.findall('os/osmatch'):
                    os_info["all_matches"].append({
                        "name": om.get('name', ''),
                        "accuracy": int(om.get('accuracy', 0))
                    })
                os_info["all_matches"] = os_info["all_matches"][:5]
            
            # Traceroute
            traceroute_elem = host.find('trace')
            if traceroute_elem is not None:
                for hop in traceroute_elem.findall('hop'):
                    traceroute.append({
                        "hop": int(hop.get('ttl', 0)),
                        "ip": hop.get('ipaddr', ''),
                        "rtt": hop.get('rtt', '')
                    })
            
            # Ports
            for port in host.findall('.//port'):
                state_elem = port.find('state')
                if state_elem is None or state_elem.get('state') not in ('open', 'open|filtered'):
                    continue
                
                proto = port.get('protocol', 'tcp')
                port_num = port.get('portid', '')
                
                service_elem = port.find('service[@name]')
                service_name = service_elem.get('name', '') if service_elem is not None else ''
                product = service_elem.get('product', '') if service_elem is not None else ''
                version = service_elem.get('version', '') if service_elem is not None else ''
                extrainfo = service_elem.get('extrainfo', '') if service_elem is not None else ''
                conf = int(service_elem.get('conf', 0)) if service_elem is not None else 0
                
                # Scripts
                scripts = {}
                for script in port.findall('script'):
                    script_id = script.get('id', '')
                    script_output = script.get('output', '')
                    if script_id:
                        scripts[script_id] = script_output.strip()
                
                open_ports.append({
                    "port": int(port_num) if port_num.isdigit() else port_num,
                    "proto": proto,
                    "state": state_elem.get('state') if state_elem is not None else 'unknown',
                    "service": service_name,
                    "product": product,
                    "version": version,
                    "extrainfo": extrainfo,
                    "conf": conf,
                    "scripts": scripts,
                })
        
        logger.info(f"[PORT_SCANNER] Parsed {len(open_ports)} open ports from XML")
        return {
            "target": self.target,
            "host_info": host_info,
            "os_info": os_info,
            "open_ports": open_ports,
            "traceroute": traceroute,
            "scan_args": args
        }

    def run(self) -> dict:
        import logging
        import platform
        import tempfile
        import xml.etree.ElementTree as ET
        logger = logging.getLogger(__name__)
        logger.info(f"[PORT_SCANNER] run() called for target {self.target}")
        
        if self._stopped:
            logger.info(f"[PORT_SCANNER] Scan stopped, returning empty results")
            return {"target": self.target, "host_info": {}, "os_info": {}, "open_ports": [], "traceroute": [], "scan_args": ""}
        
        # Determine which nmap to use
        use_wsl = False
        if wsl.nmap_path and wsl.nmap_path.startswith('/'):
            # WSL path detected (Linux path like /usr/bin/nmap)
            use_wsl = True
            logger.info(f"[PORT_SCANNER] Using WSL nmap at {wsl.nmap_path}")
        elif platform.system() == "Windows":
            # Windows nmap
            logger.info(f"[PORT_SCANNER] Using Windows nmap")
        else:
            # Linux/other
            if not wsl.nmap_path:
                logger.error(f"[PORT_SCANNER] Nmap not found")
                return {
                    "target": self.target,
                    "host_info": {},
                    "os_info": {},
                    "open_ports": [],
                    "traceroute": [],
                    "scan_args": "",
                    "error": f"Nmap not found. Install with: apt install nmap"
                }
            use_wsl = True
            logger.info(f"[PORT_SCANNER] Using Linux nmap at {wsl.nmap_path}")
        
        # Build nmap arguments
        self._nm = None
        args, ports_arg = self._build_args()
        
        # Use WSL nmap via wsl.run_nmap_command() if needed (for network access to targets)
        if use_wsl:
            try:
                logger.info(f"[PORT_SCANNER] Using WSL nmap via wsl.run_nmap_command()")
                
                # Build full nmap command
                nmap_args = [self.target]
                if ports_arg:
                    nmap_args.extend(['-p', ports_arg])
                nmap_args.extend(args.split())
                nmap_args.insert(0, '-oX')  # Add XML output first
                
                # Create temp file for XML output
                import uuid
                temp_xml = f"/tmp/nmap_{uuid.uuid4().hex}.xml"
                nmap_args.insert(1, temp_xml)
                
                logger.info(f"[PORT_SCANNER] Running: nmap {' '.join(nmap_args)}")
                result = wsl.run_nmap_command(nmap_args)
                
                if result.returncode != 0:
                    logger.error(f"[PORT_SCANNER] Nmap failed: {result.stderr}")
                    return {
                        "target": self.target,
                        "host_info": {},
                        "os_info": {},
                        "open_ports": [],
                        "traceroute": [],
                        "scan_args": args,
                        "error": f"Nmap scan failed: {result.stderr}"
                    }
                
                # Read and parse XML output from WSL
                try:
                    import subprocess
                    read_result = subprocess.run(
                        ["wsl.exe", "cat", temp_xml],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    xml_str = read_result.stdout
                except Exception as e:
                    logger.error(f"[PORT_SCANNER] Failed to read XML: {str(e)}")
                    xml_str = ""
                
                logger.info(f"[PORT_SCANNER] Nmap XML output received ({len(xml_str)} bytes)")
                return self._parse_nmap_xml(xml_str, args)
                
            except Exception as e:
                logger.error(f"[PORT_SCANNER] WSL nmap execution failed: {str(e)}")
                return {
                    "target": self.target,
                    "host_info": {},
                    "os_info": {},
                    "open_ports": [],
                    "traceroute": [],
                    "scan_args": args,
                    "error": f"WSL nmap failed: {str(e)}"
                }
        
        # Use python-nmap for Windows nmap
        try:
            logger.info(f"[PORT_SCANNER] Creating nmap PortScanner")
            nm = nmap.PortScanner()
            logger.info(f"[PORT_SCANNER] nmap PortScanner created successfully")
        except Exception as e:
            logger.error(f"[PORT_SCANNER] Nmap initialization failed: {str(e)}")
            return {
                "target": self.target,
                "host_info": {},
                "os_info": {},
                "open_ports": [],
                "traceroute": [],
                "scan_args": "",
                "error": f"Nmap initialization failed: {str(e)}"
            }
        
        self._nm = nm
        logger.info(f"[PORT_SCANNER] Starting nmap scan with args: {args}")
        nm.scan(self.target, ports_arg, arguments=args)
        logger.info(f"[PORT_SCANNER] nmap scan completed")
        logger.info(f"[PORT_SCANNER] Found {len(nm.all_hosts())} hosts")
        self._nm = None
        if self._stopped:
            return {"target": self.target, "host_info": {}, "os_info": {}, "open_ports": [], "traceroute": [], "scan_args": args}

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

                    # Parse confidence, handling empty strings from nmap
                    conf_val = s.get("conf", 0)
                    try:
                        conf = int(conf_val) if conf_val else 0
                    except (ValueError, TypeError):
                        conf = 0
                    
                    open_ports.append({
                        "port":      port,
                        "proto":     proto.upper(),
                        "state":     s.get("state", "open"),
                        "service":   s.get("name", ""),
                        "product":   s.get("product", ""),
                        "version":   s.get("version", ""),
                        "extrainfo": s.get("extrainfo", ""),
                        "cpe":       s.get("cpe", ""),
                        "conf":      conf,
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
