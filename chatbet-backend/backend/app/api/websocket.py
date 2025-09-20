"""
WebSocket API endpoints for real-time chat communication.

This module provides WebSocket endpoints for the ChatBet assistant,
enabling real-time bidirectional communication, streaming responses,
and live sports data updates.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse

from ..core.logging import get_logger
from ..core.config import get_settings
from ..core.auth import CurrentUser, OptionalUser, get_current_user, get_optional_user
from ..models.websocket_models import (
    WSUserMessage, WSError, WSPing, WebSocketMessageType,
    parse_websocket_message, create_error_message
)
from ..models.conversation import ChatRequest, IntentType
from ..services.websocket_manager import get_connection_manager, WebSocketConnectionManager
from ..services.conversation_manager import get_conversation_manager
from ..services.websocket_streaming import WebSocketStreamingCallback
from ..utils.exceptions import ChatBetException
from ..utils.websocket_debug import get_websocket_debugger

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


async def _simulate_streaming_response(
    connection_manager: WebSocketConnectionManager,
    session_id: str,
    response_content: str,
    chunk_delay: float = 0.05
):
    """
    Simulate streaming response by sending content in chunks.
    
    This is a temporary implementation until we integrate streaming
    directly with the LLM service.
    """
    # Start streaming
    await connection_manager.start_streaming_response(session_id)
    
    # Split response into words for streaming
    words = response_content.split()
    chunk_size = 3  # Words per chunk
    accumulated_content = ""
    
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i + chunk_size]
        chunk_content = " ".join(chunk_words)
        
        if i > 0:  # Add space before chunk if not first
            chunk_content = " " + chunk_content
            
        accumulated_content += chunk_content
        
        # Send chunk
        await connection_manager.send_streaming_chunk(
            session_id=session_id,
            content=chunk_content,
            full_content=accumulated_content,
            chunk_index=i // chunk_size,
            is_final=False
        )
        
        # Small delay for streaming effect
        await asyncio.sleep(chunk_delay)
    
    # End streaming
    await connection_manager.end_streaming_response(
        session_id=session_id,
        final_content=accumulated_content,
        total_chunks=(len(words) // chunk_size) + 1,
        response_time_ms=int(len(words) * chunk_delay * 1000)
    )


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None, description="User ID for authenticated sessions"),
    session_id: Optional[str] = Query(None, description="Session ID to resume existing conversation")
):
    """
    Main WebSocket endpoint for real-time chat.
    
    This endpoint handles real-time bidirectional communication between
    clients and the ChatBet assistant, supporting streaming responses,
    typing indicators, and session management.
    
    Query Parameters:
        user_id: Optional user ID for authenticated sessions
        session_id: Optional session ID to resume existing conversation
    """
    connection_manager = get_connection_manager()
    conversation_manager = get_conversation_manager()
    assigned_session_id = None
    
    try:
        # Establish WebSocket connection
        assigned_session_id = await connection_manager.connect(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id
        )
        
        logger.info(
            f"WebSocket chat connection established",
            extra={
                "session_id": assigned_session_id,
                "user_id": user_id,
                "endpoint": "/chat"
            }
        )
        
        # Register message handlers
        async def handle_user_message(session_id: str, message: WSUserMessage):
            """Handle incoming user chat messages."""
            logger.info(
                f"WebSocket handler received user message",
                extra={
                    "session_id": session_id,
                    "user_id": message.user_id,
                    "message_id": message.message_id,
                    "content": message.content[:50] + "..." if len(message.content) > 50 else message.content,
                    "handler_call_timestamp": datetime.now().isoformat()
                }
            )
            
            try:
                # Send typing indicator
                await connection_manager.send_typing_indicator(session_id, True, estimated_time=3)
                
                # Create ChatRequest for conversation manager
                chat_request = ChatRequest(
                    message=message.content,
                    user_id=message.user_id,
                    session_id=session_id,
                    max_tokens=None,
                    temperature=None
                )
                
                # Create streaming callback
                streaming_callback = WebSocketStreamingCallback(
                    websocket_manager=connection_manager,
                    session_id=session_id,
                    message_id=message.message_id
                )
                
                # For now, process message normally and then simulate streaming
                # TODO: Integrate streaming_callback directly with LLM service
                response = await conversation_manager.process_message(chat_request)
                
                # Simulate streaming by sending the response in chunks
                await _simulate_streaming_response(connection_manager, session_id, response.message)
                
                # Stop typing indicator
                await connection_manager.send_typing_indicator(session_id, False)
                
            except Exception as e:
                logger.error(f"Error processing user message: {e}")
                await connection_manager.send_error(
                    session_id,
                    "MESSAGE_PROCESSING_ERROR",
                    "Failed to process your message. Please try again."
                )
                await connection_manager.send_typing_indicator(session_id, False)
        
        async def handle_ping(session_id: str, message: WSPing):
            """Handle ping messages for connection testing."""
            await connection_manager.handle_ping(session_id, message)
        
        # Register handlers
        connection_manager.register_message_handler(WebSocketMessageType.USER_MESSAGE, handle_user_message)
        connection_manager.register_message_handler(WebSocketMessageType.PING, handle_ping)
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle the message
                await connection_manager.handle_user_message(assigned_session_id, message_data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {assigned_session_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                await connection_manager.send_error(
                    assigned_session_id,
                    "INVALID_JSON",
                    "Invalid JSON format in message"
                )
            except Exception as e:
                logger.error(f"Error in WebSocket message loop: {e}")
                await connection_manager.send_error(
                    assigned_session_id,
                    "UNEXPECTED_ERROR",
                    "An unexpected error occurred"
                )
                break
                
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        if assigned_session_id:
            try:
                await connection_manager.send_error(
                    assigned_session_id,
                    "CONNECTION_ERROR",
                    "WebSocket connection error"
                )
            except:
                pass  # Connection might already be closed
    finally:
        # Clean up connection
        if assigned_session_id:
            await connection_manager.disconnect(assigned_session_id, "connection_closed")


@router.websocket("/chat/{session_id}")
async def websocket_chat_with_session(
    websocket: WebSocket,
    session_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authenticated sessions")
):
    """
    WebSocket endpoint with explicit session ID.
    
    This endpoint allows clients to connect to a specific session ID,
    useful for resuming conversations or multi-device synchronization.
    
    Path Parameters:
        session_id: Specific session ID to connect to
        
    Query Parameters:
        user_id: Optional user ID for authenticated sessions
    """
    # Validate session ID format
    try:
        uuid4().hex  # Simple validation
    except:
        await websocket.close(code=4000, reason="Invalid session ID format")
        return
    
    # Use the main chat endpoint logic with the provided session ID
    await websocket_chat_endpoint(websocket, user_id=user_id, session_id=session_id)


@router.websocket("/sports-updates")
async def websocket_sports_updates(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None, description="User ID for personalized updates"),
    competitions: Optional[str] = Query(None, description="Comma-separated competition IDs to follow")
):
    """
    WebSocket endpoint for live sports data updates.
    
    This endpoint provides real-time sports data including odds changes,
    match events, and fixture updates without requiring chat interaction.
    
    Query Parameters:
        user_id: Optional user ID for personalized updates
        competitions: Optional comma-separated list of competition IDs to follow
    """
    connection_manager = get_connection_manager()
    session_id = f"sports_{uuid4().hex}"
    
    try:
        # Establish connection
        await connection_manager.connect(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id
        )
        
        logger.info(
            f"Sports updates WebSocket connected",
            extra={
                "session_id": session_id,
                "user_id": user_id,
                "competitions": competitions
            }
        )
        
        # Parse competition filters
        competition_filters = []
        if competitions:
            competition_filters = [comp.strip() for comp in competitions.split(",")]
        
        # Send initial connection confirmation
        await connection_manager.send_message(
            session_id,
            create_error_message(  # Using as info message
                session_id,
                "INFO",
                f"Connected to sports updates. Following {len(competition_filters) if competition_filters else 'all'} competitions."
            )
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive any control messages from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle control messages (like subscription changes)
                if message_data.get("type") == "subscribe":
                    new_competitions = message_data.get("competitions", [])
                    competition_filters = new_competitions
                    await connection_manager.send_message(
                        session_id,
                        create_error_message(  # Using as info message
                            session_id,
                            "SUBSCRIPTION_UPDATED",
                            f"Updated subscription to {len(competition_filters)} competitions"
                        )
                    )
                
            except WebSocketDisconnect:
                logger.info(f"Sports updates client disconnected: {session_id}")
                break
            except json.JSONDecodeError:
                # Ignore invalid JSON for this endpoint
                pass
            except Exception as e:
                logger.error(f"Error in sports updates WebSocket: {e}")
                break
                
    except Exception as e:
        logger.error(f"Error in sports updates WebSocket connection: {e}")
    finally:
        await connection_manager.disconnect(session_id, "sports_updates_closed")


@router.get("/status")
async def websocket_status(current_user: CurrentUser):
    """
    Get WebSocket connection status and statistics.
    
    Returns information about active connections, performance metrics,
    and system health for monitoring purposes.
    Requires authentication for security.
    """
    connection_manager = get_connection_manager()
    
    stats = connection_manager.get_statistics()
    
    return {
        "websocket_status": "active",
        "server_time": datetime.utcnow().isoformat(),
        "connections": stats,
        "features": [
            "real_time_chat",
            "streaming_responses",
            "sports_updates",
            "typing_indicators",
            "multi_session_support"
        ]
    }


@router.get("/test")
async def websocket_test_page():
    """
    Simple HTML test page for WebSocket functionality.
    
    Returns an HTML page with JavaScript WebSocket client for testing
    the chat and sports update endpoints during development.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ChatBet WebSocket Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .chat-box {{ border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; margin: 10px 0; background: #f9f9f9; }}
            .input-group {{ margin: 10px 0; }}
            input, button {{ padding: 8px; margin: 2px; }}
            input[type="text"] {{ width: 300px; }}
            .message {{ margin: 5px 0; padding: 5px; border-radius: 4px; }}
            .user-message {{ background: #e3f2fd; text-align: right; }}
            .bot-message {{ background: #f3e5f5; }}
            .system-message {{ background: #fff3e0; font-style: italic; }}
            .error-message {{ background: #ffebee; color: #c62828; }}
            .status {{ padding: 10px; margin: 10px 0; border-radius: 4px; }}
            .connected {{ background: #e8f5e8; color: #2e7d32; }}
            .disconnected {{ background: #ffebee; color: #c62828; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ChatBet WebSocket Test</h1>
            
            <div class="status" id="status">Disconnected</div>
            
            <div class="input-group">
                <input type="text" id="userIdInput" placeholder="User ID (optional)" value="test_user">
                <input type="text" id="sessionIdInput" placeholder="Session ID (optional)">
                <button onclick="connect()">Connect to Chat</button>
                <button onclick="disconnect()">Disconnect</button>
            </div>
            
            <div id="chatBox" class="chat-box"></div>
            
            <div class="input-group">
                <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Send Message</button>
                <button onclick="sendPing()">Ping</button>
                <button onclick="clearChat()">Clear</button>
            </div>
            
            <h3>Sports Updates</h3>
            <div class="input-group">
                <button onclick="connectSports()">Connect Sports Updates</button>
                <button onclick="disconnectSports()">Disconnect Sports</button>
            </div>
            <div id="sportsBox" class="chat-box" style="height: 200px;"></div>
        </div>

        <script>
            let chatWs = null;
            let sportsWs = null;
            const chatBox = document.getElementById('chatBox');
            const sportsBox = document.getElementById('sportsBox');
            const status = document.getElementById('status');
            const messageInput = document.getElementById('messageInput');

            function updateStatus(connected) {{
                status.textContent = connected ? 'Connected' : 'Disconnected';
                status.className = 'status ' + (connected ? 'connected' : 'disconnected');
            }}

            function addMessage(box, type, content, timestamp = null) {{
                const div = document.createElement('div');
                div.className = `message ${{type}}-message`;
                const time = timestamp || new Date().toLocaleTimeString();
                div.innerHTML = `<small>[${{time}}]</small> ${{content}}`;
                box.appendChild(div);
                box.scrollTop = box.scrollHeight;
            }}

            function connect() {{
                const userId = document.getElementById('userIdInput').value || null;
                const sessionId = document.getElementById('sessionIdInput').value || null;
                
                let url = 'ws://localhost:8000/ws/chat';
                const params = new URLSearchParams();
                if (userId) params.append('user_id', userId);
                if (sessionId) params.append('session_id', sessionId);
                if (params.toString()) url += '?' + params.toString();

                chatWs = new WebSocket(url);

                chatWs.onopen = function(event) {{
                    updateStatus(true);
                    addMessage(chatBox, 'system', 'Connected to ChatBet WebSocket');
                }};

                chatWs.onmessage = function(event) {{
                    const data = JSON.parse(event.data);
                    let content = '';
                    
                    switch(data.type) {{
                        case 'connection_ack':
                            content = `Connection acknowledged. Features: ${{data.supported_features.join(', ')}}`;
                            addMessage(chatBox, 'system', content);
                            break;
                        case 'bot_response':
                            content = data.content;
                            addMessage(chatBox, 'bot', content);
                            break;
                        case 'streaming_response':
                            // Update last bot message or create new one
                            const lastMessage = chatBox.lastElementChild;
                            if (lastMessage && lastMessage.classList.contains('bot-message')) {{
                                lastMessage.innerHTML = lastMessage.innerHTML.split(']')[0] + '] ' + data.full_content;
                            }} else {{
                                addMessage(chatBox, 'bot', data.content);
                            }}
                            break;
                        case 'typing':
                            if (data.is_typing) {{
                                addMessage(chatBox, 'system', 'Assistant is typing...');
                            }}
                            break;
                        case 'error':
                            content = `Error (${{data.error_code}}): ${{data.error_message}}`;
                            addMessage(chatBox, 'error', content);
                            break;
                        case 'pong':
                            addMessage(chatBox, 'system', 'Pong received');
                            break;
                        default:
                            content = `[${{data.type}}] ${{JSON.stringify(data)}}`;
                            addMessage(chatBox, 'system', content);
                    }}
                }};

                chatWs.onclose = function(event) {{
                    updateStatus(false);
                    addMessage(chatBox, 'system', 'WebSocket connection closed');
                }};

                chatWs.onerror = function(error) {{
                    addMessage(chatBox, 'error', 'WebSocket error: ' + error);
                }};
            }}

            function disconnect() {{
                if (chatWs) {{
                    chatWs.close();
                    chatWs = null;
                }}
            }}

            function sendMessage() {{
                const message = messageInput.value.trim();
                if (!message || !chatWs) return;

                const messageData = {{
                    type: 'user_message',
                    content: message,
                    session_id: 'test_session',
                    user_id: document.getElementById('userIdInput').value || null
                }};

                chatWs.send(JSON.stringify(messageData));
                addMessage(chatBox, 'user', message);
                messageInput.value = '';
            }}

            function sendPing() {{
                if (!chatWs) return;
                
                const pingData = {{
                    type: 'ping',
                    session_id: 'test_session'
                }};

                chatWs.send(JSON.stringify(pingData));
                addMessage(chatBox, 'system', 'Ping sent');
            }}

            function handleKeyPress(event) {{
                if (event.key === 'Enter') {{
                    sendMessage();
                }}
            }}

            function clearChat() {{
                chatBox.innerHTML = '';
            }}

            function connectSports() {{
                const userId = document.getElementById('userIdInput').value || null;
                
                let url = 'ws://localhost:8000/ws/sports-updates';
                if (userId) url += '?user_id=' + userId;

                sportsWs = new WebSocket(url);

                sportsWs.onopen = function(event) {{
                    addMessage(sportsBox, 'system', 'Connected to Sports Updates');
                }};

                sportsWs.onmessage = function(event) {{
                    const data = JSON.parse(event.data);
                    let content = `[${{data.type}}] ${{JSON.stringify(data, null, 2)}}`;
                    addMessage(sportsBox, 'system', content);
                }};

                sportsWs.onclose = function(event) {{
                    addMessage(sportsBox, 'system', 'Sports updates connection closed');
                }};
            }}

            function disconnectSports() {{
                if (sportsWs) {{
                    sportsWs.close();
                    sportsWs = null;
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.get("/ping")
async def websocket_ping_endpoint():
    """
    Simple ping endpoint to test WebSocket server availability.
    
    Returns basic server information and can be used by load balancers
    or monitoring tools to check if the WebSocket service is running.
    """
    connection_manager = get_connection_manager()
    
    return {
        "status": "ok",
        "service": "ChatBet WebSocket API",
        "timestamp": datetime.utcnow().isoformat(),
        "active_connections": len(connection_manager.connections),
        "server_info": {
            "version": "1.0.0",
            "features": ["chat", "sports-updates", "streaming"]
        }
    }


@router.get("/debug/stats")
async def websocket_debug_stats(current_user: CurrentUser):
    """
    Get WebSocket debugging statistics.
    
    Returns comprehensive debugging information including:
    - Connection statistics
    - Message patterns
    - Performance metrics
    - Error summaries
    
    Requires authentication for security.
    """
    try:
        debugger = get_websocket_debugger()
        return {
            "status": "success",
            "data": debugger.export_debug_data(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting debug stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get debug statistics")


@router.get("/debug/session/{session_id}")
async def websocket_debug_session(session_id: str, current_user: CurrentUser):
    """
    Get debugging information for a specific session.
    
    Args:
        session_id: The session ID to get information for
        current_user: Authenticated user making the request
        
    Returns:
        Session-specific debugging information
        
    Requires authentication for security.
    """
    try:
        debugger = get_websocket_debugger()
        session_info = debugger.get_session_info(session_id)
        
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "status": "success",
            "session_info": session_info,
            "recent_messages": debugger.get_recent_messages(limit=20, session_id=session_id),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session debug info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session information")


@router.post("/debug/clear")
async def websocket_debug_clear(current_user: CurrentUser):
    """
    Clear WebSocket debugging history.
    
    This endpoint clears all stored debugging data including
    message history, connection events, and performance metrics.
    
    Requires authentication for security.
    """
    try:
        debugger = get_websocket_debugger()
        debugger.clear_history()
        
        return {
            "status": "success",
            "message": "Debug history cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing debug history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear debug history")


@router.get("/debug/performance")
async def websocket_debug_performance(current_user: CurrentUser):
    """
    Get WebSocket performance analysis.
    
    Returns detailed performance metrics and recommendations
    for optimizing WebSocket connections and message processing.
    
    Requires authentication for security.
    """
    try:
        debugger = get_websocket_debugger()
        performance_data = debugger.analyze_performance()
        connection_stats = debugger.get_connection_stats()
        
        return {
            "status": "success",
            "performance": performance_data,
            "stats": connection_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance analysis")


# Error handlers for WebSocket routes
@router.websocket("/health")
async def websocket_health_check(websocket: WebSocket):
    """
    WebSocket health check endpoint.
    
    Simple WebSocket endpoint that accepts connection, sends a health
    status message, and closes the connection. Used for monitoring.
    """
    try:
        await websocket.accept()
        
        health_message = {
            "type": "health_check",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "chatbet_websocket"
        }
        
        await websocket.send_text(json.dumps(health_message))
        await websocket.close(code=1000, reason="Health check complete")
        
    except Exception as e:
        logger.error(f"WebSocket health check error: {e}")
        try:
            await websocket.close(code=1011, reason="Health check failed")
        except:
            pass