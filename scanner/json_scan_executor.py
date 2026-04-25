"""JSON-based scan instruction executor with schema validation."""

import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ScanDepth(str, Enum):
    """Scan depth levels."""
    QUICK = "quick"      # ~5 minutes
    MEDIUM = "medium"    # ~15 minutes
    FULL = "full"        # ~30+ minutes


class RecurringType(str, Enum):
    """Recurring schedule types."""
    ONE_TIME = "one-time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ScanModule(str, Enum):
    """Available scan modules."""
    XSS = "xss"
    SQLI = "sqli"
    CSRF = "csrf"
    REDIRECT = "redirect"
    HEADER_INJECTION = "header_injection"
    PATH_TRAVERSAL = "path_traversal"
    IDOR = "idor"
    FILE_UPLOAD = "file_upload"
    AUTH = "auth"
    HEADERS = "headers"
    RECON = "recon"
    PORTS = "ports"
    CVE = "cve"


# JSON Schema for validation
JSON_SCAN_SCHEMA = {
    "type": "object",
    "required": ["name", "target"],
    "properties": {
        "name": {
            "type": "string",
            "description": "Scan name",
            "minLength": 1,
            "maxLength": 200
        },
        "description": {
            "type": "string",
            "description": "Scan description",
            "maxLength": 1000
        },
        "target": {
            "type": "string",
            "description": "Target URL or domain",
            "pattern": "^(https?://|[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}|\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})",
        },
        "scope": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Authorized scope URLs (patterns with wildcards)",
            "default": []
        },
        "modules": {
            "oneOf": [
                {
                    "type": "array",
                    "items": {
                        "enum": ["xss", "sqli", "csrf", "redirect", "header_injection", 
                                 "path_traversal", "idor", "file_upload", "auth", "headers",
                                 "recon", "ports", "cve"]
                    },
                    "description": "Specific modules to enable"
                },
                {
                    "type": "array",
                    "items": {"enum": ["all"]},
                    "description": "Run all modules"
                }
            ],
            "default": ["all"]
        },
        "depth": {
            "type": "string",
            "enum": ["quick", "medium", "full"],
            "description": "Scan depth level",
            "default": "medium"
        },
        "concurrency": {
            "type": "integer",
            "description": "Number of concurrent requests",
            "minimum": 1,
            "maximum": 50,
            "default": 5
        },
        "timeout": {
            "type": "integer",
            "description": "Request timeout in seconds",
            "minimum": 5,
            "maximum": 3600,
            "default": 600
        },
        "notifications": {
            "type": "object",
            "description": "Notification settings",
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Email address for notifications"
                },
                "slack_webhook": {
                    "type": "string",
                    "description": "Slack webhook URL"
                },
                "teams_webhook": {
                    "type": "string",
                    "description": "Microsoft Teams webhook URL"
                },
                "severity_filter": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low", "all"],
                    "default": "high",
                    "description": "Minimum severity level for notifications"
                },
                "channels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["desktop"],
                    "description": "Notification channels (desktop, email, slack, teams)"
                }
            }
        },
        "export": {
            "type": "object",
            "description": "Export settings",
            "properties": {
                "formats": {
                    "type": "array",
                    "items": {"enum": ["pdf", "json", "csv", "html"]},
                    "description": "Export formats",
                    "default": ["json"]
                },
                "send_email": {
                    "type": "boolean",
                    "description": "Send export via email",
                    "default": False
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Email for export delivery"
                }
            }
        },
        "schedule": {
            "type": "object",
            "description": "Scheduling settings",
            "properties": {
                "recurring": {
                    "type": "string",
                    "enum": ["one-time", "daily", "weekly", "monthly"],
                    "default": "one-time",
                    "description": "Recurring pattern"
                },
                "day": {
                    "type": "string",
                    "description": "Day for weekly schedule (Monday-Sunday)",
                    "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                },
                "date": {
                    "type": "integer",
                    "description": "Date for monthly schedule (1-31)",
                    "minimum": 1,
                    "maximum": 31
                },
                "time": {
                    "type": "string",
                    "pattern": "^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
                    "description": "Time in HH:MM format (24-hour)"
                }
            }
        },
        "advanced": {
            "type": "object",
            "description": "Advanced options",
            "properties": {
                "skip_robots_txt": {
                    "type": "boolean",
                    "description": "Ignore robots.txt restrictions",
                    "default": False
                },
                "user_agent": {
                    "type": "string",
                    "description": "Custom User-Agent header",
                    "maxLength": 500
                },
                "proxy_url": {
                    "type": "string",
                    "description": "Proxy URL (http://host:port)"
                },
                "auth_type": {
                    "type": "string",
                    "enum": ["none", "basic", "bearer", "api_key", "oauth2"],
                    "description": "Authentication type",
                    "default": "none"
                },
                "auth_credentials": {
                    "type": "object",
                    "description": "Auth credentials (username, password, token, key)",
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "token": {"type": "string"},
                        "api_key": {"type": "string"}
                    }
                }
            }
        }
    }
}


