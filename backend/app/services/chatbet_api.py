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
    TournamentsResponse, FixturesResponse, OddsResponse,
    UserValidationResponse, TokenValidationResponse,
    Sport, TournamentInfo, SportWithTournaments, 
    FixtureInfo, FixturesResponseV2, LanguageType, FixtureType,
    SportFixture, SportFixturesResponse, BetUser, BetDetails, BetInfo,
    ComboBetInfo, ComboBetCalculationRequest, ComboBetCalculationResponse
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
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
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
    async def generate_token(self) -> TokenResponse:
        """
        Generate authentication token.
        
        This authenticates with the ChatBet API and returns a token
        that can be used for subsequent requests. No credentials required.
        """
        try:
            response = await self._make_request(
                "POST",
                "/auth/generate_token",
                headers={"accept": "application/json"}
            )
            
            token_data = response.json()
            token_response = TokenResponse(**token_data)
            
            # Store token for future requests
            self._auth_token = token_response.token
            # Since the API doesn't provide expiration, set a reasonable default (1 hour)
            self._token_expires_at = datetime.now() + timedelta(hours=1)
            
            logger.info("Authentication token generated successfully")
            return token_response
            
        except Exception as e:
            logger.error(f"Failed to generate token: {str(e)}")
            raise
    
    async def _ensure_authenticated(self) -> str:
        """
        Ensure we have a valid authentication token.
        
        Generates a new token if we don't have one or if it's expired.
        Returns the current valid token.
        """
        now = datetime.now()
        
        # Check if we need a new token
        if (not self._auth_token or 
            not self._token_expires_at or 
            now >= self._token_expires_at - timedelta(minutes=5)):  # Refresh 5 min early
            
            logger.info("Generating new authentication token")
            await self.generate_token()
        
        if not self._auth_token:
            raise AuthenticationError("Failed to obtain authentication token")
        
        return self._auth_token
    
    @log_function_call()
    async def test_authentication(self) -> bool:
        """
        Test if authentication is working by generating a token.
        
        Returns True if successful, False otherwise.
        """
        try:
            await self.generate_token()
            return self._auth_token is not None
        except Exception as e:
            logger.error(f"Authentication test failed: {str(e)}")
            return False
    
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
    async def validate_user(self, user_key: str) -> Optional[UserValidationResponse]:
        """
        Validate user by their user key.
        
        Args:
            user_key: The user key to validate
            
        Returns:
            UserValidationResponse if successful, None otherwise
        """
        try:
            response = await self._make_request(
                "GET",
                f"/auth/validate_user",
                params={"userKey": user_key}
            )
            
            validation_data = response.json()
            validation_response = UserValidationResponse(**validation_data)
            
            logger.debug(f"User validation response: status={validation_response.status}, userId={validation_response.userId}")
            return validation_response
            
        except Exception as e:
            logger.error(f"Error validating user with key {user_key}: {str(e)}")
            return None

    @log_function_call()
    async def validate_token_endpoint(self, token: str) -> Optional[TokenValidationResponse]:
        """
        Validate token using the dedicated token validation endpoint.
        
        Args:
            token: The token to validate
            
        Returns:
            TokenValidationResponse if successful, None otherwise
        """
        try:
            response = await self._make_request(
                "GET",
                f"/auth/validate_token",
                headers={"token": token}
            )
            
            validation_data = response.json()
            validation_response = TokenValidationResponse(**validation_data)
            
            logger.debug(f"Token validation response: {validation_response.message}")
            return validation_response
            
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return None

    @log_function_call()
    async def get_sports(self) -> List[Sport]:
        """
        Get list of available sports.
        
        Returns:
            List of Sport objects, empty list if error
        """
        try:
            response = await self._make_request(
                "GET",
                "/sports"
            )
            
            sports_data = response.json()
            sports = [Sport(**sport) for sport in sports_data]
            
            logger.debug(f"Retrieved {len(sports)} sports")
            return sports
            
        except Exception as e:
            logger.error(f"Error getting sports: {str(e)}")
            return []

    @log_function_call()
    async def get_sport_tournaments(
        self, 
        sport_id: str, 
        language: LanguageType = "en", 
        with_active_fixtures: bool = False
    ) -> List[TournamentInfo]:
        """
        Get tournaments for a specific sport.
        
        Args:
            sport_id: The ID of the sport
            language: Language for tournament names (en, es, pt_br)
            with_active_fixtures: Whether to include only tournaments with active fixtures
            
        Returns:
            List of TournamentInfo objects, empty list if error
        """
        try:
            params = {
                "sport_id": sport_id,
                "language": language,
                "with_active_fixtures": str(with_active_fixtures).lower()
            }
            
            response = await self._make_request(
                "GET",
                "/sports/tournaments",
                params=params
            )
            
            tournaments_data = response.json()
            tournaments = [TournamentInfo(**tournament) for tournament in tournaments_data]
            
            logger.debug(f"Retrieved {len(tournaments)} tournaments for sport {sport_id}")
            return tournaments
            
        except Exception as e:
            logger.error(f"Error getting tournaments for sport {sport_id}: {str(e)}")
            return []

    @log_function_call()
    async def get_all_tournaments(
        self,
        language: LanguageType = "en",
        with_active_fixtures: bool = False
    ) -> List[SportWithTournaments]:
        """
        Get all sports with their tournaments.
        
        Args:
            language: Language for tournament names (en, es, pt_br)
            with_active_fixtures: Whether to include only tournaments with active fixtures
            
        Returns:
            List of SportWithTournaments objects, empty list if error
        """
        try:
            params = {
                "language": language,
                "with_active_fixtures": str(with_active_fixtures).lower()
            }
            
            response = await self._make_request(
                "GET",
                "/sports/all-tournaments",
                params=params
            )
            
            sports_data = response.json()
            sports = [SportWithTournaments(**sport) for sport in sports_data]
            
            logger.debug(f"Retrieved {len(sports)} sports with tournaments")
            return sports
            
        except Exception as e:
            logger.error(f"Error getting all tournaments: {str(e)}")
            return []

    @log_function_call()
    async def get_fixtures(
        self,
        tournament_id: Optional[str] = None,
        fixture_type: FixtureType = "pre_match",
        language: LanguageType = "en",
        time_zone: str = "UTC"
    ) -> FixturesResponseV2:
        """
        Get fixtures for tournaments.
        
        Args:
            tournament_id: The ID of the tournament (optional)
            fixture_type: Type of fixtures (pre_match or live)
            language: Language for tournament names (en, es, pt_br)
            time_zone: Time zone for fixture times
            
        Returns:
            FixturesResponseV2 object with totalResults and fixtures list
        """
        try:
            params = {
                "type": fixture_type,
                "language": language,
                "time_zone": time_zone
            }
            
            if tournament_id:
                params["tournamentId"] = tournament_id
            
            response = await self._make_request(
                "GET",
                "/sports/fixtures",
                params=params
            )
            
            fixtures_data = response.json()
            
            # Handle the response format where first item is totalResults
            if fixtures_data and isinstance(fixtures_data[0], dict) and "totalResults" in fixtures_data[0]:
                total_results = fixtures_data[0]["totalResults"]
                fixtures_list = fixtures_data[1:] if len(fixtures_data) > 1 else []
            else:
                total_results = len(fixtures_data)
                fixtures_list = fixtures_data
            
            # Convert to FixtureInfo objects
            fixtures = [FixtureInfo(**fixture) for fixture in fixtures_list if isinstance(fixture, dict) and "id" in fixture]
            
            fixtures_response = FixturesResponseV2(
                totalResults=total_results,
                fixtures=fixtures
            )
            
            logger.debug(f"Retrieved {len(fixtures)} fixtures for tournament {tournament_id or 'all'}")
            return fixtures_response
            
        except Exception as e:
            logger.error(f"Error getting fixtures: {str(e)}")
            return FixturesResponseV2(totalResults=0, fixtures=[])

    @log_function_call()
    async def get_sport_fixtures(
        self,
        sport_id: str,
        fixture_type: FixtureType = "pre_match",
        language: LanguageType = "en",
        time_zone: str = "UTC"
    ) -> List[SportFixture]:
        """
        Get fixtures for a specific sport with detailed multilingual information.
        
        Args:
            sport_id: The ID of the sport (required)
            fixture_type: Type of fixtures (pre_match or live)
            language: Language for fixture names (en, es, pt_br)
            time_zone: Time zone for fixture times
            
        Returns:
            List of SportFixture objects with detailed multilingual data
        """
        try:
            params = {
                "sportId": sport_id,
                "type": fixture_type,
                "language": language,
                "time_zone": time_zone
            }
            
            response = await self._make_request(
                "GET",
                "/sports/sports-fixtures",
                params=params
            )
            
            fixtures_data = response.json()
            
            # Convert to SportFixture objects
            fixtures = [SportFixture(**fixture) for fixture in fixtures_data if isinstance(fixture, dict) and "id" in fixture]
            
            logger.debug(f"Retrieved {len(fixtures)} sport fixtures for sport {sport_id}")
            return fixtures
            
        except Exception as e:
            logger.error(f"Error getting sport fixtures for sport {sport_id}: {str(e)}")
            return []
    
    @log_function_call()
    async def get_user_balance(
        self, 
        user_id: str, 
        user_key: str, 
        token: str
    ) -> Optional[UserBalance]:
        """
        Get user's account balance using the actual API structure.
        
        Args:
            user_id: The user ID
            user_key: The user key
            token: Authentication token
            
        Returns:
            UserBalance with flag, money, playableBalance, withdrawableBalance, bonusBalance, and redeemedBonus
        """
        try:
            params = {
                "userId": user_id,
                "userKey": user_key
            }
            
            headers = {
                "accept": "application/json",
                "token": token
            }
            
            response = await self._make_request(
                "GET",
                "/auth/get_user_balance",
                params=params,
                headers=headers
            )
            
            balance_data = response.json()
            balance_response = UserBalance(**balance_data)
            
            logger.info(f"Retrieved user balance: money={balance_response.money}, playable={balance_response.playableBalance}")
            return balance_response
            
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
    async def place_bet(
        self, 
        bet_request: BetRequest,
        token: str,
        accept_language: str = "es",
        country_code: str = "BR"
    ) -> Optional[BetResponse]:
        """
        Place a bet with the ChatBet API using the actual API structure.
        
        Args:
            bet_request: Bet request with user and bet information
            token: Authentication token for the user
            accept_language: Language preference (default: "es")
            country_code: Country code (default: "BR")
            
        Returns:
            BetResponse with message, betId, and possibleWin
        """
        try:
            headers = {
                "accept": "application/json",
                "accept-language": accept_language,
                "country-code": country_code,
                "token": token,
                "Content-Type": "application/json"
            }
            
            response = await self._make_request(
                "POST",
                "/place-bet",
                json=bet_request.model_dump(),
                headers=headers
            )
            
            bet_data = response.json()
            bet_response = BetResponse(**bet_data)
            
            logger.info(f"Bet placed successfully: {bet_response.betId}")
            return bet_response
            
        except Exception as e:
            logger.error(f"Failed to place bet: {str(e)}")
            return None

    @log_function_call()
    async def calculate_combo_bet(
        self, 
        calculation_request: ComboBetCalculationRequest
    ) -> Optional[ComboBetCalculationResponse]:
        """
        Calculate combo bet profit and odds.
        
        Args:
            calculation_request: Request with bets info and amount
            
        Returns:
            ComboBetCalculationResponse with profit, odd, and status
        """
        try:
            headers = {
                "accept": "application/json",
                "Content-Type": "application/json"
            }
            
            response = await self._make_request(
                "POST",
                "/combo-bet-calculation",
                json=calculation_request.model_dump(),
                headers=headers
            )
            
            calculation_data = response.json()
            calculation_response = ComboBetCalculationResponse(**calculation_data)
            
            logger.info(f"Combo bet calculation completed: profit={calculation_response.profit}, odd={calculation_response.odd}")
            return calculation_response
            
        except Exception as e:
            logger.error(f"Failed to calculate combo bet: {str(e)}")
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