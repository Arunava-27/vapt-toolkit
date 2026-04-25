"""Tests for JSON scan executor."""

import pytest
import json
from scanner.json_scan_executor import (
    JSONScanExecutor, JSONScanValidator, JSONScanInstruction,
    NotificationConfig, ExportConfig, ScheduleConfig, AdvancedConfig
)


class TestJSONScanValidator:
    """Test JSON scan validator."""

    def setup_method(self):
        self.validator = JSONScanValidator()

    def test_valid_minimal_json(self):
        """Test validation of minimal valid JSON."""
        data = {
            "name": "Test Scan",
            "target": "https://example.com"
        }
        is_valid, errors = self.validator.validate(data)
        assert is_valid
        assert len(errors) == 0

    def test_valid_full_json(self):
        """Test validation of full JSON with all fields."""
        data = {
            "name": "Full Scan",
            "target": "https://example.com",
            "description": "Comprehensive scan",
            "scope": ["https://example.com/*"],
            "modules": ["xss", "sqli", "csrf"],
            "depth": "full",
            "concurrency": 8,
            "timeout": 900,
            "notifications": {
                "email": "test@example.com",
                "severity_filter": "high",
                "channels": ["email"]
            },
            "export": {
                "formats": ["pdf", "json"],
                "send_email": True
            },
            "schedule": {
                "recurring": "weekly",
                "day": "Monday",
                "time": "14:30"
            },
            "advanced": {
                "skip_robots_txt": True,
                "auth_type": "bearer"
            }
        }
        is_valid, errors = self.validator.validate(data)
        assert is_valid
        assert len(errors) == 0

    def test_missing_required_name(self):
        """Test validation fails with missing name."""
        data = {"target": "https://example.com"}
        is_valid, errors = self.validator.validate(data)
        assert not is_valid
        assert any("name" in e.lower() for e in errors)

    def test_missing_required_target(self):
        """Test validation fails with missing target."""
        data = {"name": "Test Scan"}
        is_valid, errors = self.validator.validate(data)
        assert not is_valid
        assert any("target" in e.lower() for e in errors)

    def test_empty_name(self):
        """Test validation fails with empty name."""
        data = {"name": "", "target": "https://example.com"}
        is_valid, errors = self.validator.validate(data)
        assert not is_valid
        assert any("empty" in e.lower() for e in errors)

    def test_name_too_long(self):
        """Test validation fails with name too long."""
        data = {
            "name": "x" * 201,
            "target": "https://example.com"
        }
        is_valid, errors = self.validator.validate(data)
        assert not is_valid

    def test_invalid_depth(self):
        """Test validation fails with invalid depth."""
        data = {
            "name": "Test",
            "target": "https://example.com",
            "depth": "invalid"
        }
        is_valid, errors = self.validator.validate(data)
        assert not is_valid
        assert any("depth" in e.lower() for e in errors)

    def test_valid_depth_values(self):
        """Test validation succeeds with all valid depth values."""
        for depth in ["quick", "medium", "full"]:
            data = {
                "name": "Test",
                "target": "https://example.com",
                "depth": depth
            }
            is_valid, errors = self.validator.validate(data)
            assert is_valid, f"Failed for depth: {depth}"

    def test_invalid_module(self):
        """Test validation fails with invalid module."""
        data = {
            "name": "Test",
            "target": "https://example.com",
            "modules": ["xss", "invalid_module"]
        }
        is_valid, errors = self.validator.validate(data)
        assert not is_valid
        assert any("module" in e.lower() for e in errors)

    def test_valid_all_module(self):
        """Test validation succeeds with 'all' module."""
        data = {
            "name": "Test",
            "target": "https://example.com",
            "modules": ["all"]
        }
        is_valid, errors = self.validator.validate(data)
        assert is_valid

    def test_valid_module_list(self):
        """Test validation succeeds with valid module list."""
        data = {
            "name": "Test",
            "target": "https://example.com",
            "modules": ["xss", "sqli", "csrf", "auth"]
        }
        is_valid, errors = self.validator.validate(data)
        assert is_valid

    def test_empty_modules_list(self):
        """Test validation fails with empty modules list."""
        data = {
            "name": "Test",
            "target": "https://example.com",
            "modules": []
        }
        is_valid, errors = self.validator.validate(data)
        assert not is_valid

    def test_invalid_concurrency(self):
        """Test validation fails with invalid concurrency."""
        for value in [0, -1, 51, 100]:
            data = {
                "name": "Test",
                "target": "https://example.com",
                "concurrency": value
            }
            is_valid, errors = self.validator.validate(data)
            assert not is_valid, f"Should fail for concurrency: {value}"

    def test_valid_concurrency(self):
        """Test validation succeeds with valid concurrency."""
        for value in [1, 5, 10, 50]:
            data = {
                "name": "Test",
                "target": "https://example.com",
                "concurrency": value
            }
            is_valid, errors = self.validator.validate(data)
            assert is_valid, f"Should pass for concurrency: {value}"

    def test_invalid_timeout(self):
        """Test validation fails with invalid timeout."""
        for value in [0, 1, 3601]:
            data = {
                "name": "Test",
                "target": "https://example.com",
                "timeout": value
            }
            is_valid, errors = self.validator.validate(data)
            assert not is_valid, f"Should fail for timeout: {value}"

    def test_invalid_notification_channel(self):
        """Test validation fails with invalid notification channel."""
        data = {
            "name": "Test",
            "target": "https://example.com",
            "notifications": {
                "channels": ["invalid_channel"]
            }
        }
        is_valid, errors = self.validator.validate(data)
        assert not is_valid

    def test_invalid_export_format(self):
        """Test validation fails with invalid export format."""
        data = {
            "name": "Test",
            "target": "https://example.com",
            "export": {
                "formats": ["invalid_format"]
            }
        }
        is_valid, errors = self.validator.validate(data)
        assert not is_valid

    def test_invalid_schedule_recurring(self):
        """Test validation fails with invalid recurring pattern."""
        data = {
            "name": "Test",
            "target": "https://example.com",
            "schedule": {
                "recurring": "invalid"
            }
        }
        is_valid, errors = self.validator.validate(data)
        assert not is_valid

    def test_invalid_schedule_day(self):
        """Test validation fails with invalid day."""
        data = {
            "name": "Test",
            "target": "https://example.com",
            "schedule": {
                "day": "InvalidDay"
            }
        }
        is_valid, errors = self.validator.validate(data)
        assert not is_valid

    def test_valid_schedule_day(self):
        """Test validation succeeds with valid days."""
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            data = {
                "name": "Test",
                "target": "https://example.com",
                "schedule": {
                    "day": day
                }
            }
            is_valid, errors = self.validator.validate(data)
            assert is_valid, f"Should pass for day: {day}"

    def test_invalid_time_format(self):
        """Test validation fails with invalid time format."""
        for time in ["25:00", "14:60", "14", "14:30:00", "invalid"]:
            data = {
                "name": "Test",
                "target": "https://example.com",
                "schedule": {
                    "time": time
                }
            }
            is_valid, errors = self.validator.validate(data)
            assert not is_valid, f"Should fail for time: {time}"

    def test_valid_time_format(self):
        """Test validation succeeds with valid time format."""
        for time in ["00:00", "12:30", "23:59", "14:45"]:
            data = {
                "name": "Test",
                "target": "https://example.com",
                "schedule": {
                    "time": time
                }
            }
            is_valid, errors = self.validator.validate(data)
            assert is_valid, f"Should pass for time: {time}"

    def test_invalid_schedule_date(self):
        """Test validation fails with invalid schedule date."""
        for date in [0, -1, 32]:
            data = {
                "name": "Test",
                "target": "https://example.com",
                "schedule": {
                    "date": date
                }
            }
            is_valid, errors = self.validator.validate(data)
            assert not is_valid, f"Should fail for date: {date}"

    def test_valid_auth_type(self):
        """Test validation succeeds with valid auth types."""
        for auth in ["none", "basic", "bearer", "api_key", "oauth2"]:
            data = {
                "name": "Test",
                "target": "https://example.com",
                "advanced": {
                    "auth_type": auth
                }
            }
            is_valid, errors = self.validator.validate(data)
            assert is_valid, f"Should pass for auth_type: {auth}"


