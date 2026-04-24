"""Enhanced surface mapping: endpoint discovery, parameter extraction, and inventory building."""
import asyncio
import re
import json
from typing import Optional, Dict, List, Set, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import aiohttp


@dataclass
class FormField:
    """HTML form input field."""
    name: str
    field_type: str  # text, number, email, password, hidden, file, select, textarea, etc.
    value: str = ""
    required: bool = False


@dataclass
class Form:
    """HTML form."""
    action: str
    method: str  # GET, POST
    fields: List[FormField] = field(default_factory=list)
    enctype: str = "application/x-www-form-urlencoded"  # multipart/form-data for file uploads


@dataclass
class Parameter:
    """URL parameter."""
    name: str
    param_type: str  # string, number, email, file, etc.
    value: str = ""
    source: str = "url"  # url, form, json, header, cookie


@dataclass
class Endpoint:
    """API/Web endpoint."""
    url: str
    method: str  # GET, POST, PUT, DELETE, etc.
    parameters: List[Parameter] = field(default_factory=list)
    forms: List[Form] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    auth_required: bool = False
    response_status: int = 0
    content_type: str = ""
    discovered_via: str = "crawl"  # crawl, javascript, api, form, etc.
    
    def unique_key(self) -> Tuple[str, str]:
        """Get unique key for deduplication."""
        return (self.url, self.method)


