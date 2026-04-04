"""Subdomain enumeration and passive recon module."""
import asyncio
import aiohttp
import dns.resolver

class ReconScanner:
    WORDLIST = ["www", "mail", "ftp", "dev", "api", "admin", "test", "staging", "portal"]

    def __init__(self, domain: str):
        self.domain = domain

    async def check_subdomain(self, session, sub: str) -> dict | None:
        host = f"{sub}.{self.domain}"
        try:
            answers = dns.resolver.resolve(host, "A")
            ips = [r.address for r in answers]
            return {"subdomain": host, "ips": ips}
        except Exception:
            return None

    async def run(self) -> dict:
        results = {"domain": self.domain, "subdomains": []}
        async with aiohttp.ClientSession() as session:
            tasks = [self.check_subdomain(session, sub) for sub in self.WORDLIST]
            found = await asyncio.gather(*tasks)
        results["subdomains"] = [r for r in found if r]
        return results
