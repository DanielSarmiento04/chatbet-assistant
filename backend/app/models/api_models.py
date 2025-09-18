"""
API models for external ChatBet service integration.

These models represent the data structures we expect from the ChatBet API.
I'm using Pydantic v2 here for robust validation and automatic serialization.

The cool thing about these models is that they'll automatically validate
incoming data from the API and raise clear errors if something's wrong.
This saves us from having to write tons of manual validation code.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, validator, ConfigDict


class BaseAPIModel(BaseModel):
    """Base model for all API-related models."""
    model_config = ConfigDict(
        # Allow extra fields that might come from the API
        extra='ignore',
        # Use enum values instead of enum objects in serialization
        use_enum_values=True,
        # Validate default values
        validate_default=True,
        # Allow population by field name or alias
        populate_by_name=True
    )


# === Authentication Models ===

class TokenRequest(BaseAPIModel):
    """Request model for token generation."""
    username: str = Field(..., description="User's username")
    password: str = Field(..., description="User's password")


class TokenResponse(BaseAPIModel):
    """Response model for authentication token."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user_id: Optional[str] = Field(None, description="User identifier")


class UserInfo(BaseAPIModel):
    """User information from token validation."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="User's username")
    email: Optional[str] = Field(None, description="User's email address")
    is_active: bool = Field(default=True, description="Whether user account is active")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")


class UserBalance(BaseAPIModel):
    """User's account balance information."""
    user_id: str = Field(..., description="User identifier")
    balance: Decimal = Field(..., description="Current account balance")
    currency: str = Field(default="USD", description="Currency code")
    last_updated: datetime = Field(..., description="Balance last update timestamp")


# === Sports Data Models ===

class Team(BaseAPIModel):
    """Team information."""
    id: str = Field(..., description="Unique team identifier")
    name: str = Field(..., description="Team name")
    short_name: Optional[str] = Field(None, description="Team short name or abbreviation")
    logo_url: Optional[str] = Field(None, description="Team logo URL")
    country: Optional[str] = Field(None, description="Team's country")


class Tournament(BaseAPIModel):
    """Tournament/competition information."""
    id: str = Field(..., description="Unique tournament identifier")
    name: str = Field(..., description="Tournament name")
    country: Optional[str] = Field(None, description="Tournament country")
    category: Optional[str] = Field(None, description="Tournament category (e.g., domestic, international)")
    season: Optional[str] = Field(None, description="Current season")
    start_date: Optional[datetime] = Field(None, description="Tournament start date")
    end_date: Optional[datetime] = Field(None, description="Tournament end date")


class MatchStatus(BaseAPIModel):
    """Match status information."""
    code: str = Field(..., description="Status code (e.g., 'scheduled', 'live', 'finished')")
    description: str = Field(..., description="Human-readable status description")
    short: Optional[str] = Field(None, description="Short status description")


class MatchFixture(BaseAPIModel):
    """Match fixture information."""
    id: str = Field(..., description="Unique match identifier")
    tournament: Tournament = Field(..., description="Tournament information")
    home_team: Team = Field(..., description="Home team")
    away_team: Team = Field(..., description="Away team")
    scheduled_time: datetime = Field(..., description="Match scheduled start time")
    status: MatchStatus = Field(..., description="Current match status")
    venue: Optional[str] = Field(None, description="Match venue")
    round: Optional[str] = Field(None, description="Tournament round")
    week: Optional[int] = Field(None, description="Week number")
    
    # Match result (if finished)
    home_score: Optional[int] = Field(None, description="Home team final score")
    away_score: Optional[int] = Field(None, description="Away team final score")
    
    @property
    def is_finished(self) -> bool:
        """Check if match is finished."""
        return self.status.code.lower() in ['finished', 'completed', 'ended']
    
    @property
    def is_live(self) -> bool:
        """Check if match is currently live."""
        return self.status.code.lower() in ['live', 'in_progress', 'playing']
    
    @property
    def is_scheduled(self) -> bool:
        """Check if match is scheduled for the future."""
        return self.status.code.lower() in ['scheduled', 'upcoming', 'not_started']


# === Betting Models ===

class OddsFormat(str, Enum):
    """Supported odds formats."""
    DECIMAL = "decimal"
    FRACTIONAL = "fractional"
    AMERICAN = "american"


