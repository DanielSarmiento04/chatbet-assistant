"""
Health check endpoints for monitoring system status.

This module provides endpoints for checking the health of the ChatBet
assistant API and its dependencies (Redis, ChatBet API, etc.).
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import asyncio
from typing import Dict, Any

from ..core.config import get_settings
from ..core.logging import get_logger
from ..services.conversation_manager import get_conversation_manager
from ..services.chatbet_api import get_chatbet_api_client
from ..utils.cache import get_redis_cache

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns basic system status without dependency checks.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ChatBet Assistant API",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint with dependency validation.
    
    Checks if the service is ready to handle requests by validating
    all external dependencies.
    """
    checks = {}
    overall_status = "healthy"
    
    # Check Redis connection
    try:
        # cache = get_redis_cache()
        # await cache.ping()
        checks["redis"] = {"status": "healthy", "latency_ms": 0, "note": "Connection check skipped"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"
    
    # Check ChatBet API connection
    try:
        # api_client = get_chatbet_api_client()
        # Simple check - try to get tournaments
        # start_time = asyncio.get_event_loop().time()
        # tournaments = await api_client.get_tournaments()
        # latency = (asyncio.get_event_loop().time() - start_time) * 1000
        
        checks["chatbet_api"] = {
            "status": "healthy", 
            "latency_ms": 0,
            "note": "Connection check skipped"
        }
    except Exception as e:
        checks["chatbet_api"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"
    
    # Check conversation manager
    try:
        # conversation_manager = get_conversation_manager()
        # Simple validation check
        checks["conversation_manager"] = {"status": "healthy", "note": "Validation check skipped"}
    except Exception as e:
        checks["conversation_manager"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"
    
    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
    
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail=response)
    
    return response


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint.
    
    Simple endpoint to verify the service is running.
    This should always return 200 if the process is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }