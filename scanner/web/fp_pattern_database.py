"""
False Positive Pattern Database for Vulnerability Findings

This module manages a database of known false positive patterns to automatically
filter out low-confidence findings. It applies pattern matching and confidence
adjustment logic to improve scan accuracy.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class FPPatternType(Enum):
    """Types of false positive patterns"""
    SECURITY_HEADERS = "security_headers"
    XSS_FRAMEWORK = "xss_framework"
    CSRF_FRAMEWORK = "csrf_framework"
    CORS_HEADERS = "cors_headers"
    AUTH_FRAMEWORK = "auth_framework"
    SQL_PARAMETERIZED = "sql_parameterized"
    RATE_LIMIT = "rate_limit"
    SENSITIVE_DATA = "sensitive_data"
    INJECTION = "injection"
    CUSTOM = "custom"


@dataclass
class FPPattern:
    """Represents a single false positive pattern"""
    id: str
    pattern_type: FPPatternType
    description: str
    regex_pattern: str
    severity_impact: float  # 0.5-1.0, multiplier for confidence reduction
    enabled: bool = True
    created_at: str = ""
    keywords: List[str] = None
    vulnerable_param: Optional[str] = None
    safe_framework: Optional[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class FalsePositivePatternDB:
    """
    Manages false positive patterns and applies them to findings.
    
    Patterns are checked against findings to:
    1. Identify likely false positives
    2. Adjust confidence scores
    3. Add metadata flags to findings
    """

    def __init__(self):
        self.patterns: Dict[str, FPPattern] = {}
        self.compiled_patterns: Dict[str, re.Pattern] = {}
        self._init_builtin_patterns()

    def _init_builtin_patterns(self):
        """Initialize built-in false positive patterns"""
        patterns = [
            # Security Headers FPs
            self._create_pattern(
                "sh_content_type_mismatch",
                FPPatternType.SECURITY_HEADERS,
                "X-Content-Type-Options header missing but Content-Type present",
                r"Content-Type.*charset|application/json",
                0.6,
                keywords=["content-type", "charset"],
                safe_framework="all"
            ),
            self._create_pattern(
                "sh_xss_protection_obsolete",
                FPPatternType.SECURITY_HEADERS,
                "X-XSS-Protection header missing (modern browsers ignore)",
                r"X-XSS-Protection.*0|X-XSS-Protection.*1.*mode=block",
                0.7,
                keywords=["x-xss-protection"],
                safe_framework="modern_browsers"
            ),
            self._create_pattern(
                "sh_hsts_localhost",
                FPPatternType.SECURITY_HEADERS,
                "HSTS not applicable to localhost testing",
                r"localhost|127\.0\.0\.1|::1",
                0.8,
                keywords=["hsts", "localhost"],
                safe_framework="localhost"
            ),

            # XSS Framework FPs
            self._create_pattern(
                "xss_vue_auto_escape",
                FPPatternType.XSS_FRAMEWORK,
                "Vue.js auto-escapes template interpolation {{ }}",
                r"Vue\.|vue-|\.vue|v-bind|v-if|v-for|mustache",
                0.5,
                keywords=["vue", "auto-escape", "framework"],
                safe_framework="Vue"
            ),
            self._create_pattern(
                "xss_react_jsx_escape",
                FPPatternType.XSS_FRAMEWORK,
                "React JSX escapes content by default, XSS unlikely",
                r"React\.|react-|\.jsx|dangerouslySetInnerHTML.*false|React\.createElement",
                0.5,
                keywords=["react", "jsx", "auto-escape"],
                safe_framework="React"
            ),
            self._create_pattern(
                "xss_angular_sanitizer",
                FPPatternType.XSS_FRAMEWORK,
                "Angular sanitizes HTML by default with DomSanitizer",
                r"Angular|angular-|\.module\(|ngSanitize|DomSanitizer",
                0.55,
                keywords=["angular", "sanitizer"],
                safe_framework="Angular"
            ),
            self._create_pattern(
                "xss_django_autoescape",
                FPPatternType.XSS_FRAMEWORK,
                "Django template auto-escapes HTML by default",
                r"Django|django\.|\.html|autoescape|django\.template",
                0.5,
                keywords=["django", "autoescape"],
                safe_framework="Django"
            ),
            self._create_pattern(
                "xss_jinja2_autoescape",
                FPPatternType.XSS_FRAMEWORK,
                "Jinja2 auto-escapes when autoescape=True (default)",
                r"Jinja2|jinja|\.jinja2|autoescape on",
                0.5,
                keywords=["jinja", "autoescape"],
                safe_framework="Jinja2"
            ),
            self._create_pattern(
                "xss_rails_html_escape",
                FPPatternType.XSS_FRAMEWORK,
                "Rails auto-escapes string interpolation in ERB templates",
                r"Rails|rails-|\.erb|ERB|<%= |html_escape",
                0.5,
                keywords=["rails", "erb", "autoescape"],
                safe_framework="Rails"
            ),
            self._create_pattern(
                "xss_laravel_blade_escape",
                FPPatternType.XSS_FRAMEWORK,
                "Laravel Blade escapes {{ }} by default, use {!! !!} for raw",
                r"Laravel|blade|\.blade\.php|\{\{ |\{\!\!",
                0.5,
                keywords=["laravel", "blade", "autoescape"],
                safe_framework="Laravel"
            ),
            self._create_pattern(
                "xss_csp_strict",
                FPPatternType.XSS_FRAMEWORK,
                "Strict CSP policy prevents inline script execution",
                r"Content-Security-Policy.*default-src 'none'|default-src 'self'",
                0.6,
                keywords=["csp", "strict"],
                safe_framework="CSP"
            ),

            # CSRF Framework FPs
            self._create_pattern(
                "csrf_django_token",
                FPPatternType.CSRF_FRAMEWORK,
                "Django includes CSRF token in forms automatically",
                r"Django|csrf_token|csrfmiddlewaretoken|\{% csrf_token",
                0.5,
                keywords=["django", "csrf", "token"],
                safe_framework="Django"
            ),
            self._create_pattern(
                "csrf_rails_token",
                FPPatternType.CSRF_FRAMEWORK,
                "Rails CSRF protection auto-validates POST/PUT/DELETE",
                r"Rails|rails-|authenticity_token|forgery_protection",
                0.5,
                keywords=["rails", "csrf", "token"],
                safe_framework="Rails"
            ),
            self._create_pattern(
                "csrf_spring_security",
                FPPatternType.CSRF_FRAMEWORK,
                "Spring Security provides CSRF protection with X-CSRF-TOKEN",
                r"Spring|spring-|X-CSRF-TOKEN|_csrf|CsrfFilter",
                0.5,
                keywords=["spring", "csrf"],
                safe_framework="Spring"
            ),
            self._create_pattern(
                "csrf_laravel_token",
                FPPatternType.CSRF_FRAMEWORK,
                "Laravel CSRF middleware validates token automatically",
                r"Laravel|_token|csrf_field|csrf_token",
                0.5,
                keywords=["laravel", "csrf"],
                safe_framework="Laravel"
            ),

            # CORS FPs
            self._create_pattern(
                "cors_cdn_headers",
                FPPatternType.CORS_HEADERS,
                "CDN or proxy may add CORS headers, not app vulnerability",
                r"Access-Control-Allow-Origin|CloudFlare|Akamai|CDN",
                0.7,
                keywords=["cors", "cdn"],
                safe_framework="CDN"
            ),
            self._create_pattern(
                "cors_localhost_dev",
                FPPatternType.CORS_HEADERS,
                "CORS * may be intentional for localhost development",
                r"localhost|127\.0\.0\.1|::1.*Access-Control-Allow-Origin|CORS",
                0.75,
                keywords=["cors", "localhost"],
                safe_framework="localhost_dev"
            ),

            # Authentication FPs
            self._create_pattern(
                "auth_custom_framework",
                FPPatternType.AUTH_FRAMEWORK,
                "Custom auth framework may validate credentials securely",
                r"Custom|custom_auth|proprietary|in-house",
                0.6,
                keywords=["custom", "auth"],
                safe_framework="custom"
            ),
            self._create_pattern(
                "auth_jwt_valid",
                FPPatternType.AUTH_FRAMEWORK,
                "JWT with strong signature verification is secure",
                r"JWT|bearer.*JWT|json.*web.*token|RS256|HS512",
                0.4,
                keywords=["jwt", "secure"],
                safe_framework="JWT"
            ),

            # SQL Parameterization FPs
            self._create_pattern(
                "sql_parameterized_query",
                FPPatternType.SQL_PARAMETERIZED,
                "Parameterized query prevents SQL injection",
                r"prepared.*statement|bind.*param|parameterized|placeholder|\?|parameterized",
                0.3,
                keywords=["parameterized", "sql"],
                safe_framework="all"
            ),
            self._create_pattern(
                "sql_orm_safe",
                FPPatternType.SQL_PARAMETERIZED,
                "ORM framework (SQLAlchemy, Hibernate, Django ORM) prevents SQL injection",
                r"SQLAlchemy|Hibernate|Django ORM|Entity Framework|LINQ",
                0.35,
                keywords=["orm", "sql"],
                safe_framework="ORM"
            ),

            # Rate Limiting FPs
            self._create_pattern(
                "rate_limit_implemented",
                FPPatternType.RATE_LIMIT,
                "Rate limiting already implemented, test is expected to rate limit",
                r"rate.*limit|429|Too Many Requests|X-RateLimit",
                0.8,
                keywords=["rate", "limit"],
                safe_framework="all"
            ),

            # Sensitive Data FPs
            self._create_pattern(
                "sensitive_data_test_cred",
                FPPatternType.SENSITIVE_DATA,
                "Test credentials intentionally exposed for testing",
                r"test|demo|user.*test|password.*test|admin.*test",
                0.6,
                keywords=["test", "demo"],
                safe_framework="testing"
            ),
            self._create_pattern(
                "sensitive_data_local_storage",
                FPPatternType.SENSITIVE_DATA,
                "Dev/local environment stores data locally, not prod issue",
                r"localhost|127\.0\.0\.1|internal|dev\.|\.local",
                0.7,
                keywords=["dev", "local"],
                safe_framework="dev_env"
            ),
        ]

        for pattern in patterns:
            self.patterns[pattern.id] = pattern
            try:
                self.compiled_patterns[pattern.id] = re.compile(pattern.regex_pattern, re.IGNORECASE)
            except re.error as e:
                logger.warning(f"Failed to compile regex for {pattern.id}: {e}")

    def _create_pattern(
        self,
        pattern_id: str,
        pattern_type: FPPatternType,
        description: str,
        regex_pattern: str,
        severity_impact: float,
        keywords: List[str] = None,
        safe_framework: Optional[str] = None,
    ) -> FPPattern:
        """Factory method to create FPPattern"""
        return FPPattern(
            id=pattern_id,
            pattern_type=pattern_type,
            description=description,
            regex_pattern=regex_pattern,
            severity_impact=severity_impact,
            enabled=True,
            keywords=keywords or [],
            safe_framework=safe_framework
        )

    def check_finding_against_patterns(self, finding: Dict) -> Tuple[bool, str, List[str]]:
        """
        Check a finding against all patterns to determine if it's likely a false positive.
        
        Args:
            finding: Finding dict with keys like 'title', 'description', 'response_body', etc.
        
        Returns:
            Tuple of (is_likely_false_positive, reason, matched_patterns)
        """
        matched_patterns = []
        confidence_reductions = []

        # Combine all text content from finding
        text_to_check = self._extract_finding_text(finding)

        # Check against each enabled pattern
        for pattern_id, pattern in self.patterns.items():
            if not pattern.enabled:
                continue

            compiled = self.compiled_patterns.get(pattern_id)
            if not compiled:
                continue

            # Check if pattern matches
            if compiled.search(text_to_check):
                matched_patterns.append(pattern_id)
                confidence_reductions.append(pattern.severity_impact)

        # If multiple patterns match, it's more likely a false positive
        if len(matched_patterns) >= 2:
            return True, f"Multiple patterns matched: {', '.join(matched_patterns)}", matched_patterns
        elif len(matched_patterns) == 1:
            pattern_id = matched_patterns[0]
            pattern = self.patterns[pattern_id]
            # Single pattern match - check impact
            if pattern.severity_impact >= 0.7:
                return True, f"Strong false positive pattern: {pattern.description}", matched_patterns

        return False, "", matched_patterns

    def get_confidence_adjustment(self, finding: Dict) -> float:
        """
        Calculate confidence adjustment factor for a finding.
        
        Args:
            finding: Finding dict
            
        Returns:
            Adjustment factor (0.5 - 1.0). Lower = more likely false positive
        """
        _, _, matched_patterns = self.check_finding_against_patterns(finding)

        if not matched_patterns:
            return 1.0  # No adjustment

        # Calculate composite adjustment from matched patterns
        adjustment = 1.0
        for pattern_id in matched_patterns:
            pattern = self.patterns[pattern_id]
            adjustment *= pattern.severity_impact

        # Ensure we stay within bounds
        return max(0.3, min(1.0, adjustment))

    def add_custom_pattern(self, pattern_dict: Dict) -> str:
        """
        Add a custom false positive pattern.
        
        Args:
            pattern_dict: Dict with keys: pattern_type, description, regex_pattern, 
                         severity_impact, keywords (optional)
        
        Returns:
            Pattern ID
        """
        import uuid
        from datetime import datetime

        pattern_id = f"custom_{uuid.uuid4().hex[:8]}"

        try:
            pattern = FPPattern(
                id=pattern_id,
                pattern_type=FPPatternType[pattern_dict.get("pattern_type", "CUSTOM")],
                description=pattern_dict["description"],
                regex_pattern=pattern_dict["regex_pattern"],
                severity_impact=float(pattern_dict.get("severity_impact", 0.6)),
                enabled=pattern_dict.get("enabled", True),
                keywords=pattern_dict.get("keywords", []),
                created_at=datetime.now().isoformat(),
                safe_framework=pattern_dict.get("safe_framework")
            )

            # Validate regex
            compiled = re.compile(pattern.regex_pattern, re.IGNORECASE)
            self.compiled_patterns[pattern_id] = compiled
            self.patterns[pattern_id] = pattern

            logger.info(f"Added custom pattern: {pattern_id}")
            return pattern_id

        except (re.error, ValueError, KeyError) as e:
            logger.error(f"Failed to add custom pattern: {e}")
            raise

    def remove_pattern(self, pattern_id: str) -> bool:
        """Disable or remove a pattern"""
        if pattern_id in self.patterns:
            self.patterns[pattern_id].enabled = False
            logger.info(f"Disabled pattern: {pattern_id}")
            return True
        return False

    def enable_pattern(self, pattern_id: str) -> bool:
        """Enable a previously disabled pattern"""
        if pattern_id in self.patterns:
            self.patterns[pattern_id].enabled = True
            logger.info(f"Enabled pattern: {pattern_id}")
            return True
        return False

    def list_patterns(self, pattern_type: Optional[str] = None, enabled_only: bool = True) -> List[Dict]:
        """List all patterns, optionally filtered by type"""
        result = []
        for pattern in self.patterns.values():
            if enabled_only and not pattern.enabled:
                continue
            if pattern_type and pattern.pattern_type.value != pattern_type:
                continue

            result.append({
                "id": pattern.id,
                "pattern_type": pattern.pattern_type.value,
                "description": pattern.description,
                "severity_impact": pattern.severity_impact,
                "enabled": pattern.enabled,
                "keywords": pattern.keywords,
                "safe_framework": pattern.safe_framework,
            })

        return sorted(result, key=lambda x: x["pattern_type"])

    def get_pattern_stats(self) -> Dict:
        """Get statistics about patterns"""
        enabled = sum(1 for p in self.patterns.values() if p.enabled)
        by_type = {}
        for pattern in self.patterns.values():
            ptype = pattern.pattern_type.value
            by_type[ptype] = by_type.get(ptype, 0) + (1 if pattern.enabled else 0)

        return {
            "total_patterns": len(self.patterns),
            "enabled_patterns": enabled,
            "disabled_patterns": len(self.patterns) - enabled,
            "by_type": by_type,
        }

    @staticmethod
    def _extract_finding_text(finding: Dict) -> str:
        """Extract all relevant text from a finding for pattern matching"""
        parts = []

        # Add key finding attributes
        if "title" in finding:
            parts.append(str(finding["title"]))
        if "description" in finding:
            parts.append(str(finding["description"]))
        if "test_name" in finding:
            parts.append(str(finding["test_name"]))
        if "category" in finding:
            parts.append(str(finding["category"]))
        if "response_body" in finding:
            parts.append(str(finding["response_body"])[:500])  # Limit response body
        if "response_headers" in finding:
            if isinstance(finding["response_headers"], dict):
                parts.append(" ".join(f"{k}: {v}" for k, v in finding["response_headers"].items()))
            else:
                parts.append(str(finding["response_headers"]))
        if "evidence" in finding:
            parts.append(str(finding["evidence"])[:300])

        return "\n".join(parts)
