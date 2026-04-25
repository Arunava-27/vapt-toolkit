"""
Scope management for VAPT toolkit.

Provides scope parsing, validation, expansion, and persistence.
Supports wildcards, CIDR notation, and various target formats.
"""

import ipaddress
import re
import json
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse


@dataclass
class ScopeTarget:
    """Represents a single scope target with metadata."""
    value: str
    target_type: str
    error: Optional[str] = None
    group: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ParsedScope:
    """Parsed and structured scope for scanning."""
    targets: List[ScopeTarget] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def __len__(self):
        return len([t for t in self.targets if not t.error])
    
    def __iter__(self):
        return iter([t.value for t in self.targets if not t.error])
    
    def to_dict(self):
        return {
            "targets": [t.to_dict() for t in self.targets],
            "errors": self.errors,
            "valid_count": len(self),
        }


class ScopeManager:
    """Manages scope targets with validation and expansion."""
    
    SCOPE_PRESETS_FILE = Path("data/scope_presets.json")
    
    @staticmethod
    def infer_target_type(value: str) -> str:
        """Infer the type of target (url, domain, ip, wildcard, endpoint)."""
        value = value.strip()
        
        if value.startswith(("http://", "https://")):
            return "url"
        
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$", value):
            return "ip"
        
        if "*" in value:
            return "wildcard"
        
        # Domain must contain a dot
        if "." in value and re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?(\:\d+)?$", value):
            return "domain"
        
        return "endpoint"
    
    @staticmethod
    def validate_url(url: str) -> Optional[str]:
        """Validate URL format. Return error message if invalid."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return "Invalid URL scheme (must be http or https)"
            if not parsed.netloc:
                return "Invalid URL: missing host"
            return None
        except Exception as e:
            return str(e)
    
    @staticmethod
    def validate_ip(ip: str) -> Optional[str]:
        """Validate IP or CIDR notation. Return error message if invalid."""
        try:
            if "/" in ip:
                ipaddress.ip_network(ip, strict=False)
            else:
                ipaddress.ip_address(ip)
            return None
        except ValueError as e:
            return f"Invalid IP: {str(e)}"
    
    @staticmethod
    def validate_domain(domain: str) -> Optional[str]:
        """Validate domain name format. Return error message if invalid."""
        domain = domain.strip()
        
        # Allow port numbers
        if ":" in domain:
            domain = domain.split(":")[0]
        
        # Must have at least one dot (to distinguish from single words)
        if "." not in domain:
            return "Invalid domain format (must contain at least one dot)"
        
        pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
        if not re.match(pattern, domain):
            return "Invalid domain format"
        
        return None
    
    @staticmethod
    def validate_wildcard(pattern: str) -> Optional[str]:
        """Validate wildcard pattern. Return error message if invalid."""
        pattern = pattern.strip()
        
        # Basic wildcard validation
        if not re.match(r"^(\*\.)?[a-zA-Z0-9]([a-zA-Z0-9.\-*]*[a-zA-Z0-9])?$", pattern):
            return "Invalid wildcard pattern"
        
        # Ensure at least one valid domain component
        if pattern.count("*") > 2:
            return "Too many wildcards"
        
        return None
    
    @staticmethod
    def validate_target(value: str) -> Optional[str]:
        """
        Validate a single target. Return error message if invalid, None if valid.
        """
        value = value.strip()
        
        if not value:
            return "Target cannot be empty"
        
        target_type = ScopeManager.infer_target_type(value)
        
        if target_type == "url":
            return ScopeManager.validate_url(value)
        elif target_type == "ip":
            return ScopeManager.validate_ip(value)
        elif target_type == "wildcard":
            return ScopeManager.validate_wildcard(value)
        elif target_type in ("domain", "endpoint"):
            return ScopeManager.validate_domain(value)
        
        return None
    
    @staticmethod
    def parse_scope(targets: List[str], allow_duplicates: bool = False) -> ParsedScope:
        """
        Parse and validate scope targets.
        
        Args:
            targets: List of target strings
            allow_duplicates: If False, remove duplicate targets
        
        Returns:
            ParsedScope with validated targets and errors
        """
        parsed_scope = ParsedScope()
        seen = set()
        
        for target in targets:
            target = target.strip()
            if not target:
                continue
            
            # Check duplicates
            if not allow_duplicates and target.lower() in seen:
                parsed_scope.errors.append(f"Duplicate target: {target}")
                continue
            
            seen.add(target.lower())
            
            # Validate target
            error = ScopeManager.validate_target(target)
            target_type = ScopeManager.infer_target_type(target)
            
            scope_target = ScopeTarget(
                value=target,
                target_type=target_type,
                error=error,
            )
            
            parsed_scope.targets.append(scope_target)
            
            if error:
                parsed_scope.errors.append(f"{target}: {error}")
        
        return parsed_scope
    
    @staticmethod
    def expand_scope(targets: List[str]) -> List[str]:
        """
        Expand scope targets, handling wildcards and CIDR notation.
        
        Note: This is a basic expansion. For production, use DNS enumeration.
        
        Args:
            targets: List of target strings
        
        Returns:
            Expanded list of targets (wildcards and CIDR become literal representations)
        """
        expanded = []
        
        for target in targets:
            target = target.strip()
            
            # CIDR notation: expand to network representation
            if "/" in target:
                try:
                    network = ipaddress.ip_network(target, strict=False)
                    expanded.append(f"{network.network_address}-{network.broadcast_address}")
                except ValueError:
                    expanded.append(target)
            else:
                expanded.append(target)
        
        return expanded
    
    @staticmethod
    def export_scope(targets: List[str], format: str = "json") -> str:
        """
        Export scope in specified format.
        
        Args:
            targets: List of target strings
            format: Export format ('json', 'yaml', 'txt')
        
        Returns:
            Formatted scope string
        """
        if format == "json":
            return json.dumps({"targets": targets}, indent=2)
        
        elif format == "yaml":
            lines = ["targets:"]
            lines.extend([f"  - {target}" for target in targets])
            return "\n".join(lines)
        
        elif format == "txt":
            return "\n".join(targets)
        
        else:
            raise ValueError(f"Unknown export format: {format}")
    
    @staticmethod
    def import_scope(content: str, format: str = "txt") -> List[str]:
        """
        Import scope from various formats.
        
        Args:
            content: File or string content
            format: Format type ('json', 'yaml', 'txt')
        
        Returns:
            List of target strings
        """
        targets = []
        
        if format == "json":
            try:
                data = json.loads(content)
                targets = data.get("targets", data) if isinstance(data, dict) else data
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {str(e)}")
        
        elif format == "yaml":
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("- "):
                    targets.append(line[2:].strip())
                elif line and not line.startswith("#"):
                    targets.append(line)
        
        else:  # txt and other formats
            targets = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]
        
        return targets
    
    @staticmethod
    def save_preset(name: str, targets: List[str]) -> str:
        """
        Save a scope preset.
        
        Args:
            name: Preset name
            targets: List of target strings
        
        Returns:
            Preset ID
        """
        preset_id = f"preset-{int(1e10 * hash(name + str(targets)) % 1)}"
        
        # Load existing presets
        presets = ScopeManager.load_presets()
        
        # Add new preset
        presets.append({
            "id": preset_id,
            "name": name,
            "targets": targets,
            "created_at": str(Path.cwd()),  # Placeholder timestamp
        })
        
        # Save
        ScopeManager.SCOPE_PRESETS_FILE.parent.mkdir(exist_ok=True)
        with open(ScopeManager.SCOPE_PRESETS_FILE, "w") as f:
            json.dump(presets, f, indent=2)
        
        return preset_id
    
    @staticmethod
    def load_presets() -> List[Dict[str, Any]]:
        """Load all saved scope presets."""
        if not ScopeManager.SCOPE_PRESETS_FILE.exists():
            return []
        
        try:
            with open(ScopeManager.SCOPE_PRESETS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    @staticmethod
    def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific preset by ID."""
        presets = ScopeManager.load_presets()
        return next((p for p in presets if p.get("id") == preset_id), None)
    
    @staticmethod
    def delete_preset(preset_id: str) -> bool:
        """Delete a preset by ID."""
        presets = ScopeManager.load_presets()
        original_count = len(presets)
        presets = [p for p in presets if p.get("id") != preset_id]
        
        if len(presets) < original_count:
            ScopeManager.SCOPE_PRESETS_FILE.parent.mkdir(exist_ok=True)
            with open(ScopeManager.SCOPE_PRESETS_FILE, "w") as f:
                json.dump(presets, f, indent=2)
            return True
        
        return False
    
    @staticmethod
    def validate_scope_for_scanning(targets: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate scope for active scanning.
        
        Returns:
            (is_valid, list_of_errors)
        """
        if not targets:
            return False, ["No targets defined in scope"]
        
        parsed = ScopeManager.parse_scope(targets)
        
        if parsed.errors:
            return False, parsed.errors
        
        return True, []
    
    @staticmethod
    def get_scope_summary(targets: List[str], max_items: int = 3) -> str:
        """Generate human-readable scope summary."""
        if not targets:
            return "No scope defined (all targets allowed)"
        
        if len(targets) == 1:
            return f"In-scope: {targets[0]}"
        
        shown = targets[:max_items]
        suffix = f"... +{len(targets) - max_items} more" if len(targets) > max_items else ""
        return f"In-scope: {', '.join(shown)}{suffix}"


# Singleton instance
_scope_manager_instance = ScopeManager()


def get_scope_manager() -> ScopeManager:
    """Get the scope manager singleton instance."""
    return _scope_manager_instance
