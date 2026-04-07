"""Port scanning using python-nmap."""
import nmap

# Port range presets — "top-N" triggers --top-ports N instead of a range
PRESETS = {
    "top-100":  ("--top-ports 100",  None),
    "top-1000": ("--top-ports 1000", None),
    "top-5000": ("--top-ports 5000", None),
}

class PortScanner:
    def __init__(self, target: str, port_range: str = "top-1000", version_detect: bool = False):
        self.target = target
        self.port_range = port_range
        self.version_detect = version_detect

    def run(self) -> dict:
        nm = nmap.PortScanner()
        base = "-T4 --open -n"
        if self.version_detect:
            base += " -sV --version-intensity 5"

        if self.port_range in PRESETS:
            extra, ports_arg = PRESETS[self.port_range]
            nm.scan(self.target, ports_arg, arguments=f"{base} {extra}")
        else:
            nm.scan(self.target, self.port_range, arguments=base)

        open_ports = []
        for host in nm.all_hosts():
            for proto in nm[host].all_protocols():
                for port in sorted(nm[host][proto].keys()):
                    state = nm[host][proto][port]
                    if state["state"] == "open":
                        open_ports.append({
                            "port": port,
                            "service": state.get("name", ""),
                            "version": state.get("version", ""),
                            "product": state.get("product", ""),
                        })
        return {"target": self.target, "open_ports": open_ports}
