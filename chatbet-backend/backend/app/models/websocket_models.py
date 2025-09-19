"""
WebSocket message models for real-time communication.

This module defines the Pydantic models for all WebSocket message types
used in the ChatBet real-time chat system, including user messages,
bot responses, streaming updates, and sports data broadcasts.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, Any, List, Dict, Union
from datetime import datetime
from enum import Enum
import uuid

from .conversation import IntentType


class WebSocketMessageType(str, Enum):
    """Enumeration of WebSocket message types."""
    
    # Chat messages
    USER_MESSAGE = "user_message"
    BOT_RESPONSE = "bot_response"
    STREAMING_RESPONSE = "streaming_response"
    STREAMING_START = "streaming_start"
    STREAMING_END = "streaming_end"
    
    # Status indicators
    TYPING = "typing"
    PROCESSING = "processing"
    
    # System messages
    CONNECTION_ACK = "connection_ack"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    
    # Sports data updates
    SPORTS_UPDATE = "sports_update"
    ODDS_UPDATE = "odds_update"
    MATCH_UPDATE = "match_update"
    
    # Session management
    SESSION_CREATED = "session_created"
    SESSION_RESUMED = "session_resumed"
    SESSION_ENDED = "session_ended"


class WSBaseMessage(BaseModel):
    """Base WebSocket message structure with common fields."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class WSUserMessage(WSBaseMessage):
    """User message sent to the assistant."""
    
    type: Literal[WebSocketMessageType.USER_MESSAGE] = WebSocketMessageType.USER_MESSAGE
    content: str = Field(..., min_length=1, max_length=4000)
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WSBotResponse(WSBaseMessage):
    """Complete bot response message."""
    
    type: Literal[WebSocketMessageType.BOT_RESPONSE] = WebSocketMessageType.BOT_RESPONSE
    content: str
    detected_intent: Optional[IntentType] = None
    intent_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    response_time_ms: Optional[int] = None
    token_count: Optional[int] = None
    function_calls_made: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    is_final: bool = True


class WSStreamingResponse(WSBaseMessage):
    """Streaming response chunk during real-time generation."""
    
    type: Literal[WebSocketMessageType.STREAMING_RESPONSE] = WebSocketMessageType.STREAMING_RESPONSE
    content: str  # Partial content chunk
    full_content: Optional[str] = None  # Accumulated content so far
    is_final: bool = False
    chunk_index: int = 0


class WSStreamingStart(WSBaseMessage):
    """Indicates start of streaming response."""
    
    type: Literal[WebSocketMessageType.STREAMING_START] = WebSocketMessageType.STREAMING_START
    estimated_tokens: Optional[int] = None
    detected_intent: Optional[IntentType] = None


class WSStreamingEnd(WSBaseMessage):
    """Indicates end of streaming response."""
    
    type: Literal[WebSocketMessageType.STREAMING_END] = WebSocketMessageType.STREAMING_END
    final_content: str
    total_chunks: int
    response_time_ms: int
    token_count: Optional[int] = None
    suggested_actions: List[str] = Field(default_factory=list)


class WSTypingIndicator(WSBaseMessage):
    """Typing indicator message."""
    
    type: Literal[WebSocketMessageType.TYPING] = WebSocketMessageType.TYPING
    is_typing: bool
    estimated_time_seconds: Optional[int] = None


class WSProcessingIndicator(WSBaseMessage):
    """Processing indicator for complex operations."""
    
    type: Literal[WebSocketMessageType.PROCESSING] = WebSocketMessageType.PROCESSING
    is_processing: bool
    operation: Optional[str] = None  # "thinking", "fetching_data", "analyzing"
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)


class WSConnectionAck(WSBaseMessage):
    """Connection acknowledgment message."""
    
    type: Literal[WebSocketMessageType.CONNECTION_ACK] = WebSocketMessageType.CONNECTION_ACK
    server_time: datetime = Field(default_factory=datetime.utcnow)
    client_id: str
    supported_features: List[str] = Field(default_factory=list)


class WSPing(WSBaseMessage):
    """Ping message for connection testing."""
    
    type: Literal[WebSocketMessageType.PING] = WebSocketMessageType.PING


class WSPong(WSBaseMessage):
    """Pong response to ping."""
    
    type: Literal[WebSocketMessageType.PONG] = WebSocketMessageType.PONG
    ping_timestamp: datetime


class WSError(WSBaseMessage):
    """Error message."""
    
    type: Literal[WebSocketMessageType.ERROR] = WebSocketMessageType.ERROR
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    retry_after_seconds: Optional[int] = None


class SportsUpdateType(str, Enum):
    """Types of sports data updates."""
    
    ODDS_CHANGE = "odds_change"
    MATCH_START = "match_start"
    MATCH_END = "match_end"
    GOAL_SCORED = "goal_scored"
    CARD_ISSUED = "card_issued"
    SUBSTITUTION = "substitution"
    HALF_TIME = "half_time"
    FULL_TIME = "full_time"
    FIXTURE_ADDED = "fixture_added"
    FIXTURE_CANCELLED = "fixture_cancelled"


class WSSportsUpdate(WSBaseMessage):
    """Sports data update message."""
    
    type: Literal[WebSocketMessageType.SPORTS_UPDATE] = WebSocketMessageType.SPORTS_UPDATE
    update_type: SportsUpdateType
    match_id: Optional[str] = None
    tournament_id: Optional[str] = None
    data: Dict[str, Any]
    priority: Literal["low", "medium", "high"] = "medium"


