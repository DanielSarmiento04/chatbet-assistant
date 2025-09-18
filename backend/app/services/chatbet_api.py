"""
ChatBet API client with connection pooling, retry logic, and caching.

This is our main interface to the external ChatBet sports betting API.
I'm building this with production-grade features like circuit breakers,
automatic retries, and comprehensive error handling.

The caching strategy here is crucial - we cache different types of data
for different durations based on how frequently they change. Tournament
data is pretty stable (24h cache), but live odds change constantly (30s cache).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from contextlib import asynccontextmanager

import httpx
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    RetryError
)

from ..core.config import settings
from ..core.logging import get_logger, log_function_call
from ..models.api_models import (
    TokenRequest, TokenResponse, UserInfo, UserBalance,
    Tournament, MatchFixture, MatchOdds, BetRequest, BetResponse,
    TournamentsResponse, FixturesResponse, OddsResponse
)

logger = get_logger(__name__)


class APIError(Exception):
    """Base exception for API-related errors."""
    pass


class AuthenticationError(APIError):
    """Authentication-related errors."""
    pass


class RateLimitError(APIError):
    """Rate limiting errors."""
    pass


class ServiceUnavailableError(APIError):
    """Service unavailable errors."""
    pass


class CircuitBreakerError(APIError):
    """Circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Simple circuit breaker implementation.
    
    This prevents cascading failures by temporarily stopping requests
    to a failing service. Much better than hammering a service that's already down!
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def can_execute(self) -> bool:
        """Check if requests can be executed."""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if self.last_failure_time and (
                datetime.now() - self.last_failure_time
            ).seconds > self.timeout:
                self.state = "half-open"
                return True
            return False
        
        # half-open state - allow one request to test
        return True
    
    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class ChatBetAPIClient:
    """
    Comprehensive API client for ChatBet service.
    
    This client handles all communication with the external ChatBet API,
    including authentication, data retrieval, and bet placement simulation.
    
    Key features:
    - Automatic token management and refresh
    - Circuit breaker for resilience
    - Comprehensive caching with different TTLs
    - Retry logic with exponential backoff
    - Connection pooling for performance
    """
    
    def __init__(self):
        self.base_url = settings.chatbet_api_base_url
        self.timeout = settings.chatbet_api_timeout
        
        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30
            )
        )
        
        # Circuit breaker for resilience
        self.circuit_breaker = CircuitBreaker()
        
        # Simple in-memory cache (in production, use Redis)
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Authentication state
        self._auth_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Clean up HTTP client."""
        await self.client.aclose()
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any] = None) -> str:
        """Generate cache key for endpoint and parameters."""
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            return f"{endpoint}?{param_str}"
        return endpoint
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if datetime.now() < cache_entry["expires"]:
                logger.debug(f"Cache hit for {cache_key}")
                return cache_entry["data"]
            else:
                # Remove expired entry
                del self._cache[cache_key]
                logger.debug(f"Cache expired for {cache_key}")
        return None
    
    def _set_cache(self, cache_key: str, data: Any, ttl_seconds: int):
        """Store data in cache with TTL."""
        self._cache[cache_key] = {
            "data": data,
            "expires": datetime.now() + timedelta(seconds=ttl_seconds)
        }
        logger.debug(f"Cached data for {cache_key} (TTL: {ttl_seconds}s)")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic and circuit breaker.
        
        This is the core method that handles all HTTP communication
        with the ChatBet API. It includes retry logic, circuit breaking,
        and comprehensive error handling.
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            raise CircuitBreakerError("Circuit breaker is open")
        
        try:
            # Add common headers
            headers = kwargs.get("headers", {})
            if self._auth_token:
                headers["Authorization"] = f"Bearer {self._auth_token}"
            kwargs["headers"] = headers
            
            # Make the request
            response = await self.client.request(method, endpoint, **kwargs)
            
            # Handle different status codes
            if response.status_code == 401:
                logger.warning("Authentication failed - token may be expired")
                raise AuthenticationError("Authentication failed")
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded")
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 500:
                logger.error(f"Server error: {response.status_code}")
                raise ServiceUnavailableError(f"Server error: {response.status_code}")
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            # Record success for circuit breaker
            self.circuit_breaker.record_success()
            
            return response
            
        except Exception as e:
            # Record failure for circuit breaker
            self.circuit_breaker.record_failure()
            
            logger.error(f"Request failed: {method} {endpoint} - {str(e)}")
            raise
    
    @log_function_call()
    async def generate_token(self, username: str, password: str) -> TokenResponse:
        """
        Generate authentication token.
        
        This authenticates with the ChatBet API and returns a token
        that can be used for subsequent requests.
        """
        request_data = TokenRequest(username=username, password=password)
        
        try:
            response = await self._make_request(
                "POST",
                "/auth/generate_token",
                json=request_data.model_dump()
            )
            
            token_data = response.json()
            token_response = TokenResponse(**token_data)
            
            # Store token for future requests
            self._auth_token = token_response.access_token
            self._token_expires_at = datetime.now() + timedelta(
                seconds=token_response.expires_in
            )
            
            logger.info("Authentication token generated successfully")
            return token_response
            
        except Exception as e:
            logger.error(f"Failed to generate token: {str(e)}")
            raise
    
    @log_function_call()
    async def validate_token(self, token: Optional[str] = None) -> Optional[UserInfo]:
        """
        Validate authentication token.
        
        This checks if a token is still valid and returns user information.
        Uses the stored token if no token is provided.
        """
        check_token = token or self._auth_token
        if not check_token:
            logger.warning("No token available for validation")
            return None
        
        try:
            response = await self._make_request(
                "GET",
                "/auth/validate_token",
                headers={"Authorization": f"Bearer {check_token}"}
            )
            
            user_data = response.json()
            user_info = UserInfo(**user_data)
            
            logger.debug(f"Token validated for user: {user_info.username}")
            return user_info
            
        except AuthenticationError:
            logger.warning("Token validation failed - token is invalid")
            # Clear stored token if it's invalid
            if not token:  # Only clear if we were checking our stored token
                self._auth_token = None
                self._token_expires_at = None
            return None
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return None
    
    @log_function_call()
    async def get_user_balance(self, token: Optional[str] = None) -> Optional[UserBalance]:
        """Get user's account balance."""
        check_token = token or self._auth_token
        if not check_token:
            logger.warning("No token available for balance check")
            return None
        
        try:
            response = await self._make_request(
                "GET",
                "/auth/get_user_balance",
                headers={"Authorization": f"Bearer {check_token}"}
            )
            
            balance_data = response.json()
            return UserBalance(**balance_data)
            
        except Exception as e:
            logger.error(f"Failed to get user balance: {str(e)}")
            return None
    
    @log_function_call()
    async def get_tournaments(self, force_refresh: bool = False) -> List[Tournament]:
        """
        Get available tournaments.
        
        Tournaments don't change very often, so we cache them for 24 hours
        to reduce API calls and improve performance.
        """
        cache_key = self._get_cache_key("/sports/tournaments")
        
        # Check cache first (unless forcing refresh)
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return [Tournament(**item) for item in cached_data]
        
        try:
            response = await self._make_request("GET", "/sports/tournaments")
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict) and "data" in data:
                tournaments_data = data["data"]
            elif isinstance(data, list):
                tournaments_data = data
            else:
                tournaments_data = []
            
            # Cache for 24 hours
            self._set_cache(cache_key, tournaments_data, settings.cache_ttl_tournaments)
            
            tournaments = [Tournament(**item) for item in tournaments_data]
            logger.info(f"Retrieved {len(tournaments)} tournaments")
            return tournaments
            
        except Exception as e:
            logger.error(f"Failed to get tournaments: {str(e)}")
            return []
    
    @log_function_call()
    async def get_fixtures(
        self, 
        tournament_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        force_refresh: bool = False
    ) -> List[MatchFixture]:
        """
        Get match fixtures.
        
        Fixtures change throughout the day but not as frequently as odds,
        so we cache them for 4 hours.
        """
        params = {}
        if tournament_id:
            params["tournament_id"] = tournament_id
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        
        cache_key = self._get_cache_key("/sports/fixtures", params)
        
        # Check cache first
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return [MatchFixture(**item) for item in cached_data]
        
        try:
            response = await self._make_request("GET", "/sports/fixtures", params=params)
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict) and "data" in data:
                fixtures_data = data["data"]
            elif isinstance(data, list):
                fixtures_data = data
            else:
                fixtures_data = []
            
            # Cache for 4 hours
            self._set_cache(cache_key, fixtures_data, settings.cache_ttl_fixtures)
            
            fixtures = [MatchFixture(**item) for item in fixtures_data]
            logger.info(f"Retrieved {len(fixtures)} fixtures")
            return fixtures
            
        except Exception as e:
            logger.error(f"Failed to get fixtures: {str(e)}")
            return []
    
    @log_function_call()
    async def get_odds(
        self, 
        match_id: Optional[str] = None,
        tournament_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> List[MatchOdds]:
        """
        Get betting odds.
        
        Odds change frequently, especially for live matches, so we only
        cache them for 30 seconds to ensure users get recent data.
        """
        params = {}
        if match_id:
            params["match_id"] = match_id
        if tournament_id:
            params["tournament_id"] = tournament_id
        
        cache_key = self._get_cache_key("/sports/odds", params)
        
        # Check cache first
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return [MatchOdds(**item) for item in cached_data]
        
        try:
            response = await self._make_request("GET", "/sports/odds", params=params)
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict) and "data" in data:
                odds_data = data["data"]
            elif isinstance(data, list):
                odds_data = data
            else:
                odds_data = []
            
            # Cache for 30 seconds (odds change frequently)
            self._set_cache(cache_key, odds_data, settings.cache_ttl_odds)
            
            odds = [MatchOdds(**item) for item in odds_data]
            logger.info(f"Retrieved odds for {len(odds)} matches")
            return odds
            
        except Exception as e:
            logger.error(f"Failed to get odds: {str(e)}")
            return []
    
    @log_function_call()
    async def place_bet(self, bet_request: BetRequest, token: Optional[str] = None) -> Optional[BetResponse]:
        """
        Place a bet (simulation).
        
        This simulates placing a bet with the ChatBet API. In the real system,
        this would actually place a bet, but for this assessment we're just
        simulating the process.
        """
        check_token = token or self._auth_token
        if not check_token:
            logger.warning("No token available for bet placement")
            return None
        
        try:
            response = await self._make_request(
                "POST",
                "/place-bet",
                json=bet_request.model_dump(),
                headers={"Authorization": f"Bearer {check_token}"}
            )
            
            bet_data = response.json()
            bet_response = BetResponse(**bet_data)
            
            logger.info(f"Bet placed successfully: {bet_response.bet_id}")
            return bet_response
            
        except Exception as e:
            logger.error(f"Failed to place bet: {str(e)}")
            return None
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        logger.info("API cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        expired_entries = 0
        
        now = datetime.now()
        for entry in self._cache.values():
            if now >= entry["expires"]:
                expired_entries += 1
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_hit_ratio": "Not implemented"  # Would need request counters
        }


# Global API client instance
_api_client: Optional[ChatBetAPIClient] = None


def get_chatbet_api_client() -> ChatBetAPIClient:
    """Get global ChatBet API client instance."""
    global _api_client
    if _api_client is None:
        _api_client = ChatBetAPIClient()
    return _api_client


async def get_api_client() -> ChatBetAPIClient:
    """
    Get global API client instance.
    
    This ensures we reuse the same HTTP connection pool across requests
    for better performance.
    """
    global _api_client
    if _api_client is None:
        _api_client = ChatBetAPIClient()
    return _api_client


async def cleanup_api_client():
    """Cleanup function to be called on app shutdown."""
    global _api_client
    if _api_client:
        await _api_client.close()
        _api_client = None