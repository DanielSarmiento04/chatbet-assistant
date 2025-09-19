"""
API models for external ChatBet service integration.

These models represent the data structures we expect from the ChatBet API.
I'm using Pydantic v2 here for robust validation and automatic serialization.

The cool thing about these models is that they'll automatically validate
incoming data from the API and raise clear errors if something's wrong.
This saves us from having to write tons of manual validation code.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Literal
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


class TokenResponse(BaseModel):
    """Response model for token generation"""
    token: str
    
    # Backward compatibility with old field name
    @property
    def access_token(self) -> str:
        return self.token


class UserValidationResponse(BaseModel):
    """Response model for user validation"""
    status: bool
    userId: int


class TokenValidationResponse(BaseModel):
    """Response model for token validation"""
    message: str


class Sport(BaseModel):
    """Model for sport information"""
    alias: str
    profit: Dict[str, Any] = Field(default_factory=dict)
    id: str
    name: str
    name_es: str
    name_en: str
    name_pt_br: str


class SportName(BaseModel):
    """Model for sport name translations"""
    en: str
    es: str
    pt_br: str


class TournamentInfo(BaseModel):
    """Model for tournament information"""
    profit: Dict[str, Any] = Field(default_factory=dict)
    sport_name: SportName
    tournament_name: str
    tournament_id: str


# New models for the updated endpoints
class SimpleTournament(BaseModel):
    """Model for simple tournament information"""
    tournamentId: str
    name: str
    order: int


class SportWithTournaments(BaseModel):
    """Model for sport with nested tournaments"""
    id: str
    name: str
    tournaments: List[SimpleTournament]


class Competitor(BaseModel):
    """Model for team/competitor information"""
    name: str
    id: str
    jerseyIcon: str


class TournamentSimple(BaseModel):
    """Model for simple tournament info in fixtures"""
    name: str
    id: str


class FixtureInfo(BaseModel):
    """Model for fixture information"""
    source: int
    id: str
    startTime: str
    tournament: TournamentSimple
    sportId: str
    homeCompetitor: Competitor
    awayCompetitor: Competitor


class FixturesResponseV2(BaseModel):
    """Model for fixtures response with total count"""
    totalResults: int
    fixtures: List[FixtureInfo] = Field(default_factory=list)


# Type literals for validation
LanguageType = Literal["en", "es", "pt_br"]
FixtureType = Literal["pre_match", "live"]


# === New Sport Fixtures Models ===

class MultiLanguageName(BaseModel):
    """Model for multilingual names"""
    en: str
    es: str
    pt_br: str


class TeamData(BaseModel):
    """Model for team data in sport fixtures"""
    name: MultiLanguageName


class SportFixture(BaseModel):
    """Model for sport fixture information with detailed structure"""
    tournament_name: MultiLanguageName
    away_team_data: TeamData
    source: int
    tournament_id: str
    home_team_data: TeamData
    id: str
    startTime: str
    startTimeIndex: str
    homeCompetitorName: MultiLanguageName
    homeCompetitorId: MultiLanguageName
    awayCompetitorName: MultiLanguageName
    awayCompetitorId: MultiLanguageName


class SportFixturesResponse(BaseModel):
    """Model for sport fixtures response"""
    fixtures: List[SportFixture] = Field(default_factory=list)


class UserInfo(BaseAPIModel):
    """User information from token validation."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="User's username")
    email: Optional[str] = Field(None, description="User's email address")
    is_active: bool = Field(default=True, description="Whether user account is active")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")


class UserBalance(BaseModel):
    """User's account balance information from the actual API structure."""
    flag: int
    money: float
    playableBalance: float
    withdrawableBalance: float
    bonusBalance: float
    redeemedBonus: float


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


class MatchOdds(BaseModel):
    """Complete odds information for a match with the actual API structure."""
    status: str
    main_market: str
    result: Optional[Any] = None
    result_regular_time: Optional[Any] = None
    score: Optional[Any] = None
    both_teams_to_score: Optional[Any] = None
    double_chance: Optional[Any] = None
    over_under: Optional[Any] = None
    handicap: Optional[Any] = None
    half_time_total: Optional[Any] = None
    half_time_result: Optional[Any] = None
    half_time_handicap: Optional[Any] = None
    win: Optional[Any] = None
    draw_no_bet: Optional[Any] = None
    goal_first_half: Optional[Any] = None
    goal_second_half: Optional[Any] = None
    goal_both_halves: Optional[Any] = None
    total_corners_home: Optional[Any] = None
    total_corners_away: Optional[Any] = None
    last_goal: Optional[Any] = None
    result_five_entries: Optional[Any] = None
    result_first_period: Optional[Any] = None


# === Betting Simulation Models ===

class BetUser(BaseModel):
    """User information for bet placement"""
    userKey: str
    id: str


class BetDetails(BaseModel):
    """Individual bet details"""
    betId: str
    fixtureId: str
    odd: str
    sportId: str
    tournamentId: str


class BetInfo(BaseModel):
    """Bet information containing amount and bet details"""
    amount: str
    betId: List[BetDetails]
    source: str


class BetRequest(BaseModel):
    """Request to place a bet with the actual API structure"""
    user: BetUser
    betInfo: BetInfo


class BetResponse(BaseModel):
    """Response from placing a bet with the actual API structure"""
    message: str
    betId: str
    possibleWin: float


# === Combo Bet Calculation Models ===

class ComboBetInfo(BaseModel):
    """Individual bet information for combo bet calculation"""
    betId: str
    fixtureId: str
    sportId: str
    tournamentId: str
    odd: float


class ComboBetCalculationRequest(BaseModel):
    """Request for combo bet calculation"""
    betsInfo: List[ComboBetInfo]
    amount: float


class ComboBetCalculationResponse(BaseModel):
    """Response from combo bet calculation"""
    profit: float
    odd: float
    status: str


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