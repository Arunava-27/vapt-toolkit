"""VAPT Toolkit — FastAPI backend with modular architecture."""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import os

# Initialize database
from database import init_db
init_db()

# Initialize core managers
from scanner.notifications import get_notification_manager
from scanner.webhooks import get_webhook_manager
from scanner.reporters.template_engine import TemplateEngine
from scanner.web.fp_pattern_database import FalsePositivePatternDB
from wsl_config import wsl

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global state
ACTIVE_SCANS = {}
template_engine = TemplateEngine(db_conn_factory=True)
fp_pattern_db = FalsePositivePatternDB()
notification_manager = get_notification_manager()
webhook_manager = get_webhook_manager()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting VAPT Toolkit server...")
    # Initialize any required resources here
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

app.include_router(scan.router, prefix="/api", tags=["scans"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(bulk.router, prefix="/api", tags=["bulk"])
app.include_router(webhooks.router, prefix="/api", tags=["webhooks"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])
app.include_router(admin.router, prefix="/api", tags=["admin"])

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
