"""
Security and authentication utilities.

This module handles JWT token validation, user authentication, and security
middleware. I'm keeping this simple but secure - using the ChatBet API's
own authentication system rather than rolling our own user management.

The approach here is to act as a proxy for authentication - we validate
tokens with the ChatBet API and cache the results for performance.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import wraps

import httpx
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

logger = logging.getLogger(__name__)

# Security scheme for FastAPI automatic docs
security = HTTPBearer(auto_error=False)


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


class AuthenticationService:
    """
    Handles authentication with the ChatBet API.
    
    This service acts as a bridge between our app and the ChatBet authentication
    system. We validate tokens with their API and cache successful validations
    to reduce API calls and improve performance.
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.chatbet_api_base_url,
            timeout=settings.chatbet_api_timeout
        )
        # Simple in-memory cache for token validation
        # In production, this would use Redis
        self._token_cache: Dict[str, Dict[str, Any]] = {}
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a token with the ChatBet API.
        
        Returns user information if token is valid, None otherwise.
        We cache successful validations for 15 minutes to reduce API load.
        """
        # Check cache first (simple TTL implementation)
        cache_key = f"token:{token}"
        if cache_key in self._token_cache:
            cached_data = self._token_cache[cache_key]
            if datetime.now() < cached_data["expires"]:
                logger.debug("Token validation cache hit")
                return cached_data["user_data"]
            else:
                # Remove expired cache entry
                del self._token_cache[cache_key]
        
        try:
            # Validate with ChatBet API
            response = await self.client.get(
                "/auth/validate_token",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Cache successful validation for 15 minutes
                self._token_cache[cache_key] = {
                    "user_data": user_data,
                    "expires": datetime.now() + timedelta(minutes=15)
                }
                
                logger.info(f"Token validated successfully for user: {user_data.get('username', 'unknown')}")
                return user_data
            else:
                logger.warning(f"Token validation failed with status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return None
    
    async def get_user_balance(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user balance from ChatBet API."""
        try:
            response = await self.client.get(
                "/auth/get_user_balance",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get user balance, status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user balance: {str(e)}")
            return None
    
    async def close(self):
        """Clean up HTTP client."""
        await self.client.aclose()


# Global auth service instance
auth_service = AuthenticationService()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to get current authenticated user.
    
    This is used as a dependency in protected endpoints. It extracts the
    Bearer token from the request and validates it with the ChatBet API.
    
    Returns None if no token or invalid token (for optional auth).
    Raises HTTPException for required auth when token is invalid.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    user_data = await auth_service.validate_token(token)
    
    if not user_data:
        # Log the attempt for security monitoring
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"Invalid token attempt from IP: {client_ip}")
        return None
    
    return user_data


async def require_auth(
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    FastAPI dependency that requires authentication.
    
    Use this dependency when an endpoint requires a valid user.
    It will raise 401 Unauthorized if no valid token is provided.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def rate_limit(max_requests: int = None, window_seconds: int = None):
    """
    Simple rate limiting decorator.
    
    This is a basic rate limiter based on IP address. In production,
    you'd want to use Redis or a dedicated rate limiting service.
    """
    max_req = max_requests or settings.rate_limit_requests
    window = window_seconds or settings.rate_limit_window
    
    # Simple in-memory rate limiting (replace with Redis in production)
    request_counts: Dict[str, Dict[str, Any]] = {}
    
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            now = datetime.now()
            
            # Clean old entries
            cutoff = now - timedelta(seconds=window)
            request_counts[client_ip] = {
                "count": request_counts.get(client_ip, {}).get("count", 0),
                "window_start": request_counts.get(client_ip, {}).get("window_start", now)
            }
            
            # Reset counter if window expired
            if request_counts[client_ip]["window_start"] < cutoff:
                request_counts[client_ip] = {"count": 0, "window_start": now}
            
            # Check rate limit
            if request_counts[client_ip]["count"] >= max_req:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            # Increment counter
            request_counts[client_ip]["count"] += 1
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    import uuid
    return str(uuid.uuid4())


async def cleanup_security():
    """Cleanup function to be called on app shutdown."""
    await auth_service.close()


def get_api_key_auth():
    """
    API key authentication dependency for FastAPI.
    
    This can be used as a dependency in FastAPI routes to require
    API key authentication.
    """
    from fastapi import HTTPException, Security
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    
    security_scheme = HTTPBearer()
    
    def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
        if not credentials or credentials.credentials != settings.secret_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        return credentials.credentials
    
    return verify_api_key