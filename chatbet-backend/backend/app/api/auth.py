"""
Authentication API endpoints.

This module provides authentication endpoints for the ChatBet assistant,
including token generation, validation, and user management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta

from ..core.config import settings
from ..core.logging import get_logger
from ..models.api_models import (
    TokenRequest, TokenResponse, UserValidationResponse, 
    TokenValidationResponse, UserInfo
)
from ..services.chatbet_api import get_api_client
from ..utils.exceptions import AuthenticationError

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/generate_token", response_model=TokenResponse)
async def generate_token() -> TokenResponse:
    """
    Generate authentication token from ChatBet API.
    
    This endpoint forwards the token generation request to the ChatBet API
    and returns the token for client authentication.
    """
    try:
        api_client = await get_api_client()
        token_response = await api_client.generate_token()
        
        logger.info("Authentication token generated successfully")
        return token_response
        
    except Exception as e:
        logger.error(f"Failed to generate token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authentication token"
        )


@router.post("/validate_token")
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenValidationResponse:
    """
    Validate authentication token.
    
    Validates the provided token against the ChatBet API and returns
    validation status and user information if valid.
    """
    try:
        token = credentials.credentials
        api_client = await get_api_client()
        
        # Validate token with ChatBet API
        validation_response = await api_client.validate_token_endpoint(token)
        
        if not validation_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        logger.info("Token validated successfully")
        return validation_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation failed"
        )


@router.get("/user_info")
async def get_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[UserInfo]:
    """
    Get user information from valid token.
    
    Returns user information associated with the provided valid token.
    """
    try:
        token = credentials.credentials
        api_client = await get_api_client()
        
        # Get user info using token
        user_info = await api_client.validate_token(token)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or user not found"
            )
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.post("/refresh_token", response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenResponse:
    """
    Refresh authentication token.
    
    Generates a new token using the current valid token.
    """
    try:
        # First validate the current token
        token = credentials.credentials
        api_client = await get_api_client()
        
        user_info = await api_client.validate_token(token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Generate new token
        new_token_response = await api_client.generate_token()
        
        logger.info("Token refreshed successfully")
        return new_token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )