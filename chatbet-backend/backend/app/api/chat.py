"""
Chat API endpoints for conversational interactions.

This module provides the main chat endpoints for the ChatBet assistant,
including message processing, conversation management, and streaming responses.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict, Any, Optional
import json
import asyncio
from datetime import datetime

from ..core.logging import get_logger
from ..core.auth import CurrentUser, OptionalUser
from ..models.conversation import ChatRequest, ChatResponse, IntentType
from ..models.api_models import UserInfo
from ..services.conversation_manager import get_conversation_manager
from ..utils.exceptions import ConversationException, LLMException, APIException

logger = get_logger(__name__)
router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest, 
    current_user: OptionalUser = None
) -> ChatResponse:
    """
    Send a message to the ChatBet assistant.
    
    Processes the user's message and returns an intelligent response
    with betting insights, recommendations, or general information.
    
    Authentication is optional - provides enhanced features when authenticated.
    """
    try:
        conversation_manager = get_conversation_manager()
        
        # If user is authenticated, update request with user info
        if current_user:
            request.user_id = current_user.user_id
            logger.info(
                f"Processing authenticated chat message",
                extra={
                    "user_id": current_user.user_id,
                    "username": current_user.username,
                    "message_length": len(request.message),
                    "session_id": request.session_id
                }
            )
        else:
            logger.info(
                f"Processing anonymous chat message",
                extra={
                    "user_id": request.user_id,
                    "message_length": len(request.message),
                    "session_id": request.session_id
                }
            )
        
        # Process the message through the conversation manager
        response = await conversation_manager.process_message(request)
        
        logger.info(
            f"Chat message processed successfully",
            extra={
                "user_id": request.user_id,
                "response_type": response.detected_intent,
                "session_id": request.session_id,
                "authenticated": current_user is not None
            }
        )
        
        return response
        
    except ConversationException as e:
        logger.error(f"Conversation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except APIException as e:
        logger.error(f"External API error: {e.message}")
        raise HTTPException(status_code=502, detail="External service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error processing message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


"""
@router.post("/stream")
async def stream_message(request: ChatRequest) -> StreamingResponse:
    # Streaming functionality commented out until conversation manager is fully implemented
    # This would require complex conversation manager integration
    pass
"""


@router.get("/conversations/{user_id}")
async def get_conversation_history(
    user_id: str,
    current_user: CurrentUser,
    session_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get conversation history for a user.
    
    Returns the conversation history, optionally filtered by session.
    Requires authentication - users can only access their own conversations.
    """
    try:
        # Security check: users can only access their own conversations
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: You can only access your own conversations"
            )
        
        conversation_manager = get_conversation_manager()
        
        # If no session_id provided, return empty result for now
        # In a full implementation, we'd list all sessions for the user
        if not session_id:
            return {
                "user_id": user_id,
                "session_id": None,
                "conversations": None,
                "limit": limit,
                "offset": offset,
                "message": "session_id parameter is required"
            }
        
        history = await conversation_manager.get_conversation_history(
            session_id=session_id,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "conversations": history,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")


@router.delete("/conversations/{user_id}")
async def clear_conversation_history(
    user_id: str,
    current_user: CurrentUser,
    session_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, str]:
    """
    Clear conversation history for a user.
    
    Optionally clear only a specific session.
    Requires authentication - users can only clear their own conversations.
    """
    try:
        # Security check: users can only clear their own conversations
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: You can only clear your own conversations"
            )
        
        conversation_manager = get_conversation_manager()
        
        # Add to background tasks for async processing
        if background_tasks:
            background_tasks.add_task(
                conversation_manager.clear_conversation_history,
                user_id=user_id,
                session_id=session_id
            )
        else:
            await conversation_manager.clear_conversation_history(
                user_id=user_id,
                session_id=session_id
            )
        
        return {
            "message": "Conversation history cleared successfully",
            "user_id": user_id,
            "session_id": session_id or "all"
        }
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to clear conversation history")


@router.get("/intents")
async def get_supported_intents(current_user: CurrentUser) -> Dict[str, Any]:
    """
    Get list of supported conversation intents.
    
    Returns information about what types of queries the assistant can handle.
    Requires authentication.
    """
    intents = [
        {
            "type": IntentType.GENERAL_BETTING_INFO.value,
            "description": "General betting information and explanations",
            "examples": [
                "What is a handicap bet?",
                "How do odds work?",
                "Explain over/under betting"
            ]
        },
        {
            "type": IntentType.MATCH_INQUIRY.value,
            "description": "Information about specific matches and fixtures",
            "examples": [
                "When is Barcelona vs Real Madrid?",
                "Show me today's matches",
                "What are the odds for Liverpool vs Arsenal?"
            ]
        },
        {
            "type": IntentType.ODDS_COMPARISON.value,
            "description": "Compare odds across different betting markets",
            "examples": [
                "Compare odds for Manchester United to win",
                "Best odds for over 2.5 goals",
                "Show me all odds for this match"
            ]
        },
        {
            "type": IntentType.BETTING_RECOMMENDATION.value,
            "description": "Personalized betting recommendations and analysis",
            "examples": [
                "What should I bet on today?",
                "Give me a safe betting strategy",
                "Recommend bets for this weekend"
            ]
        },
        {
            "type": IntentType.TOURNAMENT_INFO.value,
            "description": "Tournament schedules, standings, and information",
            "examples": [
                "Show me Premier League table",
                "When does Champions League start?",
                "Tournament fixtures this week"
            ]
        }
    ]
    
    return {
        "supported_intents": intents,
        "total_count": len(intents),
        "timestamp": datetime.utcnow().isoformat()
    }