"""
Sports data streaming service for real-time updates.

This module provides live sports data streaming capabilities,
including odds changes, match events, and fixture updates
broadcasted to connected WebSocket clients.
"""

import asyncio
import json
import logging
from typing import Dict, Set, List, Optional, Any, Literal
from datetime import datetime, timedelta
from collections import defaultdict

from ..core.logging import get_logger
from ..models.websocket_models import (
    WSSportsUpdate, WSOddsUpdate, WSMatchUpdate, SportsUpdateType
)
from ..services.websocket_manager import WebSocketConnectionManager
from ..services.chatbet_api import get_api_client

logger = get_logger(__name__)


class SportsDataStreamer:
    """
    Live sports data streaming service.
    
    This service monitors sports APIs for changes and broadcasts
    updates to connected WebSocket clients in real-time.
    """
    
    def __init__(self, websocket_manager: WebSocketConnectionManager):
        self.websocket_manager = websocket_manager
        self.api_client = None
        
        # Streaming state
        self.is_streaming = False
        self.streaming_tasks: Set[asyncio.Task] = set()
        
        # Data caching for change detection
        self.cached_odds: Dict[str, Any] = {}
        self.cached_matches: Dict[str, Any] = {}
        self.cached_fixtures: Dict[str, Any] = {}
        
        # Subscription tracking
        self.subscribed_sessions: Dict[str, Set[str]] = defaultdict(set)  # session_id -> competition_ids
        self.competition_subscribers: Dict[str, Set[str]] = defaultdict(set)  # competition_id -> session_ids
        
        # Update intervals (in seconds)
        self.odds_update_interval = 30
        self.fixture_update_interval = 300  # 5 minutes
        self.match_event_interval = 10  # For live matches
        
        # Performance tracking
        self.total_updates_sent = 0
        self.last_update_time = None
    
    async def initialize(self):
        """Initialize the sports data streamer."""
        try:
            self.api_client = await get_api_client()
            logger.info("Sports data streamer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize sports data streamer: {e}")
            raise
    
    async def start_streaming(self):
        """Start background sports data streaming."""
        if self.is_streaming:
            logger.warning("Sports data streaming already active")
            return
        
        self.is_streaming = True
        logger.info("Starting sports data streaming")
        
        # Start background streaming tasks
        tasks = [
            asyncio.create_task(self._stream_odds_updates()),
            asyncio.create_task(self._stream_fixture_updates()),
            asyncio.create_task(self._stream_match_events()),
            asyncio.create_task(self._cleanup_inactive_subscriptions())
        ]
        
        for task in tasks:
            self.streaming_tasks.add(task)
            task.add_done_callback(self.streaming_tasks.discard)
        
        logger.info(f"Started {len(tasks)} sports data streaming tasks")
    
    async def stop_streaming(self):
        """Stop all sports data streaming."""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        logger.info("Stopping sports data streaming")
        
        # Cancel all streaming tasks
        for task in self.streaming_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.streaming_tasks:
            await asyncio.gather(*self.streaming_tasks, return_exceptions=True)
        
        self.streaming_tasks.clear()
        logger.info("Sports data streaming stopped")
    
    async def subscribe_session(self, session_id: str, competition_ids: Optional[List[str]] = None):
        """
        Subscribe a session to sports updates.
        
        Args:
            session_id: Session to subscribe
            competition_ids: Optional list of competition IDs to follow (None for all)
        """
        if competition_ids:
            self.subscribed_sessions[session_id] = set(competition_ids)
            for comp_id in competition_ids:
                self.competition_subscribers[comp_id].add(session_id)
        else:
            # Subscribe to all competitions
            self.subscribed_sessions[session_id] = set()
        
        logger.info(
            f"Session {session_id} subscribed to sports updates",
            extra={
                "session_id": session_id,
                "competition_count": len(competition_ids) if competition_ids else "all"
            }
        )
    
    async def unsubscribe_session(self, session_id: str):
        """
        Unsubscribe a session from sports updates.
        
        Args:
            session_id: Session to unsubscribe
        """
        # Remove from subscribed sessions
        competition_ids = self.subscribed_sessions.pop(session_id, set())
        
        # Remove from competition subscribers
        for comp_id in competition_ids:
            self.competition_subscribers[comp_id].discard(session_id)
            if not self.competition_subscribers[comp_id]:
                del self.competition_subscribers[comp_id]
        
        logger.info(f"Session {session_id} unsubscribed from sports updates")
    
    async def _stream_odds_updates(self):
        """Background task to stream odds changes."""
        logger.info("Starting odds updates streaming")
        
        while self.is_streaming:
            try:
                if not self.api_client:
                    logger.warning("API client not initialized, skipping odds update")
                    await asyncio.sleep(self.odds_update_interval)
                    continue
                
                # For now, simulate odds data since we need specific parameters
                # In production, you'd fetch from subscribed competitions
                await self._simulate_odds_update()
                
                self.last_update_time = datetime.utcnow()
                
                # Sleep until next update
                await asyncio.sleep(self.odds_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in odds updates streaming: {e}")
                await asyncio.sleep(60)  # Wait before retrying
        
        logger.info("Odds updates streaming stopped")
    
    async def _stream_fixture_updates(self):
        """Background task to stream fixture changes."""
        logger.info("Starting fixture updates streaming")
        
        while self.is_streaming:
            try:
                if not self.api_client:
                    logger.warning("API client not initialized, skipping fixture update")
                    await asyncio.sleep(self.fixture_update_interval)
                    continue
                
                # For now, simulate fixture updates
                # In production, you'd call the API with specific parameters
                await self._simulate_fixture_update()
                
                # Sleep until next update
                await asyncio.sleep(self.fixture_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in fixture updates streaming: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
        
        logger.info("Fixture updates streaming stopped")
    
    async def _stream_match_events(self):
        """Background task to stream live match events."""
        logger.info("Starting match events streaming")
        
        while self.is_streaming:
            try:
                # For now, this is a placeholder for live match events
                # In a real implementation, this would connect to a live sports feed
                
                # Check for any live matches and simulate some events
                await self._check_live_matches()
                
                # Sleep until next check
                await asyncio.sleep(self.match_event_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in match events streaming: {e}")
                await asyncio.sleep(30)
        
        logger.info("Match events streaming stopped")
    
    async def _check_and_broadcast_odds_change(self, odds_data: Any):
        """
        Check for odds changes and broadcast to subscribers.
        
        Args:
            odds_data: Current odds data
        """
        try:
            match_id = odds_data.match_id
            
            # Compare with cached odds
            cached_odds = self.cached_odds.get(match_id)
            
            if cached_odds:
                # Check for significant changes
                changes_detected = self._detect_odds_changes(cached_odds, odds_data)
                
                if changes_detected:
                    # Broadcast odds update
                    await self._broadcast_odds_update(odds_data, cached_odds)
            
            # Update cache
            self.cached_odds[match_id] = odds_data.model_dump() if hasattr(odds_data, 'model_dump') else odds_data
            
        except Exception as e:
            logger.error(f"Error checking odds changes: {e}")
    
    async def _check_and_broadcast_fixture_change(self, fixture_data: Any):
        """
        Check for fixture changes and broadcast to subscribers.
        
        Args:
            fixture_data: Current fixture data
        """
        try:
            fixture_id = fixture_data.id
            
            # Compare with cached fixture
            if fixture_id not in self.cached_fixtures:
                # New fixture
                await self._broadcast_sports_update(
                    SportsUpdateType.FIXTURE_ADDED,
                    fixture_data.tournament.id if hasattr(fixture_data, 'tournament') else None,
                    fixture_id,
                    {
                        "fixture": fixture_data.model_dump() if hasattr(fixture_data, 'model_dump') else fixture_data,
                        "description": f"New fixture: {getattr(fixture_data, 'homeCompetitor', {}).get('name', 'Home')} vs {getattr(fixture_data, 'awayCompetitor', {}).get('name', 'Away')}"
                    }
                )
            
            # Update cache
            self.cached_fixtures[fixture_id] = fixture_data.model_dump() if hasattr(fixture_data, 'model_dump') else fixture_data
            
        except Exception as e:
            logger.error(f"Error checking fixture changes: {e}")
    
    async def _check_live_matches(self):
        """Check for live match events (placeholder implementation)."""
        try:
            # This is a simplified implementation
            # In reality, you'd connect to a live sports data feed
            
            current_time = datetime.utcnow()
            
            # Simulate some live events occasionally
            if current_time.second % 30 == 0:  # Every 30 seconds
                await self._simulate_match_event()
                
        except Exception as e:
            logger.error(f"Error checking live matches: {e}")
    
    async def _simulate_odds_update(self):
        """Simulate odds update for demo purposes."""
        try:
            # Create simulated odds data
            import random
            
            match_id = f"demo_match_{random.randint(1, 5)}"
            
            # Simulate odds changes
            home_odds = round(random.uniform(1.5, 3.0), 2)
            draw_odds = round(random.uniform(2.8, 4.5), 2)
            away_odds = round(random.uniform(1.8, 4.0), 2)
            
            # Check if we have previous odds
            old_odds = self.cached_odds.get(match_id, {})
            
            # Create new odds data
            new_odds_data = {
                "match_id": match_id,
                "markets": [{
                    "outcomes": [
                        {"odds": home_odds, "name": "Home"},
                        {"odds": draw_odds, "name": "Draw"},
                        {"odds": away_odds, "name": "Away"}
                    ]
                }]
            }
            
            # If we have old odds, check for changes and broadcast
            if old_odds and self._detect_odds_changes(old_odds, type('MockOdds', (), new_odds_data)()):
                await self._broadcast_simulated_odds_update(match_id, old_odds, new_odds_data)
            
            # Update cache
            self.cached_odds[match_id] = new_odds_data
            
        except Exception as e:
            logger.error(f"Error simulating odds update: {e}")
    
    async def _simulate_fixture_update(self):
        """Simulate fixture update for demo purposes."""
        try:
            import random
            from datetime import datetime, timedelta
            
            # Occasionally add a new fixture
            if random.random() < 0.1:  # 10% chance
                fixture_id = f"demo_fixture_{random.randint(100, 999)}"
                
                if fixture_id not in self.cached_fixtures:
                    fixture_data = {
                        "id": fixture_id,
                        "homeCompetitor": {"name": f"Team {random.choice(['A', 'B', 'C', 'D'])}"},
                        "awayCompetitor": {"name": f"Team {random.choice(['X', 'Y', 'Z'])}"},
                        "startTime": (datetime.utcnow() + timedelta(hours=random.randint(1, 48))).isoformat(),
                        "tournament": {"id": "demo_tournament_1"}
                    }
                    
                    # Broadcast new fixture
                    await self._broadcast_sports_update(
                        SportsUpdateType.FIXTURE_ADDED,
                        "demo_tournament_1",
                        fixture_id,
                        {
                            "fixture": fixture_data,
                            "description": f"New fixture: {fixture_data['homeCompetitor']['name']} vs {fixture_data['awayCompetitor']['name']}"
                        }
                    )
                    
                    # Update cache
                    self.cached_fixtures[fixture_id] = fixture_data
            
        except Exception as e:
            logger.error(f"Error simulating fixture update: {e}")
    
    async def _broadcast_simulated_odds_update(self, match_id: str, old_odds: Dict[str, Any], new_odds: Dict[str, Any]):
        """Broadcast simulated odds update."""
        try:
            # Determine movement direction
            old_home_odds = old_odds.get("markets", [{}])[0].get("outcomes", [{}])[0].get("odds", 0)
            new_home_odds = new_odds.get("markets", [{}])[0].get("outcomes", [{}])[0].get("odds", 0)
            
            movement = "up" if new_home_odds > old_home_odds else "down"
            
            odds_update = WSOddsUpdate(
                session_id="sports_system",
                match_id=match_id,
                market_type="1x2",
                old_odds=old_home_odds,
                new_odds={
                    "home": new_odds["markets"][0]["outcomes"][0]["odds"],
                    "draw": new_odds["markets"][0]["outcomes"][1]["odds"],
                    "away": new_odds["markets"][0]["outcomes"][2]["odds"]
                },
                movement_direction=movement
            )
            
            await self._broadcast_to_all_subscribers(odds_update)
            
        except Exception as e:
            logger.error(f"Error broadcasting simulated odds update: {e}")
    
    async def _simulate_match_event(self):
        """Simulate a match event for demo purposes."""
        try:
            import random
            
            events = ["goal", "yellow_card", "substitution", "corner", "free_kick"]
            players = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
            teams = ["Home Team", "Away Team"]
            
            match_update = WSMatchUpdate(
                session_id="sports_system",
                match_id=f"demo_match_{random.randint(1, 3)}",
                event_type=random.choice(events),
                minute=random.randint(1, 90),
                player=random.choice(players),
                team=random.choice(teams),
                description=f"Demo {random.choice(events).replace('_', ' ')} event",
                score={"home": random.randint(0, 3), "away": random.randint(0, 3)}
            )
            
            # Broadcast to all subscribed sessions
            await self._broadcast_to_all_subscribers(match_update)
            
        except Exception as e:
            logger.error(f"Error simulating match event: {e}")
    
    def _detect_odds_changes(self, old_odds: Dict[str, Any], new_odds: Any) -> bool:
        """
        Detect significant changes in odds.
        
        Args:
            old_odds: Previously cached odds
            new_odds: Current odds data
            
        Returns:
            True if significant changes detected
        """
        try:
            # Simple change detection - in reality, you'd want more sophisticated logic
            old_markets = old_odds.get("markets", [])
            new_markets = getattr(new_odds, "markets", [])
            
            if len(old_markets) != len(new_markets):
                return True
            
            # Check for odds value changes
            for i, old_market in enumerate(old_markets):
                if i < len(new_markets):
                    new_market = new_markets[i]
                    
                    old_outcomes = old_market.get("outcomes", [])
                    new_outcomes = getattr(new_market, "outcomes", [])
                    
                    for j, old_outcome in enumerate(old_outcomes):
                        if j < len(new_outcomes):
                            new_outcome = new_outcomes[j]
                            old_odds_value = old_outcome.get("odds", 0)
                            new_odds_value = getattr(new_outcome, "odds", 0)
                            
                            # Check for significant change (>5%)
                            if abs(old_odds_value - new_odds_value) / max(old_odds_value, 1) > 0.05:
                                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting odds changes: {e}")
            return False
    
    async def _broadcast_odds_update(self, new_odds: Any, old_odds: Dict[str, Any]):
        """
        Broadcast odds update to subscribers.
        
        Args:
            new_odds: Current odds data
            old_odds: Previous odds data
        """
        try:
            # Create odds update message
            odds_update = WSOddsUpdate(
                session_id="sports_system",
                match_id=new_odds.match_id,
                market_type="1x2",  # Simplified
                old_odds=old_odds.get("markets", [{}])[0].get("outcomes", [{}])[0].get("odds") if old_odds.get("markets") else None,
                new_odds={
                    "home": getattr(new_odds.markets[0].outcomes[0], "odds", 0) if new_odds.markets else 0,
                    "draw": getattr(new_odds.markets[0].outcomes[1], "odds", 0) if len(new_odds.markets[0].outcomes) > 1 else 0,
                    "away": getattr(new_odds.markets[0].outcomes[2], "odds", 0) if len(new_odds.markets[0].outcomes) > 2 else 0
                },
                movement_direction="up"  # Simplified
            )
            
            await self._broadcast_to_all_subscribers(odds_update)
            
        except Exception as e:
            logger.error(f"Error broadcasting odds update: {e}")
    
    async def _broadcast_sports_update(
        self,
        update_type: SportsUpdateType,
        tournament_id: Optional[str],
        match_id: Optional[str],
        data: Dict[str, Any],
        priority: Literal["low", "medium", "high"] = "medium"
    ):
        """
        Broadcast general sports update.
        
        Args:
            update_type: Type of sports update
            tournament_id: Optional tournament ID
            match_id: Optional match ID
            data: Update data
            priority: Update priority
        """
        try:
            sports_update = WSSportsUpdate(
                session_id="sports_system",
                update_type=update_type,
                tournament_id=tournament_id,
                match_id=match_id,
                data=data,
                priority=priority
            )
            
            await self._broadcast_to_subscribers(sports_update, tournament_id)
            
        except Exception as e:
            logger.error(f"Error broadcasting sports update: {e}")
    
    async def _broadcast_to_subscribers(self, message: Any, competition_id: Optional[str] = None):
        """
        Broadcast message to relevant subscribers.
        
        Args:
            message: Message to broadcast
            competition_id: Optional competition filter
        """
        try:
            target_sessions = set()
            
            if competition_id:
                # Broadcast to subscribers of specific competition
                target_sessions.update(self.competition_subscribers.get(competition_id, set()))
            
            # Also broadcast to sessions subscribed to all competitions
            for session_id, subscriptions in self.subscribed_sessions.items():
                if not subscriptions:  # Empty set means subscribed to all
                    target_sessions.add(session_id)
            
            # Send to each target session
            successful_sends = 0
            for session_id in target_sessions:
                try:
                    if await self.websocket_manager.send_message(session_id, message):
                        successful_sends += 1
                except Exception as e:
                    logger.warning(f"Failed to send sports update to session {session_id}: {e}")
            
            if successful_sends > 0:
                self.total_updates_sent += successful_sends
                logger.debug(f"Sports update sent to {successful_sends} sessions")
            
        except Exception as e:
            logger.error(f"Error broadcasting to subscribers: {e}")
    
    async def _broadcast_to_all_subscribers(self, message: Any):
        """
        Broadcast message to all sports subscribers.
        
        Args:
            message: Message to broadcast
        """
        await self._broadcast_to_subscribers(message)
    
    async def _cleanup_inactive_subscriptions(self):
        """Background task to clean up inactive subscriptions."""
        while self.is_streaming:
            try:
                # Sleep for 5 minutes between cleanup cycles
                await asyncio.sleep(300)
                
                # Get list of active connections
                active_sessions = set(self.websocket_manager.connections.keys())
                
                # Remove subscriptions for inactive sessions
                inactive_sessions = []
                for session_id in self.subscribed_sessions:
                    if session_id not in active_sessions:
                        inactive_sessions.append(session_id)
                
                for session_id in inactive_sessions:
                    await self.unsubscribe_session(session_id)
                
                if inactive_sessions:
                    logger.info(f"Cleaned up {len(inactive_sessions)} inactive sports subscriptions")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in subscription cleanup: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get sports streaming statistics."""
        return {
            "is_streaming": self.is_streaming,
            "active_tasks": len(self.streaming_tasks),
            "subscribed_sessions": len(self.subscribed_sessions),
            "total_competitions": len(self.competition_subscribers),
            "total_updates_sent": self.total_updates_sent,
            "last_update_time": self.last_update_time.isoformat() if self.last_update_time else None,
            "cached_odds_count": len(self.cached_odds),
            "cached_fixtures_count": len(self.cached_fixtures)
        }


# Global sports data streamer instance
_sports_streamer: Optional[SportsDataStreamer] = None


def get_sports_streamer(websocket_manager: WebSocketConnectionManager) -> SportsDataStreamer:
    """Get global sports data streamer instance."""
    global _sports_streamer
    if _sports_streamer is None:
        _sports_streamer = SportsDataStreamer(websocket_manager)
    return _sports_streamer


async def cleanup_sports_streamer():
    """Cleanup function to be called on app shutdown."""
    global _sports_streamer
    if _sports_streamer:
        await _sports_streamer.stop_streaming()
        _sports_streamer = None