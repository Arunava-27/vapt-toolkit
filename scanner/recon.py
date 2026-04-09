"""
Subdomain enumeration and passive recon module.

Wordlist files (in wordlists/ dir, relative to project root):
  • subdomains-ctf.txt       ~180 names  — fast, CTF-focused
  • subdomains-top5000.txt   5 000 names — good general coverage  (default)
  • subdomains-top20000.txt  20 000 names— deep enumeration

Discovery methods:
  1. Certificate Transparency  — crt.sh (passive, no key)
  2. HackerTarget API          — hackertarget.com (passive, no key)
  3. RapidDNS scrape           — rapiddns.io (passive, no key)
  4. DNS brute-force           — loaded from wordlist file

Resolution per subdomain:
  • A   records (IPv4)
  • AAAA records (IPv6)
  • CNAME chain (full canonical path)
  • MX / NS / A for root domain

CDN detection via CNAME patterns for 49+ providers.
"""
import asyncio
import re
import os
from pathlib import Path
from typing import Optional

import aiohttp
import dns.asyncresolver
import dns.resolver
import dns.exception


# ── Wordlist loading ──────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_WORDLISTS_DIR = _PROJECT_ROOT / "wordlists"

WORDLIST_PRESETS = {
    "ctf":     "subdomains-ctf.txt",
    "small":   "subdomains-ctf.txt",
    "medium":  "subdomains-top5000.txt",
    "large":   "subdomains-top20000.txt",
}

# Minimal built-in fallback (used only when files are missing)
_BUILTIN_FALLBACK = [
    "www","mail","ftp","dev","api","admin","test","staging","portal",
    "login","auth","vpn","remote","git","jenkins","app","beta","demo",
    "static","cdn","media","docs","shop","blog","internal","backup",
    "db","mysql","redis","elastic","kibana","monitor","dashboard",
    "ns1","ns2","mx1","smtp","imap","webmail","autodiscover","secure",
]


