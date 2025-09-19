"""
Security dependencies for authentication and authorization.

This module provides security dependencies that can be used to protect
API routes and ensure only authenticated users can access certain endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Annotated
import asyncio
from functools import wraps

from ..core.logging import get_logger
from ..models.api_models import UserInfo
from ..services.chatbet_api import get_api_client
from ..utils.exceptions import AuthenticationError

logger = get_logger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInfo:
    """
    Get current authenticated user from token.
    
    This dependency validates the token and returns user information.
    Raises HTTP 401 if token is invalid.
    """
    try:
        token = credentials.credentials
        api_client = await get_api_client()
        
        # Validate token and get user info
        user_info = await api_client.validate_token(token)
        
        if not user_info:
            logger.warning(f"Invalid token attempt: {token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Authenticated user: {user_info.username}")
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[UserInfo]:
    """
    Get current user if token is provided (optional authentication).
    
    This dependency allows endpoints to work with or without authentication,
    but provides user info if a valid token is present.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        api_client = await get_api_client()
        
        # Validate token and get user info
        user_info = await api_client.validate_token(token)
        
        if user_info:
            logger.debug(f"Optional auth - authenticated user: {user_info.username}")
        else:
            logger.debug("Optional auth - invalid token provided")
        
        return user_info
        
    except Exception as e:
        logger.warning(f"Optional authentication error: {str(e)}")
        return None


async def validate_token_only(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Validate token without fetching user info.
    
    Returns the validated token string. Useful for endpoints that only
    need to verify authentication without user details.
    """
    try:
        token = credentials.credentials
        api_client = await get_api_client()
        
        # Quick token validation
        validation_response = await api_client.validate_token_endpoint(token)
        
        if not validation_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return token
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation service error"
        )


def require_authentication(func):
    """
    Decorator to require authentication for a function.
    
    This can be used as an alternative to the dependency injection approach.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would need to be implemented based on the specific use case
        # For now, we'll rely on the dependency injection approach
        return await func(*args, **kwargs)
    
    return wrapper


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[UserInfo, Depends(get_current_user)]
OptionalUser = Annotated[Optional[UserInfo], Depends(get_optional_user)]
ValidatedToken = Annotated[str, Depends(validate_token_only)]