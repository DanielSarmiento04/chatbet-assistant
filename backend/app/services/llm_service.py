"""
Enhanced LLM service with Gemini AI integration.

This is the heart of our conversational AI system. I'm using Google's Gemini
because it offers excellent conversation capabilities and the free tier makes
it accessible for this assessment.

Key features:
- Structured prompts for sports betting domain expertise
- Function calling for API integration
- Context management and token optimization
- Response streaming capabilities
- Performance monitoring and error handling
"""

import json
import logging
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from datetime import datetime
import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.logging import get_logger, log_function_call
from ..models.conversation import IntentType, IntentClassificationResult
from ..models.api_models import Tournament, MatchFixture, MatchOdds
from ..services.chatbet_api import get_api_client

logger = get_logger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class TokenLimitError(LLMError):
    """Token limit exceeded error."""
    pass


class FunctionCallError(LLMError):
    """Function calling error."""
    pass


class IntentClassifier(BaseModel):
    """Intent classification output model."""
    intent: IntentType = Field(..., description="The detected intent category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the intent")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    reasoning: str = Field(..., description="Brief explanation of why this intent was chosen")


class ChatBetLLMService:
    """
    Enhanced LLM service for ChatBet conversational AI.
    
    This service handles all LLM interactions, including intent classification,
    response generation, and function calling for API integration.
    
    I chose Gemini over OpenAI because:
    1. Free tier availability (as mentioned in requirements)
    2. Excellent conversation capabilities 
    3. Good function calling support
    4. Fast response times for real-time chat
    """
    
    def __init__(self):
        # Initialize Gemini model with optimized settings
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=settings.gemini_temperature,
            max_tokens=settings.gemini_max_tokens,
            timeout=settings.gemini_timeout,
            max_retries=2,
            # Enable function calling
            convert_system_message_to_human=False
        )
        
        # Initialize API client for function calls
        self._api_client = None
        
        # Performance tracking
        self._total_requests = 0
        self._total_tokens = 0
        self._avg_response_time = 0.0
        
        # Setup intent classification
        self._setup_intent_classifier()
        
        # Setup function calling tools
        self._setup_tools()
    
    def _setup_intent_classifier(self):
        """Setup intent classification chain."""
        intent_system_prompt = """You are an expert intent classifier for a sports betting conversational AI.

Your job is to analyze user messages and classify them into one of these categories:

MATCH_SCHEDULE_QUERY: User asking about match schedules, when teams play, fixtures
- Examples: "When does Barcelona play?", "What matches are today?", "Who plays tomorrow?"

ODDS_INFORMATION_QUERY: User asking about betting odds, prices, or probabilities  
- Examples: "What are the odds for Barcelona vs Real?", "How much does a draw pay?"

BETTING_RECOMMENDATION: User asking for betting advice or recommendations
- Examples: "What should I bet on?", "Which team should I back?", "Best bet today?"

TEAM_COMPARISON: User comparing teams or asking about team strengths
- Examples: "Who's better, Barcelona or Real?", "Compare these teams"

USER_BALANCE_QUERY: User asking about their account balance or money
- Examples: "How much money do I have?", "What's my balance?", "Can I afford this bet?"

BET_SIMULATION: User wants to place a bet or simulate betting
- Examples: "I want to bet $50 on Barcelona", "Place a bet for me"

GENERAL_SPORTS_QUERY: General sports questions not related to betting
- Examples: "Tell me about football", "Who won the World Cup?"

GREETING: General greetings and conversation starters
- Examples: "Hello", "Hi there", "Good morning"

HELP_REQUEST: User asking for help or instructions
- Examples: "Help me", "How does this work?", "What can you do?"

UNCLEAR: Message is unclear or doesn't fit other categories
- Examples: Incomplete sentences, unclear context

Analyze the user's message and respond with:
1. The most likely intent
2. Confidence score (0.0 to 1.0)
3. Any relevant entities extracted (team names, dates, amounts, etc.)
4. Brief reasoning for your classification

Be accurate and confident in your classifications. Consider context and user intent carefully."""

        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", intent_system_prompt),
            ("human", "Classify this message: '{message}'")
        ])
        
        self.intent_parser = PydanticOutputParser(pydantic_object=IntentClassifier)
        
        self.intent_chain = (
            self.intent_prompt 
            | self.llm.with_structured_output(IntentClassifier)
        )
    
    def _setup_tools(self):
        """Setup LangChain tools for function calling."""
        
        @tool
        async def get_tournaments() -> List[Dict[str, Any]]:
            """Get list of available tournaments and competitions."""
            try:
                api_client = await get_api_client()
                tournaments = await api_client.get_tournaments()
                return [t.model_dump() for t in tournaments[:10]]  # Limit to prevent token overflow
            except Exception as e:
                logger.error(f"Error getting tournaments: {e}")
                return []
        
        @tool
        async def get_fixtures(tournament_id: Optional[str] = None, days_ahead: int = 7) -> List[Dict[str, Any]]:
            """
            Get upcoming match fixtures.
            
            Args:
                tournament_id: Optional tournament ID to filter by
                days_ahead: Number of days ahead to look for matches (default 7)
            """
            try:
                api_client = await get_api_client()
                end_date = datetime.now().replace(hour=23, minute=59, second=59)
                
                fixtures = await api_client.get_fixtures(
                    tournament_id=tournament_id,
                    date_from=datetime.now(),
                    date_to=end_date
                )
                
                # Sort by date and limit results
                fixtures.sort(key=lambda x: x.scheduled_time)
                return [f.model_dump() for f in fixtures[:15]]  # Limit to prevent token overflow
                
            except Exception as e:
                logger.error(f"Error getting fixtures: {e}")
                return []
        
        @tool
        async def get_odds(match_id: Optional[str] = None) -> List[Dict[str, Any]]:
            """
            Get betting odds for matches.
            
            Args:
                match_id: Optional specific match ID to get odds for
            """
            try:
                api_client = await get_api_client()
                odds = await api_client.get_odds(match_id=match_id)
                
                # Limit results and simplify for LLM consumption
                simplified_odds = []
                for odd in odds[:10]:  # Limit matches
                    match_odds = {
                        "match_id": odd.match_id,
                        "markets": []
                    }
                    
                    for market in odd.markets[:3]:  # Limit markets per match
                        market_data = {
                            "market_name": market.name,
                            "bet_type": market.bet_type,
                            "outcomes": [
                                {"name": outcome.name, "odds": float(outcome.odds)}
                                for outcome in market.outcomes
                            ]
                        }
                        match_odds["markets"].append(market_data)
                    
                    simplified_odds.append(match_odds)
                
                return simplified_odds
                
            except Exception as e:
                logger.error(f"Error getting odds: {e}")
                return []
        
        @tool
        async def search_team_matches(team_name: str) -> List[Dict[str, Any]]:
            """
            Search for upcoming matches for a specific team.
            
            Args:
                team_name: Name of the team to search for
            """
            try:
                api_client = await get_api_client()
                fixtures = await api_client.get_fixtures()
                
                # Simple team name matching (case-insensitive)
                team_matches = []
                for fixture in fixtures:
                    if (team_name.lower() in fixture.home_team.name.lower() or 
                        team_name.lower() in fixture.away_team.name.lower()):
                        team_matches.append(fixture.model_dump())
                
                # Sort by date and limit
                team_matches.sort(key=lambda x: x["scheduled_time"])
                return team_matches[:10]
                
            except Exception as e:
                logger.error(f"Error searching team matches: {e}")
                return []
        
        self.tools = [get_tournaments, get_fixtures, get_odds, search_team_matches]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
    
    @log_function_call()
    async def classify_intent(self, message: str) -> IntentClassificationResult:
        """
        Classify user intent from message.
        
        This is crucial for routing the conversation to the right logic
        and ensuring we provide relevant responses.
        """
        start_time = datetime.now()
        
        try:
            result = await self.intent_chain.ainvoke({"message": message})
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(f"Intent classified in {response_time:.2f}ms: {result.intent}")
            
            return IntentClassificationResult(
                intent=result.intent,
                confidence=result.confidence,
                entities=result.entities,
                alternatives=[]  # Could be enhanced with alternative intents
            )
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            # Return fallback classification
            return IntentClassificationResult(
                intent=IntentType.UNCLEAR,
                confidence=0.0,
                entities={},
                alternatives=[]
            )
    
    @log_function_call()
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[BaseMessage],
        user_context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> str:
        """
        Generate conversational response using Gemini.
        
        This is the main response generation method that takes user input
        and conversation history to generate contextually appropriate responses.
        """
        start_time = datetime.now()
        
        try:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(user_context)
            
            # Prepare messages
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history (limited to prevent token overflow)
            recent_history = conversation_history[-settings.max_conversation_history:]
            messages.extend(recent_history)
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))
            
            if stream:
                return await self._generate_streaming_response(messages)
            else:
                # Generate response with tool calling
                response = await self.llm_with_tools.ainvoke(messages)
                
                # Handle tool calls if present
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    response = await self._handle_tool_calls(response, messages)
                
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                self._update_performance_metrics(response_time, len(response.content))
                
                return response.content
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
    
    async def _generate_streaming_response(self, messages: List[BaseMessage]) -> AsyncGenerator[str, None]:
        """Generate streaming response chunks."""
        try:
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield "I apologize, but I'm having trouble with the streaming response."
    
    async def _handle_tool_calls(self, response, messages: List[BaseMessage]) -> AIMessage:
        """Handle function/tool calls from the LLM."""
        try:
            # Execute tool calls
            tool_results = []
            
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # Find and execute the tool
                for tool in self.tools:
                    if tool.name == tool_name:
                        result = await tool.ainvoke(tool_args)
                        tool_results.append({
                            "tool_call_id": tool_call["id"],
                            "tool_name": tool_name,
                            "result": result
                        })
                        break
            
            # Create a follow-up message with tool results
            if tool_results:
                tool_message = f"Based on the data I retrieved:\n{json.dumps(tool_results, indent=2)}\n\nNow let me provide you with a helpful response:"
                
                # Add tool results to conversation and get final response
                messages.append(response)
                messages.append(HumanMessage(content=tool_message))
                
                final_response = await self.llm.ainvoke(messages)
                return final_response
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling tool calls: {e}")
            return AIMessage(content="I encountered an issue while retrieving the latest information. Let me help you with what I know.")
    
    def _build_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build comprehensive system prompt for sports betting expertise.
        
        This prompt establishes the AI's personality, knowledge domain,
        and behavioral guidelines for sports betting conversations.
        """
        base_prompt = """You are ChatBet Assistant, an expert conversational AI specializing in sports betting and match analysis.