def load_wordlist(preset: str = "medium", custom_path: str | None = None) -> list[str]:
    """
    Load a wordlist and return as a list of stripped, lowercase, non-empty strings.
    Priority: custom_path > preset file > built-in fallback.
    """
    path: Path | None = None

    if custom_path:
        path = Path(custom_path)
    elif preset in WORDLIST_PRESETS:
        path = _WORDLISTS_DIR / WORDLIST_PRESETS[preset]
    else:
        # Try treating preset as a bare filename in the wordlists dir
        candidate = _WORDLISTS_DIR / preset
        if candidate.exists():
            path = candidate

    if path and path.exists():
        words = [
            line.strip().lower()
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        return words

    # Fallback — warn and continue
    import warnings
    warnings.warn(
        f"Wordlist not found (preset={preset!r}, path={path}). "
        "Using built-in fallback. Run: python -c \"from scanner.recon import download_wordlists; "
        "import asyncio; asyncio.run(download_wordlists())\"",
        RuntimeWarning, stacklevel=2,
    )
    return _BUILTIN_FALLBACK


async def download_wordlists():
    """Download SecLists wordlists into the wordlists/ directory."""
    _WORDLISTS_DIR.mkdir(parents=True, exist_ok=True)
    urls = {
        "subdomains-top5000.txt": (
            "https://raw.githubusercontent.com/danielmiessler/SecLists"
            "/master/Discovery/DNS/subdomains-top1million-5000.txt"
        ),
        "subdomains-top20000.txt": (
            "https://raw.githubusercontent.com/danielmiessler/SecLists"
            "/master/Discovery/DNS/subdomains-top1million-20000.txt"
        ),
    }
    async with aiohttp.ClientSession() as session:
        for fname, url in urls.items():
            dest = _WORDLISTS_DIR / fname
            if dest.exists():
                print(f"  [skip] {fname} already exists")
                continue
            print(f"  [download] {fname} ...")
            async with session.get(url) as r:
                if r.status == 200:
                    dest.write_bytes(await r.read())
                    print(f"  [ok] {fname}")
                else:
                    print(f"  [fail] {fname} — HTTP {r.status}")


# ── CDN fingerprints (CNAME suffix → CDN name) ────────────────────────────────
CDN_CNAME_MAP = {
    "cdn.cloudflare.net":     "Cloudflare",
    ".cloudflare.com":        "Cloudflare",
    "cloudfront.net":         "AWS CloudFront",
    "elb.amazonaws.com":      "AWS ELB",
    "amazonaws.com":          "AWS",
    "fastly.net":             "Fastly",
    "fastlylb.net":           "Fastly",
    "akamai.net":             "Akamai",
    "akamaiedge.net":         "Akamai",
    "akamaitechnologies.com": "Akamai",
    "akadns.net":             "Akamai",
    "akamaized.net":          "Akamai",
    "incapdns.net":           "Imperva Incapsula",
    "impervadns.net":         "Imperva Incapsula",
    "sucuri.net":             "Sucuri",
    "azurewebsites.net":      "Azure App Service",
    "trafficmanager.net":     "Azure Traffic Manager",
    "azureedge.net":          "Azure CDN",
    "azurefd.net":            "Azure Front Door",
    "googleusercontent.com":  "Google Cloud",
    "googleapis.com":         "Google Cloud",
    "appspot.com":            "Google App Engine",
    "netlify.app":            "Netlify",
    "netlify.com":            "Netlify",
    "vercel.app":             "Vercel",
    "vercel.com":             "Vercel",
    ".now.sh":                "Vercel",
    "heroku.com":             "Heroku",
    "herokudns.com":          "Heroku",
    "myshopify.com":          "Shopify",
    "pantheonsite.io":        "Pantheon",
    "squarespace.com":        "Squarespace",
    "wpvip.com":              "WordPress VIP",
    "kxcdn.com":              "KeyCDN",
    "b-cdn.net":              "BunnyCDN",
    "limelight.com":          "Limelight",
    "llnwd.net":              "Limelight",
    "edgecastcdn.net":        "Edgio",
    "edgio.net":              "Edgio",
    "stackpathcdn.com":       "StackPath",
    "cachefly.net":           "CacheFly",
    "cdn77.org":              "CDN77",
    "rackcdn.com":            "Rackspace CDN",
    "github.io":              "GitHub Pages",
    "onrender.com":           "Render",
    "fly.dev":                "Fly.io",
    "railway.app":            "Railway",
    "pages.dev":              "Cloudflare Pages",
    "web.app":                "Firebase",
    "firebaseapp.com":        "Firebase",
}


def _detect_cdn(cname_chain: list[str]) -> Optional[str]:
    for cname in cname_chain:
        cn = cname.lower().rstrip(".")
        for pattern, provider in CDN_CNAME_MAP.items():
            if cn.endswith(pattern.lower().lstrip(".")):
                return provider
    return None


# ── DNS resolution ────────────────────────────────────────────────────────────

async def _resolve_host(host: str) -> dict:
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout  = 3
    resolver.lifetime = 5

    ipv4: list[str] = []
    ipv6: list[str] = []
    cname_chain: list[str] = []

    try:
        ans = await resolver.resolve(host, "A")
        ipv4 = [r.address for r in ans]
        canonical = ans.canonical_name.to_text()
        if canonical.rstrip(".").lower() != host.lower():
            cname_chain.append(canonical)
    except Exception:
        pass

    if not cname_chain:
        try:
            ans = await resolver.resolve(host, "CNAME")
            target = ans[0].target.to_text()
            cname_chain.append(target)
            try:
                ans2 = await resolver.resolve(target.rstrip("."), "CNAME")
                cname_chain.append(ans2[0].target.to_text())
            except Exception:
                pass
        except Exception:
            pass

    try:
        ans = await resolver.resolve(host, "AAAA")
        ipv6 = [r.address for r in ans]
    except Exception:
        pass

    cdn = _detect_cdn(cname_chain) if cname_chain else None

    return {
        "ipv4": ipv4,
        "ipv6": ipv6,
        "cname_chain": [c.rstrip(".") for c in cname_chain],
        "cdn": cdn,
    }


# ── Passive sources ───────────────────────────────────────────────────────────

async def _crtsh(session: aiohttp.ClientSession, domain: str) -> set[str]:
    subs: set[str] = set()
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status == 200:
                data = await r.json(content_type=None)
                for entry in data:
                    for n in entry.get("name_value", "").splitlines():
                        n = n.strip().lower().lstrip("*.")
                        if n.endswith(f".{domain}"):
                            sub = n[: -len(f".{domain}")]
                            if sub and "." not in sub:
                                subs.add(sub)
    except Exception:
        pass
    return subs


async def _hackertarget(session: aiohttp.ClientSession, domain: str) -> set[str]:
    subs: set[str] = set()
    try:
        async with session.get(
            f"https://api.hackertarget.com/hostsearch/?q={domain}",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as r:
            if r.status == 200:
                for line in (await r.text()).splitlines():
                    if "," in line:
                        host = line.split(",")[0].strip().lower()
                        if host.endswith(f".{domain}"):
                            sub = host[: -len(f".{domain}")]
                            if sub and "." not in sub:
                                subs.add(sub)
    except Exception:
        pass
    return subs


async def _rapiddns(session: aiohttp.ClientSession, domain: str) -> set[str]:
    subs: set[str] = set()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; vapt-toolkit/1.0)"}
    try:
        async with session.get(
            f"https://rapiddns.io/subdomain/{domain}?full=1",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as r:
            if r.status == 200:
                for m in re.finditer(
                    r'<td>([a-z0-9_\-]+)\.' + re.escape(domain) + r'</td>',
                    await r.text(), re.I,
                ):
                    subs.add(m.group(1).lower())
    except Exception:
        pass
    return subs


# ── Brute-force ───────────────────────────────────────────────────────────────

async def _brute_dns(subs: list[str], domain: str, concurrency: int = 80,
                     progress_cb=None) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)
    found: list[dict] = []
    total = len(subs)
    done_count = 0

    async def probe(sub: str):
        nonlocal done_count
        async with sem:
            host = f"{sub}.{domain}"
            info = await _resolve_host(host)
            if info["ipv4"] or info["ipv6"]:
                found.append({
                    "subdomain": host,
                    "ips":       info["ipv4"],
                    "ipv4":      info["ipv4"],
                    "ipv6":      info["ipv6"],
                    "cname":     info["cname_chain"],
                    "cdn":       info["cdn"],
                    "source":    "brute",
                })
            done_count += 1
            if progress_cb and total > 0 and done_count % 250 == 0:
                pct = int(done_count * 100 / total)
                await progress_cb(
                    f"DNS brute-force: {done_count}/{total} ({pct}%) — {len(found)} hit(s) so far"
                )

    await asyncio.gather(*[probe(s) for s in subs])
    return found


# ── Root domain info ──────────────────────────────────────────────────────────

async def _root_info(domain: str) -> dict:
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = 3
    resolver.lifetime = 5
    mx: list[str] = []
    ns: list[str] = []
    a:  list[str] = []
    try:
        mx = sorted({str(r.exchange).rstrip(".") for r in await resolver.resolve(domain, "MX")})
    except Exception:
        pass
    try:
        ns = sorted({str(r.target).rstrip(".") for r in await resolver.resolve(domain, "NS")})
    except Exception:
        pass
    try:
        a = [r.address for r in await resolver.resolve(domain, "A")]
    except Exception:
        pass
    return {"mx": mx, "ns": ns, "a": a}


# ── Main scanner class ────────────────────────────────────────────────────────

class ReconScanner:
    def __init__(self, domain: str, wordlist: str = "medium",
                 custom_wordlist_path: str | None = None):
        """
        domain              — target domain (e.g. example.com)
        wordlist            — preset name: "ctf" | "medium" (default) | "large"
                              or a filename inside the wordlists/ directory
        custom_wordlist_path — absolute/relative path to any file; overrides preset
        """
        self.domain = domain.lower().strip()
        self.wordlist_preset = wordlist
        self.custom_wordlist_path = custom_wordlist_path

    async def run(self, progress_cb=None) -> dict:
        words = load_wordlist(self.wordlist_preset, self.custom_wordlist_path)
        wordlist_size = len(words)

        if progress_cb:
            await progress_cb(
                f"Querying passive sources: crt.sh, HackerTarget, RapidDNS…"
            )
        async with aiohttp.ClientSession() as session:
            passive_sets = await asyncio.gather(
                _crtsh(session, self.domain),
                _hackertarget(session, self.domain),
                _rapiddns(session, self.domain),
            )

        passive_subs: set[str] = set().union(*passive_sets)
        if progress_cb:
            await progress_cb(
                f"Passive sources returned {len(passive_subs)} unique subdomain(s)"
            )

        brute_list = sorted(set(words) | passive_subs)
        if progress_cb:
            await progress_cb(
                f"Starting DNS brute-force on {len(brute_list)} candidate(s) "
                f"(wordlist: {wordlist_size}, passive: {len(passive_subs)})…"
            )

        all_found = await _brute_dns(brute_list, self.domain, progress_cb=progress_cb)

        seen: set[str] = set()
        unique: list[dict] = []
        for item in all_found:
            if item["subdomain"] not in seen:
                seen.add(item["subdomain"])
                unique.append(item)

        unique.sort(key=lambda x: (0 if x["cdn"] is None else 1, x["subdomain"]))

        root = await _root_info(self.domain)

        return {
            "domain":        self.domain,
            "subdomains":    unique,
            "root":          root,
            "passive_found": len(passive_subs),
            "wordlist_size": wordlist_size,
            "total":         len(unique),
        }
