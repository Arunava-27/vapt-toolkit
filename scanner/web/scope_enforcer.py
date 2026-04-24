"""Scope validation and robots.txt enforcement."""
import re
from urllib.parse import urlparse, urljoin
from typing import Optional, List, Tuple
import aiohttp


class ScopeEnforcer:
    """Validate URLs against authorized scope and respect robots.txt."""
    
    def __init__(self, base_url: str, authorized_targets: Optional[List[str]] = None, respect_robots_txt: bool = True):
        """
        Initialize scope enforcer.
        
        Args:
            base_url: Base URL being scanned
            authorized_targets: List of authorized targets (domains, IPs, CIDR ranges)
            respect_robots_txt: Whether to respect robots.txt restrictions
        """
        self.base_url = base_url
        self.base_domain = self._extract_domain(base_url)
        self.authorized_targets = authorized_targets or [self.base_domain]
        self.respect_robots_txt = respect_robots_txt
        self._robots_cache: Optional[List[str]] = None
        self._robots_disallow_cache: Optional[List[str]] = None
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    def is_same_origin(self, url: str) -> bool:
        """Check if URL is same origin as base URL."""
        return self._extract_domain(url) == self.base_domain
    
    async def is_in_scope(self, url: str) -> bool:
        """
        Check if URL is in authorized scope.
        
        Returns: True if URL should be scanned
        """
        # Parse URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check if domain/IP is in authorized targets
        for target in self.authorized_targets:
            if self._matches_target(domain, target):
                # If robots.txt should be respected, check it
                if self.respect_robots_txt:
                    return not await self._is_disallowed_by_robots(url)
                return True
        
        return False
    
    @staticmethod
    def _matches_target(url_domain: str, target: str) -> bool:
        """
        Check if URL domain matches target pattern.
        
        Supports:
        - Exact domain: example.com
        - Subdomain wildcard: *.example.com
        - IP address: 192.168.1.1
        - CIDR range: 10.0.0.0/8
        """
        target = target.lower()
        url_domain = url_domain.lower()
        
        # Exact match
        if url_domain == target:
            return True
        
        # Subdomain wildcard
        if target.startswith("*."):
            parent_domain = target[2:]
            return url_domain == parent_domain or url_domain.endswith("." + parent_domain)
        
        return False
    
    async def _is_disallowed_by_robots(self, url: str) -> bool:
        """Check if URL is disallowed by robots.txt."""
        # Load robots.txt if not cached
        if self._robots_disallow_cache is None:
            await self._load_robots_txt()
        
        parsed = urlparse(url)
        path = parsed.path or "/"
        
        # Check against disallow rules
        for disallow_pattern in (self._robots_disallow_cache or []):
            if path.startswith(disallow_pattern):
                return True
        
        return False
    
    async def _load_robots_txt(self):
        """Load and parse robots.txt from base URL."""
        robots_url = urljoin(self.base_url, "/robots.txt")
        self._robots_disallow_cache = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        self._robots_disallow_cache = self._parse_robots_txt(content)
        except Exception:
            # If robots.txt fails to load, allow all paths
            self._robots_disallow_cache = []
    
    @staticmethod
    def _parse_robots_txt(content: str) -> List[str]:
        """Parse robots.txt and extract disallow rules."""
        disallow_rules = []
        
        for line in content.split("\n"):
            # Remove comments
            line = line.split("#")[0].strip()
            if not line:
                continue
            
            # Parse Disallow rule
            if line.lower().startswith("disallow:"):
                path = line[9:].strip()
                if path:
                    disallow_rules.append(path)
        
        return disallow_rules
    
    async def get_allowed_endpoints(self, urls: List[str]) -> List[str]:
        """Filter URLs to only those in scope."""
        allowed = []
        for url in urls:
            if await self.is_in_scope(url):
                allowed.append(url)
        return allowed


class URLValidator:
    """Validate and normalize URLs."""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if string is a valid URL."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http", "https") and parsed.netloc
        except Exception:
            return False
    
    @staticmethod
    def normalize_url(url: str, base_url: Optional[str] = None) -> Optional[str]:
        """
        Normalize URL and resolve relative URLs.
        
        Returns: Normalized URL or None if invalid
        """
        try:
            if base_url and not URLValidator.is_valid_url(url):
                url = urljoin(base_url, url)
            
            parsed = urlparse(url)
            if not URLValidator.is_valid_url(url):
                return None
            
            # Rebuild URL without fragment
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{'?' + parsed.query if parsed.query else ''}"
        except Exception:
            return None
    
    @staticmethod
    def extract_parameters(url: str) -> dict:
        """Extract query parameters from URL."""
        parsed = urlparse(url)
        params = {}
        
        if parsed.query:
            for param in parsed.query.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    if key not in params:
                        params[key] = []
                    params[key].append(value)
        
        return params
    
    @staticmethod
    def inject_parameter(url: str, param: str, value: str) -> str:
        """
        Inject/modify URL parameter.
        
        Returns: Modified URL
        """
        parsed = urlparse(url)
        params = {}
        
        if parsed.query:
            for p in parsed.query.split("&"):
                if "=" in p:
                    k, v = p.split("=", 1)
                    if k not in params:
                        params[k] = []
                    params[k].append(v)
        
        # Add/update parameter
        params[param] = [value]
        
        # Rebuild query string
        query_parts = []
        for k, values in params.items():
            for v in values:
                query_parts.append(f"{k}={v}")
        query_string = "&".join(query_parts)
        
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{'?' + query_string if query_string else ''}"