PERSONALITY & TONE:
- Friendly, knowledgeable, and helpful
- Use a conversational tone without excessive formality
- Be enthusiastic about sports while maintaining professionalism
- Always prioritize responsible gambling

CORE EXPERTISE:
- Sports betting odds analysis and interpretation
- Match predictions and team comparisons
- Tournament and fixture information
- Betting strategy and risk management
- Sports knowledge across major leagues and competitions

CAPABILITIES:
- Access real-time sports data and betting odds
- Provide betting recommendations with risk analysis
- Explain betting concepts and strategies
- Help users understand odds and probabilities
- Simulate bet placements and calculations

IMPORTANT GUIDELINES:
1. Always promote responsible gambling
2. Never guarantee betting outcomes
3. Clearly explain risks and probabilities
4. Provide balanced analysis, not just positive predictions
5. Suggest appropriate stake sizes relative to bankroll
6. Warn about high-risk bets appropriately

RESPONSE STYLE:
- Keep responses concise but informative
- Use bullet points for multiple pieces of information
- Include specific numbers (odds, dates, times) when available
- Ask clarifying questions when user intent is unclear
- Provide actionable insights, not just raw data

WHEN USING TOOLS:
- Use get_tournaments() for tournament/league information
- Use get_fixtures() for match schedules and upcoming games
- Use get_odds() for current betting odds and markets
- Use search_team_matches() when user asks about specific teams

