from fastapi import HTTPException, Header
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    api_key: Optional[str] = None
) -> str:
    """
    Verify API key from header or query parameter
    
    Args:
        x_api_key: API key from X-API-Key header
        api_key: API key from query parameter
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    # Skip auth if API_KEY is not set (development mode)
    if not settings.API_KEY:
        logger.warning("API_KEY not set - authentication disabled")
        return ""

    # Check header first, then query parameter
    provided_key = x_api_key or api_key

    if not provided_key:
        logger.warning("Missing API key")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Unauthorized",
                "message": "Missing API key. Provide via X-API-Key header or api_key query parameter."
            }
        )

    if provided_key != settings.API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Unauthorized",
                "message": "Invalid API key"
            }
        )

    return provided_key