class WSOddsUpdate(WSBaseMessage):
    """Betting odds update message."""
    
    type: Literal[WebSocketMessageType.ODDS_UPDATE] = WebSocketMessageType.ODDS_UPDATE
    match_id: str
    market_type: str
    old_odds: Optional[Dict[str, float]] = None
    new_odds: Dict[str, float]
    change_percentage: Optional[float] = None
    movement_direction: Literal["up", "down", "stable"] = "stable"


class WSMatchUpdate(WSBaseMessage):
    """Live match update message."""
    
    type: Literal[WebSocketMessageType.MATCH_UPDATE] = WebSocketMessageType.MATCH_UPDATE
    match_id: str
    event_type: str  # "goal", "card", "substitution", etc.
    minute: Optional[int] = None
    player: Optional[str] = None
    team: Optional[str] = None
    description: str
    score: Optional[Dict[str, int]] = None


class WSSessionCreated(WSBaseMessage):
    """Session created notification."""
    
    type: Literal[WebSocketMessageType.SESSION_CREATED] = WebSocketMessageType.SESSION_CREATED
    user_id: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WSSessionResumed(WSBaseMessage):
    """Session resumed notification."""
    
    type: Literal[WebSocketMessageType.SESSION_RESUMED] = WebSocketMessageType.SESSION_RESUMED
    user_id: Optional[str] = None
    last_activity: datetime
    message_count: int = 0


class WSSessionEnded(WSBaseMessage):
    """Session ended notification."""
    
    type: Literal[WebSocketMessageType.SESSION_ENDED] = WebSocketMessageType.SESSION_ENDED
    reason: str = "user_disconnect"
    duration_seconds: Optional[int] = None
    message_count: int = 0


# Union type for all WebSocket messages
WSMessage = Union[
    WSUserMessage,
    WSBotResponse,
    WSStreamingResponse,
    WSStreamingStart,
    WSStreamingEnd,
    WSTypingIndicator,
    WSProcessingIndicator,
    WSConnectionAck,
    WSPing,
    WSPong,
    WSError,
    WSSportsUpdate,
    WSOddsUpdate,
    WSMatchUpdate,
    WSSessionCreated,
    WSSessionResumed,
    WSSessionEnded,
]


class WSMessageEnvelope(BaseModel):
    """Envelope for WebSocket message transmission."""
    
    version: str = "1.0"
    compression: Optional[str] = None
    message: WSMessage
    
    class Config:
        # Enable serialization of union types
        use_enum_values = True


# Message type mapping for parsing
MESSAGE_TYPE_MAP = {
    WebSocketMessageType.USER_MESSAGE: WSUserMessage,
    WebSocketMessageType.BOT_RESPONSE: WSBotResponse,
    WebSocketMessageType.STREAMING_RESPONSE: WSStreamingResponse,
    WebSocketMessageType.STREAMING_START: WSStreamingStart,
    WebSocketMessageType.STREAMING_END: WSStreamingEnd,
    WebSocketMessageType.TYPING: WSTypingIndicator,
    WebSocketMessageType.PROCESSING: WSProcessingIndicator,
    WebSocketMessageType.CONNECTION_ACK: WSConnectionAck,
    WebSocketMessageType.PING: WSPing,
    WebSocketMessageType.PONG: WSPong,
    WebSocketMessageType.ERROR: WSError,
    WebSocketMessageType.SPORTS_UPDATE: WSSportsUpdate,
    WebSocketMessageType.ODDS_UPDATE: WSOddsUpdate,
    WebSocketMessageType.MATCH_UPDATE: WSMatchUpdate,
    WebSocketMessageType.SESSION_CREATED: WSSessionCreated,
    WebSocketMessageType.SESSION_RESUMED: WSSessionResumed,
    WebSocketMessageType.SESSION_ENDED: WSSessionEnded,
}


def parse_websocket_message(data: dict) -> WSMessage:
    """
    Parse incoming WebSocket message data into appropriate model.
    
    Args:
        data: Dictionary containing message data
        
    Returns:
        Parsed WebSocket message instance
        
    Raises:
        ValueError: If message type is unknown or parsing fails
    """
    message_type = data.get("type")
    if not message_type:
        raise ValueError("Message type is required")
    
    try:
        message_type_enum = WebSocketMessageType(message_type)
    except ValueError:
        raise ValueError(f"Unknown message type: {message_type}")
    
    message_class = MESSAGE_TYPE_MAP.get(message_type_enum)
    if not message_class:
        raise ValueError(f"No parser for message type: {message_type}")
    
    return message_class(**data)


def create_error_message(
    session_id: str,
    error_code: str,
    error_message: str,
    details: Optional[Dict[str, Any]] = None
) -> WSError:
    """
    Helper function to create error messages.
    
    Args:
        session_id: Session identifier
        error_code: Error code identifier
        error_message: Human-readable error message
        details: Optional additional error details
        
    Returns:
        WSError message instance
    """
    return WSError(
        session_id=session_id,
        error_code=error_code,
        error_message=error_message,
        details=details or {}
    )


def create_typing_indicator(
    session_id: str,
    is_typing: bool,
    estimated_time: Optional[int] = None
) -> WSTypingIndicator:
    """
    Helper function to create typing indicators.
    
    Args:
        session_id: Session identifier
        is_typing: Whether typing is active
        estimated_time: Estimated response time in seconds
        
    Returns:
        WSTypingIndicator message instance
    """
    return WSTypingIndicator(
        session_id=session_id,
        is_typing=is_typing,
        estimated_time_seconds=estimated_time
    )