@dataclass
class NotificationConfig:
    """Notification configuration."""
    email: Optional[str] = None
    slack_webhook: Optional[str] = None
    teams_webhook: Optional[str] = None
    severity_filter: str = "high"
    channels: List[str] = field(default_factory=lambda: ["desktop"])

    def to_dict(self) -> dict:
        return {
            "email": self.email,
            "slack_webhook": self.slack_webhook,
            "teams_webhook": self.teams_webhook,
            "severity_filter": self.severity_filter,
            "channels": self.channels
        }


@dataclass
class ExportConfig:
    """Export configuration."""
    formats: List[str] = field(default_factory=lambda: ["json"])
    send_email: bool = False
    email: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "formats": self.formats,
            "send_email": self.send_email,
            "email": self.email
        }


@dataclass
class ScheduleConfig:
    """Schedule configuration."""
    recurring: str = "one-time"
    day: Optional[str] = None
    date: Optional[int] = None
    time: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "recurring": self.recurring,
            "day": self.day,
            "date": self.date,
            "time": self.time
        }


@dataclass
class AdvancedConfig:
    """Advanced configuration."""
    skip_robots_txt: bool = False
    user_agent: Optional[str] = None
    proxy_url: Optional[str] = None
    auth_type: str = "none"
    auth_credentials: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "skip_robots_txt": self.skip_robots_txt,
            "user_agent": self.user_agent,
            "proxy_url": self.proxy_url,
            "auth_type": self.auth_type,
            "auth_credentials": self.auth_credentials or {}
        }


@dataclass
class JSONScanInstruction:
    """Parsed JSON scan instruction."""
    name: str
    target: str
    description: str = ""
    scope: List[str] = field(default_factory=list)
    modules: List[str] = field(default_factory=lambda: ["all"])
    depth: str = "medium"
    concurrency: int = 5
    timeout: int = 600
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    export_config: ExportConfig = field(default_factory=ExportConfig)
    schedule_config: ScheduleConfig = field(default_factory=ScheduleConfig)
    advanced_config: AdvancedConfig = field(default_factory=AdvancedConfig)

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "name": self.name,
            "target": self.target,
            "description": self.description,
            "scope": self.scope,
            "modules": self.modules,
            "depth": self.depth,
            "concurrency": self.concurrency,
            "timeout": self.timeout,
            "notifications": self.notifications.to_dict(),
            "export": self.export_config.to_dict(),
            "schedule": self.schedule_config.to_dict(),
            "advanced": self.advanced_config.to_dict()
        }


