"""
Betting-specific models for simulation and analysis.

These models handle bet calculations, recommendations, and simulation
logic for the ChatBet system. They work alongside the API models
but focus on the business logic side of betting.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, validator, ConfigDict

from .api_models import BetType, Outcome, Market, MatchFixture


class BetStatus(str, Enum):
    """Status of a bet in our simulation system."""
    PENDING = "pending"      # Bet placed, waiting for match result
    WON = "won"             # Bet won
    LOST = "lost"           # Bet lost
    VOID = "void"           # Bet voided (match cancelled, etc.)
    CASHED_OUT = "cashed_out"  # Bet cashed out early


class RiskLevel(str, Enum):
    """Risk levels for betting recommendations."""
    VERY_LOW = "very_low"    # Almost guaranteed wins, very low odds
    LOW = "low"              # Safe bets with decent odds
    MEDIUM = "medium"        # Balanced risk/reward
    HIGH = "high"            # Risky bets with high potential payout
    VERY_HIGH = "very_high"  # Long shots, lottery-style bets


class BaseBettingModel(BaseModel):
    """Base model for betting-related models."""
    model_config = ConfigDict(
        extra='ignore',
        use_enum_values=True,
        validate_default=True,
        # Use Decimal for monetary values
        json_encoders={
            Decimal: lambda v: float(v)
        }
    )


class BetCalculation(BaseBettingModel):
    """
    Calculation results for a potential bet.
    
    This helps users understand the potential returns and risks
    before placing a bet.
    """
    stake: Decimal = Field(..., description="Bet stake amount")
    odds: Decimal = Field(..., description="Odds for the bet")
    potential_payout: Decimal = Field(..., description="Total potential payout (stake + profit)")
    potential_profit: Decimal = Field(..., description="Potential profit")
    implied_probability: Decimal = Field(..., description="Implied probability from odds")
    
    @validator('stake', 'odds')
    def validate_positive(cls, v):
        """Ensure stake and odds are positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v
    
    @classmethod
    def calculate(cls, stake: Decimal, odds: Decimal) -> 'BetCalculation':
        """Calculate bet returns from stake and odds."""
        potential_payout = stake * odds
        potential_profit = potential_payout - stake
        implied_probability = 1 / odds
        
        return cls(
            stake=stake,
            odds=odds,
            potential_payout=potential_payout,
            potential_profit=potential_profit,
            implied_probability=implied_probability
        )
    
    @property
    def return_on_investment(self) -> Decimal:
        """Calculate ROI percentage."""
        return (self.potential_profit / self.stake) * 100


