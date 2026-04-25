"""
JavaScript File Analyzer

Analyzes JavaScript files for:
- Hidden API endpoints (fetch, axios, fetch, etc.)
- Hardcoded secrets (AWS keys, tokens, API keys, etc.)
- Debug code (console.log, debugger statements)
- Exposed source maps
- Security-related TODO/FIXME comments
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urljoin, urlparse
import aiohttp

logger = logging.getLogger(__name__)


class SecretType(Enum):
    """Types of secrets that can be hardcoded"""
    AWS_KEY = "AWS Access Key"
    AWS_SECRET = "AWS Secret Key"
    GITHUB_TOKEN = "GitHub Token"
    STRIPE_KEY = "Stripe API Key"
    SLACK_TOKEN = "Slack Token"
    FIREBASE_KEY = "Firebase Key"
    GENERIC_API_KEY = "Generic API Key"
    BEARER_TOKEN = "Bearer Token"
    JWT_TOKEN = "JWT Token"
    PASSWORD = "Hardcoded Password"


class DebugCodeType(Enum):
    """Types of debug code"""
    CONSOLE_LOG = "console.log"
    CONSOLE_ERROR = "console.error"
    CONSOLE_WARN = "console.warn"
    CONSOLE_DEBUG = "console.debug"
    DEBUGGER = "debugger statement"
    ALERT = "alert() call"
    COMMENTED_AUTH = "Commented-out authentication"


@dataclass
class APIEndpoint:
    """Discovered API endpoint in JavaScript"""
    url: str
    method: str = "GET"
    line_number: int = 0
    source_pattern: str = ""
    full_context: str = ""


@dataclass
class HardcodedSecret:
    """Discovered hardcoded secret in JavaScript"""
    secret_type: SecretType
    pattern_match: str
    line_number: int = 0
    context: str = ""
    severity: str = "High"


@dataclass
class DebugCodeInstance:
    """Found debug code instance"""
    code_type: DebugCodeType
    code_snippet: str
    line_number: int = 0
    context: str = ""


class JavaScriptAnalyzer:
    """Analyzes JavaScript files for security issues"""

    def __init__(self, base_url: str = "", timeout: int = 10):
        """
        Initialize JavaScript analyzer.
        
        Args:
            base_url: Base URL for resolving relative paths
            timeout: HTTP request timeout in seconds
        """
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
        # Pattern definitions for secret detection
        self._secret_patterns = {
            SecretType.AWS_KEY: [
                r'\bAKIA[0-9A-Z]{16}\b',
            ],
            SecretType.AWS_SECRET: [
                r'(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?',
            ],
            SecretType.GITHUB_TOKEN: [
                r'ghp_[A-Za-z0-9_]{36,255}',
                r'gho_[A-Za-z0-9_]{36,255}',
                r'ghu_[A-Za-z0-9_]{36,255}',
            ],
            SecretType.STRIPE_KEY: [
                r'sk_live_[A-Za-z0-9]{10,}',
                r'sk_test_[A-Za-z0-9]{10,}',
                r'pk_live_[A-Za-z0-9]{10,}',
                r'pk_test_[A-Za-z0-9]{10,}',
            ],
            SecretType.SLACK_TOKEN: [
                r'xox[baprs]-[0-9A-Za-z]{10,48}',
            ],
            SecretType.FIREBASE_KEY: [
                r'AIza[0-9A-Za-z\-_]{25,}',
                r'(?:firebase|fb)_?key\s*[=:]\s*["\']([A-Za-z0-9\-_]{20,})["\']',
            ],
            SecretType.GENERIC_API_KEY: [
                r'(?:api[_-]?key|apikey|api-key)\s*[=:]\s*["\']([A-Za-z0-9\-_]{20,})["\']',
                r'(?:api[_-]?secret|apisecret)\s*[=:]\s*["\']([A-Za-z0-9\-_]{20,})["\']',
            ],
            SecretType.BEARER_TOKEN: [
                r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',
                r'bearer\s+[A-Za-z0-9\-._~+/]+=*',
            ],
            SecretType.JWT_TOKEN: [
                r'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.?[A-Za-z0-9_-]*',
            ],
            SecretType.PASSWORD: [
                r'(?:password|passwd|pwd)\s*[=:]\s*["\']([^\'"]{4,})["\']',
            ],
        }
        
        # Pattern definitions for endpoint detection
        self._endpoint_patterns = [
            (r"fetch\(['\"]([^'\"]+)['\"]", "fetch"),
            (r"fetch\(new\s+URL\(['\"]([^'\"]+)['\"]", "fetch (URL constructor)"),
            (r"axios\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]", "axios"),
            (r"\.ajax\(\{[^}]*url\s*:\s*['\"]([^'\"]+)['\"]", "jQuery.ajax"),
            (r"\$\.ajax\(\{[^}]*url\s*:\s*['\"]([^'\"]+)['\"]", "$.ajax"),
            (r"\.open\(['\"]([A-Z]+)['\"],\s*['\"]([^'\"]+)['\"]", "XMLHttpRequest.open"),
            (r"open\(['\"]([A-Z]+)['\"],\s*['\"]([^'\"]+)['\"]", "XMLHttpRequest.open simplified"),
            (r"fetch\(['\"]([^'\"]+)['\"],\s*\{[^}]*method\s*:\s*['\"]([A-Z]+)['\"]", "fetch with method"),
            (r"@(GET|POST|PUT|DELETE|PATCH)\(['\"]([^'\"]+)['\"]", "Java/Spring annotation"),
        ]
        
        # Debug code patterns
        self._debug_patterns = {
            DebugCodeType.CONSOLE_LOG: r'console\.log\s*\(',
            DebugCodeType.CONSOLE_ERROR: r'console\.error\s*\(',
            DebugCodeType.CONSOLE_WARN: r'console\.warn\s*\(',
            DebugCodeType.CONSOLE_DEBUG: r'console\.debug\s*\(',
            DebugCodeType.DEBUGGER: r'\bdebugger\b(?!\s*:)',
            DebugCodeType.ALERT: r'alert\s*\(',
            DebugCodeType.COMMENTED_AUTH: r'//\s*(?:auth|login|password|token|api[_-]?key)',
        }

    async def analyze_js_file(self, js_content: str, file_url: str = "") -> Dict[str, Any]:
        """
        Analyze a single JavaScript file.
        
        Args:
            js_content: JavaScript source code
            file_url: URL of the JavaScript file
            
        Returns:
            Dictionary with endpoints, secrets, and debug code findings
        """
        results = {
            "file_url": file_url,
            "endpoints": self.extract_endpoints(js_content),
            "secrets": self.detect_secrets(js_content),
            "debug_code": self.find_debug_code(js_content),
            "source_maps": self.check_source_maps(file_url),
        }
        
        return results

    def extract_endpoints(self, js_content: str) -> List[Dict[str, Any]]:
        """
        Extract API endpoints from JavaScript code.
        
        Handles:
        - fetch('/api/...')
        - axios.post('/...')
        - jQuery.ajax({url: '...'})
        - XMLHttpRequest.open()
        """
        endpoints = []
        lines = js_content.split('\n')
        
        for pattern, source_type in self._endpoint_patterns:
            try:
                for match in re.finditer(pattern, js_content, re.IGNORECASE | re.MULTILINE):
                    groups = match.groups()
                    
                    # Extract endpoint URL from match groups
                    endpoint_url = None
                    method = "GET"
                    
                    if source_type == "fetch (URL constructor)":
                        endpoint_url = groups[0] if groups else None
                    elif source_type == "axios":
                        method = groups[0].upper() if groups and len(groups) > 0 else "GET"
                        endpoint_url = groups[1] if groups and len(groups) > 1 else None
                    elif source_type == "jQuery.ajax":
                        endpoint_url = groups[0] if groups else None
                    elif source_type in ["XMLHttpRequest.open", "XMLHttpRequest.open simplified"]:
                        method = groups[0].upper() if groups and len(groups) > 0 else "GET"
                        endpoint_url = groups[1] if groups and len(groups) > 1 else None
                    elif source_type == "fetch with method":
                        endpoint_url = groups[0] if groups and len(groups) > 0 else None
                        method = groups[1].upper() if groups and len(groups) > 1 else "GET"
                    elif source_type == "Java/Spring annotation":
                        method = groups[0].upper() if groups and len(groups) > 0 else "GET"
                        endpoint_url = groups[1] if groups and len(groups) > 1 else None
                    else:
                        endpoint_url = groups[0] if groups else None
                    
                    if endpoint_url and not endpoint_url.startswith(("http://", "https://", "//")):
                        # Calculate line number
                        line_num = js_content[:match.start()].count('\n') + 1
                        
                        # Get context (surrounding lines)
                        context_start = max(0, line_num - 2)
                        context_end = min(len(lines), line_num + 1)
                        context = '\n'.join(lines[context_start:context_end])
                        
                        endpoint = {
                            "url": endpoint_url,
                            "method": method,
                            "line_number": line_num,
                            "source_pattern": source_type,
                            "context": context,
                        }
                        
                        # Avoid duplicates
                        if not any(e["url"] == endpoint["url"] for e in endpoints):
                            endpoints.append(endpoint)
            except re.error as e:
                logger.debug(f"Regex error with pattern {source_type}: {e}")
        
        return endpoints

    def detect_secrets(self, js_content: str) -> List[Dict[str, Any]]:
        """
        Detect hardcoded secrets in JavaScript.
        
        Detects:
        - AWS keys (AKIA...)
        - GitHub tokens (ghp_...)
        - Stripe keys (sk_live_...)
        - API keys (apiKey, api_key)
        - Bearer tokens
        - JWT tokens
        - Hardcoded passwords
        """
        secrets = []
        lines = js_content.split('\n')
        seen_patterns = set()
        
        for secret_type, patterns in self._secret_patterns.items():
            for pattern in patterns:
                try:
                    for match in re.finditer(pattern, js_content, re.IGNORECASE | re.MULTILINE):
                        pattern_match = match.group(0)
                        
                        # Skip if we've already reported this exact match
                        if pattern_match in seen_patterns:
                            continue
                        
                        line_num = js_content[:match.start()].count('\n') + 1
                        
                        # Get context
                        context_start = max(0, line_num - 1)
                        context_end = min(len(lines), line_num)
                        context = lines[context_start] if context_start < len(lines) else ""
                        
                        # Determine severity based on secret type
                        if secret_type in [SecretType.AWS_KEY, SecretType.STRIPE_KEY, SecretType.PASSWORD]:
                            severity = "Critical"
                        elif secret_type in [SecretType.GITHUB_TOKEN, SecretType.AWS_SECRET, SecretType.JWT_TOKEN]:
                            severity = "High"
                        else:
                            severity = "Medium"
                        
                        # Skip very common false positives
                        if secret_type == SecretType.BEARER_TOKEN:
                            # Filter out Bearer in comments or example code
                            if any(x in context.lower() for x in ["example", "mock", "test", "demo", "placeholder"]):
                                continue
                        
                        if secret_type == SecretType.JWT_TOKEN:
                            # JWT tokens are very common in dev code
                            if "eyJ" not in pattern_match:
                                continue
                        
                        secret = {
                            "type": secret_type.value,
                            "match": pattern_match[:30] + "..." if len(pattern_match) > 30 else pattern_match,
                            "line_number": line_num,
                            "context": context.strip(),
                            "severity": severity,
                        }
                        
                        secrets.append(secret)
                        seen_patterns.add(pattern_match)
                except re.error as e:
                    logger.debug(f"Regex error with secret pattern {secret_type}: {e}")
        
        return secrets

    def find_debug_code(self, js_content: str) -> List[Dict[str, Any]]:
        """
        Find debug code instances.
        
        Detects:
        - console.log/warn/error/debug
        - debugger statements
        - alert() calls
        - Commented-out authentication code
        """
        debug_instances = []
        lines = js_content.split('\n')
        
        for debug_type, pattern in self._debug_patterns.items():
            try:
                for match in re.finditer(pattern, js_content, re.IGNORECASE):
                    line_num = js_content[:match.start()].count('\n') + 1
                    
                    # Get context
                    context_start = max(0, line_num - 1)
                    context_end = min(len(lines), line_num)
                    context = lines[context_start] if context_start < len(lines) else ""
                    
                    # Extract the full statement (up to semicolon or newline)
                    line_content = lines[line_num - 1] if line_num - 1 < len(lines) else ""
                    
                    instance = {
                        "type": debug_type.value,
                        "line_number": line_num,
                        "code": line_content.strip(),
                        "context": context.strip(),
                    }
                    
                    debug_instances.append(instance)
            except re.error as e:
                logger.debug(f"Regex error with debug pattern {debug_type}: {e}")
        
        return debug_instances

    def check_source_maps(self, file_url: str) -> List[Dict[str, Any]]:
        """
        Check for exposed source maps.
        
        Source maps (.js.map) expose original source code.
        """
        source_maps = []
        
        if file_url and file_url.endswith('.js'):
            # Check if .map file might exist
            map_url = file_url + '.map'
            source_maps.append({
                "potential_map": map_url,
                "severity": "High",
                "issue": "Source map file might expose original source code",
            })
        
        return source_maps

    async def analyze_js_urls(
        self,
        js_urls: List[str],
        session: aiohttp.ClientSession = None,
        progress_cb=None,
    ) -> Dict[str, Any]:
        """
        Analyze multiple JavaScript files from URLs.
        
        Args:
            js_urls: List of JavaScript file URLs
            session: aiohttp session (creates new one if not provided)
            progress_cb: Async callback for progress updates
            
        Returns:
            Combined analysis results from all files
        """
        close_session = session is None
        if session is None:
            session = aiohttp.ClientSession()
        
        try:
            all_endpoints = []
            all_secrets = []
            all_debug = []
            all_source_maps = []
            analyzed_files = 0
            
            for js_url in js_urls:
                try:
                    if progress_cb:
                        await progress_cb(f"Analyzing JavaScript: {js_url}")
                    
                    # Fetch JavaScript file
                    async with session.get(js_url, timeout=self.timeout, allow_redirects=True) as resp:
                        if resp.status == 200:
                            js_content = await resp.text(errors='ignore')
                            
                            # Analyze the file
                            analysis = await self.analyze_js_file(js_content, js_url)
                            
                            all_endpoints.extend(analysis["endpoints"])
                            all_secrets.extend(analysis["secrets"])
                            all_debug.extend(analysis["debug_code"])
                            all_source_maps.extend(analysis["source_maps"])
                            analyzed_files += 1
                except Exception as e:
                    logger.debug(f"Error analyzing {js_url}: {e}")
            
            return {
                "analyzed_files": analyzed_files,
                "total_endpoints": len(all_endpoints),
                "total_secrets": len(all_secrets),
                "total_debug_instances": len(all_debug),
                "endpoints": all_endpoints,
                "secrets": all_secrets,
                "debug_code": all_debug,
                "source_maps": all_source_maps,
            }
        finally:
            if close_session:
                await session.close()

    def extract_endpoints_from_content(self, js_content: str) -> List[str]:
        """Extract just the endpoint URLs from JavaScript content."""
        endpoints = self.extract_endpoints(js_content)
        return [ep["url"] for ep in endpoints]

    def has_secrets(self, js_content: str) -> bool:
        """Check if JavaScript contains any hardcoded secrets."""
        return len(self.detect_secrets(js_content)) > 0

    def has_debug_code(self, js_content: str) -> bool:
        """Check if JavaScript contains debug code."""
        return len(self.find_debug_code(js_content)) > 0

    def get_severity_summary(self, analysis: Dict[str, Any]) -> Dict[str, int]:
        """Get summary of findings by severity level."""
        summary = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0,
            "Info": 0,
        }
        
        # Count secrets by severity
        for secret in analysis.get("secrets", []):
            severity = secret.get("severity", "Medium")
            if severity in summary:
                summary[severity] += 1
        
        # Debug code is typically Low/Medium
        debug_count = len(analysis.get("debug_code", []))
        if debug_count > 0:
            summary["Low"] += debug_count
        
        # Source maps are High
        sourcemap_count = len(analysis.get("source_maps", []))
        summary["High"] += sourcemap_count
        
        return summary
