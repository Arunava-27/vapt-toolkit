"""CVE correlation module — queries NVD API for known vulnerabilities."""
import asyncio
import os
import aiohttp

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
# Without API key: 5 req / 30s → throttle to 1 req / 6s
# With NVD_API_KEY env var: 50 req / 30s → 1 req / 0.6s
_API_KEY = os.environ.get("NVD_API_KEY", "")
_REQUEST_DELAY = 0.6 if _API_KEY else 6.0


class CVEScanner:
    def __init__(self, open_ports: list[dict]):
        self.open_ports = open_ports

    async def query_nvd(self, session: aiohttp.ClientSession, keyword: str) -> list[dict]:
        headers = {"apiKey": _API_KEY} if _API_KEY else {}
        params = {"keywordSearch": keyword, "resultsPerPage": 5}
        try:
            async with session.get(
                NVD_API_URL, params=params, headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 429:
                    # Rate limited — wait and retry once
                    await asyncio.sleep(30)
                    async with session.get(NVD_API_URL, params=params, headers=headers,
                                           timeout=aiohttp.ClientTimeout(total=15)) as r2:
                        data = await r2.json() if r2.status == 200 else {}
                elif resp.status == 200:
                    data = await resp.json()
                else:
                    return []

                cves = []
                for item in data.get("vulnerabilities", []):
                    cve = item.get("cve", {})
                    cve_id = cve.get("id", "N/A")
                    descriptions = cve.get("descriptions", [])
                    description = next(
                        (d["value"] for d in descriptions if d.get("lang") == "en"), "N/A"
                    )
                    metrics = cve.get("metrics", {})
                    severity, score = "N/A", "N/A"
                    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                        if key in metrics and metrics[key]:
                            m = metrics[key][0]
                            cvss_data = m.get("cvssData", {})
                            severity = cvss_data.get("baseSeverity") or m.get("baseSeverity", "N/A")
                            score = cvss_data.get("baseScore", "N/A")
                            break
                    cves.append({"cve_id": cve_id, "description": description[:300],
                                 "severity": severity, "score": score})
                return cves
        except Exception:
            return []

    async def run(self) -> dict:
        results = []
        async with aiohttp.ClientSession() as session:
            for entry in self.open_ports:
                service = entry.get("service", "").strip()
                version = entry.get("version", "").strip()
                if not service:
                    continue
                keyword = f"{service} {version}".strip() if version else service
                cves = await self.query_nvd(session, keyword)
                results.append({
                    "port": entry["port"],
                    "service": service,
                    "version": version,
                    "cves": cves,
                })
                # Throttle to respect NVD rate limits
                await asyncio.sleep(_REQUEST_DELAY)

        total_cves = sum(len(r["cves"]) for r in results)
        return {"correlations": results, "total_cves": total_cves}
