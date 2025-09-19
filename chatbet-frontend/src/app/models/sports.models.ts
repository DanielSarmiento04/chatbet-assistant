/**
 * Sports and betting related models for ChatBet frontend.
 */

export interface Sport {
  id: string;
  name: string;
  icon?: string;
  isActive: boolean;
  popularityRank: number;
}

export interface League {
  id: string;
  name: string;
  sport: string;
  country: string;
  logo?: string;
  season: string;
  isActive: boolean;
  startDate: Date;
  endDate: Date;
}

export interface Team {
  id: string;
  name: string;
  shortName: string;
  logo?: string;
  country: string;
  founded?: number;
  venue?: string;
  website?: string;
  colors: {
    primary: string;
    secondary: string;
  };
}

export interface Match {
  id: string;
  homeTeam: Team;
  awayTeam: Team;
  competition: League;
  date: Date;
  venue: string;
  status: MatchStatus;
  round?: string;
  matchday?: number;

  // Score information
  score?: MatchScore;

  // Match statistics (if available)
  stats?: MatchStats;

  // Betting information
  odds?: MatchOdds[];
}

export enum MatchStatus {
  SCHEDULED = 'scheduled',
  LIVE = 'live',
  HALFTIME = 'halftime',
  FINISHED = 'finished',
  POSTPONED = 'postponed',
  CANCELLED = 'cancelled',
  SUSPENDED = 'suspended'
}

export interface MatchScore {
  home: number;
  away: number;
  halfTime?: {
    home: number;
    away: number;
  };
  extraTime?: {
    home: number;
    away: number;
  };
  penalties?: {
    home: number;
    away: number;
  };
}

export interface MatchStats {
  possession: {
    home: number;
    away: number;
  };
  shots: {
    home: number;
    away: number;
  };
  shotsOnTarget: {
    home: number;
    away: number;
  };
  corners: {
    home: number;
    away: number;
  };
  fouls: {
    home: number;
    away: number;
  };
  yellowCards: {
    home: number;
    away: number;
  };
  redCards: {
    home: number;
    away: number;
  };
}

export interface MatchOdds {
  bookmaker: string;
  bookmakerLogo?: string;
  markets: BettingMarket[];
  lastUpdated: Date;
}

export interface BettingMarket {
  name: string;
  type: MarketType;
  outcomes: BettingOutcome[];
}

export enum MarketType {
  MATCH_RESULT = 'match_result',
  BOTH_TEAMS_TO_SCORE = 'both_teams_to_score',
  OVER_UNDER_GOALS = 'over_under_goals',
  CORRECT_SCORE = 'correct_score',
  FIRST_GOALSCORER = 'first_goalscorer',
  HANDICAP = 'handicap',
  DOUBLE_CHANCE = 'double_chance'
}

export interface BettingOutcome {
  name: string;
  odds: number;
  isActive: boolean;
  line?: number; // For over/under, handicap markets
}

export interface Tournament {
  id: string;
  name: string;
  shortName: string;
  country: string;
  sport: string;
  logo?: string;
  type: TournamentType;
  season: string;
  currentRound?: string;

  // Tournament specific data
  standings?: Standings;
  topScorers?: TopScorer[];
  matches?: Match[];

  // Tournament format
  format: {
    numberOfTeams: number;
    numberOfRounds?: number;
    hasPlayoffs: boolean;
    promotionSpots?: number;
    relegationSpots?: number;
  };
}

export enum TournamentType {
  LEAGUE = 'league',
  CUP = 'cup',
  PLAYOFFS = 'playoffs',
  INTERNATIONAL = 'international'
}

export interface Standings {
  groups?: StandingsGroup[];
  table: StandingsEntry[];
  lastUpdated: Date;
}

export interface StandingsGroup {
  name: string;
  table: StandingsEntry[];
}

export interface StandingsEntry {
  position: number;
  team: Team;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  form: FormResult[];

  // Additional status
  status?: 'promotion' | 'champions_league' | 'europa_league' | 'relegation' | 'none';
}

export enum FormResult {
  WIN = 'W',
  DRAW = 'D',
  LOSS = 'L'
}

export interface TopScorer {
  player: Player;
  team: Team;
  goals: number;
  assists?: number;
  appearances: number;
  minutesPlayed?: number;
  penaltyGoals?: number;
}

export interface Player {
  id: string;
  name: string;
  position: PlayerPosition;
  age: number;
  nationality: string;
  photo?: string;
}

export enum PlayerPosition {
  GOALKEEPER = 'goalkeeper',
  DEFENDER = 'defender',
  MIDFIELDER = 'midfielder',
  FORWARD = 'forward'
}

// Betting specific models
export interface BettingRecommendation {
  id: string;
  title: string;
  description: string;
  match: Match;
  market: BettingMarket;
  recommendedOutcome: BettingOutcome;
  confidence: number;
  reasoning: string[];
  expectedValue: number;
  riskLevel: RiskLevel;

  // Analysis data
  stats?: RecommendationStats;
  trends?: string[];

  // Metadata
  createdAt: Date;
  expiresAt: Date;
}

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
}

export interface RecommendationStats {
  homeFormLast5: FormResult[];
  awayFormLast5: FormResult[];
  headToHeadRecord: {
    homeWins: number;
    draws: number;
    awayWins: number;
    lastMeetings: Match[];
  };
  avgGoalsScored: {
    home: number;
    away: number;
  };
  avgGoalsConceded: {
    home: number;
    away: number;
  };
}

// Odds comparison
export interface OddsComparison {
  match: Match;
  markets: MarketComparison[];
  bestOverallBookmaker?: string;
  lastUpdated: Date;
}

export interface MarketComparison {
  market: BettingMarket;
  bestOdds: {
    outcome: string;
    odds: number;
    bookmaker: string;
  }[];
  averageOdds: Record<string, number>;
  oddsTrend: 'rising' | 'falling' | 'stable';
}

// News and insights
export interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content?: string;
  author: string;
  publishedAt: Date;
  category: NewsCategory;
  tags: string[];
  relatedTeams?: Team[];
  relatedMatches?: Match[];
  imageUrl?: string;
  sourceUrl?: string;
}

export enum NewsCategory {
  MATCH_PREVIEW = 'match_preview',
  MATCH_REPORT = 'match_report',
  TRANSFER_NEWS = 'transfer_news',
  INJURY_UPDATE = 'injury_update',
  BETTING_TIPS = 'betting_tips',
  ANALYSIS = 'analysis'
}

// Live data
export interface LiveMatchUpdate {
  matchId: string;
  type: LiveUpdateType;
  minute: number;
  message: string;
  data?: unknown;
  timestamp: Date;
}

export enum LiveUpdateType {
  GOAL = 'goal',
  YELLOW_CARD = 'yellow_card',
  RED_CARD = 'red_card',
  SUBSTITUTION = 'substitution',
  KICK_OFF = 'kick_off',
  HALF_TIME = 'half_time',
  SECOND_HALF = 'second_half',
  FULL_TIME = 'full_time',
  PENALTY = 'penalty',
  VAR_DECISION = 'var_decision'
}

// Utility types for sports data
export type MatchFilter = {
  sport?: string;
  league?: string;
  team?: string;
  date?: Date;
  status?: MatchStatus;
};

export type TournamentFilter = {
  sport?: string;
  country?: string;
  type?: TournamentType;
  season?: string;
};

export type OddsFilter = {
  market?: MarketType;
  bookmaker?: string;
  minOdds?: number;
  maxOdds?: number;
};
