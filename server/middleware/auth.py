"""Authentication middleware and dependencies for API key validation."""

from fastapi import Header, HTTPException, Depends
from scanner.api_auth import validate_api_key, check_rate_limit


async def get_api_key(authorization: str = Header(None)) -> str:
    """Extract and validate API key from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    try:
        scheme, credentials = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
        return credentials
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")


async def require_api_key(api_key: str = Depends(get_api_key)) -> str:
    """Dependency: validate API key and check rate limit."""
    project_id = validate_api_key(api_key)
    if not project_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not check_rate_limit(api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded (100 requests/min)")
    
    return project_id
