"""
Logging configuration for the ChatBet application.

This module sets up structured logging with correlation IDs, performance
monitoring, and different output formats for development vs production.

I'm using Python's built-in logging with some enhancements for better
observability in production environments.
"""

import logging
import logging.config
import sys
import json
from typing import Any, Dict
from datetime import datetime
from contextvars import ContextVar
from functools import wraps

from .config import settings

# Context variable for correlation ID tracking
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record):
        record.correlation_id = correlation_id_var.get('')
        return True


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    This is super useful in production because it makes logs machine-readable
    for log aggregation systems like ELK stack, Datadog, etc.
    """
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add correlation ID if available
        correlation_id = getattr(record, 'correlation_id', '')
        if correlation_id:
            log_entry['correlation_id'] = correlation_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'exc_info', 'exc_text',
                          'stack_info', 'getMessage', 'correlation_id']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


def setup_logging():
    """
    Configure logging for the application.
    
    This sets up different logging configurations based on the environment:
    - Development: Human-readable format with colors
    - Production: JSON format for structured logging
    """
    
    # Base logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': settings.log_format,
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'json': {
                '()': JSONFormatter,
            },
        },
        'filters': {
            'correlation': {
                '()': CorrelationFilter,
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': settings.log_level,
                'formatter': 'json' if settings.enable_json_logs else 'default',
                'filters': ['correlation'],
                'stream': sys.stdout,
            },
        },
        'root': {
            'level': settings.log_level,
            'handlers': ['console'],
        },
        'loggers': {
            # FastAPI and Uvicorn loggers
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
            'uvicorn.error': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
            # HTTP client loggers (reduce noise)
            'httpx': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False,
            },
            'httpcore': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False,
            },
            # Our application loggers
            'app': {
                'level': settings.log_level,
                'handlers': ['console'],
                'propagate': False,
            },
        },
    }
    
    # Apply the configuration
    logging.config.dictConfig(config)
    
    # Set up root logger
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {settings.environment} environment")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(f"app.{name}")


def log_function_call(logger: logging.Logger | None = None):
    """
    Decorator to log function calls with performance timing.
    
    This is really handy for debugging and monitoring performance
    of critical functions, especially API calls and LLM interactions.
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_logger = logger or get_logger(func.__module__)
            start_time = datetime.now()
            
            func_logger.debug(
                f"Starting function call: {func.__name__}",
                extra={'function': func.__name__, 'args_count': len(args), 'kwargs_count': len(kwargs)}
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                func_logger.debug(
                    f"Function call completed: {func.__name__} ({duration:.3f}s)",
                    extra={'function': func.__name__, 'duration': duration, 'success': True}
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                func_logger.error(
                    f"Function call failed: {func.__name__} ({duration:.3f}s) - {str(e)}",
                    extra={'function': func.__name__, 'duration': duration, 'success': False, 'error': str(e)},
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_logger = logger or get_logger(func.__module__)
            start_time = datetime.now()
            
            func_logger.debug(
                f"Starting function call: {func.__name__}",
                extra={'function': func.__name__, 'args_count': len(args), 'kwargs_count': len(kwargs)}
            )
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                func_logger.debug(
                    f"Function call completed: {func.__name__} ({duration:.3f}s)",
                    extra={'function': func.__name__, 'duration': duration, 'success': True}
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                func_logger.error(
                    f"Function call failed: {func.__name__} ({duration:.3f}s) - {str(e)}",
                    extra={'function': func.__name__, 'duration': duration, 'success': False, 'error': str(e)},
                    exc_info=True
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def set_correlation_id(correlation_id: str):
    """Set correlation ID for the current context."""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str:
    """Get correlation ID from the current context."""
    return correlation_id_var.get('')