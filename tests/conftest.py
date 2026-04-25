"""
Pytest configuration and shared fixtures for the VAPT toolkit test suite.
"""
import pytest
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.execute.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    return mock_conn


@pytest.fixture
def sample_project():
    """Sample project data for testing."""
    return {
        "id": "proj_test_123",
        "target": "https://example.com",
        "name": "Test Project",
        "status": "completed",
        "scans": [
            {
                "scan_id": "scan_001",
                "timestamp": datetime.now().isoformat(),
                "findings": 15,
                "severity": "high"
            }
        ],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_scan_result():
    """Sample scan result for testing."""
    return {
        "scan_id": "scan_test_001",
        "target": "https://example.com",
        "status": "completed",
        "started_at": datetime.now().isoformat(),
        "completed_at": (datetime.now() + timedelta(minutes=5)).isoformat(),
        "findings": [
            {
                "id": "vuln_001",
                "type": "XSS",
                "severity": "high",
                "confidence": 0.95,
                "endpoint": "/api/search",
                "parameter": "q",
                "payload": "<script>alert('xss')</script>",
                "evidence": "Payload reflected in response",
                "cwe": "CWE-79",
                "owasp": "A03:2021 – Injection"
            },
            {
                "id": "vuln_002",
                "type": "SQLi",
                "severity": "critical",
                "confidence": 0.98,
                "endpoint": "/api/users",
                "parameter": "id",
                "payload": "1' OR '1'='1",
                "evidence": "Time-based SQLi detected",
                "cwe": "CWE-89",
                "owasp": "A03:2021 – Injection"
            }
        ],
        "statistics": {
            "critical": 1,
            "high": 3,
            "medium": 5,
            "low": 2,
            "total": 11
        }
    }


@pytest.fixture
def sample_webhook():
    """Sample webhook data for testing."""
    return {
        "id": "webhook_test_001",
        "project_id": "proj_test_123",
        "url": "https://example.com/webhook",
        "events": ["scan_completed", "finding_discovered"],
        "secret_hash": "hashed_secret_value",
        "enabled": True,
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_schedule():
    """Sample schedule data for testing."""
    return {
        "id": "schedule_test_001",
        "project_id": "proj_test_123",
        "frequency": "daily",
        "time": "02:00",
        "enabled": True,
        "last_run": datetime.now().isoformat(),
        "next_run": (datetime.now() + timedelta(days=1)).isoformat(),
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_api_key():
    """Sample API key data for testing."""
    return {
        "id": "key_test_001",
        "project_id": "proj_test_123",
        "key": "vaptkey_abcdef123456789",
        "key_hash": "hashed_key_value",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat()
    }


@pytest.fixture
def sample_notification():
    """Sample notification data for testing."""
    return {
        "type": "finding_discovered",
        "severity": "high",
        "title": "XSS Vulnerability Found",
        "description": "Reflected XSS found in /api/search endpoint",
        "project_id": "proj_test_123",
        "scan_id": "scan_test_001",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession."""
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"status": "ok"})
    mock_response.text = AsyncMock(return_value="<html></html>")
    mock_response.headers = {}
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.head = AsyncMock(return_value=mock_response)
    return mock_session


@pytest.fixture
def mock_requests():
    """Mock requests library."""
    mock_req = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"status": "ok"})
    mock_response.text = "<html></html>"
    mock_response.headers = {}
    mock_req.get = MagicMock(return_value=mock_response)
    mock_req.post = MagicMock(return_value=mock_response)
    return mock_req


@pytest.fixture
def mock_smtp():
    """Mock SMTP server for email tests."""
    mock_server = MagicMock()
    mock_server.send_message = MagicMock()
    return mock_server


@pytest.fixture
def mock_nmap():
    """Mock nmap scanner."""
    mock_nm = MagicMock()
    mock_nm.scan = MagicMock(return_value=None)
    mock_nm.all_hosts = MagicMock(return_value=["192.168.1.1"])
    return mock_nm


@pytest.fixture
def sample_scope_targets():
    """Sample scope targets for testing."""
    return {
        "urls": [
            "https://example.com",
            "https://api.example.com/v1"
        ],
        "domains": [
            "example.com",
            "*.example.com",
            "api.example.com"
        ],
        "ips": [
            "192.168.1.1",
            "10.0.0.0/24"
        ],
        "mixed": [
            "https://example.com:8080",
            "example.com",
            "192.168.1.1",
            "*.example.com",
            "10.0.0.0/8"
        ]
    }


@pytest.fixture
def sample_fp_pattern():
    """Sample false positive pattern for testing."""
    return {
        "id": "fp_pattern_001",
        "project_id": "proj_test_123",
        "pattern_type": "regex",
        "description": "Known FP - jQuery AJAX call",
        "regex_pattern": r'\.ajax\(\{.*url:\s*["\']\/api',
        "severity_impact": 0,
        "enabled": True,
        "keywords": ["ajax", "jquery", "api"],
        "safe_framework": "jquery",
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_bulk_job():
    """Sample bulk scanning job for testing."""
    return {
        "id": "bulk_job_001",
        "project_id": "proj_test_123",
        "status": "in_progress",
        "progress": 45,
        "total_targets": 10,
        "completed_count": 4,
        "failed_count": 1,
        "created_at": datetime.now().isoformat(),
        "started_at": datetime.now().isoformat(),
        "config": {
            "scan_type": "quick",
            "parallel_scans": 3
        }
    }


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "asyncio: mark test as async test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security-related"
    )
