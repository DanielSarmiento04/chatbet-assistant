"""
FastAPI application routes and middleware setup.

This module sets up all the routes, middleware, error handlers,
and application configuration for the ChatBet assistant.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uuid
from typing import AsyncGenerator

from . import app
from .routes import llm_service
from .core.config import get_settings
from .core.logging import setup_logging, get_logger
from .core.security import get_api_key_auth
from .api.chat import router as chat_router
from .api.health import router as health_router
from .api.websocket import router as websocket_router
from .utils.exceptions import ChatBetException
from .services.conversation_manager import get_conversation_manager
from .services.websocket_manager import WebSocketConnectionManager
from .services.sports_streaming import get_sports_streamer, cleanup_sports_streamer

# Setup logging first
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


# Configure FastAPI application
app.docs_url = "/docs" if settings.debug else None
app.redoc_url = "/redoc" if settings.debug else None

# Set up lifespan events manually since we can't modify constructor after creation
@app.on_event("startup")
async def startup_event():
    """Handle application startup."""
    logger.info("Starting ChatBet Assistant API")
    
    try:
        # Initialize WebSocket manager
        websocket_manager = WebSocketConnectionManager()
        app.state.websocket_manager = websocket_manager
        
        # Initialize sports streamer
        sports_streamer = get_sports_streamer(websocket_manager)
        await sports_streamer.initialize()
        await sports_streamer.start_streaming()
        app.state.sports_streamer = sports_streamer
        
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown."""
    logger.info("Shutting down ChatBet Assistant API")
    
    try:
        # Cleanup sports streamer
        await cleanup_sports_streamer()
        
        # Cleanup WebSocket connections
        if hasattr(app.state, 'websocket_manager'):
            manager = app.state.websocket_manager
            active_sessions = list(manager.connections.keys())
            for session_id in active_sessions:
                await manager.disconnect(session_id, "server_shutdown")
        
        logger.info("Services cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# # Add middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[str(origin) for origin in settings.cors_origins],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# app.middleware.
# app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests and responses."""
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    start_time = time.time()
    
    logger.info(
        "Request started",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers)
        }
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        "Request completed",
        extra={
            "correlation_id": correlation_id,
            "status_code": response.status_code,
            "process_time": process_time
        }
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response


@app.exception_handler(ChatBetException)
async def chatbet_exception_handler(request: Request, exc: ChatBetException):
    """Handle ChatBet-specific exceptions."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.error(
        f"ChatBet exception: {exc.message}",
        extra={
            "correlation_id": correlation_id,
            "error_code": getattr(exc, 'error_code', 'unknown'),
            "details": exc.details
        },
        exc_info=exc
    )
    
    status_code = getattr(exc, 'status_code', 500)
    error_code = getattr(exc, 'error_code', 'unknown_error')
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_code,
            "message": exc.message,
            "details": exc.details,
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "correlation_id": correlation_id,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={"correlation_id": correlation_id},
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id
        }
    )


# Include existing and new routers
app.include_router(llm_service.router)
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(
    chat_router, 
    prefix="/api/v1/chat", 
    tags=["chat"],
    dependencies=[Depends(get_api_key_auth)] if not settings.debug else []
)
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "ChatBet Assistant API",
        "version": "1.0.0",
        "description": "Intelligent conversational assistant for sports betting insights",
        "docs_url": "/docs" if settings.debug else None,
        "health_url": "/health",
        "legacy_message": "Hello World"  # Keep compatibility with existing endpoint
    }
