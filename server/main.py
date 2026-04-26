"""VAPT Toolkit — FastAPI backend with modular architecture."""

import sys
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
import os

# Ensure project root is in Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Initialize database
from database import init_db
init_db()

# Initialize core managers
from scanner.notifications import get_notification_manager
from scanner.webhooks import get_webhook_manager
from scanner.reporters.template_engine import TemplateEngine
from scanner.web.fp_pattern_database import FalsePositivePatternDB
from scanner.json_scan_executor import JSONScanExecutor, JSONScanValidator
from wsl_config import wsl

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global state
ACTIVE_SCANS = {}
template_engine = TemplateEngine(db_conn_factory=True)
fp_pattern_db = FalsePositivePatternDB()
notification_manager = get_notification_manager()
webhook_manager = get_webhook_manager()
json_scan_executor = JSONScanExecutor()
json_scan_validator = JSONScanValidator()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting VAPT Toolkit server...")
    logger.info(f"WSL Status: {wsl.get_status()}")
    yield
    # Shutdown
    logger.info("Shutting down VAPT Toolkit server...")

# Create FastAPI app
app = FastAPI(
    title="VAPT Toolkit REST API",
    version="1.0.0",
    description="REST API for bulk scanning, status tracking, and automation.",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
from server.routes import scan, projects, reports, bulk, webhooks, notifications, admin

# Initialize route module globals
scan.json_scan_executor = json_scan_executor
scan.json_scan_validator = json_scan_validator
scan.ACTIVE_SCANS = ACTIVE_SCANS

app.include_router(scan.router, prefix="/api", tags=["scans"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(bulk.router, prefix="/api", tags=["bulk"])
app.include_router(webhooks.router, prefix="/api", tags=["webhooks"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])
app.include_router(admin.router, prefix="/api", tags=["admin"])

# Mount static files (frontend built dist folder)
frontend_dist = PROJECT_ROOT / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    logger.info(f"Mounted frontend static files from {frontend_dist}")
else:
    logger.warning(f"Frontend dist folder not found at {frontend_dist}. Frontend files will not be served.")

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="VAPT Toolkit REST API",
        version="1.0.0",
        description="REST API for bulk scanning, status tracking, and automation.",
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "custom",
            "description": "API key authentication. Use format: Bearer <api_key>"
        }
    }
    
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=False)