class JSONScanValidator:
    """Validates JSON scan instructions against schema."""

    def __init__(self):
        self.schema = JSON_SCAN_SCHEMA
        self.errors: List[str] = []

    def validate(self, json_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate JSON scan instruction.
        Returns: (is_valid, error_messages)
        """
        self.errors = []

        # Required fields
        if "name" not in json_data:
            self.errors.append("Missing required field: 'name'")
        if "target" not in json_data:
            self.errors.append("Missing required field: 'target'")

        if self.errors:
            return False, self.errors

        # Field-by-field validation
        self._validate_name(json_data.get("name"))
        self._validate_target(json_data.get("target"))
        self._validate_description(json_data.get("description"))
        self._validate_scope(json_data.get("scope", []))
        self._validate_modules(json_data.get("modules", ["all"]))
        self._validate_depth(json_data.get("depth", "medium"))
        self._validate_concurrency(json_data.get("concurrency", 5))
        self._validate_timeout(json_data.get("timeout", 600))
        self._validate_notifications(json_data.get("notifications", {}))
        self._validate_export(json_data.get("export", {}))
        self._validate_schedule(json_data.get("schedule", {}))
        self._validate_advanced(json_data.get("advanced", {}))

        return len(self.errors) == 0, self.errors

    def validate_json(self, json_str: str) -> tuple[bool, List[str]]:
        """
        Validate JSON scan instruction from string.
        Parses JSON then validates.
        Returns: (is_valid, error_messages)
        """
        try:
            if isinstance(json_str, str):
                json_data = json.loads(json_str)
            else:
                json_data = json_str
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON syntax: {str(e)}"]
        except Exception as e:
            return False, [f"Error parsing JSON: {str(e)}"]
        
        return self.validate(json_data)

    def _validate_name(self, name: Any) -> None:
        if not isinstance(name, str):
            self.errors.append("Field 'name' must be a string")
            return
        if not name.strip():
            self.errors.append("Field 'name' cannot be empty")
        elif len(name) > 200:
            self.errors.append("Field 'name' must be <= 200 characters")

    def _validate_target(self, target: Any) -> None:
        if not isinstance(target, str):
            self.errors.append("Field 'target' must be a string")
            return
        if not target.strip():
            self.errors.append("Field 'target' cannot be empty")

    def _validate_description(self, description: Any) -> None:
        if description is None:
            return
        if not isinstance(description, str):
            self.errors.append("Field 'description' must be a string")
            return
        if len(description) > 1000:
            self.errors.append("Field 'description' must be <= 1000 characters")

    def _validate_scope(self, scope: Any) -> None:
        if scope is None:
            return
        if not isinstance(scope, list):
            self.errors.append("Field 'scope' must be an array of strings")
            return
        for item in scope:
            if not isinstance(item, str):
                self.errors.append("All scope items must be strings (URL patterns)")

    def _validate_modules(self, modules: Any) -> None:
        valid_modules = {"all", "xss", "sqli", "csrf", "redirect", "header_injection",
                        "path_traversal", "idor", "file_upload", "auth", "headers", "recon", "ports", "cve"}
        if not isinstance(modules, list):
            self.errors.append("Field 'modules' must be an array")
            return
        if not modules:
            self.errors.append("Field 'modules' cannot be empty")
            return
        for module in modules:
            if module not in valid_modules:
                self.errors.append(f"Invalid module: '{module}'. Valid: {valid_modules}")

    def _validate_depth(self, depth: Any) -> None:
        valid_depths = {"quick", "medium", "full"}
        if depth not in valid_depths:
            self.errors.append(f"Field 'depth' must be one of: {valid_depths}")

    def _validate_concurrency(self, concurrency: Any) -> None:
        if not isinstance(concurrency, int):
            self.errors.append("Field 'concurrency' must be an integer")
            return
        if concurrency < 1 or concurrency > 50:
            self.errors.append("Field 'concurrency' must be between 1 and 50")

    def _validate_timeout(self, timeout: Any) -> None:
        if not isinstance(timeout, int):
            self.errors.append("Field 'timeout' must be an integer")
            return
        if timeout < 5 or timeout > 3600:
            self.errors.append("Field 'timeout' must be between 5 and 3600 seconds")

    def _validate_notifications(self, notifications: Any) -> None:
        if not isinstance(notifications, dict):
            self.errors.append("Field 'notifications' must be an object")
            return

        valid_channels = {"desktop", "email", "slack", "teams"}
        valid_severities = {"critical", "high", "medium", "low", "all"}

        if "severity_filter" in notifications:
            if notifications["severity_filter"] not in valid_severities:
                self.errors.append(f"Invalid 'notifications.severity_filter': {valid_severities}")

        if "channels" in notifications:
            if not isinstance(notifications["channels"], list):
                self.errors.append("Field 'notifications.channels' must be an array")
            else:
                for channel in notifications["channels"]:
                    if channel not in valid_channels:
                        self.errors.append(f"Invalid notification channel: '{channel}'. Valid: {valid_channels}")

    def _validate_export(self, export: Any) -> None:
        if not isinstance(export, dict):
            self.errors.append("Field 'export' must be an object")
            return

        valid_formats = {"pdf", "json", "csv", "html"}
        if "formats" in export:
            if not isinstance(export["formats"], list):
                self.errors.append("Field 'export.formats' must be an array")
            else:
                for fmt in export["formats"]:
                    if fmt not in valid_formats:
                        self.errors.append(f"Invalid export format: '{fmt}'. Valid: {valid_formats}")

    def _validate_schedule(self, schedule: Any) -> None:
        if not isinstance(schedule, dict):
            self.errors.append("Field 'schedule' must be an object")
            return

        valid_recurring = {"one-time", "daily", "weekly", "monthly"}
        valid_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

        if "recurring" in schedule:
            if schedule["recurring"] not in valid_recurring:
                self.errors.append(f"Invalid 'schedule.recurring': {valid_recurring}")

        if "day" in schedule:
            if schedule["day"] not in valid_days:
                self.errors.append(f"Invalid 'schedule.day': {valid_days}")

        if "date" in schedule:
            if not isinstance(schedule["date"], int) or schedule["date"] < 1 or schedule["date"] > 31:
                self.errors.append("Field 'schedule.date' must be between 1 and 31")

        if "time" in schedule:
            if not self._is_valid_time(schedule["time"]):
                self.errors.append("Field 'schedule.time' must be in HH:MM format (24-hour)")

    def _validate_advanced(self, advanced: Any) -> None:
        if not isinstance(advanced, dict):
            self.errors.append("Field 'advanced' must be an object")
            return

        valid_auth = {"none", "basic", "bearer", "api_key", "oauth2"}
        if "auth_type" in advanced:
            if advanced["auth_type"] not in valid_auth:
                self.errors.append(f"Invalid 'advanced.auth_type': {valid_auth}")

    @staticmethod
    def _is_valid_time(time_str: str) -> bool:
        """Check if time is in HH:MM format."""
        if not isinstance(time_str, str):
            return False
        parts = time_str.split(":")
        if len(parts) != 2:
            return False
        try:
            hours, minutes = int(parts[0]), int(parts[1])
            return 0 <= hours < 24 and 0 <= minutes < 60
        except ValueError:
            return False


class JSONScanExecutor:
    """Executes scans from JSON instructions."""

    def __init__(self):
        self.validator = JSONScanValidator()

    def parse_json_instruction(self, json_str: str) -> Optional[JSONScanInstruction]:
        """
        Parse and validate JSON scan instruction.
        Returns: JSONScanInstruction or None if invalid.
        """
        try:
            data = json.loads(json_str) if isinstance(json_str, str) else json_str
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return None

        is_valid, errors = self.validator.validate(data)
        if not is_valid:
            logger.error(f"Validation errors: {errors}")
            return None

        # Parse nested configs
        notifications = NotificationConfig(
            email=data.get("notifications", {}).get("email"),
            slack_webhook=data.get("notifications", {}).get("slack_webhook"),
            teams_webhook=data.get("notifications", {}).get("teams_webhook"),
            severity_filter=data.get("notifications", {}).get("severity_filter", "high"),
            channels=data.get("notifications", {}).get("channels", ["desktop"])
        )

        export_config = ExportConfig(
            formats=data.get("export", {}).get("formats", ["json"]),
            send_email=data.get("export", {}).get("send_email", False),
            email=data.get("export", {}).get("email")
        )

        schedule_config = ScheduleConfig(
            recurring=data.get("schedule", {}).get("recurring", "one-time"),
            day=data.get("schedule", {}).get("day"),
            date=data.get("schedule", {}).get("date"),
            time=data.get("schedule", {}).get("time")
        )

        advanced_config = AdvancedConfig(
            skip_robots_txt=data.get("advanced", {}).get("skip_robots_txt", False),
            user_agent=data.get("advanced", {}).get("user_agent"),
            proxy_url=data.get("advanced", {}).get("proxy_url"),
            auth_type=data.get("advanced", {}).get("auth_type", "none"),
            auth_credentials=data.get("advanced", {}).get("auth_credentials")
        )

        instruction = JSONScanInstruction(
            name=data.get("name"),
            target=data.get("target"),
            description=data.get("description", ""),
            scope=data.get("scope", []),
            modules=data.get("modules", ["all"]),
            depth=data.get("depth", "medium"),
            concurrency=data.get("concurrency", 5),
            timeout=data.get("timeout", 600),
            notifications=notifications,
            export_config=export_config,
            schedule_config=schedule_config,
            advanced_config=advanced_config
        )

        return instruction

    def validate_json(self, json_str: str) -> tuple[bool, List[str]]:
        """
        Validate JSON string without parsing.
        Returns: (is_valid, error_messages)
        """
        try:
            data = json.loads(json_str) if isinstance(json_str, str) else json_str
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {str(e)}"]

        return self.validator.validate(data)

    def get_schema(self) -> dict:
        """Return the JSON schema for UI builders."""
        return JSON_SCAN_SCHEMA

    def suggest_corrections(self, json_str: str) -> List[str]:
        """Suggest corrections for common errors."""
        suggestions = []
        
        try:
            data = json.loads(json_str) if isinstance(json_str, str) else json_str
        except json.JSONDecodeError as e:
            suggestions.append(f"JSON syntax error: {str(e)}")
            return suggestions

        is_valid, errors = self.validator.validate(data)
        if is_valid:
            return []

        # Provide helpful suggestions
        for error in errors:
            if "name" in error and "required" in error.lower():
                suggestions.append("💡 Add 'name' field: a descriptive scan name")
            elif "target" in error and "required" in error.lower():
                suggestions.append("💡 Add 'target' field: the URL or domain to scan")
            elif "modules" in error and "empty" in error.lower():
                suggestions.append("💡 Set 'modules' to ['all'] or specific modules: ['xss', 'sqli']")
            elif "depth" in error:
                suggestions.append("💡 Use 'depth': 'quick' | 'medium' | 'full'")
            elif "concurrency" in error:
                suggestions.append("💡 Set 'concurrency' between 1-50 (default: 5)")
            else:
                suggestions.append(f"⚠️ {error}")

        return suggestions