class TestJSONScanExecutor:
    """Test JSON scan executor."""

    def setup_method(self):
        self.executor = JSONScanExecutor()

    def test_parse_valid_json_string(self):
        """Test parsing valid JSON string."""
        json_str = json.dumps({
            "name": "Test Scan",
            "target": "https://example.com"
        })
        instruction = self.executor.parse_json_instruction(json_str)
        assert instruction is not None
        assert instruction.name == "Test Scan"
        assert instruction.target == "https://example.com"

    def test_parse_valid_json_dict(self):
        """Test parsing valid JSON dict."""
        data = {
            "name": "Test Scan",
            "target": "https://example.com"
        }
        instruction = self.executor.parse_json_instruction(data)
        assert instruction is not None
        assert instruction.name == "Test Scan"

    def test_parse_invalid_json_string(self):
        """Test parsing invalid JSON string returns None."""
        json_str = "{ invalid json"
        instruction = self.executor.parse_json_instruction(json_str)
        assert instruction is None

    def test_parse_invalid_json_data(self):
        """Test parsing invalid JSON data returns None."""
        data = {"target": "https://example.com"}  # missing required name
        instruction = self.executor.parse_json_instruction(data)
        assert instruction is None

    def test_instruction_defaults(self):
        """Test that instruction has correct defaults."""
        data = {
            "name": "Test",
            "target": "https://example.com"
        }
        instruction = self.executor.parse_json_instruction(data)
        assert instruction.description == ""
        assert instruction.scope == []
        assert instruction.modules == ["all"]
        assert instruction.depth == "medium"
        assert instruction.concurrency == 5
        assert instruction.timeout == 600
        assert instruction.notifications.severity_filter == "high"
        assert instruction.advanced_config.skip_robots_txt == False

    def test_instruction_to_dict(self):
        """Test converting instruction to dict."""
        data = {
            "name": "Test",
            "target": "https://example.com",
            "modules": ["xss", "sqli"],
            "depth": "full"
        }
        instruction = self.executor.parse_json_instruction(data)
        result = instruction.to_dict()
        assert result["name"] == "Test"
        assert result["target"] == "https://example.com"
        assert result["modules"] == ["xss", "sqli"]
        assert result["depth"] == "full"

    def test_validate_json_string_valid(self):
        """Test validate_json with valid string."""
        json_str = json.dumps({
            "name": "Test",
            "target": "https://example.com"
        })
        is_valid, errors = self.executor.validate_json(json_str)
        assert is_valid
        assert len(errors) == 0

    def test_validate_json_string_invalid(self):
        """Test validate_json with invalid string."""
        json_str = "{ invalid"
        is_valid, errors = self.executor.validate_json(json_str)
        assert not is_valid
        assert len(errors) > 0

    def test_suggest_corrections(self):
        """Test suggestions for common errors."""
        json_str = json.dumps({
            "target": "https://example.com"
        })
        suggestions = self.executor.suggest_corrections(json_str)
        assert len(suggestions) > 0
        assert any("name" in s.lower() for s in suggestions)

    def test_get_schema(self):
        """Test getting JSON schema."""
        schema = self.executor.get_schema()
        assert schema is not None
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        assert "name" in schema["required"]
        assert "target" in schema["required"]

    def test_parse_with_all_fields(self):
        """Test parsing instruction with all fields."""
        data = {
            "name": "Full Scan",
            "target": "https://example.com",
            "description": "Test description",
            "scope": ["https://example.com/*"],
            "modules": ["xss", "sqli", "csrf"],
            "depth": "full",
            "concurrency": 10,
            "timeout": 1200,
            "notifications": {
                "email": "test@example.com",
                "slack_webhook": "https://hooks.slack.com/...",
                "severity_filter": "medium",
                "channels": ["email", "slack"]
            },
            "export": {
                "formats": ["pdf", "json", "csv"],
                "send_email": True,
                "email": "report@example.com"
            },
            "schedule": {
                "recurring": "weekly",
                "day": "Monday",
                "time": "14:30"
            },
            "advanced": {
                "skip_robots_txt": True,
                "user_agent": "Custom UA",
                "proxy_url": "http://proxy.example.com:8080",
                "auth_type": "bearer",
                "auth_credentials": {"token": "abc123"}
            }
        }
        instruction = self.executor.parse_json_instruction(data)
        assert instruction is not None
        assert instruction.name == "Full Scan"
        assert instruction.description == "Test description"
        assert instruction.modules == ["xss", "sqli", "csrf"]
        assert instruction.depth == "full"
        assert instruction.concurrency == 10
        assert instruction.timeout == 1200
        assert instruction.notifications.email == "test@example.com"
        assert instruction.export_config.send_email == True
        assert instruction.schedule_config.recurring == "weekly"
        assert instruction.advanced_config.skip_robots_txt == True


class TestNotificationConfig:
    """Test notification configuration."""

    def test_notification_config_defaults(self):
        """Test notification config defaults."""
        config = NotificationConfig()
        assert config.email is None
        assert config.slack_webhook is None
        assert config.severity_filter == "high"
        assert config.channels == ["desktop"]

    def test_notification_config_to_dict(self):
        """Test converting notification config to dict."""
        config = NotificationConfig(
            email="test@example.com",
            severity_filter="medium",
            channels=["email", "slack"]
        )
        result = config.to_dict()
        assert result["email"] == "test@example.com"
        assert result["severity_filter"] == "medium"
        assert result["channels"] == ["email", "slack"]


class TestExportConfig:
    """Test export configuration."""

    def test_export_config_defaults(self):
        """Test export config defaults."""
        config = ExportConfig()
        assert config.formats == ["json"]
        assert config.send_email == False
        assert config.email is None

    def test_export_config_to_dict(self):
        """Test converting export config to dict."""
        config = ExportConfig(
            formats=["pdf", "json", "csv"],
            send_email=True,
            email="report@example.com"
        )
        result = config.to_dict()
        assert result["formats"] == ["pdf", "json", "csv"]
        assert result["send_email"] == True
        assert result["email"] == "report@example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
