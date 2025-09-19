"""
Conversation and chat models for the ChatBet application.

These models handle the conversational aspects of our chatbot,
including message history, user interactions, and LLM responses.

I'm designing these to work seamlessly with LangChain while providing
strong typing and validation for our chat system.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal, Union
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, ConfigDict


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class IntentType(str, Enum):
    """
    Supported conversation intents.
    
    These help our system understand what the user is trying to accomplish
    and route to the appropriate response logic.
    """
    # Match and schedule queries
    MATCH_SCHEDULE_QUERY = "match_schedule_query"
    MATCH_INQUIRY = "match_inquiry"  # Alias for API compatibility
    TEAM_SCHEDULE_QUERY = "team_schedule_query"
    TOURNAMENT_INFO_QUERY = "tournament_info_query"
    TOURNAMENT_INFO = "tournament_info"  # Alias for API compatibility
    
    # Odds and betting information
    ODDS_INFORMATION_QUERY = "odds_information_query"
    ODDS_COMPARISON = "odds_comparison"  # Alias for API compatibility
    BETTING_RECOMMENDATION = "betting_recommendation"
    TEAM_COMPARISON = "team_comparison"
    MATCH_PREDICTION = "match_prediction"
    
    # User account and betting
    USER_BALANCE_QUERY = "user_balance_query"
    BET_SIMULATION = "bet_simulation"
    BET_HISTORY_QUERY = "bet_history_query"
    
    # General conversation
    GENERAL_SPORTS_QUERY = "general_sports_query"
    GENERAL_BETTING_INFO = "general_betting_info"  # Alias for API compatibility
    GREETING = "greeting"
    HELP_REQUEST = "help_request"
    UNCLEAR = "unclear"


class ConfidenceLevel(str, Enum):
    """Confidence levels for intent classification."""
    HIGH = "high"      # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"        # < 0.5


class BaseConversationModel(BaseModel):
    """Base model for conversation-related models."""
    model_config = ConfigDict(
        extra='forbid',
        use_enum_values=True,
        validate_default=True,
        str_strip_whitespace=True
    )


class ChatMessage(BaseConversationModel):
    """
    Individual chat message in a conversation.
    
    This represents a single message from either the user or assistant,
    with metadata for tracking and analysis.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique message identifier")
    role: MessageRole = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    
    # Optional metadata
    user_id: Optional[str] = Field(None, description="User identifier if authenticated")
    session_id: Optional[str] = Field(None, description="Conversation session identifier")
    
    # Intent analysis (for user messages)
    detected_intent: Optional[IntentType] = Field(None, description="Detected user intent")
    intent_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Intent confidence score")
    
    # Response metadata (for assistant messages)
    response_time_ms: Optional[int] = Field(None, description="Response generation time in milliseconds")
    token_count: Optional[int] = Field(None, description="Token count for LLM response")
    
    # Function calling metadata
    function_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Function calls made")
    
    @validator('content')
    def validate_content(cls, v):
        """Ensure message content is not empty."""
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v
    
    @property
    def confidence_level(self) -> Optional[ConfidenceLevel]:
        """Get confidence level category."""
        if self.intent_confidence is None:
            return None
        
        if self.intent_confidence > 0.8:
            return ConfidenceLevel.HIGH
        elif self.intent_confidence > 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW


class ConversationContext(BaseConversationModel):
    """
    Context information for the current conversation.
    
    This includes user preferences, conversation state, and any relevant
    data that should persist across multiple message exchanges.
    """
    session_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="Authenticated user identifier")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation timestamp")
    last_activity: datetime = Field(default_factory=datetime.now, description="Last activity timestamp")
    
    # User preferences and state
    preferred_teams: List[str] = Field(default_factory=list, description="User's preferred teams")
    preferred_tournaments: List[str] = Field(default_factory=list, description="User's preferred tournaments")
    timezone: Optional[str] = Field(None, description="User's timezone")
    language: str = Field(default="en", description="User's preferred language")
    
    # Current conversation context
    current_topic: Optional[str] = Field(None, description="Current conversation topic")
    mentioned_teams: List[str] = Field(default_factory=list, description="Teams mentioned in conversation")
    mentioned_matches: List[str] = Field(default_factory=list, description="Matches mentioned in conversation")
    
    # Authentication state
    is_authenticated: bool = Field(default=False, description="Whether user is authenticated")
    auth_token: Optional[str] = Field(None, description="Authentication token")
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def add_mentioned_team(self, team_name: str):
        """Add a team to the mentioned teams list."""
        if team_name not in self.mentioned_teams:
            self.mentioned_teams.append(team_name)
    
    def add_mentioned_match(self, match_id: str):
        """Add a match to the mentioned matches list."""
        if match_id not in self.mentioned_matches:
            self.mentioned_matches.append(match_id)