Remember: You're helping users make informed betting decisions, not just providing information."""

        # Add user-specific context if available
        if user_context:
            context_additions = []
            
            if user_context.get("preferred_teams"):
                context_additions.append(f"User's favorite teams: {', '.join(user_context['preferred_teams'])}")
            
            if user_context.get("timezone"):
                context_additions.append(f"User timezone: {user_context['timezone']}")
            
            if user_context.get("is_authenticated"):
                context_additions.append("User is authenticated and can place bets")
            
            if context_additions:
                base_prompt += f"\n\nUSER CONTEXT:\n" + "\n".join(context_additions)
        
        return base_prompt
    
    def _update_performance_metrics(self, response_time_ms: float, token_count: int):
        """Update performance tracking metrics."""
        self._total_requests += 1
        self._total_tokens += token_count
        
        # Simple moving average for response time
        self._avg_response_time = (
            (self._avg_response_time * (self._total_requests - 1) + response_time_ms) 
            / self._total_requests
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get LLM performance statistics."""
        return {
            "total_requests": self._total_requests,
            "total_tokens_used": self._total_tokens,
            "average_response_time_ms": round(self._avg_response_time, 2),
            "average_tokens_per_request": (
                round(self._total_tokens / self._total_requests, 2) 
                if self._total_requests > 0 else 0
            )
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        if self._api_client:
            await self._api_client.close()


# Global LLM service instance
_llm_service: Optional[ChatBetLLMService] = None


def get_llm_service() -> ChatBetLLMService:
    """Get global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = ChatBetLLMService()
    return _llm_service


async def cleanup_llm_service():
    """Cleanup function to be called on app shutdown."""
    global _llm_service
    if _llm_service:
        await _llm_service.cleanup()
        _llm_service = None