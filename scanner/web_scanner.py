"""Web vulnerability scanner — SQLi, XSS, open redirect detection."""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

SQLI_PAYLOADS = ["'", "' OR '1'='1", "\" OR \"1\"=\"1", "' OR 1=1--", "'; DROP TABLE users--"]
XSS_PAYLOADS = ['<script>alert(1)</script>', '"><img src=x onerror=alert(1)>', "';alert(1)//"]
REDIRECT_PARAMS = ["redirect", "url", "next", "return", "returnTo", "goto", "dest", "destination"]
REDIRECT_PAYLOAD = "https://evil.example.com"

SQLI_ERRORS = [
    "sql syntax", "mysql_fetch", "ora-", "syntax error", "unclosed quotation",
    "pg_query", "sqlite3", "you have an error in your sql syntax",
]


def inject_param(url: str, param: str, payload: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    qs[param] = [payload]
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


class WebScanner:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.findings = []

    async def fetch(self, session: aiohttp.ClientSession, url: str, **kwargs):
        try:
            async with session.get(url, allow_redirects=False, timeout=self.timeout, **kwargs) as resp:
                text = await resp.text(errors="ignore")
                return resp.status, resp.headers, text
        except Exception:
            return None, {}, ""

    async def fetch_post(self, session: aiohttp.ClientSession, url: str, data: dict):
        try:
            async with session.post(url, data=data, allow_redirects=False, timeout=self.timeout) as resp:
                text = await resp.text(errors="ignore")
                return resp.status, text
        except Exception:
            return None, ""

    async def collect_forms(self, session: aiohttp.ClientSession) -> list[dict]:
        _, _, html = await self.fetch(session, self.base_url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        forms = []
        for form in soup.find_all("form"):
            action = urljoin(self.base_url, form.get("action") or "")
            method = (form.get("method") or "get").lower()
            inputs = {
                inp.get("name"): inp.get("value", "test")
                for inp in form.find_all("input")
                if inp.get("name")
            }
            forms.append({"action": action, "method": method, "inputs": inputs})
        return forms

    async def collect_url_params(self, session: aiohttp.ClientSession) -> list[str]:
        """Collect query parameters from links on the base page."""
        _, _, html = await self.fetch(session, self.base_url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        params = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            parsed = urlparse(href)
            if parsed.query:
                params.update(parse_qs(parsed.query).keys())
        return list(params)

    async def test_sqli_url(self, session: aiohttp.ClientSession, param: str):
        for payload in SQLI_PAYLOADS:
            url = inject_param(self.base_url, param, payload)
            _, _, body = await self.fetch(session, url)
            if any(err in body.lower() for err in SQLI_ERRORS):
                self.findings.append({
                    "type": "SQL Injection",
                    "severity": "Critical",
                    "location": url,
                    "parameter": param,
                    "payload": payload,
                    "evidence": "SQL error message in response",
                })
                return  # one finding per param is enough

    async def test_xss_url(self, session: aiohttp.ClientSession, param: str):
        for payload in XSS_PAYLOADS:
            url = inject_param(self.base_url, param, payload)
            _, _, body = await self.fetch(session, url)
            if payload in body:
                self.findings.append({
                    "type": "Reflected XSS",
                    "severity": "High",
                    "location": url,
                    "parameter": param,
                    "payload": payload,
                    "evidence": "Payload reflected in response body",
                })
                return

    async def test_open_redirect(self, session: aiohttp.ClientSession):
        for param in REDIRECT_PARAMS:
            url = inject_param(self.base_url, param, REDIRECT_PAYLOAD)
            status, headers, _ = await self.fetch(session, url)
            location = headers.get("Location", "")
            if status in (301, 302, 303, 307, 308) and REDIRECT_PAYLOAD in location:
                self.findings.append({
                    "type": "Open Redirect",
                    "severity": "Medium",
                    "location": url,
                    "parameter": param,
                    "payload": REDIRECT_PAYLOAD,
                    "evidence": f"Redirects to {location}",
                })

    async def test_sqli_form(self, session: aiohttp.ClientSession, form: dict):
        for field in form["inputs"]:
            for payload in SQLI_PAYLOADS:
                data = {**form["inputs"], field: payload}
                _, body = await self.fetch_post(session, form["action"], data)
                if any(err in body.lower() for err in SQLI_ERRORS):
                    self.findings.append({
                        "type": "SQL Injection (Form)",
                        "severity": "Critical",
                        "location": form["action"],
                        "parameter": field,
                        "payload": payload,
                        "evidence": "SQL error message in response",
                    })
                    break

    async def test_xss_form(self, session: aiohttp.ClientSession, form: dict):
        for field in form["inputs"]:
            for payload in XSS_PAYLOADS:
                data = {**form["inputs"], field: payload}
                _, body = await self.fetch_post(session, form["action"], data)
                if payload in body:
                    self.findings.append({
                        "type": "Reflected XSS (Form)",
                        "severity": "High",
                        "location": form["action"],
                        "parameter": field,
                        "payload": payload,
                        "evidence": "Payload reflected in response body",
                    })
                    break

    async def run(self) -> dict:
        async with aiohttp.ClientSession() as session:
            forms = await self.collect_forms(session)
            url_params = await self.collect_url_params(session)

            tasks = []

            for param in url_params:
                tasks.append(self.test_sqli_url(session, param))
                tasks.append(self.test_xss_url(session, param))

            tasks.append(self.test_open_redirect(session))

            for form in forms:
                tasks.append(self.test_sqli_form(session, form))
                tasks.append(self.test_xss_form(session, form))

            await asyncio.gather(*tasks)

        return {
            "target": self.base_url,
            "findings": self.findings,
            "total": len(self.findings),
        }
