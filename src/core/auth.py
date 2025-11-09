"""
Authentication and authorization for DevMind Pipeline API.
Provides API key validation for securing endpoints.
"""

from typing import Optional

import structlog
from fastapi import HTTPException, Request, status

logger = structlog.get_logger(__name__)


class APIKeyAuth:
    """API key authentication provider."""

    def __init__(self, valid_api_key: str):
        """
        Initialize API key authenticator.

        Args:
            valid_api_key: The valid API key for authentication
        """
        self.valid_api_key = valid_api_key

    async def __call__(self, request: Request) -> str:
        """
        Validate API key from request headers.

        Args:
            request: FastAPI request object

        Returns:
            Validated API key

        Raises:
            HTTPException: If API key is missing or invalid
        """
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning("Missing API key in request", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-API-Key header",
            )

        if api_key != self.valid_api_key:
            logger.warning(
                "Invalid API key provided",
                path=request.url.path,
                provided_key_length=len(api_key),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )

        return api_key


def get_api_key_auth(valid_api_key: str) -> APIKeyAuth:
    """
    Factory function to create API key authenticator.

    Args:
        valid_api_key: The valid API key for authentication

    Returns:
        APIKeyAuth instance
    """
    return APIKeyAuth(valid_api_key)
