"""Port scanning using python-nmap."""
import nmap

class PortScanner:
    def __init__(self, target: str, port_range: str = "1-1024"):
        self.target = target
        self.port_range = port_range

    def run(self) -> dict:
        nm = nmap.PortScanner()
        nm.scan(self.target, self.port_range, arguments="-sV -T4")
        open_ports = []
        for host in nm.all_hosts():
            for proto in nm[host].all_protocols():
                for port in nm[host][proto].keys():
                    state = nm[host][proto][port]
                    if state["state"] == "open":
                        open_ports.append({
                            "port": port,
                            "service": state.get("name", ""),
                            "version": state.get("version", ""),
                        })
        return {"target": self.target, "open_ports": open_ports}
