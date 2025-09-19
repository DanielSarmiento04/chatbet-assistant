"""
WebSocket connection manager for real-time communication.

This module provides a comprehensive WebSocket connection manager that handles
multiple concurrent chat sessions, message routing, and connection lifecycle
management for the ChatBet real-time chat system.
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Set, List, Any, Callable
from datetime import datetime, timedelta
from uuid import uuid4
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..core.logging import get_logger
from ..models.websocket_models import (
    WSMessage, WSBaseMessage, WSUserMessage, WSBotResponse, WSError,
    WSTypingIndicator, WSConnectionAck, WSPing, WSPong, WSStreamingResponse,
    WSStreamingStart, WSStreamingEnd, WSSportsUpdate, WSSessionCreated,
    WSSessionEnded, WebSocketMessageType, parse_websocket_message,
    create_error_message, create_typing_indicator
)

logger = get_logger(__name__)


class ConnectionInfo:
    """Information about a WebSocket connection."""
    
    def __init__(self, websocket: WebSocket, session_id: str, user_id: Optional[str] = None):
        self.websocket = websocket
        self.session_id = session_id
        self.user_id = user_id
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.message_count = 0
        self.is_authenticated = user_id is not None
        self.client_info: Dict[str, Any] = {}
        
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
        
    def increment_message_count(self):
        """Increment message counter."""
        self.message_count += 1
        
    @property
    def connection_duration(self) -> timedelta:
        """Get connection duration."""
        return datetime.utcnow() - self.connected_at
        
    @property
    def is_idle(self) -> bool:
        """Check if connection is idle (no activity for 5 minutes)."""
        return datetime.utcnow() - self.last_activity > timedelta(minutes=5)


class WebSocketConnectionManager:
    """
    Multi-session WebSocket connection manager.
    
    This class manages WebSocket connections for real-time chat functionality,
    handling connection lifecycle, message routing, session management, and
    broadcasting capabilities for the ChatBet assistant.
    """
    
    def __init__(self):
        # Active connections by session ID
        self.connections: Dict[str, ConnectionInfo] = {}
        
        # User to sessions mapping for multi-device support
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Connection statistics
        self.total_connections = 0
        self.total_messages = 0
        self.started_at = datetime.utcnow()
        
        # Event handlers
        self.message_handlers: Dict[WebSocketMessageType, List[Callable]] = defaultdict(list)
        
        # Start background cleanup task
        self._start_cleanup_task()
    
    async def connect(
        self, 
        websocket: WebSocket, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket instance
            session_id: Optional session ID (generates new if None)
            user_id: Optional user ID for authenticated sessions
            
        Returns:
            Session ID for the connection
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid4())
        
        try:
            # Accept the WebSocket connection
            await websocket.accept()
            
            # Create connection info
            connection_info = ConnectionInfo(websocket, session_id, user_id)
            
            # Store connection
            self.connections[session_id] = connection_info
            
            # Update user sessions mapping
            if user_id:
                self.user_sessions[user_id].add(session_id)
            
            # Update statistics
            self.total_connections += 1
            
            logger.info(
                f"WebSocket connection established",
                extra={
                    "session_id": session_id,
                    "user_id": user_id,
                    "total_connections": len(self.connections)
                }
            )
            
            # Send connection acknowledgment
            await self.send_message(
                session_id,
                WSConnectionAck(
                    session_id=session_id,
                    client_id=session_id,
                    supported_features=[
                        "streaming_responses",
                        "typing_indicators", 
                        "sports_updates",
                        "ping_pong"
                    ]
                )
            )
            
            # Send session created event
            await self.send_message(
                session_id,
                WSSessionCreated(
                    session_id=session_id,
                    user_id=user_id
                )
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error establishing WebSocket connection: {e}")
            raise
    
    async def disconnect(self, session_id: str, reason: str = "client_disconnect"):
        """
        Handle client disconnection.
        
        Args:
            session_id: Session to disconnect
            reason: Reason for disconnection
        """
        if session_id not in self.connections:
            return
        
        connection_info = self.connections[session_id]
        
        try:
            # Send session ended message if connection is still active
            if not connection_info.websocket.client_state.DISCONNECTED:
                await self.send_message(
                    session_id,
                    WSSessionEnded(
                        session_id=session_id,
                        reason=reason,
                        duration_seconds=int(connection_info.connection_duration.total_seconds()),
                        message_count=connection_info.message_count
                    )
                )
        except:
            # Connection might already be closed
            pass
        
        # Remove from user sessions mapping
        if connection_info.user_id:
            user_sessions = self.user_sessions.get(connection_info.user_id, set())
            user_sessions.discard(session_id)
            if not user_sessions:
                # Remove user entry if no more sessions
                self.user_sessions.pop(connection_info.user_id, None)
        
        # Remove connection
        del self.connections[session_id]
        
        logger.info(
            f"WebSocket connection closed",
            extra={
                "session_id": session_id,
                "reason": reason,
                "duration_seconds": int(connection_info.connection_duration.total_seconds()),
                "message_count": connection_info.message_count,
                "remaining_connections": len(self.connections)
            }
        )
    
    async def send_message(self, session_id: str, message: WSMessage) -> bool:
        """
        Send message to a specific session.
        
        Args:
            session_id: Target session ID
            message: Message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if session_id not in self.connections:
            logger.warning(f"Attempted to send message to non-existent session: {session_id}")
            return False
        
        connection_info = self.connections[session_id]
        
        try:
            # Serialize message to JSON
            message_data = message.model_dump(mode='json')
            await connection_info.websocket.send_text(json.dumps(message_data))
            
            # Update connection activity
            connection_info.update_activity()
            
            logger.debug(
                f"Message sent to session {session_id}",
                extra={
                    "message_type": message_data.get("type"),
                    "session_id": session_id
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to session {session_id}: {e}")
            # Connection might be dead, schedule for cleanup
            await self.disconnect(session_id, "send_error")
            return False
    
    async def broadcast_to_user(self, user_id: str, message: WSMessage) -> int:
        """
        Broadcast message to all sessions of a user.
        
        Args:
            user_id: Target user ID
            message: Message to broadcast
            
        Returns:
            Number of sessions that received the message
        """
        user_sessions = self.user_sessions.get(user_id, set())
        sent_count = 0
        
        for session_id in list(user_sessions):  # Create copy to avoid modification during iteration
            if await self.send_message(session_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, message: WSMessage) -> int:
        """
        Broadcast message to all connected sessions.
        
        Args:
            message: Message to broadcast
            
        Returns:
            Number of sessions that received the message
        """
        sent_count = 0
        
        for session_id in list(self.connections.keys()):
            if await self.send_message(session_id, message):
                sent_count += 1
        
        return sent_count
    
    async def handle_user_message(self, session_id: str, message_data: dict) -> bool:
        """
        Handle incoming user message.
        
        Args:
            session_id: Session ID that sent the message
            message_data: Raw message data
            
        Returns:
            True if message was handled successfully
        """
        if session_id not in self.connections:
            return False
        
        connection_info = self.connections[session_id]
        
        try:
            # Parse the message
            message = parse_websocket_message(message_data)
            
            # Update connection activity and stats
            connection_info.update_activity()
            connection_info.increment_message_count()
            self.total_messages += 1
            
            # Call registered handlers for this message type
            handlers = self.message_handlers.get(message.type, [])
            for handler in handlers:
                try:
                    await handler(session_id, message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
            
            logger.debug(
                f"User message handled",
                extra={
                    "session_id": session_id,
                    "message_type": message.type,
                    "content_length": len(getattr(message, 'content', ''))
                }
            )
            
            return True
            
        except ValidationError as e:
            logger.warning(f"Invalid message format from session {session_id}: {e}")
            await self.send_error(session_id, "INVALID_MESSAGE_FORMAT", str(e))
            return False
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            await self.send_error(session_id, "MESSAGE_PROCESSING_ERROR", "Failed to process message")
            return False
    
    async def send_typing_indicator(
        self, 
        session_id: str, 
        is_typing: bool, 
        estimated_time: Optional[int] = None
    ):
        """
        Send typing indicator to a session.
        
        Args:
            session_id: Target session
            is_typing: Whether typing is active
            estimated_time: Estimated response time in seconds
        """
        typing_message = create_typing_indicator(session_id, is_typing, estimated_time)
        await self.send_message(session_id, typing_message)
    
    async def send_error(
        self, 
        session_id: str, 
        error_code: str, 
        error_message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Send error message to a session.
        
        Args:
            session_id: Target session
            error_code: Error code identifier
            error_message: Human-readable error message
            details: Optional additional error details
        """
        error_msg = create_error_message(session_id, error_code, error_message, details)
        await self.send_message(session_id, error_msg)
    
    async def start_streaming_response(
        self, 
        session_id: str, 
        estimated_tokens: Optional[int] = None
    ):
        """
        Signal start of streaming response.
        
        Args:
            session_id: Target session
            estimated_tokens: Estimated number of tokens in response
        """
        start_message = WSStreamingStart(
            session_id=session_id,
            estimated_tokens=estimated_tokens
        )
        await self.send_message(session_id, start_message)
    
    async def send_streaming_chunk(
        self, 
        session_id: str, 
        content: str,
        full_content: str,
        chunk_index: int,
        is_final: bool = False
    ):
        """
        Send streaming response chunk.
        
        Args:
            session_id: Target session
            content: Chunk content
            full_content: Accumulated content so far
            chunk_index: Index of this chunk
            is_final: Whether this is the final chunk
        """
        chunk_message = WSStreamingResponse(
            session_id=session_id,
            content=content,
            full_content=full_content,
            chunk_index=chunk_index,
            is_final=is_final
        )
        await self.send_message(session_id, chunk_message)
    
    async def end_streaming_response(
        self, 
        session_id: str, 
        final_content: str,
        total_chunks: int,
        response_time_ms: int,
        suggested_actions: Optional[List[str]] = None
    ):
        """
        Signal end of streaming response.
        
        Args:
            session_id: Target session
            final_content: Complete response content
            total_chunks: Total number of chunks sent
            response_time_ms: Total response time
            suggested_actions: Optional follow-up suggestions
        """
        end_message = WSStreamingEnd(
            session_id=session_id,
            final_content=final_content,
            total_chunks=total_chunks,
            response_time_ms=response_time_ms,
            suggested_actions=suggested_actions or []
        )
        await self.send_message(session_id, end_message)
    
    async def handle_ping(self, session_id: str, ping_message: WSPing):
        """
        Handle ping message and send pong response.
        
        Args:
            session_id: Session that sent the ping
            ping_message: Ping message
        """
        pong_message = WSPong(
            session_id=session_id,
            ping_timestamp=ping_message.timestamp
        )
        await self.send_message(session_id, pong_message)
    
    def register_message_handler(
        self, 
        message_type: WebSocketMessageType, 
        handler: Callable
    ):
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Async handler function
        """
        self.message_handlers[message_type].append(handler)
        logger.debug(f"Registered handler for message type: {message_type}")
    
    def get_connection_info(self, session_id: str) -> Optional[ConnectionInfo]:
        """
        Get connection information for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            ConnectionInfo if session exists, None otherwise
        """
        return self.connections.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> Set[str]:
        """
        Get all session IDs for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Set of session IDs
        """
        return self.user_sessions.get(user_id, set()).copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get connection manager statistics.
        
        Returns:
            Dictionary containing various statistics
        """
        return {
            "active_connections": len(self.connections),
            "total_connections": self.total_connections,
            "total_messages": self.total_messages,
            "unique_users": len(self.user_sessions),
            "uptime_seconds": int((datetime.utcnow() - self.started_at).total_seconds()),
            "authenticated_sessions": sum(
                1 for conn in self.connections.values() if conn.is_authenticated
            ),
            "idle_connections": sum(
                1 for conn in self.connections.values() if conn.is_idle
            )
        }
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        task = asyncio.create_task(self._cleanup_idle_connections())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def _cleanup_idle_connections(self):
        """Background task to clean up idle connections."""
        while True:
            try:
                # Sleep for 1 minute between cleanup cycles
                await asyncio.sleep(60)
                
                # Find idle connections
                idle_sessions = [
                    session_id for session_id, conn in self.connections.items()
                    if conn.is_idle
                ]
                
                # Disconnect idle sessions
                for session_id in idle_sessions:
                    logger.info(f"Disconnecting idle session: {session_id}")
                    await self.disconnect(session_id, "idle_timeout")
                
                if idle_sessions:
                    logger.info(f"Cleaned up {len(idle_sessions)} idle connections")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def shutdown(self):
        """
        Shutdown the connection manager and close all connections.
        """
        logger.info("Shutting down WebSocket connection manager")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Close all connections
        disconnect_tasks = []
        for session_id in list(self.connections.keys()):
            disconnect_tasks.append(self.disconnect(session_id, "server_shutdown"))
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        logger.info("WebSocket connection manager shutdown complete")


# Global connection manager instance
_connection_manager: Optional[WebSocketConnectionManager] = None


def get_connection_manager() -> WebSocketConnectionManager:
    """Get global WebSocket connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = WebSocketConnectionManager()
    return _connection_manager


async def cleanup_connection_manager():
    """Cleanup function to be called on app shutdown."""
    global _connection_manager
    if _connection_manager:
        await _connection_manager.shutdown()
        _connection_manager = None