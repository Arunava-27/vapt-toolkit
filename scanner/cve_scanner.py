"""CVE correlation module — queries NVD API for known vulnerabilities."""
import asyncio
import aiohttp

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


class CVEScanner:
    def __init__(self, open_ports: list[dict]):
        """
        open_ports: list of dicts with keys 'port', 'service', 'version'
        """
        self.open_ports = open_ports

    async def query_nvd(self, session: aiohttp.ClientSession, keyword: str) -> list[dict]:
        params = {"keywordSearch": keyword, "resultsPerPage": 5}
        try:
            async with session.get(NVD_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                cves = []
                for item in data.get("vulnerabilities", []):
                    cve = item.get("cve", {})
                    cve_id = cve.get("id", "N/A")
                    descriptions = cve.get("descriptions", [])
                    description = next(
                        (d["value"] for d in descriptions if d.get("lang") == "en"), "N/A"
                    )
                    metrics = cve.get("metrics", {})
                    severity = "N/A"
                    score = "N/A"
                    # Prefer CVSSv3.1, fallback to v3.0, then v2
                    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                        if key in metrics and metrics[key]:
                            m = metrics[key][0]
                            cvss_data = m.get("cvssData", {})
                            severity = (
                                cvss_data.get("baseSeverity")
                                or m.get("baseSeverity", "N/A")
                            )
                            score = cvss_data.get("baseScore", "N/A")
                            break
                    cves.append({
                        "cve_id": cve_id,
                        "description": description[:300],
                        "severity": severity,
                        "score": score,
                    })
                return cves
        except Exception:
            return []

    async def run(self) -> dict:
        results = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            service_entries = []
            for entry in self.open_ports:
                service = entry.get("service", "").strip()
                version = entry.get("version", "").strip()
                if not service:
                    continue
                keyword = f"{service} {version}".strip() if version else service
                service_entries.append({"port": entry["port"], "service": service, "version": version, "keyword": keyword})
                tasks.append(self.query_nvd(session, keyword))

            cve_lists = await asyncio.gather(*tasks)

            for entry, cves in zip(service_entries, cve_lists):
                results.append({
                    "port": entry["port"],
                    "service": entry["service"],
                    "version": entry["version"],
                    "cves": cves,
                })

        total_cves = sum(len(r["cves"]) for r in results)
        return {"correlations": results, "total_cves": total_cves}
