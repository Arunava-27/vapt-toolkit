#!/usr/bin/env python3
"""
VAPT Toolkit REST API Server

This is the main entry point that delegates to the modular server package.

The actual server implementation has been refactored into:
  server/
  ├── main.py (FastAPI app + route registration)
  ├── routes/ (endpoint modules)
  │   ├── scan.py
  │   ├── projects.py
  │   ├── reports.py
  │   ├── bulk.py
  │   ├── webhooks.py
  │   ├── notifications.py
  │   └── admin.py
  ├── services/ (business logic)
  │   └── scan_service.py
  └── middleware/ (auth, rate limiting)
      └── auth.py

For development, run:
    python server.py

For production, run:
    uvicorn server.main:app --host 0.0.0.0 --port 8000

Or with gunicorn:
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker server.main:app
"""

if __name__ == "__main__":
    import uvicorn
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting VAPT Toolkit server from modular server package...")
    
    # Run the modular server
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
