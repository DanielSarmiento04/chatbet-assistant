"""
Conversation manager with LangChain integration and memory management.

This is the orchestrator for our conversational AI system. It combines
LangChain's conversation management with our domain-specific logic for
sports betting. The key insight here is using ConversationBufferWindowMemory
to maintain context while preventing token overflow.

Why LangChain? It gives us:
1. Built-in conversation memory management
2. Easy integration with different LLMs
3. Conversation chains with context
4. Tool/function calling support
5. Streaming responses out of the box
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, AsyncGenerator
from datetime import datetime
import asyncio
from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from ..core.config import settings
from ..core.logging import get_logger, log_function_call
from ..models.conversation import (
    Conversation, ConversationContext, ChatMessage, MessageRole,
    IntentType, ChatRequest, ChatResponse, IntentClassificationResult
)
from ..models.betting import BetRecommendation, BettingStrategy
from ..services.llm_service import get_llm_service
from ..services.chatbet_api import get_api_client

logger = get_logger(__name__)


class ConversationError(Exception):
    """Base exception for conversation-related errors."""
    pass


class MemoryFullError(ConversationError):
    """Memory buffer is full."""
    pass


class ConversationManager:
    """
    Main conversation manager using LangChain.
    
    This class orchestrates the entire conversation flow:
    1. Intent classification to understand user goals
    2. Context management to maintain conversation state
    3. Response generation with domain expertise
    4. Memory management to prevent token overflow
    5. Function calling for real-time data integration
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
        
        # Session storage (in production, use Redis)
        self.sessions: Dict[str, Conversation] = {}
        self.memories: Dict[str, InMemoryChatMessageHistory] = {}
        
        # Performance tracking
        self._total_conversations = 0
        self._avg_response_time = 0.0
    
    @log_function_call()
    async def start_conversation(
        self, 
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Conversation:
        """
        Start a new conversation or resume existing one.
        
        This creates the conversation context and initializes memory.
        The beauty of LangChain is that it handles the complexity of
        maintaining conversation state for us.
        """
        if not session_id:
            session_id = str(uuid4())
        
        # Check if conversation already exists
        if session_id in self.sessions:
            logger.debug(f"Resuming conversation: {session_id}")
            return self.sessions[session_id]
        
        # Create new conversation
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            is_authenticated=user_id is not None,
            timezone="UTC",
            current_topic=None,
            auth_token=None
        )
        
        conversation = Conversation(
            id=session_id,
            context=context,
            title=None
        )
        
        # Initialize LangChain memory - using new recommended approach
        history = InMemoryChatMessageHistory()
        
        # Store in session cache
        self.sessions[session_id] = conversation
        self.memories[session_id] = history
        
        self._total_conversations += 1
        logger.info(f"Started new conversation: {session_id}")
        
        return conversation
    
    async def _generate_contextual_response(
        self,
        conversation: Conversation,
        intent_result: IntentClassificationResult,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate contextual response based on intent and conversation history.
        
        This method routes to different response strategies based on the
        classified intent. It's the heart of our conversation logic.
        """
        user_message = conversation.last_user_message
        if not user_message:
            return "I don't see a message to respond to."
            
        conversation_history = self._convert_to_langchain_messages(conversation)
        
        # Build enhanced context
        enhanced_context = {
            "intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "entities": intent_result.entities,
            "conversation_context": conversation.context.model_dump(),
        }
        
        if user_context:
            enhanced_context.update(user_context)
        
        # Route based on intent
        if intent_result.intent == IntentType.MATCH_SCHEDULE_QUERY:
            return await self._handle_schedule_query(user_message.content, conversation_history, enhanced_context)
        
        elif intent_result.intent == IntentType.ODDS_INFORMATION_QUERY:
            return await self._handle_odds_query(user_message.content, conversation_history, enhanced_context)
        
        elif intent_result.intent == IntentType.BETTING_RECOMMENDATION:
            return await self._handle_betting_recommendation(user_message.content, conversation_history, enhanced_context)
        
        elif intent_result.intent == IntentType.TEAM_COMPARISON:
            return await self._handle_team_comparison(user_message.content, conversation_history, enhanced_context)
        
        elif intent_result.intent == IntentType.USER_BALANCE_QUERY:
            return await self._handle_balance_query(user_message.content, conversation_history, enhanced_context)
        
        elif intent_result.intent == IntentType.BET_SIMULATION:
            return await self._handle_bet_simulation(user_message.content, conversation_history, enhanced_context)
        
        elif intent_result.intent == IntentType.GREETING:
            return await self._handle_greeting(user_message.content, conversation_history, enhanced_context)
        
        elif intent_result.intent == IntentType.HELP_REQUEST:
            return await self._handle_help_request(user_message.content, conversation_history, enhanced_context)
        
        else:
            # General response for unclear or general queries
            return await self.llm_service.generate_response(
                user_message.content, conversation_history, enhanced_context
            )
    
    async def _handle_schedule_query(self, user_message: str, history: List[BaseMessage], context: Dict[str, Any]) -> str:
        """Handle match schedule queries with real-time data."""
        # Extract team names from entities if available
        entities = context.get("entities", {})
        team_name = entities.get("team_name")
        
        if team_name:
            context["specific_team"] = team_name
            context["query_type"] = "team_specific_schedule"
        else:
            context["query_type"] = "general_schedule"
        
        return await self.llm_service.generate_response(user_message, history, context)
    
    async def _handle_odds_query(self, user_message: str, history: List[BaseMessage], context: Dict[str, Any]) -> str:
        """Handle odds information queries."""
        context["query_type"] = "odds_information"
        context["include_odds_explanation"] = True
        
        return await self.llm_service.generate_response(user_message, history, context)
    
    async def _handle_betting_recommendation(self, user_message: str, history: List[BaseMessage], context: Dict[str, Any]) -> str:
        """Handle betting recommendation requests."""
        context["query_type"] = "betting_recommendation"
        context["include_risk_warning"] = True
        context["include_reasoning"] = True
        
        return await self.llm_service.generate_response(user_message, history, context)
    
    async def _handle_team_comparison(self, user_message: str, history: List[BaseMessage], context: Dict[str, Any]) -> str:
        """Handle team comparison queries."""
        context["query_type"] = "team_comparison"
        context["include_stats"] = True
        
        return await self.llm_service.generate_response(user_message, history, context)
    
    async def _handle_balance_query(self, user_message: str, history: List[BaseMessage], context: Dict[str, Any]) -> str:
        """Handle user balance queries."""
        if not context.get("conversation_context", {}).get("is_authenticated"):
            return "To check your balance, you'll need to sign in first. Would you like me to help you with that?"
        
        context["query_type"] = "balance_query"
        return await self.llm_service.generate_response(user_message, history, context)
    
    async def _handle_bet_simulation(self, user_message: str, history: List[BaseMessage], context: Dict[str, Any]) -> str:
        """Handle bet placement simulation."""
        context["query_type"] = "bet_simulation"
        context["include_calculation"] = True
        context["include_risk_warning"] = True
        
        return await self.llm_service.generate_response(user_message, history, context)
    
    async def _handle_greeting(self, user_message: str, history: List[BaseMessage], context: Dict[str, Any]) -> str:
        """Handle greetings and conversation starters."""
        context["query_type"] = "greeting"
        context["show_capabilities"] = True
        
        return await self.llm_service.generate_response(user_message, history, context)
    
    async def _handle_help_request(self, user_message: str, history: List[BaseMessage], context: Dict[str, Any]) -> str:
        """Handle help requests."""
        help_response = """I'm ChatBet Assistant, your sports betting companion! Here's what I can help you with:

🏆 **Match Information**
- "When does Barcelona play?"
- "What matches are on this weekend?"
- "Show me Premier League fixtures"

💰 **Betting Odds & Analysis**
- "What are the odds for Real Madrid vs Barcelona?"
- "Which team has better odds today?"
- "Explain these betting odds to me"

🎯 **Betting Recommendations**
- "What's a good bet for tonight?"
- "Should I bet on the over or under?"
- "Give me a safe betting tip"

⚖️ **Team Comparisons**
- "Compare Barcelona vs Real Madrid"
- "Who's the favorite in this match?"
- "Which team has better form?"

📊 **Account & Betting**
- "What's my balance?" (requires sign-in)
- "Help me place a bet"
- "Calculate my potential winnings"

Just ask me anything about sports betting, and I'll help you make informed decisions! Remember, I always promote responsible gambling."""
        
        return help_response
    
    def _convert_to_langchain_messages(self, conversation: Conversation) -> List[BaseMessage]:
        """Convert our ChatMessage objects to LangChain BaseMessage objects."""
        messages = []
        
        for msg in conversation.get_recent_messages():
            if msg.role == MessageRole.USER:
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                messages.append(AIMessage(content=msg.content))
            elif msg.role == MessageRole.SYSTEM:
                messages.append(SystemMessage(content=msg.content))
        
        return messages
    
    def _generate_suggested_actions(self, intent: IntentType) -> List[str]:
        """Generate contextual follow-up suggestions based on intent."""
        suggestions_map = {
            IntentType.MATCH_SCHEDULE_QUERY: [
                "Ask about specific teams",
                "Check betting odds for these matches",
                "Get tournament information"
            ],
            IntentType.ODDS_INFORMATION_QUERY: [
                "Get betting recommendations",
                "Compare odds across matches",
                "Simulate a bet"
            ],
            IntentType.BETTING_RECOMMENDATION: [
                "Check your balance",
                "Simulate the recommended bet",
                "Ask for safer alternatives"
            ],
            IntentType.TEAM_COMPARISON: [
                "Check their upcoming matches",
                "See current betting odds",
                "Get head-to-head statistics"
            ],
            IntentType.GREETING: [
                "Ask about today's matches",
                "Get betting recommendations",
                "Check your balance"
            ],
            IntentType.HELP_REQUEST: [
                "Ask about specific teams",
                "Get today's best bets",
                "Learn about betting types"
            ]
        }
        
        return suggestions_map.get(intent, [
            "Ask about match schedules",
            "Get betting recommendations",
            "Check odds for popular teams"
        ])
    
    def _update_performance_metrics(self, response_time_ms: int):
        """Update performance tracking metrics."""
        if self._total_conversations > 0:
            self._avg_response_time = (
                (self._avg_response_time * (self._total_conversations - 1) + response_time_ms) 
                / self._total_conversations
            )
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Optional[Conversation]:
        """Get conversation history for a session."""
        conversation = self.sessions.get(session_id)
        if not conversation:
            return None
        
        # Apply pagination to messages if needed
        if limit > 0 and len(conversation.messages) > offset:
            # Create a copy of the conversation with paginated messages
            start_idx = offset
            end_idx = offset + limit
            paginated_messages = conversation.messages[start_idx:end_idx]
            
            # Create new conversation with paginated messages
            paginated_conversation = Conversation(
                id=conversation.id,
                context=conversation.context,
                messages=paginated_messages,
                title=conversation.title,
                is_active=conversation.is_active
            )
            return paginated_conversation
        
        return conversation
    
    async def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        if session_id in self.memories:
            self.memories[session_id].clear()
            del self.memories[session_id]
        
        logger.info(f"Cleared conversation: {session_id}")
        return True
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get conversation manager performance statistics."""
        return {
            "total_conversations": self._total_conversations,
            "active_sessions": len(self.sessions),
            "average_response_time_ms": round(self._avg_response_time, 2),
            "memory_usage_mb": len(self.sessions) * 0.1  # Rough estimate
        }
    
    async def initialize(self):
        """Initialize the conversation manager."""
        logger.info("Initializing conversation manager")
        # LLM service initialization is handled in the service itself
        logger.info("Conversation manager initialized successfully")
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat message and return response.
        
        This is the main entry point for message processing.
        """
        start_time = datetime.now()
        
        try:
            # Get or create conversation
            conversation = await self.start_conversation(
                user_id=request.user_id,
                session_id=request.session_id
            )
            history = self.memories[conversation.id]
            
            # Classify user intent first
            intent_result = await self.llm_service.classify_intent(request.message)
            logger.debug(f"Classified intent: {intent_result.intent} (confidence: {intent_result.confidence})")
            
            # Create user message
            user_msg = ChatMessage(
                role=MessageRole.USER,
                content=request.message,
                session_id=conversation.id,
                user_id=request.user_id,
                detected_intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                response_time_ms=None,
                token_count=None,
                function_calls=None
            )
            
            # Add to conversation
            conversation.add_message(user_msg)
            
            # Add to LangChain memory
            history.add_user_message(request.message)
            
            # Generate response based on intent
            response_content = await self._generate_contextual_response(
                conversation=conversation,
                intent_result=intent_result,
                user_context={}
            )
            
            # Ensure response content is not empty
            if not response_content or not response_content.strip():
                response_content = "I apologize, but I'm having trouble generating a response right now. Please try asking your question again."
            
            # Create assistant message
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            # Create assistant message
            assistant_msg = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=response_content,
                session_id=conversation.id,
                user_id=request.user_id,
                detected_intent=None,
                intent_confidence=None,
                response_time_ms=response_time_ms,
                token_count=None,
                function_calls=None
            )
            
            # Add to conversation and memory
            conversation.add_message(assistant_msg)
            history.add_ai_message(response_content)
            
            # Update performance metrics
            self._update_performance_metrics(response_time_ms)
            
            # Generate suggested actions based on intent
            suggested_actions = self._generate_suggested_actions(intent_result.intent)
            
            return ChatResponse(
                message=response_content,
                session_id=conversation.id,
                message_id=assistant_msg.id,
                response_time_ms=response_time_ms,
                token_count=None,  # Could be populated with actual token count
                detected_intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                function_calls_made=[],  # Would be populated if function calls were made
                suggested_actions=suggested_actions
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            # Return error response
            error_response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return ChatResponse(
                message="I apologize, but I encountered an error processing your request. Please try again.",
                session_id=request.session_id or str(uuid4()),
                message_id=str(uuid4()),
                response_time_ms=error_response_time,
                token_count=None,
                detected_intent=IntentType.UNCLEAR,
                intent_confidence=0.0,
                function_calls_made=[],
                suggested_actions=["Try rephrasing your question", "Ask for help"]
            )
    
    async def process_message_stream(self, request: ChatRequest) -> AsyncGenerator[ChatResponse, None]:
        """
        Process message with streaming response.
        
        Yields response chunks for real-time experience.
        """
        try:
            # Get or create conversation
            conversation = await self.start_conversation(
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            # Create chat message
            user_message = ChatMessage(
                role=MessageRole.USER,
                content=request.message,
                session_id=conversation.id,
                user_id=request.user_id,
                detected_intent=None,
                intent_confidence=None,
                response_time_ms=None,
                token_count=None,
                function_calls=None
            )
            
            # Stream the response
            response_chunks = []
            async for chunk in self._stream_response(user_message, conversation):
                response_chunks.append(chunk.message)
                yield chunk
            
            # Save final message to conversation
            final_message = "".join(response_chunks)
            assistant_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=final_message,
                session_id=conversation.id,
                user_id=request.user_id,
                detected_intent=None,
                intent_confidence=None,
                response_time_ms=None,
                token_count=None,
                function_calls=None
            )
            conversation.messages.append(user_message)
            conversation.messages.append(assistant_message)
            
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}", exc_info=True)
            yield ChatResponse(
                message="I apologize, but I encountered an error. Please try again.",
                session_id=request.session_id or str(uuid4()),
                message_id=str(uuid4()),
                response_time_ms=0,
                token_count=None,
                detected_intent=IntentType.UNCLEAR,
                intent_confidence=0.0,
                function_calls_made=[],
                suggested_actions=[]
            )
    
    async def _stream_response(
        self, 
        user_message: ChatMessage, 
        conversation: Conversation
    ) -> AsyncGenerator[ChatResponse, None]:
        """Internal method for streaming responses."""
        # This is a simplified streaming implementation
        # In practice, you'd want to stream from the LLM service
        
        # Process normally first
        response_content = await self._generate_contextual_response(
            conversation=conversation,
            intent_result=IntentClassificationResult(
                intent=IntentType.GENERAL_SPORTS_QUERY,
                confidence=0.8
            ),
            user_context={}
        )
        
        # Split into chunks for streaming effect
        words = response_content.split()
        chunk_size = 3  # Words per chunk
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            yield ChatResponse(
                message=chunk_text + " ",
                session_id=conversation.id,
                message_id=str(uuid4()),
                response_time_ms=100,  # Simulated time
                token_count=None,
                detected_intent=IntentType.GENERAL_SPORTS_QUERY,
                intent_confidence=0.8,
                function_calls_made=[],
                suggested_actions=[]
            )
            
            # Small delay for streaming effect
            await asyncio.sleep(0.1)
    
    async def clear_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ):
        """Clear conversation history for a user."""
        if session_id:
            # Clear specific session
            if session_id in self.sessions:
                del self.sessions[session_id]
            if session_id in self.memories:
                del self.memories[session_id]
        else:
            # Clear all sessions for user
            sessions_to_remove = []
            for sid, conversation in self.sessions.items():
                if conversation.context.user_id == user_id:
                    sessions_to_remove.append(sid)
            
            for sid in sessions_to_remove:
                if sid in self.sessions:
                    del self.sessions[sid]
                if sid in self.memories:
                    del self.memories[sid]
        
        logger.info(f"Cleared conversation history for user {user_id}, session {session_id}")

    async def cleanup(self):
        """Cleanup resources."""
        self.sessions.clear()
        self.memories.clear()
        await self.llm_service.cleanup()

    async def process_message_with_streaming(
        self, 
        request: ChatRequest, 
        streaming_callback
    ) -> None:
        """
        Process a chat message with WebSocket streaming.
        
        This method integrates with WebSocket streaming callbacks to provide
        real-time response generation for connected clients.
        
        Args:
            request: Chat request containing user message
            streaming_callback: WebSocket streaming callback instance
        """
        start_time = datetime.now()
        
        try:
            # Get or create conversation
            conversation = await self.start_conversation(
                user_id=request.user_id,
                session_id=request.session_id
            )
            history = self.memories[conversation.id]
            
            # Classify user intent first
            intent_result = await self.llm_service.classify_intent(request.message)
            logger.debug(f"Classified intent: {intent_result.intent} (confidence: {intent_result.confidence})")
            
            # Create user message
            user_msg = ChatMessage(
                role=MessageRole.USER,
                content=request.message,
                session_id=conversation.id,
                user_id=request.user_id,
                detected_intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                response_time_ms=None,
                token_count=None,
                function_calls=None
            )
            
            # Add to conversation and memory
            conversation.add_message(user_msg)
            history.add_user_message(request.message)
            
            # Generate streaming response with callback
            await self._generate_streaming_response(
                conversation=conversation,
                intent_result=intent_result,
                streaming_callback=streaming_callback,
                user_context={}
            )
            
        except Exception as e:
            logger.error(f"Error in streaming message processing: {str(e)}", exc_info=True)
            # The streaming callback should handle error notification
            raise
    
    async def _generate_streaming_response(
        self,
        conversation: Conversation,
        intent_result: IntentClassificationResult,
        streaming_callback,
        user_context: Optional[Dict[str, Any]] = None
    ):
        """
        Generate streaming response using the provided callback.
        
        This method integrates the LLM service with WebSocket streaming
        to provide real-time response generation.
        """
        user_message = conversation.last_user_message
        if not user_message:
            raise ValueError("No user message found in conversation")
            
        conversation_history = self._convert_to_langchain_messages(conversation)
        
        # Build enhanced context
        enhanced_context = {
            "intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "entities": intent_result.entities,
            "conversation_context": conversation.context.model_dump(),
        }
        
        if user_context:
            enhanced_context.update(user_context)
        
        # Generate response with streaming callback
        # Note: For now, we'll use the standard generate_response and implement
        # streaming at the WebSocket level. A future enhancement would be to 
        # modify the LLM service to accept streaming callbacks directly.
        response_content = await self.llm_service.generate_response(
            user_message=user_message.content,
            conversation_history=conversation_history,
            user_context=enhanced_context,
            stream=True
        )
        
        # Create assistant message for conversation history
        response_time_ms = int((datetime.now() - datetime.now()).total_seconds() * 1000)  # Will be updated by callback
        assistant_msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response_content,
            session_id=conversation.id,
            user_id=conversation.context.user_id,
            detected_intent=None,
            intent_confidence=None,
            response_time_ms=response_time_ms,
            token_count=None,
            function_calls=None
        )
        
        # Add to conversation and memory
        conversation.add_message(assistant_msg)
        history = self.memories[conversation.id]
        history.add_ai_message(response_content)


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get global conversation manager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager


async def cleanup_conversation_manager():
    """Cleanup function to be called on app shutdown."""
    global _conversation_manager
    if _conversation_manager:
        await _conversation_manager.cleanup()
        _conversation_manager = None