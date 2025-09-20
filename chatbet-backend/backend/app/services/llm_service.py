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
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator, Union
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


# Cache for tournament mapping
_tournament_cache: Optional[Dict[str, str]] = None

async def _get_tournament_id_mapping() -> Dict[str, str]:
    """
    Get mapping of tournament names to IDs.
    
    Returns a dictionary mapping lowercase tournament names to their API IDs.
    """
    global _tournament_cache
    
    if _tournament_cache is not None:
        return _tournament_cache
    
    try:
        api_client = await get_api_client()
        all_tournaments = await api_client.get_all_tournaments(with_active_fixtures=True)
        
        mapping = {}
        for sport in all_tournaments:
            for tournament in sport.tournaments:
                name_lower = tournament.name.lower()
                mapping[name_lower] = tournament.tournamentId
                
                # Add common aliases
                if "la liga" in name_lower:
                    mapping["la liga"] = tournament.tournamentId
                    mapping["spanish league"] = tournament.tournamentId
                elif "premier league" in name_lower:
                    mapping["premier league"] = tournament.tournamentId
                    mapping["english league"] = tournament.tournamentId
                elif "bundesliga" in name_lower:
                    mapping["bundesliga"] = tournament.tournamentId
                    mapping["german league"] = tournament.tournamentId
                elif "serie a" in name_lower:
                    mapping["serie a"] = tournament.tournamentId
                    mapping["italian league"] = tournament.tournamentId
                elif "ligue 1" in name_lower:
                    mapping["ligue 1"] = tournament.tournamentId
                    mapping["french league"] = tournament.tournamentId
        
        _tournament_cache = mapping
        logger.info(f"Cached {len(mapping)} tournament mappings")
        return mapping
        
    except Exception as e:
        logger.error(f"Failed to build tournament mapping: {e}")
        return {}


async def _resolve_tournament_id(tournament_input: Optional[str]) -> Optional[str]:
    """
    Resolve tournament input to a valid tournament ID.
    
    Args:
        tournament_input: Could be a tournament ID, name, or None
        
    Returns:
        Valid tournament ID or None
    """
    if not tournament_input:
        return None
    
    # If it's already a numeric ID, return as-is
    if tournament_input.isdigit():
        return tournament_input
    
    # Try to find by name
    mapping = await _get_tournament_id_mapping()
    return mapping.get(tournament_input.lower())