class SurfaceMapper:
    """Map application surface: crawl, extract parameters, build endpoint inventory."""
    
    def __init__(self, base_url: str, max_depth: int = 2, max_pages: int = 100, timeout: int = 10):
        """
        Initialize surface mapper.
        
        Args:
            base_url: Starting URL
            max_depth: Crawl depth (0 = only base URL, 1 = one level deep, etc.)
            max_pages: Maximum pages to crawl
            timeout: HTTP request timeout (seconds)
        """
        self.base_url = base_url.rstrip("/")
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
        self.endpoints: Dict[Tuple[str, str], Endpoint] = {}
        self._visited_urls: Set[str] = set()
        self._javascript_urls: Set[str] = set()
    
    # ── URL Helpers ───────────────────────────────────────────────────────────
    
    @staticmethod
    def _same_origin(base: str, url: str) -> bool:
        """Check if URL is same origin as base."""
        base_parsed = urlparse(base)
        url_parsed = urlparse(url)
        return base_parsed.netloc == url_parsed.netloc
    
    @staticmethod
    def _normalize_url(url: str, base_url: str) -> Optional[str]:
        """Normalize and resolve relative URLs."""
        try:
            # Resolve relative URL
            resolved = urljoin(base_url, url)
            parsed = urlparse(resolved)
            
            # Remove fragment
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            
            # Limit query parameters to avoid infinite variations
            if "?" in normalized:
                path, query = normalized.split("?", 1)
                params = query.split("&")
                if len(params) > 10:
                    return None
                normalized = f"{path}?{query}"
            
            return normalized
        except Exception:
            return None
    
    # ── Crawling ───────────────────────────────────────────────────────────────
    
    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> Tuple[Optional[str], Dict[str, str], int]:
        """
        Fetch page content.
        
        Returns: (content, headers, status_code)
        """
        try:
            async with session.get(url, allow_redirects=True, timeout=self.timeout) as resp:
                content = await resp.text(errors="ignore")
                return content, dict(resp.headers), resp.status
        except Exception:
            return None, {}, 0
    
    async def _crawl(
        self,
        session: aiohttp.ClientSession,
        url: str,
        depth: int,
        progress_cb=None,
    ) -> List[str]:
        """
        Recursively crawl pages.
        
        Returns: List of discovered URLs
        """
        if url in self._visited_urls or depth > self.max_depth or len(self._visited_urls) >= self.max_pages:
            return []
        
        self._visited_urls.add(url)
        discovered_urls = [url]
        
        if progress_cb:
            await progress_cb(f"Crawling: {url} (depth {depth})")
        
        # Fetch page
        content, headers, status = await self._fetch_page(session, url)
        if not content:
            return discovered_urls
        
        # Create endpoint from page
        endpoint = Endpoint(
            url=url,
            method="GET",
            headers=dict(headers),
            response_status=status,
            content_type=headers.get("Content-Type", ""),
            discovered_via="crawl",
        )
        
        # Extract parameters from URL
        parsed_url = urlparse(url)
        if parsed_url.query:
            for param_name, param_values in parse_qs(parsed_url.query, keep_blank_values=True).items():
                for param_val in param_values:
                    endpoint.parameters.append(Parameter(
                        name=param_name,
                        param_type="string",
                        value=param_val,
                        source="url",
                    ))
        
        # Store endpoint
        key = endpoint.unique_key()
        if key not in self.endpoints:
            self.endpoints[key] = endpoint
        
        # Parse HTML
        soup = BeautifulSoup(content, "html.parser")
        
        # Extract forms
        await self._extract_forms(soup, url, endpoint)
        
        # Extract links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            normalized = self._normalize_url(href, url)
            if normalized and self._same_origin(self.base_url, normalized) and normalized not in self._visited_urls:
                discovered_urls.extend(
                    await self._crawl(session, normalized, depth + 1, progress_cb)
                )
        
        # Extract JavaScript URLs for further analysis
        for script in soup.find_all("script", src=True):
            script_url = self._normalize_url(script["src"], url)
            if script_url and self._same_origin(self.base_url, script_url):
                self._javascript_urls.add(script_url)
        
        return discovered_urls
    
    # ── Parameter Extraction ──────────────────────────────────────────────────
    
    async def _extract_forms(self, soup: BeautifulSoup, page_url: str, endpoint: Endpoint):
        """Extract forms from HTML page."""
        for form_elem in soup.find_all("form"):
            action = form_elem.get("action", page_url)
            action = self._normalize_url(action, page_url) or page_url
            method = (form_elem.get("method", "GET") or "GET").upper()
            enctype = form_elem.get("enctype", "application/x-www-form-urlencoded")
            
            form = Form(action=action, method=method, enctype=enctype)
            
            # Extract input fields
            for input_elem in form_elem.find_all(["input", "select", "textarea"]):
                field_name = input_elem.get("name")
                if not field_name:
                    continue
                
                if input_elem.name == "input":
                    field_type = input_elem.get("type", "text").lower()
                    field_value = input_elem.get("value", "")
                    required = "required" in input_elem.attrs
                elif input_elem.name == "select":
                    field_type = "select"
                    field_value = ""
                    required = "required" in input_elem.attrs
                else:  # textarea
                    field_type = "textarea"
                    field_value = input_elem.string or ""
                    required = "required" in input_elem.attrs
                
                form.fields.append(FormField(
                    name=field_name,
                    field_type=field_type,
                    value=field_value,
                    required=required,
                ))
                
                # Also add as parameter to endpoint
                endpoint.parameters.append(Parameter(
                    name=field_name,
                    param_type=field_type,
                    value=field_value,
                    source="form",
                ))
            
            endpoint.forms.append(form)
            
            # Create endpoint for form action if different
            if action != endpoint.url or method != endpoint.method:
                form_endpoint = Endpoint(
                    url=action,
                    method=method,
                    parameters=[],
                    forms=[form],
                    discovered_via="form",
                )
                key = form_endpoint.unique_key()
                if key not in self.endpoints:
                    self.endpoints[key] = form_endpoint
    
    async def _extract_json_endpoints(self, session: aiohttp.ClientSession, progress_cb=None) -> List[Endpoint]:
        """Extract API endpoints from JSON responses."""
        json_endpoints = []
        
        # Try common API endpoints
        api_paths = [
            "/api",
            "/api/v1",
            "/api/v2",
            "/graphql",
            "/rest/api",
            "/v1",
            "/v2",
        ]
        
        for path in api_paths:
            url = urljoin(self.base_url, path)
            normalized = self._normalize_url(url, self.base_url)
            if not normalized:
                continue
            
            if progress_cb:
                await progress_cb(f"Checking API endpoint: {normalized}")
            
            content, headers, status = await self._fetch_page(session, normalized)
            if status == 200 and content:
                try:
                    # Try to parse as JSON
                    data = json.loads(content)
                    
                    # Look for common API response patterns
                    if isinstance(data, dict):
                        endpoint = Endpoint(
                            url=normalized,
                            method="GET",
                            headers=dict(headers),
                            response_status=status,
                            content_type=headers.get("Content-Type", ""),
                            discovered_via="api_scan",
                        )
                        key = endpoint.unique_key()
                        if key not in self.endpoints:
                            self.endpoints[key] = endpoint
                        json_endpoints.append(endpoint)
                except json.JSONDecodeError:
                    pass
        
        return json_endpoints
    
    async def _analyze_javascript(self, session: aiohttp.ClientSession, progress_cb=None):
        """Analyze JavaScript for API endpoints and parameter hints."""
        # Regex patterns for common API calls
        patterns = [
            r'fetch\(["\']([^"\']+)["\']',
            r'XMLHttpRequest.*open\(["\']([A-Z]+)["\'],\s*["\']([^"\']+)["\']',
            r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']',
            r'\.ajax\(\{[^}]*url:\s*["\']([^"\']+)["\']',
            r'@(GET|POST|PUT|DELETE)\(["\']([^"\']+)["\']',  # Java annotations
        ]
        
        for js_url in list(self._javascript_urls)[:10]:  # Limit to first 10 JS files
            if progress_cb:
                await progress_cb(f"Analyzing JavaScript: {js_url}")
            
            content, _, status = await self._fetch_page(session, js_url)
            if status == 200 and content:
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            # Handle multiple capture groups
                            endpoint_url = match[-1] if match else ""
                        else:
                            endpoint_url = match
                        
                        if endpoint_url and endpoint_url.startswith("/"):
                            normalized = self._normalize_url(endpoint_url, self.base_url)
                            if normalized and self._same_origin(self.base_url, normalized):
                                endpoint = Endpoint(
                                    url=normalized,
                                    method="GET",
                                    discovered_via="javascript",
                                )
                                key = endpoint.unique_key()
                                if key not in self.endpoints:
                                    self.endpoints[key] = endpoint
    
    # ── Results & Output ──────────────────────────────────────────────────────
    
    async def run(self, progress_cb=None) -> dict:
        """
        Run surface mapping.
        
        Returns: Endpoint inventory
        """
        async with aiohttp.ClientSession() as session:
            # Phase 1: Crawl pages
            if progress_cb:
                await progress_cb(f"Starting crawl from {self.base_url} (max depth: {self.max_depth})")
            
            await self._crawl(session, self.base_url, 0, progress_cb)
            
            # Phase 2: Extract API endpoints
            if progress_cb:
                await progress_cb("Scanning for API endpoints...")
            
            await self._extract_json_endpoints(session, progress_cb)
            
            # Phase 3: Analyze JavaScript
            if progress_cb:
                await progress_cb("Analyzing JavaScript for API calls...")
            
            await self._analyze_javascript(session, progress_cb)
        
        # Build results
        results = {
            "target": self.base_url,
            "total_endpoints": len(self.endpoints),
            "total_parameters": sum(len(e.parameters) for e in self.endpoints.values()),
            "total_forms": sum(len(e.forms) for e in self.endpoints.values()),
            "endpoints": [
                {
                    "url": e.url,
                    "method": e.method,
                    "parameters": [
                        {"name": p.name, "type": p.param_type, "value": p.value, "source": p.source}
                        for p in e.parameters
                    ],
                    "forms": [
                        {
                            "action": f.action,
                            "method": f.method,
                            "enctype": f.enctype,
                            "fields": [
                                {"name": fld.name, "type": fld.field_type, "required": fld.required}
                                for fld in f.fields
                            ],
                        }
                        for f in e.forms
                    ],
                    "response_status": e.response_status,
                    "content_type": e.content_type,
                    "discovered_via": e.discovered_via,
                }
                for e in self.endpoints.values()
            ],
        }
        
        return results
    
    def get_endpoints(self) -> List[Endpoint]:
        """Get all discovered endpoints."""
        return list(self.endpoints.values())
    
    def get_endpoints_by_method(self, method: str) -> List[Endpoint]:
        """Get endpoints by HTTP method."""
        return [e for e in self.endpoints.values() if e.method == method]
    
    def get_endpoints_with_parameters(self) -> List[Endpoint]:
        """Get endpoints that have parameters."""
        return [e for e in self.endpoints.values() if e.parameters or e.forms]
    
    def get_vulnerable_endpoints(self) -> List[Endpoint]:
        """Get endpoints most likely to have vulnerabilities."""
        # Filter for POST/PUT/DELETE and endpoints with parameters
        vulnerable = []
        for e in self.endpoints.values():
            if (e.method in ("POST", "PUT", "DELETE", "PATCH") or e.parameters or e.forms):
                vulnerable.append(e)
        return sorted(vulnerable, key=lambda x: len(x.parameters) + len(x.forms), reverse=True)
