"""
Scope validation and target verification for active scans.

Ensures that only explicitly authorized targets are scanned.
Prevents accidental scanning of out-of-scope systems.
"""
import ipaddress
import re
from typing import Optional
from urllib.parse import urlparse


def is_valid_ip(target: str) -> bool:
    """Check if target is a valid IP address."""
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        return False


def is_valid_domain(target: str) -> bool:
    """Check if target is a valid domain name."""
    # Allow: example.com, sub.example.com, example.co.uk, etc.
    domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
    return bool(re.match(domain_pattern, target.lower()))


def is_valid_url(target: str) -> bool:
    """Check if target is a valid HTTP(S) URL."""
    try:
        parsed = urlparse(target)
        return parsed.scheme in ("http", "https") and parsed.netloc
    except Exception:
        return False


def normalize_target(target: str) -> tuple[str, str]:
    """
    Normalize target and return (normalized_target, target_type).
    
    Returns:
        - ("192.168.1.1", "ip") for IP addresses
        - ("example.com", "domain") for domains
        - ("https://example.com", "url") for URLs
        - Raises ValueError if invalid
    """
    target = target.strip()
    
    # Try URL first
    if target.startswith(("http://", "https://")):
        if is_valid_url(target):
            return target, "url"
        raise ValueError(f"Invalid URL: {target}")
    
    # Try IP
    if is_valid_ip(target):
        return target, "ip"
    
    # Try domain
    if is_valid_domain(target):
        return target, "domain"
    
    raise ValueError(
        f"Invalid target: {target}. "
        "Must be: IP address, domain name, or HTTP(S) URL"
    )


def validate_scope(
    target: str,
    scope: Optional[list[str]] = None,
    allow_private: bool = True,
) -> bool:
    """
    Validate that target is in scope for active scanning.
    
    Args:
        target: Target IP, domain, or URL
        scope: List of allowed targets. If None, only basic validation done.
        allow_private: Allow private/RFC1918 IP ranges
    
    Returns:
        True if target is in scope, False otherwise
        
    Raises:
        ValueError if target format is invalid
    """
    norm_target, target_type = normalize_target(target)
    
    # Private IP check
    if not allow_private and target_type == "ip":
        try:
            ip = ipaddress.ip_address(norm_target)
            if ip.is_private or ip.is_loopback:
                return False
        except ValueError:
            pass
    
    # If no scope list, basic validation only
    if scope is None:
        return True
    
    # Check against scope list
    scope = [s.strip().lower() for s in scope]
    
    if target_type == "url":
        parsed = urlparse(norm_target)
        netloc = parsed.netloc.lower()
        for allowed in scope:
            if netloc == allowed or netloc.endswith(f".{allowed}"):
                return True
    elif target_type == "domain":
        norm_lower = norm_target.lower()
        for allowed in scope:
            allowed_lower = allowed.lower()
            if norm_lower == allowed_lower or norm_lower.endswith(f".{allowed_lower}"):
                return True
    elif target_type == "ip":
        if norm_target in scope:
            return True
        # Check CIDR ranges
        try:
            target_ip = ipaddress.ip_address(norm_target)
            for allowed in scope:
                try:
                    if target_ip in ipaddress.ip_network(allowed, strict=False):
                        return True
                except ValueError:
                    pass
        except ValueError:
            pass
    
    return False


def get_scope_summary(scope: list[str]) -> str:
    """Generate human-readable scope summary."""
    if not scope:
        return "No scope defined (all targets allowed)"
    if len(scope) == 1:
        return f"In-scope: {scope[0]}"
    return f"In-scope: {', '.join(scope[:3])}{'...' if len(scope) > 3 else ''}"