class BetRecommendation(BaseBettingModel):
    """
    A betting recommendation with analysis.
    
    This provides users with suggestions based on odds analysis,
    risk assessment, and betting strategy.
    """
    match_id: str = Field(..., description="Match identifier")
    match_info: Optional[MatchFixture] = Field(None, description="Match details")
    
    # Recommendation details
    market_id: str = Field(..., description="Recommended market")
    outcome_id: str = Field(..., description="Recommended outcome")
    outcome_name: str = Field(..., description="Human-readable outcome name")
    
    # Betting details
    recommended_odds: Decimal = Field(..., description="Recommended odds")
    suggested_stake: Optional[Decimal] = Field(None, description="Suggested stake amount")
    max_stake: Optional[Decimal] = Field(None, description="Maximum recommended stake")
    
    # Analysis
    risk_level: RiskLevel = Field(..., description="Risk assessment")
    confidence_score: Decimal = Field(..., ge=0, le=1, description="Confidence in recommendation")
    reasoning: str = Field(..., description="Explanation for the recommendation")
    
    # Value assessment
    value_rating: Decimal = Field(..., ge=0, le=10, description="Value rating (0-10)")
    implied_probability: Decimal = Field(..., description="Implied probability from odds")
    estimated_probability: Optional[Decimal] = Field(None, description="Our estimated probability")
    
    # Additional context
    key_factors: List[str] = Field(default_factory=list, description="Key factors influencing recommendation")
    warnings: List[str] = Field(default_factory=list, description="Important warnings or considerations")
    
    @property
    def has_value(self) -> bool:
        """Check if bet offers good value."""
        if self.estimated_probability is None:
            return self.value_rating >= 6
        return self.estimated_probability > self.implied_probability
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if recommendation has high confidence."""
        return self.confidence_score >= 0.7


class BetPortfolio(BaseBettingModel):
    """
    Analysis of a user's betting portfolio/recommendations.
    
    This helps users understand their overall betting strategy
    and risk distribution.
    """
    user_id: str = Field(..., description="User identifier")
    total_stake: Decimal = Field(default=Decimal('0'), description="Total stake across all bets")
    potential_payout: Decimal = Field(default=Decimal('0'), description="Total potential payout")
    potential_profit: Decimal = Field(default=Decimal('0'), description="Total potential profit")
    
    # Risk analysis
    risk_distribution: Dict[RiskLevel, int] = Field(
        default_factory=dict, 
        description="Number of bets by risk level"
    )
    average_odds: Optional[Decimal] = Field(None, description="Average odds across all bets")
    
    # Recommendations
    recommendations: List[BetRecommendation] = Field(
        default_factory=list, 
        description="Current bet recommendations"
    )
    
    @property
    def expected_return(self) -> Decimal:
        """Calculate expected return across all recommendations."""
        if not self.recommendations:
            return Decimal('0')
        
        total_expected = Decimal('0')
        for rec in self.recommendations:
            if rec.estimated_probability and rec.suggested_stake:
                expected_value = (
                    rec.estimated_probability * (rec.recommended_odds * rec.suggested_stake) +
                    (1 - rec.estimated_probability) * (-rec.suggested_stake)
                )
                total_expected += expected_value
        
        return total_expected
    
    @property
    def risk_score(self) -> Decimal:
        """Calculate overall risk score (0-10)."""
        if not self.recommendations:
            return Decimal('5')  # Neutral
        
        risk_weights = {
            RiskLevel.VERY_LOW: 1,
            RiskLevel.LOW: 3,
            RiskLevel.MEDIUM: 5,
            RiskLevel.HIGH: 7,
            RiskLevel.VERY_HIGH: 9
        }
        
        total_weight = sum(
            risk_weights[rec.risk_level] * (rec.suggested_stake or Decimal('1'))
            for rec in self.recommendations
        )
        total_stake = sum(rec.suggested_stake or Decimal('1') for rec in self.recommendations)
        
        return total_weight / total_stake if total_stake > 0 else Decimal('5')


class SimulatedBet(BaseBettingModel):
    """
    A simulated bet for tracking and analysis.
    
    Since we're not placing real bets, we simulate them to provide
    users with realistic betting experience and track performance.
    """
    id: str = Field(..., description="Unique bet identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Bet details
    match_id: str = Field(..., description="Match identifier")
    market_id: str = Field(..., description="Market identifier")
    outcome_id: str = Field(..., description="Outcome identifier")
    outcome_name: str = Field(..., description="Human-readable outcome name")
    
    # Financial details
    stake: Decimal = Field(..., description="Bet stake")
    odds: Decimal = Field(..., description="Odds at time of placement")
    potential_payout: Decimal = Field(..., description="Potential total payout")
    
    # Status and timing
    status: BetStatus = Field(default=BetStatus.PENDING, description="Current bet status")
    placed_at: datetime = Field(default_factory=datetime.now, description="Bet placement time")
    settled_at: Optional[datetime] = Field(None, description="Bet settlement time")
    
    # Results (when settled)
    actual_payout: Optional[Decimal] = Field(None, description="Actual payout received")
    profit_loss: Optional[Decimal] = Field(None, description="Profit or loss amount")
    
    # Metadata
    recommendation_id: Optional[str] = Field(None, description="ID of recommendation this bet was based on")
    notes: Optional[str] = Field(None, description="User notes about the bet")
    
    def settle_bet(self, won: bool) -> None:
        """Settle the bet as won or lost."""
        self.settled_at = datetime.now()
        
        if won:
            self.status = BetStatus.WON
            self.actual_payout = self.potential_payout
            self.profit_loss = self.potential_payout - self.stake
        else:
            self.status = BetStatus.LOST
            self.actual_payout = Decimal('0')
            self.profit_loss = -self.stake
    
    @property
    def is_settled(self) -> bool:
        """Check if bet is settled."""
        return self.status in [BetStatus.WON, BetStatus.LOST, BetStatus.VOID]
    
    @property
    def return_on_investment(self) -> Optional[Decimal]:
        """Calculate ROI if bet is settled."""
        if not self.is_settled or self.profit_loss is None:
            return None
        return (self.profit_loss / self.stake) * 100


class BettingStrategy(BaseBettingModel):
    """
    User's betting strategy and preferences.
    
    This helps personalize recommendations and manage risk according
    to the user's preferences and betting style.
    """
    user_id: str = Field(..., description="User identifier")
    
    # Risk preferences
    max_risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Maximum acceptable risk level")
    risk_tolerance: Decimal = Field(default=Decimal('0.1'), ge=0, le=1, description="Risk tolerance (0-1)")
    
    # Stake management
    default_stake_percentage: Decimal = Field(
        default=Decimal('0.02'), 
        ge=0, 
        le=1, 
        description="Default stake as percentage of balance"
    )
    max_stake_percentage: Decimal = Field(
        default=Decimal('0.05'), 
        ge=0, 
        le=1, 
        description="Maximum stake as percentage of balance"
    )
    
    # Betting preferences
    preferred_bet_types: List[BetType] = Field(
        default_factory=list, 
        description="Preferred types of bets"
    )
    min_odds: Decimal = Field(default=Decimal('1.1'), description="Minimum acceptable odds")
    max_odds: Decimal = Field(default=Decimal('10.0'), description="Maximum acceptable odds")
    
    # Strategy parameters
    value_threshold: Decimal = Field(
        default=Decimal('0.05'), 
        description="Minimum value edge required for bet"
    )
    confidence_threshold: Decimal = Field(
        default=Decimal('0.6'), 
        description="Minimum confidence required for recommendation"
    )
    
    # Bankroll management
    stop_loss_percentage: Optional[Decimal] = Field(
        None, 
        description="Stop loss as percentage of starting bankroll"
    )
    take_profit_percentage: Optional[Decimal] = Field(
        None, 
        description="Take profit as percentage of starting bankroll"
    )
    
    def calculate_stake(self, balance: Decimal, confidence: Decimal, odds: Decimal) -> Decimal:
        """
        Calculate appropriate stake based on strategy.
        
        This uses a simplified Kelly Criterion approach adjusted for
        user's risk tolerance and confidence level.
        """
        # Base stake as percentage of balance
        base_stake = balance * self.default_stake_percentage
        
        # Adjust for confidence (higher confidence = higher stake)
        confidence_multiplier = min(confidence / 0.5, 2.0)  # Cap at 2x
        
        # Adjust for odds (avoid over-betting on low odds)
        odds_adjustment = min(float(odds) / 2.0, 1.5)  # Slight preference for higher odds
        
        # Calculate final stake
        adjusted_stake = base_stake * confidence_multiplier * odds_adjustment
        
        # Apply maximum stake limit
        max_stake = balance * self.max_stake_percentage
        final_stake = min(adjusted_stake, max_stake)
        
        return final_stake


class BettingAnalytics(BaseBettingModel):
    """
    Analytics and performance metrics for betting history.
    
    This provides insights into betting performance and helps
    improve future recommendations.
    """
    user_id: str = Field(..., description="User identifier")
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    
    # Basic metrics
    total_bets: int = Field(default=0, description="Total number of bets")
    won_bets: int = Field(default=0, description="Number of winning bets")
    lost_bets: int = Field(default=0, description="Number of losing bets")
    pending_bets: int = Field(default=0, description="Number of pending bets")
    
    # Financial metrics
    total_staked: Decimal = Field(default=Decimal('0'), description="Total amount staked")
    total_payout: Decimal = Field(default=Decimal('0'), description="Total payouts received")
    net_profit: Decimal = Field(default=Decimal('0'), description="Net profit/loss")
    
    # Performance metrics
    win_rate: Decimal = Field(default=Decimal('0'), description="Win rate percentage")
    average_odds: Decimal = Field(default=Decimal('0'), description="Average odds of all bets")
    roi: Decimal = Field(default=Decimal('0'), description="Return on investment percentage")
    
    # Risk metrics
    largest_win: Decimal = Field(default=Decimal('0'), description="Largest single win")
    largest_loss: Decimal = Field(default=Decimal('0'), description="Largest single loss")
    max_drawdown: Decimal = Field(default=Decimal('0'), description="Maximum drawdown percentage")
    
    # Breakdown by bet type
    performance_by_type: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Performance breakdown by bet type"
    )
    
    # Breakdown by risk level
    performance_by_risk: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Performance breakdown by risk level"
    )
    
    @property
    def is_profitable(self) -> bool:
        """Check if betting has been profitable."""
        return self.net_profit > 0
    
    @property
    def average_stake(self) -> Decimal:
        """Calculate average stake per bet."""
        return self.total_staked / self.total_bets if self.total_bets > 0 else Decimal('0')
    
    @property
    def profit_factor(self) -> Decimal:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_loss = abs(min(self.net_profit, Decimal('0')))
        if gross_loss == 0:
            return Decimal('999999')  # Effectively infinite if no losses
        
        gross_profit = max(self.net_profit, Decimal('0'))
        return gross_profit / gross_loss if gross_loss > 0 else Decimal('0')