class Conversation(BaseConversationModel):
    """
    Complete conversation with message history and context.
    
    This is the main model that ties together all messages in a conversation
    along with the context and metadata.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique conversation identifier")
    context: ConversationContext = Field(..., description="Conversation context")
    messages: List[ChatMessage] = Field(default_factory=list, description="Message history")
    
    # Conversation metadata
    title: Optional[str] = Field(None, description="Conversation title (auto-generated)")
    is_active: bool = Field(default=True, description="Whether conversation is active")
    
    def add_message(self, message: ChatMessage):
        """Add a message to the conversation."""
        # Set session ID if not already set
        if message.session_id is None:
            message.session_id = self.context.session_id
        
        # Update user ID from context if authenticated
        if self.context.is_authenticated and message.user_id is None:
            message.user_id = self.context.user_id
        
        self.messages.append(message)
        self.context.update_activity()
    
    def get_recent_messages(self, count: int = 10) -> List[ChatMessage]:
        """Get the most recent messages."""
        return self.messages[-count:] if count < len(self.messages) else self.messages
    
    def get_user_messages(self) -> List[ChatMessage]:
        """Get all user messages."""
        return [msg for msg in self.messages if msg.role == MessageRole.USER]
    
    def get_assistant_messages(self) -> List[ChatMessage]:
        """Get all assistant messages."""
        return [msg for msg in self.messages if msg.role == MessageRole.ASSISTANT]
    
    @property
    def message_count(self) -> int:
        """Total number of messages in conversation."""
        return len(self.messages)
    
    @property
    def last_message(self) -> Optional[ChatMessage]:
        """Get the last message in conversation."""
        return self.messages[-1] if self.messages else None
    
    @property
    def last_user_message(self) -> Optional[ChatMessage]:
        """Get the last user message."""
        user_messages = self.get_user_messages()
        return user_messages[-1] if user_messages else None


# === Request/Response Models for API ===

class ChatRequest(BaseConversationModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message content")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation continuity")
    user_id: Optional[str] = Field(None, description="User identifier if authenticated")
    
    # Optional request parameters
    include_context: bool = Field(default=True, description="Whether to include conversation context")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for response")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="LLM temperature override")


class ChatResponse(BaseConversationModel):
    """Response model for chat endpoint."""
    message: str = Field(..., description="Assistant response message")
    session_id: str = Field(..., description="Session identifier")
    message_id: str = Field(..., description="Unique message identifier")
    
    # Response metadata
    response_time_ms: int = Field(..., description="Response generation time")
    token_count: Optional[int] = Field(None, description="Response token count")
    
    # Intent analysis
    detected_intent: Optional[IntentType] = Field(None, description="Detected user intent")
    intent_confidence: Optional[float] = Field(None, description="Intent confidence score")
    
    # Function calling results
    function_calls_made: List[str] = Field(default_factory=list, description="Names of functions called")
    
    # Suggestions for follow-up
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested follow-up actions")


class StreamingChatResponse(BaseConversationModel):
    """Streaming response chunk for real-time chat."""
    chunk: str = Field(..., description="Response chunk content")
    session_id: str = Field(..., description="Session identifier")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
    
    # Metadata (included only in final chunk)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")


class ConversationSummary(BaseConversationModel):
    """Summary of a conversation for listing/overview purposes."""
    id: str = Field(..., description="Conversation identifier")
    title: Optional[str] = Field(None, description="Conversation title")
    message_count: int = Field(..., description="Total number of messages")
    last_message_preview: str = Field(..., description="Preview of last message")
    created_at: datetime = Field(..., description="Conversation creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    is_active: bool = Field(default=True, description="Whether conversation is active")


class IntentClassificationResult(BaseConversationModel):
    """Result of intent classification."""
    intent: IntentType = Field(..., description="Detected intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    
    # Extracted entities
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities from message")
    
    # Alternative intents
    alternatives: List[Dict[str, Union[IntentType, float]]] = Field(
        default_factory=list, 
        description="Alternative intents with confidence scores"
    )