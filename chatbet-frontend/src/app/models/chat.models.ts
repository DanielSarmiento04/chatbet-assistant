/**
 * Chat and conversation models for ChatBet frontend.
 * Based on backend models with TypeScript specific optimizations.
 */

export enum MessageRole {
  SYSTEM = 'system',
  USER = 'user',
  ASSISTANT = 'assistant',
  FUNCTION = 'function'
}

export enum IntentType {
  // Match and schedule queries
  MATCH_SCHEDULE_QUERY = 'match_schedule_query',
  MATCH_INQUIRY = 'match_inquiry',
  TEAM_SCHEDULE_QUERY = 'team_schedule_query',
  TOURNAMENT_INFO_QUERY = 'tournament_info_query',
  TOURNAMENT_INFO = 'tournament_info',

  // Odds and betting information
  ODDS_INFORMATION_QUERY = 'odds_information_query',
  ODDS_COMPARISON = 'odds_comparison',
  BETTING_RECOMMENDATION = 'betting_recommendation',
  TEAM_COMPARISON = 'team_comparison',
  MATCH_PREDICTION = 'match_prediction',

  // User account and betting
  USER_BALANCE_QUERY = 'user_balance_query',
  BET_SIMULATION = 'bet_simulation',
  BET_HISTORY_QUERY = 'bet_history_query',

  // General conversation
  GENERAL_SPORTS_QUERY = 'general_sports_query',
  GENERAL_BETTING_INFO = 'general_betting_info',
  GREETING = 'greeting',
  HELP_REQUEST = 'help_request',
  UNCLEAR = 'unclear'
}

export enum ConfidenceLevel {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

export enum MessageType {
  TEXT = 'text',
  MATCH_CARD = 'match_card',
  ODDS_TABLE = 'odds_table',
  RECOMMENDATION = 'recommendation',
  TOURNAMENT_INFO = 'tournament_info',
  ERROR = 'error',
  TYPING = 'typing'
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  messageType: MessageType;

  // Optional metadata
  userId?: string;
  sessionId?: string;

  // Intent analysis (for user messages)
  detectedIntent?: IntentType;
  intentConfidence?: number;

  // Response metadata (for assistant messages)
  responseTimeMs?: number;
  tokenCount?: number;

  // Rich content data
  data?: MatchData | OddsData | RecommendationData | TournamentData;

  // UI state
  isLoading?: boolean;
  hasError?: boolean;
  errorMessage?: string;
}

export interface MatchData {
  id: string;
  homeTeam: string;
  awayTeam: string;
  homeTeamLogo?: string;
  awayTeamLogo?: string;
  date: Date;
  tournament: string;
  venue?: string;
  status: 'scheduled' | 'live' | 'finished' | 'postponed';
  score?: {
    home: number;
    away: number;
  };
  odds?: {
    homeWin: number;
    draw?: number;
    awayWin: number;
  };
}

export interface OddsData {
  matchId: string;
  match: string;
  homeTeam: string;
  awayTeam: string;
  bookmakers: BookmakerOdds[];
  lastUpdated: Date;
}

export interface BookmakerOdds {
  name: string;
  logo?: string;
  homeWin: number;
  draw?: number;
  awayWin: number;
  overUnder?: {
    over25: number;
    under25: number;
  };
}

export interface RecommendationData {
  id: string;
  title: string;
  description: string;
  confidence: number;
  confidenceLevel: ConfidenceLevel;
  recommendedBet: {
    type: string;
    selection: string;
    odds: number;
    stake?: number;
    potentialReturn?: number;
  };
  reasoning: string[];
  riskLevel: 'low' | 'medium' | 'high';
  matchId?: string;
}

export interface TournamentData {
  id: string;
  name: string;
  country: string;
  logo?: string;
  season: string;
  standings?: TeamStanding[];
  fixtures?: MatchData[];
  topScorers?: PlayerStats[];
}

export interface TeamStanding {
  position: number;
  team: string;
  logo?: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  form: string[];
}

export interface PlayerStats {
  name: string;
  team: string;
  goals: number;
  assists?: number;
  appearances: number;
}

export interface ConversationContext {
  sessionId: string;
  userId?: string;
  createdAt: Date;
  lastActivity: Date;

  // User preferences
  preferredTeams: string[];
  preferredTournaments: string[];
  timezone?: string;
  language: string;

  // Current conversation context
  currentTopic?: string;
  mentionedTeams: string[];
  mentionedMatches: string[];

  // Authentication state
  isAuthenticated: boolean;
  authToken?: string;
}

export interface Conversation {
  id: string;
  context: ConversationContext;
  messages: ChatMessage[];
  title?: string;
  isActive: boolean;
}

// API Request/Response models
export interface ChatRequest {
  message: string;
  sessionId?: string;
  userId?: string;
  includeContext?: boolean;
  maxTokens?: number;
  temperature?: number;
}

export interface ChatResponse {
  message: string;
  sessionId: string;
  messageId: string;
  responseTimeMs: number;
  tokenCount?: number;
  detectedIntent?: IntentType;
  intentConfidence?: number;
  functionCallsMade: string[];
  suggestedActions: string[];
}

export interface StreamingChatResponse {
  chunk: string;
  sessionId: string;
  isFinal: boolean;
  metadata?: Record<string, unknown>;
}

export interface ConversationSummary {
  id: string;
  title?: string;
  messageCount: number;
  lastMessagePreview: string;
  createdAt: Date;
  lastActivity: Date;
  isActive: boolean;
}

export interface IntentClassificationResult {
  intent: IntentType;
  confidence: number;
  entities: Record<string, unknown>;
  alternatives: Array<{
    intent: IntentType;
    confidence: number;
  }>;
}

// User authentication and account models
export interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  balance?: number;
  currency: string;
  isVerified: boolean;
  preferences: UserPreferences;
  createdAt: Date;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  notifications: {
    email: boolean;
    push: boolean;
    sound: boolean;
  };
  favoriteTeams: string[];
  favoriteTournaments: string[];
  defaultStake: number;
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'message' | 'typing' | 'error' | 'connection' | 'disconnect';
  data: unknown;
  timestamp: Date;
}

export interface TypingIndicator {
  userId: string;
  isTyping: boolean;
  sessionId: string;
}

// Error handling
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
  timestamp: Date;
}

// Chat UI state
export interface ChatUIState {
  isLoading: boolean;
  isConnected: boolean;
  isTyping: boolean;
  lastError?: ApiError;
  suggestedPrompts: string[];
  currentSessionId?: string;
}

// Utility types
export type MessageWithoutTimestamp = Omit<ChatMessage, 'timestamp'>;
export type CreateMessagePayload = Omit<ChatMessage, 'id' | 'timestamp'>;
export type UpdateMessagePayload = Partial<Pick<ChatMessage, 'content' | 'data' | 'hasError' | 'errorMessage'>>;
