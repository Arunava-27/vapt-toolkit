"""Multi-source CVE correlation: NVD, CIRCL CVE Search, GitHub Security Advisories, SearchSploit."""
import asyncio
import json
import os
import shutil
import subprocess

import aiohttp

from wsl_config import wsl

# ── API endpoints ──────────────────────────────────────────────────────────────
NVD_API_URL          = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CIRCL_SEARCH_URL     = "https://cve.circl.lu/api/search"
GITHUB_ADVISORIES_URL = "https://api.github.com/advisories"

_NVD_KEY   = os.environ.get("NVD_API_KEY", "")
_NVD_DELAY = 0.6 if _NVD_KEY else 6.0          # 50/30s with key, 5/30s without

_HAS_SEARCHSPLOIT = bool(wsl.searchsploit_path)


class CVEScanner:
    def __init__(self, open_ports: list[dict] = None, recon_data: dict = None):
        """
        Initialize CVE scanner.
        
        Args:
            open_ports: List of port dicts with service/version (from active scans)
            recon_data: Recon results dict with discovered hosts/services (from passive scans)
        """
        self.open_ports = open_ports or []
        self.recon_data = recon_data or {}

    # ── NVD ───────────────────────────────────────────────────────────────────
    async def _query_nvd(self, session: aiohttp.ClientSession, keyword: str) -> list[dict]:
        headers = {"apiKey": _NVD_KEY} if _NVD_KEY else {}
        params  = {"keywordSearch": keyword, "resultsPerPage": 5}
        try:
            async with session.get(NVD_API_URL, params=params, headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 429:
                    await asyncio.sleep(30)
                    async with session.get(NVD_API_URL, params=params, headers=headers,
                                           timeout=aiohttp.ClientTimeout(total=15)) as r2:
                        data = await r2.json() if r2.status == 200 else {}
                elif resp.status == 200:
                    data = await resp.json()
                else:
                    return []

            results = []
            for item in data.get("vulnerabilities", []):
                cve  = item.get("cve", {})
                cid  = cve.get("id", "")
                if not cid:
                    continue
                desc = next((d["value"] for d in cve.get("descriptions", [])
                             if d.get("lang") == "en"), "")
                metrics = cve.get("metrics", {})
                severity, score = "N/A", "N/A"
                for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                    if metrics.get(key):
                        m  = metrics[key][0]
                        cd = m.get("cvssData", {})
                        severity = cd.get("baseSeverity") or m.get("baseSeverity", "N/A")
                        score    = cd.get("baseScore", "N/A")
                        break
                results.append({
                    "cve_id":      cid,
                    "description": desc[:300],
                    "severity":    severity,
                    "score":       score,
                    "source":      "NVD",
                    "references":  [f"https://nvd.nist.gov/vuln/detail/{cid}"],
                    "exploits":    [],
                })
            return results
        except Exception:
            return []

    # ── CIRCL CVE Search (free, no key) ───────────────────────────────────────
    async def _query_circl(self, session: aiohttp.ClientSession, keyword: str) -> list[dict]:
        words = keyword.strip().split()
        vendor  = words[0] if words else keyword
        product = words[1] if len(words) > 1 else words[0]
        candidates = [
            f"{CIRCL_SEARCH_URL}/{vendor}/{product}",
            f"{CIRCL_SEARCH_URL}/{product}/{product}",
        ]
        data = None
        for url in candidates:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        break
            except Exception:
                continue
        if not data:
            return []

        # Ensure items is always a list
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("results", [])
            if not isinstance(items, list):
                items = []
        else:
            items = []
        
        results = []
        for item in items[:5]:
            cid = item.get("id", "")
            if not cid:
                continue
            exploits = [r for r in item.get("references", [])
                        if any(k in r.lower() for k in ("exploit-db", "exploitdb", "/edb-"))]
            raw_score = item.get("cvss", "N/A")
            try:
                score = float(raw_score)
                severity = ("CRITICAL" if score >= 9 else "HIGH" if score >= 7
                            else "MEDIUM" if score >= 4 else "LOW")
            except (ValueError, TypeError):
                score, severity = "N/A", "N/A"
            results.append({
                "cve_id":      cid,
                "description": item.get("summary", "")[:300],
                "severity":    severity,
                "score":       str(score),
                "source":      "CIRCL",
                "references":  item.get("references", [])[:6],
                "exploits":    exploits,
            })
        return results

    # ── GitHub Security Advisories (free, no key for public data) ─────────────
    async def _query_github(self, session: aiohttp.ClientSession, keyword: str) -> list[dict]:
        params  = {"query": keyword, "per_page": 5}
        headers = {"Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28"}
        try:
            async with session.get(GITHUB_ADVISORIES_URL, params=params, headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return []
                items = await resp.json()
        except Exception:
            return []

        _score_map = {"CRITICAL": 9.5, "HIGH": 7.5, "MEDIUM": 5.0, "LOW": 2.0}
        results = []
        for item in (items if isinstance(items, list) else []):
            ghsa_id  = item.get("ghsa_id", "")
            cve_id   = item.get("cve_id") or ghsa_id
            severity = (item.get("severity") or "N/A").upper()
            cvss_obj = item.get("cvss") or {}
            score    = cvss_obj.get("score", _score_map.get(severity, "N/A"))
            desc     = (item.get("description") or item.get("summary") or "")[:300]
            url      = item.get("html_url", f"https://github.com/advisories/{ghsa_id}")
            results.append({
                "cve_id":      cve_id,
                "description": desc,
                "severity":    severity,
                "score":       str(score),
                "source":      "GitHub",
                "references":  [url],
                "exploits":    [],
            })
        return results

    # ── SearchSploit (local exploit-db, if installed) ─────────────────────────
    def _run_searchsploit(self, keyword: str) -> list[dict]:
        if not _HAS_SEARCHSPLOIT:
            return []
        try:
            # Use WSL searchsploit if available
            if wsl.searchsploit_path:
                import platform
                if platform.system() == "Windows":
                    cmd = ["wsl.exe", "searchsploit", "-j", "--disable-colour", keyword]
                else:
                    cmd = [wsl.searchsploit_path, "-j", "--disable-colour", keyword]
            else:
                cmd = ["searchsploit", "-j", "--disable-colour", keyword]
            
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=10, encoding='utf-8', errors='ignore')
            if out.returncode != 0:
                return []
            data = json.loads(out.stdout)
        except json.JSONDecodeError:
            return []
        except Exception as e:
            print(f"SearchSploit error: {e}")
            return []

        results = []
        try:
            for exp in data.get("RESULTS_EXPLOIT", [])[:5]:
                edb_id = exp.get("EDB-ID", "")
                if not edb_id:
                    continue
                edb_url = f"https://www.exploit-db.com/exploits/{edb_id}"
                results.append({
                    "cve_id":           f"EDB-{edb_id}",
                    "description":      exp.get("Title", "")[:300],
                    "severity":         "N/A",
                    "score":            "N/A",
                    "source":           "ExploitDB",
                    "references":       [edb_url],
                    "exploits":         [edb_url],
                    "exploit_type":     exp.get("Type", ""),
                    "exploit_platform": exp.get("Platform", ""),
                })
        except Exception as e:
            print(f"SearchSploit parsing error: {e}")
            return []
        
        return results

    # ── Merge & deduplicate ───────────────────────────────────────────────────
    @staticmethod
    def _merge(lists: list[list[dict]]) -> list[dict]:
        seen: dict[str, dict] = {}
        for lst in lists:
            for item in lst:
                cid = item["cve_id"]
                if cid not in seen:
                    seen[cid] = item
                else:
                    ex = seen[cid]
                    if item["source"] not in ex["source"]:
                        ex["source"] = f"{ex['source']}, {item['source']}"
                    ex["exploits"] = list(set(ex["exploits"] + item["exploits"]))
        return list(seen.values())

    # ── Main ──────────────────────────────────────────────────────────────────
    async def run(self, progress_cb=None) -> dict:
        results = []
        
        # Gather lookup targets from both port scans AND OSINT recon
        lookup_targets = []
        
        # From port scans (active scans)
        for entry in self.open_ports:
            service = entry.get("service", "").strip()
            version = entry.get("version", "").strip()
            if service:
                keyword = f"{service} {version}".strip() if version else service
                lookup_targets.append({
                    "source": "port",
                    "port": entry.get("port", "?"),
                    "service": service,
                    "version": version,
                    "keyword": keyword,
                })
        
        # From OSINT recon (passive scans)
        # For passive scans, we search for CVEs related to the target domain/organization
        if self.recon_data:
            root_domain = self.recon_data.get("domain", "").lower()
            
            # Search for the domain itself (may find organizational CVEs, compromises, etc.)
            if root_domain:
                lookup_targets.append({
                    "source": "osint_domain",
                    "keyword": root_domain,
                })
            
            # Extract organization name if possible (first part of domain)
            org_name = root_domain.split(".")[0] if root_domain else ""
            if org_name and len(org_name) > 3:  # Only if meaningful
                lookup_targets.append({
                    "source": "osint_org",
                    "keyword": org_name,
                })
        
        # If no targets to lookup, return empty
        if not lookup_targets:
            return {"cves": []}
        
        # Deduplicate keywords to avoid excessive requests
        seen_keywords = set()
        unique_targets = []
        for target in lookup_targets:
            kw = target.get("keyword", "").lower().strip()
            if kw and kw not in seen_keywords:
                seen_keywords.add(kw)
                unique_targets.append(target)
        
        lookup_targets = unique_targets
        total_targets = len(lookup_targets)
        
        if progress_cb:
            await progress_cb(f"Searching for CVEs on {total_targets} OSINT target(s)…")
        
        async with aiohttp.ClientSession() as session:
            for i, target in enumerate(lookup_targets):
                keyword = target.get("keyword", "").strip()
                if not keyword:
                    continue
                
                # Progress message depends on source
                if target["source"] == "port":
                    msg = f"CVE lookup {i + 1}/{total_targets}: {keyword} (port {target['port']})"
                else:
                    msg = f"CVE lookup {i + 1}/{total_targets}: {keyword} (OSINT)"
                
                if progress_cb:
                    await progress_cb(msg)
                
                # NVD, CIRCL, GitHub run concurrently
                nvd_cves, circl_cves, gh_cves = await asyncio.gather(
                    self._query_nvd(session, keyword),
                    self._query_circl(session, keyword),
                    self._query_github(session, keyword),
                )
                loop = asyncio.get_event_loop()
                sploit_cves = await loop.run_in_executor(
                    None, self._run_searchsploit, keyword
                )

                merged = self._merge([nvd_cves, circl_cves, gh_cves, sploit_cves])
                
                # Format result based on source
                if target["source"] == "port":
                    results.append({
                        "port":    target["port"],
                        "service": target["service"],
                        "version": target["version"],
                        "cves":    merged,
                    })
                else:
                    results.append({
                        "source":  target["source"],
                        "keyword": keyword,
                        "cves":    merged,
                    })
                
                await asyncio.sleep(_NVD_DELAY)

        total_cves = sum(len(r["cves"]) for r in results)
        sources = ["NVD", "CIRCL", "GitHub Advisory"]
        if _HAS_SEARCHSPLOIT:
            sources.append("ExploitDB (local)")
        return {
            "correlations":          results,
            "total_cves":            total_cves,
            "sources_used":          sources,
            "searchsploit_available": _HAS_SEARCHSPLOIT,
        }
