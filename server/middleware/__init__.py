"""Middleware module for VAPT Toolkit."""

from .auth import get_api_key, require_api_key

__all__ = ["get_api_key", "require_api_key"]