class BetType(str, Enum):
    """Supported bet types."""
    MATCH_WINNER = "match_winner"  # 1X2
    OVER_UNDER = "over_under"
    BOTH_TEAMS_SCORE = "both_teams_score"
    HANDICAP = "handicap"
    CORRECT_SCORE = "correct_score"


class Outcome(BaseAPIModel):
    """Individual betting outcome."""
    id: str = Field(..., description="Unique outcome identifier")
    name: str = Field(..., description="Outcome name (e.g., 'Home', 'Draw', 'Away')")
    odds: Decimal = Field(..., description="Odds value")
    odds_format: str = Field(default=OddsFormat.DECIMAL, description="Odds format")
    is_available: bool = Field(default=True, description="Whether outcome is available for betting")
    
    @validator('odds')
    def validate_odds(cls, v):
        """Ensure odds are positive."""
        if v <= 0:
            raise ValueError("Odds must be positive")
        return v


class Market(BaseAPIModel):
    """Betting market information."""
    id: str = Field(..., description="Unique market identifier")
    name: str = Field(..., description="Market name")
    bet_type: str = Field(..., description="Type of bet")
    outcomes: List[Outcome] = Field(..., description="Available outcomes")
    is_active: bool = Field(default=True, description="Whether market is active")
    
    # Optional market-specific parameters
    handicap_value: Optional[Decimal] = Field(None, description="Handicap value for handicap bets")
    total_value: Optional[Decimal] = Field(None, description="Total value for over/under bets")


class MatchOdds(BaseAPIModel):
    """Complete odds information for a match."""
    match_id: str = Field(..., description="Match identifier")
    match: Optional[MatchFixture] = Field(None, description="Match fixture details")
    markets: List[Market] = Field(..., description="Available betting markets")
    last_updated: datetime = Field(..., description="Odds last update timestamp")
    
    def get_market_by_type(self, bet_type: str) -> Optional[Market]:
        """Get market by bet type."""
        for market in self.markets:
            if market.bet_type == bet_type:
                return market
        return None
    
    def get_main_market(self) -> Optional[Market]:
        """Get the main 1X2 market if available."""
        return self.get_market_by_type(BetType.MATCH_WINNER)


# === Betting Simulation Models ===

class BetRequest(BaseAPIModel):
    """Request to place a bet."""
    match_id: str = Field(..., description="Match identifier")
    market_id: str = Field(..., description="Market identifier")
    outcome_id: str = Field(..., description="Outcome identifier")
    stake: Decimal = Field(..., description="Bet stake amount")
    odds: Decimal = Field(..., description="Odds at time of bet placement")
    
    @validator('stake')
    def validate_stake(cls, v):
        """Ensure stake is positive."""
        if v <= 0:
            raise ValueError("Stake must be positive")
        return v
    
    @validator('odds')
    def validate_odds(cls, v):
        """Ensure odds are positive."""
        if v <= 0:
            raise ValueError("Odds must be positive")
        return v


class BetResponse(BaseAPIModel):
    """Response from placing a bet."""
    bet_id: str = Field(..., description="Unique bet identifier")
    status: str = Field(..., description="Bet status (e.g., 'accepted', 'rejected')")
    message: Optional[str] = Field(None, description="Status message")
    potential_payout: Optional[Decimal] = Field(None, description="Potential payout if bet wins")
    placed_at: datetime = Field(..., description="Bet placement timestamp")


# === API Response Wrappers ===

class APIResponse(BaseAPIModel):
    """Generic API response wrapper."""
    success: bool = Field(default=True, description="Whether request was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")


class PaginatedResponse(BaseAPIModel):
    """Paginated API response."""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=50, description="Items per page")
    has_next: bool = Field(default=False, description="Whether there are more pages")
    has_prev: bool = Field(default=False, description="Whether there are previous pages")


class TournamentsResponse(APIResponse):
    """Response for tournaments endpoint."""
    data: List[Tournament] = Field(..., description="List of tournaments")


class FixturesResponse(APIResponse):
    """Response for fixtures endpoint."""
    data: List[MatchFixture] = Field(..., description="List of match fixtures")


class OddsResponse(APIResponse):
    """Response for odds endpoint."""
    data: List[MatchOdds] = Field(..., description="List of match odds")