async def _retry_api_call(func, max_retries: int = 2, delay: float = 1.0, *args, **kwargs):
    """
    Internal retry helper for API calls.
    
    This provides retry logic without interfering with LangChain tool schema generation.
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            # Check if result indicates an error
            if isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                if isinstance(first_item, dict) and first_item.get("status") == "error":
                    if attempt < max_retries:
                        logger.warning(f"API call failed on attempt {attempt + 1}, retrying...")
                        await asyncio.sleep(delay * (2 ** attempt))
                        continue
            return result
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"API call failed on attempt {attempt + 1}: {str(e)}, retrying...")
                await asyncio.sleep(delay * (2 ** attempt))
                continue
            else:
                logger.error(f"API call failed after {max_retries + 1} attempts: {str(e)}")
    
    # If we get here, all retries failed
    if last_exception:
        raise last_exception
    # This should never happen, but just in case
    return []


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
            async def _get_tournaments_impl():
                api_client = await get_api_client()
                tournaments = await api_client.get_tournaments()                
                if not tournaments:
                    return [{
                        "status": "no_tournaments", 
                        "message": "No tournaments currently available",
                        "suggestion": "Please try again later"
                    }]
                return [t.model_dump() for t in tournaments[:10]]  # Limit to prevent token overflow
            
            try:
                return await _retry_api_call(_get_tournaments_impl)
            except Exception as e:
                logger.error(f"Error getting tournaments: {e}")
                return [{
                    "status": "error",
                    "message": f"Unable to retrieve tournaments: {str(e)}",
                    "suggestion": "Please try again later"
                }]
        
        @tool
        async def get_fixtures(tournament_id: Optional[str] = None, days_ahead: int = 7) -> List[Dict[str, Any]]:
            """
            Get upcoming match fixtures.
            
            Args:
                tournament_id: Optional tournament ID to filter by (can be name like "La Liga" or ID like "545")
                days_ahead: Number of days ahead to look for matches (default 7)
            """
            async def _get_fixtures_impl():
                api_client = await get_api_client()
                
                # Resolve tournament ID if provided
                resolved_tournament_id = None
                if tournament_id:
                    resolved_tournament_id = await _resolve_tournament_id(tournament_id)
                    if not resolved_tournament_id:
                        return [{
                            "status": "invalid_tournament",
                            "message": f"Tournament '{tournament_id}' not found or not available",
                            "suggestion": "Try using a different tournament name or check available tournaments first"
                        }]
                
                # Get fixtures using the correct API method signature
                fixtures_response = await api_client.get_fixtures(
                    tournament_id=resolved_tournament_id,
                    fixture_type="pre_match",
                    language="en",
                    time_zone="UTC"
                )
                
                # Extract fixtures from response
                fixtures = fixtures_response.fixtures
                
                # Check if we have results
                if not fixtures:
                    return [{
                        "status": "no_fixtures",
                        "message": f"No upcoming fixtures found" + (f" for tournament {tournament_id}" if tournament_id else ""),
                        "suggestion": "Try checking other tournaments or live matches"
                    }]
                
                return [f.model_dump() for f in fixtures[:15]]  # Limit results
            
            try:
                return await _retry_api_call(_get_fixtures_impl)
            except Exception as e:
                logger.error(f"Error getting fixtures: {e}")
                return [{
                    "status": "error",
                    "message": f"Unable to retrieve fixtures: {str(e)}",
                    "suggestion": "Please try again later"
                }]
        
        @tool
        async def get_odds(
            sport_id: str = "1", 
            tournament_id: Optional[str] = None, 
            fixture_id: Optional[str] = None,
            amount: float = 100.0
        ) -> List[Dict[str, Any]]:
            """
            Get betting odds for matches.
            
            Args:
                sport_id: ID of the sport (default: "1" for soccer)
                tournament_id: Optional tournament ID
                fixture_id: Optional specific fixture ID
                amount: Bet amount for odds calculation (default: 100.0)
            """
            try:
                # If no specific fixture is provided, we can't get odds
                # The API requires sport_id, tournament_id, fixture_id, and amount
                if not fixture_id or not tournament_id:
                    logger.warning("Cannot get odds without fixture_id and tournament_id")
                    return [{
                        "status": "missing_info",
                        "message": "To get betting odds, I need a specific match/fixture ID and tournament ID",
                        "suggestion": "Please ask about odds for a specific match from the fixtures list"
                    }]
                
                api_client = await get_api_client()
                
                async def _get_odds_api_call():
                    return await api_client.get_odds(
                        sport_id=sport_id,
                        tournament_id=tournament_id,
                        fixture_id=fixture_id,
                        amount=amount
                    )
                
                # For get_odds, we don't need the complex retry logic since it returns MatchOdds object
                # Just do a simple retry
                odds: Optional[MatchOdds] = None
                last_exception = None
                for attempt in range(3):  # 3 attempts total
                    try:
                        odds = await _get_odds_api_call()
                        break
                    except Exception as e:
                        last_exception = e
                        if attempt < 2:  # Only sleep if we have more attempts
                            await asyncio.sleep(1.0 * (2 ** attempt))
                        continue
                else:
                    # All retries failed
                    if last_exception:
                        raise last_exception
                
                if not odds:
                    return [{
                        "status": "no_odds",
                        "message": f"No betting odds available for fixture {fixture_id}",
                        "suggestion": "This match might not have odds available yet, or betting might be suspended"
                    }]
                
                # Simplify odds data for LLM consumption based on actual MatchOdds structure
                simplified_odds = {
                    "fixture_id": fixture_id,
                    "status": odds.status,
                    "main_market": odds.main_market,
                    "markets": []
                }
                
                # Extract available betting markets from MatchOdds attributes
                available_markets = []
                
                # Check main result market (1X2)
                if odds.result is not None:
                    available_markets.append({
                        "market_name": "Match Result (1X2)",
                        "data": odds.result
                    })
                
                # Check over/under market
                if odds.over_under is not None:
                    available_markets.append({
                        "market_name": "Over/Under",
                        "data": odds.over_under
                    })
                
                # Check both teams to score
                if odds.both_teams_to_score is not None:
                    available_markets.append({
                        "market_name": "Both Teams to Score",
                        "data": odds.both_teams_to_score
                    })
                
                # Check double chance
                if odds.double_chance is not None:
                    available_markets.append({
                        "market_name": "Double Chance",
                        "data": odds.double_chance
                    })
                
                # Check handicap
                if odds.handicap is not None:
                    available_markets.append({
                        "market_name": "Handicap",
                        "data": odds.handicap
                    })
                
                if not available_markets:
                    return [{
                        "status": "no_markets",
                        "message": f"No betting markets available for fixture {fixture_id}",
                        "suggestion": "This match might not have betting markets open yet"
                    }]
                
                # Limit to top 3 markets to prevent token overflow
                simplified_odds["markets"] = available_markets[:3]
                
                return [simplified_odds]
                
            except Exception as e:
                logger.error(f"Error getting odds: {e}")
                return [{
                    "status": "error",
                    "message": f"Unable to retrieve odds: {str(e)}",
                    "suggestion": "Please try again later"
                }]
        
        @tool
        async def search_team_matches(team_name: str) -> List[Dict[str, Any]]:
            """
            Search for upcoming matches for a specific team.
            
            Args:
                team_name: Name of the team to search for
            """
            try:
                api_client = await get_api_client()
                fixtures_response = await api_client.get_fixtures()
                
                # Simple team name matching (case-insensitive)
                team_matches = []
                for fixture in fixtures_response.fixtures:  # Access the fixtures list from the response
                    if (team_name.lower() in fixture.homeCompetitor.name.lower() or 
                        team_name.lower() in fixture.awayCompetitor.name.lower()):
                        team_matches.append(fixture.model_dump())
                
                if not team_matches:
                    return [{
                        "status": "no_matches",
                        "message": f"No upcoming matches found for '{team_name}'",
                        "suggestion": f"The team '{team_name}' might not have upcoming fixtures, or try checking the team name spelling",
                        "total_searched": len(fixtures_response.fixtures)
                    }]
                
                # Sort by date and limit
                team_matches.sort(key=lambda x: x["startTime"])
                return team_matches[:10]
                
            except Exception as e:
                logger.error(f"Error searching team matches: {e}")
                return [{
                    "status": "error",
                    "message": f"Unable to search for '{team_name}' matches: {str(e)}",
                    "suggestion": "Please try again later or check the team name"
                }]
        
        @tool
        async def get_live_matches(tournament_id: Optional[str] = None) -> List[Dict[str, Any]]:
            """
            Get currently live matches as an alternative to upcoming fixtures.
            
            Args:
                tournament_id: Optional tournament ID to filter by (can be name like "La Liga" or ID like "545")
            """
            try:
                api_client = await get_api_client()
                
                # Resolve tournament ID if provided
                resolved_tournament_id = None
                if tournament_id:
                    resolved_tournament_id = await _resolve_tournament_id(tournament_id)
                    if not resolved_tournament_id:
                        return [{
                            "status": "invalid_tournament",
                            "message": f"Tournament '{tournament_id}' not found or not available",
                            "suggestion": "Try using a different tournament name or check available tournaments first"
                        }]
                
                # Get live fixtures using the correct API method signature
                fixtures_response = await api_client.get_fixtures(
                    tournament_id=resolved_tournament_id,
                    fixture_type="live",
                    language="en",
                    time_zone="UTC"
                )
                
                # Extract fixtures from response
                fixtures = fixtures_response.fixtures
                
                # Check if we have results
                if not fixtures:
                    return [{
                        "status": "no_live_matches",
                        "message": f"No live matches currently ongoing for tournament {tournament_id or 'all tournaments'}",
                        "suggestion": "Check back later or try looking for upcoming fixtures",
                        "total_results": fixtures_response.totalResults
                    }]
                
                # Sort by date and limit results
                fixtures_list = [f.model_dump() for f in fixtures[:10]]  # Limit to prevent token overflow
                return fixtures_list
                
            except Exception as e:
                logger.error(f"Error getting live matches: {e}")
                return [{
                    "status": "error",
                    "message": f"Unable to retrieve live matches: {str(e)}",
                    "suggestion": "Please try again later"
                }]
        
        self.tools = [get_tournaments, get_fixtures, get_live_matches, get_odds, search_team_matches]
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
            
            # Ensure result is an IntentClassifier instance
            if not isinstance(result, IntentClassifier):
                logger.warning(f"Unexpected result type from intent chain: {type(result)}")
                # Try to create IntentClassifier from dict if possible
                if isinstance(result, dict):
                    result = IntentClassifier(**result)
                else:
                    raise ValueError(f"Invalid result type: {type(result)}")
            
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
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate conversational response using Gemini.
        
        This is the main response generation method that takes user input
        and conversation history to generate contextually appropriate responses.
        """
        start_time = datetime.now()
        
        try:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(user_context)
            
            # Prepare messages - use List[BaseMessage] type
            messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
            
            # Add conversation history (limited to prevent token overflow)
            recent_history = conversation_history[-settings.max_conversation_history:]
            messages.extend(recent_history)
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))
            
            if stream:
                # Return the async generator for streaming
                return self._generate_streaming_response(messages)
            else:
                # Generate response with tool calling
                response = await self.llm_with_tools.ainvoke(messages)
                
                # Handle tool calls if present
                if hasattr(response, 'tool_calls') and getattr(response, 'tool_calls', None):
                    response = await self._handle_tool_calls(response, messages)
                
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Safely get content
                content = getattr(response, 'content', '')
                if isinstance(content, list):
                    # Join list content into string
                    content = ' '.join(str(item) for item in content if item)
                elif not isinstance(content, str):
                    content = str(content) if content else ''
                
                self._update_performance_metrics(response_time, len(content))
                
                return content
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
    
    async def _generate_streaming_response(self, messages: List[BaseMessage]) -> AsyncGenerator[str, None]:
        """Generate streaming response chunks."""
        try:
            async for chunk in self.llm.astream(messages):
                content = getattr(chunk, 'content', '')
                if content:
                    # Ensure content is a string
                    if isinstance(content, list):
                        # Join list content into string
                        content_str = ' '.join(str(item) for item in content if item)
                    elif isinstance(content, str):
                        content_str = content
                    else:
                        content_str = str(content)
                    
                    if content_str.strip():  # Only yield non-empty content
                        yield content_str
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield "I apologize, but I'm having trouble with the streaming response."
    
    async def _handle_tool_calls(self, response, messages: List[BaseMessage]) -> AIMessage:
        """Handle function/tool calls from the LLM."""
        try:
            # Execute tool calls
            tool_results = []
            failed_tools = []
            
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # Find and execute the tool
                for tool in self.tools:
                    if tool.name == tool_name:
                        try:
                            result = await tool.ainvoke(tool_args)
                            # Check if result indicates an error or no data
                            if isinstance(result, list) and len(result) > 0:
                                first_item = result[0]
                                if isinstance(first_item, dict):
                                    status = first_item.get("status")
                                    if status == "error":
                                        failed_tools.append({
                                            "tool_name": tool_name,
                                            "error": first_item.get("message", "Unknown error"),
                                            "suggestion": first_item.get("suggestion", "Please try again")
                                        })
                                    elif status == "no_tournaments":
                                        # This is OK, not an error
                                        pass
                            
                            tool_results.append({
                                "tool_call_id": tool_call["id"],
                                "tool_name": tool_name,
                                "result": result
                            })
                        except Exception as e:
                            logger.error(f"Tool {tool_name} failed: {str(e)}")
                            failed_tools.append({
                                "tool_name": tool_name,
                                "error": str(e),
                                "suggestion": "Please try again later"
                            })
                        break
            
            # Create a follow-up message with tool results and error context
            if tool_results:
                tool_message = f"Based on the data I retrieved:\n{json.dumps(tool_results, indent=2)}"
                
                # Add context about failed tools if any
                if failed_tools:
                    tool_message += f"\n\nNote: Some data sources had issues:\n{json.dumps(failed_tools, indent=2)}"
                
                tool_message += "\n\nNow let me provide you with a helpful response:"
                
                # Add tool results to conversation and get final response
                messages.append(response)
                messages.append(HumanMessage(content=tool_message))
                
                final_response = await self.llm.ainvoke(messages)
                # Ensure we return an AIMessage
                if isinstance(final_response, AIMessage):
                    return final_response
                else:
                    # Convert to AIMessage if needed
                    content = getattr(final_response, 'content', '')
                    if isinstance(content, list):
                        content = ' '.join(str(item) for item in content if item)
                    return AIMessage(content=str(content))
            
            # Convert response to AIMessage if needed
            if isinstance(response, AIMessage):
                return response
            else:
                content = getattr(response, 'content', '')
                if isinstance(content, list):
                    content = ' '.join(str(item) for item in content if item)
                return AIMessage(content=str(content))
            
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
- Use get_live_matches() for currently ongoing matches
- Use get_odds() for current betting odds and markets
- Use search_team_matches() when user asks about specific teams

HANDLING EMPTY OR ERROR RESPONSES:
- If tools return empty data or no results, provide helpful explanations
- Suggest alternative queries or different tournaments
- Explain why data might not be available (off-season, no upcoming matches, etc.)
- Always maintain a helpful tone even when data is unavailable
- Offer related information or suggestions for what the user could try instead

EXAMPLE RESPONSES FOR COMMON SCENARIOS:
- No fixtures available: "I don't see any upcoming fixtures for [tournament] right now. This could be because it's the off-season or between match rounds. Would you like me to check other tournaments or show you what tournaments are currently active?"
- No odds available: "Betting odds aren't available for this match yet. This usually happens when matches are far in the future or betting hasn't opened. Let me help you find matches with available odds."
- Team not found: "I couldn't find any upcoming matches for [team]. The team name might need to be more specific, or they might not have scheduled matches soon. Can you try the full team name or ask about a different team?"

Remember: You're helping users make informed betting decisions, not just providing information. Always be helpful even when data is limited."""

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
        # Note: API client cleanup is handled by the get_api_client() function
        # No resources to cleanup in LLM service itself
        pass


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