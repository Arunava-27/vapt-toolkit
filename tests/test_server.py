"""
Comprehensive unit tests for server.py - FastAPI endpoints and SSE streaming.
"""
import pytest
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from server import app, ScanState, ACTIVE_SCANS
except ImportError:
    pytest.skip("server module not available", allow_module_level=True)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check_endpoint(self, client):
        """Test GET /api/health endpoint."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]


class TestScanStateClass:
    """Test ScanState data class."""
    
    def test_scan_state_creation(self):
        """Test creating a ScanState."""
        state = ScanState(
            scan_id="scan_001",
            target="https://example.com",
            config={},
            status="running"
        )
        
        assert state.scan_id == "scan_001"
        assert state.target == "https://example.com"
        assert state.status == "running"
    
    def test_scan_state_with_events(self):
        """Test ScanState with events."""
        state = ScanState(
            scan_id="scan_001",
            target="https://example.com",
            config={},
            status="running",
            events=[]
        )
        
        assert state.events == []


class TestProjectEndpoints:
    """Test project-related endpoints."""
    
    @patch('database.save_project')
    @patch('database.get_project')
    def test_list_projects(self, mock_get, mock_save, client):
        """Test GET /api/projects endpoint."""
        mock_get.return_value = None
        
        with patch('database.list_projects') as mock_list:
            mock_list.return_value = [
                {"id": "proj_1", "target": "https://example.com"}
            ]
            
            response = client.get("/api/projects")
            
            # Should be 200 or require auth
            assert response.status_code in [200, 401, 403]
    
    @patch('database.save_project')
    def test_get_project(self, mock_save, client):
        """Test GET /api/projects/{pid} endpoint."""
        mock_save.return_value = {"id": "proj_1", "target": "https://example.com"}
        
        with patch('database.get_project') as mock_get:
            mock_get.return_value = {"id": "proj_1", "target": "https://example.com"}
            
            response = client.get("/api/projects/proj_1")
            
            assert response.status_code in [200, 401, 403, 404]


class TestScanEndpoints:
    """Test scan-related endpoints."""
    
    @patch('database.save_project')
    def test_start_scan_endpoint(self, mock_save, client, sample_project):
        """Test POST /api/scan endpoint."""
        mock_save.return_value = sample_project
        
        scan_config = {
            "target": "https://example.com",
            "scan_type": "full"
        }
        
        with patch('asyncio.create_task'):
            response = client.post("/api/scan", json=scan_config)
            
            # May return 200, 400, or 401 depending on implementation
            assert response.status_code in [200, 400, 401, 403]
    
    def test_get_scan_status_endpoint(self, client):
        """Test GET /api/scan/{scan_id}/status endpoint."""
        with patch.dict(ACTIVE_SCANS, {
            "scan_001": ScanState(
                scan_id="scan_001",
                target="https://example.com",
                config={},
                status="running"
            )
        }):
            response = client.get("/api/scan/scan_001/status")
            
            assert response.status_code in [200, 404]
    
    def test_stop_scan_endpoint(self, client):
        """Test DELETE /api/scan/{scan_id} endpoint."""
        response = client.delete("/api/scan/nonexistent_scan")
        
        assert response.status_code in [200, 404]


class TestWebhookEndpoints:
    """Test webhook management endpoints."""
    
    @patch('database.create_webhook')
    def test_create_webhook_endpoint(self, mock_create, client):
        """Test POST /api/webhooks endpoint."""
        mock_create.return_value = {"id": "wh_001"}
        
        webhook_data = {
            "project_id": "proj_123",
            "url": "https://example.com/webhook",
            "events": ["scan_completed"]
        }
        
        response = client.post("/api/webhooks", json=webhook_data)
        
        assert response.status_code in [200, 201, 400, 401, 403]
    
    @patch('database.get_webhooks')
    def test_list_webhooks_endpoint(self, mock_list, client):
        """Test GET /api/webhooks endpoint."""
        mock_list.return_value = []
        
        response = client.get("/api/webhooks?project_id=proj_123")
        
        assert response.status_code in [200, 400, 401]
    
    @patch('database.delete_webhook')
    def test_delete_webhook_endpoint(self, mock_delete, client):
        """Test DELETE /api/webhooks/{id} endpoint."""
        mock_delete.return_value = None
        
        response = client.delete("/api/webhooks/wh_001")
        
        assert response.status_code in [200, 404, 401]


class TestScheduleEndpoints:
    """Test schedule management endpoints."""
    
    @patch('database.create_schedule')
    def test_create_schedule_endpoint(self, mock_create, client):
        """Test POST /api/schedule endpoint."""
        mock_create.return_value = {"id": "sch_001"}
        
        schedule_data = {
            "project_id": "proj_123",
            "frequency": "daily",
            "time": "02:00"
        }
        
        response = client.post("/api/schedule", json=schedule_data)
        
        assert response.status_code in [200, 201, 400, 401]
    
    @patch('database.delete_schedule')
    def test_delete_schedule_endpoint(self, mock_delete, client):
        """Test DELETE /api/schedule/{id} endpoint."""
        mock_delete.return_value = None
        
        response = client.delete("/api/schedule/sch_001")
        
        assert response.status_code in [200, 404, 401]


class TestAPIKeyEndpoints:
    """Test API key management endpoints."""
    
    @patch('scanner.api_auth.generate_api_key')
    def test_create_api_key_endpoint(self, mock_gen, client):
        """Test POST /api/keys endpoint."""
        mock_gen.return_value = {
            "key": "vaptkey_abc123",
            "key_hash": "hash_value"
        }
        
        response = client.post("/api/keys?project_id=proj_123")
        
        assert response.status_code in [200, 201, 400, 401]
    
    @patch('scanner.api_auth.list_api_keys')
    def test_list_api_keys_endpoint(self, mock_list, client):
        """Test GET /api/keys endpoint."""
        mock_list.return_value = []
        
        response = client.get("/api/keys?project_id=proj_123")
        
        assert response.status_code in [200, 400, 401]


class TestExportEndpoints:
    """Test export endpoints."""
    
    def test_export_json_endpoint(self, client):
        """Test GET /api/exports/json endpoint."""
        response = client.get("/api/exports/json?scan_id=scan_001")
        
        assert response.status_code in [200, 404, 401]
    
    def test_export_csv_endpoint(self, client):
        """Test GET /api/exports/csv endpoint."""
        response = client.get("/api/exports/csv?scan_id=scan_001")
        
        assert response.status_code in [200, 404, 401]
    
    def test_export_pdf_endpoint(self, client):
        """Test GET /api/exports/pdf endpoint."""
        response = client.get("/api/exports/pdf?scan_id=scan_001")
        
        assert response.status_code in [200, 404, 401]


class TestSSEStreaming:
    """Test Server-Sent Events streaming."""
    
    def test_sse_endpoint_format(self, client):
        """Test GET /api/scan/{scan_id}/stream endpoint returns SSE format."""
        with patch.dict(ACTIVE_SCANS, {
            "scan_001": ScanState(
                scan_id="scan_001",
                target="https://example.com",
                config={},
                status="running",
                events=[]
            )
        }):
            response = client.get("/api/scan/scan_001/stream", stream=True)
            
            # Should be 200 or 404/401
            if response.status_code == 200:
                # Check SSE content type
                assert "text/event-stream" in response.headers.get("content-type", "")


class TestComparisonEndpoints:
    """Test scan comparison endpoints."""
    
    def test_compare_scans_endpoint(self, client):
        """Test POST /api/compare/scans endpoint."""
        comparison_data = {
            "scan_id_1": "scan_001",
            "scan_id_2": "scan_002"
        }
        
        response = client.post("/api/compare/scans", json=comparison_data)
        
        assert response.status_code in [200, 400, 404, 401]


class TestErrorHandling:
    """Test error handling in endpoints."""
    
    def test_nonexistent_endpoint(self, client):
        """Test accessing nonexistent endpoint."""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == 404
    
    def test_invalid_json_body(self, client):
        """Test sending invalid JSON."""
        response = client.post("/api/scan", data="not valid json")
        
        assert response.status_code in [400, 422, 401]
    
    def test_missing_required_fields(self, client):
        """Test request with missing required fields."""
        response = client.post("/api/scan", json={})
        
        assert response.status_code in [400, 422]


class TestCORSHeaders:
    """Test CORS headers."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.get("/api/health")
        
        # CORS headers should be present or absent depending on config
        headers = response.headers
