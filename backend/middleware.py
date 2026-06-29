"""
HireIntel API Key Authentication Middleware.

Validates the X-API-Key header on all incoming requests.
If HIREINTEL_API_KEY is not set in the environment, auth is disabled
(open access for local development).
"""

import os
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Simple API key middleware.

    - Reads HIREINTEL_API_KEY from environment.
    - If not set, all requests pass through (dev mode).
    - If set, every request must include a matching X-API-Key header.
    - Skips auth for: GET /, GET /docs, GET /openapi.json, GET /redoc
    """

    # Paths that never require auth
    OPEN_PATHS = frozenset({"/"  , "/docs", "/openapi.json", "/redoc"})

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        expected_key = os.getenv("HIREINTEL_API_KEY")

        # If no key configured, auth is disabled (open dev mode)
        if not expected_key:
            return await call_next(request)

        # Allow unauthenticated access to health / docs endpoints
        if request.url.path in self.OPEN_PATHS:
            return await call_next(request)

        # Allow OPTIONS pre-flight requests (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Validate key
        provided_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        if not provided_key or provided_key != expected_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key. Provide a valid X-API-Key header.",
            )

        return await call_next(request)
