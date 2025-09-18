"""
Custom exceptions for the ChatBet application.

Having well-defined exceptions makes error handling much cleaner
and helps with debugging. I'm organizing them by domain so it's
easy to catch specific types of errors where appropriate.
"""

from typing import Optional, Dict, Any


# === Base Exceptions ===

class ChatBetException(Exception):
    """
    Base exception class for all ChatBet-related errors.
    
    This provides a consistent interface for handling errors throughout
    the application with structured error information.
    """
    
    def __init__(
        self, 
        message: str,
        error_code: str = "unknown_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ChatBetException):
    """Data validation errors."""
    pass


class ConfigurationError(ChatBetException):
    """Configuration-related errors."""
    pass


# === API and External Service Exceptions ===

class APIError(ChatBetException):
    """Base exception for external API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.status_code = status_code


class AuthenticationError(APIError):
    """Authentication failed with external service."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""
    pass


class ServiceUnavailableError(APIError):
    """External service is unavailable."""
    pass


class CircuitBreakerError(APIError):
    """Circuit breaker is open."""
    pass


# === Conversation and LLM Exceptions ===

class ConversationError(ChatBetException):
    """Base exception for conversation-related errors."""
    pass


class LLMError(ConversationError):
    """LLM service errors."""
    pass


class TokenLimitError(LLMError):
    """Token limit exceeded."""
    pass


class IntentClassificationError(ConversationError):
    """Intent classification failed."""
    pass


class MemoryFullError(ConversationError):
    """Conversation memory is full."""
    pass


# === Betting and Domain Exceptions ===

class BettingError(ChatBetException):
    """Base exception for betting-related errors."""
    pass


class InsufficientBalanceError(BettingError):
    """User has insufficient balance for the bet."""
    pass


class InvalidBetError(BettingError):
    """Bet parameters are invalid."""
    pass


class MarketClosedError(BettingError):
    """Betting market is closed."""
    pass


class OddsChangedError(BettingError):
    """Odds have changed since bet was initiated."""
    pass


# === Cache and Performance Exceptions ===

class CacheError(ChatBetException):
    """Cache-related errors."""
    pass


class CacheUnavailableError(CacheError):
    """Cache service is unavailable."""
    pass


class PerformanceError(ChatBetException):
    """Performance-related errors (timeouts, etc.)."""
    pass


# === Security Exceptions ===

class SecurityError(ChatBetException):
    """Security-related errors."""
    pass


class UnauthorizedError(SecurityError):
    """User is not authorized for this action."""
    pass


class ForbiddenError(SecurityError):
    """Action is forbidden."""
    pass


# === Utility Functions ===

def get_error_details(exception: Exception) -> Dict[str, Any]:
    """
    Extract error details from an exception for logging/debugging.
    
    This is really handy for structured logging and error reporting.
    """
    details = {
        "error_type": type(exception).__name__,
        "error_message": str(exception),
    }
    
    # Add custom details if it's our custom exception
    if isinstance(exception, ChatBetException):
        details.update(exception.details)
        if hasattr(exception, 'status_code') and exception.status_code:
            details["status_code"] = exception.status_code
    
    # Add traceback in development
    import traceback
    details["traceback"] = traceback.format_exc()
    
    return details


def is_retryable_error(exception: Exception) -> bool:
    """
    Check if an error is retryable.
    
    This helps determine whether we should retry a failed operation
    or fail fast for certain types of errors.
    """
    # Don't retry validation or authentication errors
    if isinstance(exception, (ValidationError, AuthenticationError, UnauthorizedError)):
        return False
    
    # Don't retry business logic errors
    if isinstance(exception, (InvalidBetError, InsufficientBalanceError)):
        return False
    
    # Retry network and service errors
    if isinstance(exception, (ServiceUnavailableError, RateLimitError, PerformanceError)):
        return True
    
    # Default to not retrying unknown errors
    return False


# === Exception Aliases for API Routes ===
# These aliases provide consistent naming for API error handling
APIException = APIError
LLMException = LLMError 
ConversationException = ConversationError
BettingException = BettingError
CacheException = CacheError
ValidationException = ValidationError
AuthenticationException = AuthenticationError