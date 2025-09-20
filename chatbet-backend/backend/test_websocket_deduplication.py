#!/usr/bin/env python3
"""
Test script to verify WebSocket message deduplication.

This script tests that the WebSocket system properly handles duplicate messages
and prevents multiple responses to the same user message.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict

from app.services.websocket_manager import WebSocketConnectionManager
from app.models.websocket_models import WSUserMessage, WebSocketMessageType


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.messages_sent = []
        self.is_closed = False
    
    async def accept(self):
        """Mock accept method."""
        pass
    
    async def send_text(self, data: str):
        """Mock send_text method."""
        if not self.is_closed:
            self.messages_sent.append(data)
    
    async def close(self, code: int = 1000, reason: str = ""):
        """Mock close method."""
        self.is_closed = True


async def test_message_deduplication():
    """Test that duplicate messages are properly filtered out."""
    print("Testing WebSocket message deduplication...")
    
    # Initialize connection manager
    manager = WebSocketConnectionManager()
    
    # Create mock WebSocket and connect
    mock_websocket = MockWebSocket()
    session_id = await manager.connect(mock_websocket, user_id="test_user")
    
    # Create a test message
    message_id = str(uuid.uuid4())
    test_message = {
        "type": "user_message",
        "content": "Hello, this is a test message",
        "user_id": "test_user",
        "session_id": session_id,
        "message_id": message_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Track handler calls
    handler_calls = []
    
    async def test_handler(session_id: str, message):
        """Test message handler that tracks calls."""
        handler_calls.append({
            "session_id": session_id,
            "message_id": getattr(message, 'message_id', None),
            "content": getattr(message, 'content', None),
            "timestamp": datetime.utcnow().isoformat()
        })
        print(f"Handler called for message: {message.content[:30]}...")
    
    # Register the test handler
    manager.register_message_handler(WebSocketMessageType.USER_MESSAGE, test_handler)
    
    print(f"Sending first message with ID: {message_id}")
    # Send the message first time
    result1 = await manager.handle_user_message(session_id, test_message)
    print(f"First message result: {result1}")
    
    # Small delay to ensure timestamp difference
    await asyncio.sleep(0.1)
    
    print(f"Sending duplicate message with same ID: {message_id}")
    # Send the same message again (duplicate)
    result2 = await manager.handle_user_message(session_id, test_message)
    print(f"Second message result: {result2}")
    
    # Send it one more time
    await asyncio.sleep(0.1)
    print(f"Sending another duplicate message with same ID: {message_id}")
    result3 = await manager.handle_user_message(session_id, test_message)
    print(f"Third message result: {result3}")
    
    # Verify results
    print(f"\nResults:")
    print(f"First message processed: {result1}")
    print(f"Second message processed: {result2}")
    print(f"Third message processed: {result3}")
    print(f"Total handler calls: {len(handler_calls)}")
    print(f"Expected: 1 call, Actual: {len(handler_calls)} calls")
    
    # Print handler call details
    for i, call in enumerate(handler_calls):
        print(f"Call {i+1}: {call}")
    
    # Test with different message ID
    print(f"\nTesting with different message ID...")
    new_message_id = str(uuid.uuid4())
    new_message = test_message.copy()
    new_message["message_id"] = new_message_id
    new_message["content"] = "This is a different message"
    
    print(f"Sending message with new ID: {new_message_id}")
    result4 = await manager.handle_user_message(session_id, new_message)
    print(f"New message result: {result4}")
    
    print(f"Final handler calls: {len(handler_calls)}")
    print(f"Expected: 2 calls, Actual: {len(handler_calls)} calls")
    
    # Assertions
    assert result1 == True, "First message should be processed"
    assert result2 == False, "Second message should be rejected (duplicate)"
    assert result3 == False, "Third message should be rejected (duplicate)"
    assert result4 == True, "New message should be processed"
    assert len(handler_calls) == 2, f"Expected 2 handler calls, got {len(handler_calls)}"
    
    print("✅ All tests passed! Message deduplication is working correctly.")


async def test_connection_replacement():
    """Test that multiple connections with same session ID are handled properly."""
    print("\nTesting connection replacement...")
    
    manager = WebSocketConnectionManager()
    
    # Create first connection
    mock_websocket1 = MockWebSocket()
    session_id = "test_session_123"
    session_id_returned1 = await manager.connect(mock_websocket1, session_id=session_id, user_id="test_user")
    
    assert session_id_returned1 == session_id
    assert session_id in manager.connections
    assert not mock_websocket1.is_closed
    
    print(f"First connection established: {session_id}")
    
    # Create second connection with same session ID
    mock_websocket2 = MockWebSocket()
    session_id_returned2 = await manager.connect(mock_websocket2, session_id=session_id, user_id="test_user")
    
    assert session_id_returned2 == session_id
    assert session_id in manager.connections
    
    # Give some time for the close operation
    await asyncio.sleep(0.1)
    
    print(f"Second connection established: {session_id}")
    print(f"First connection closed: {mock_websocket1.is_closed}")
    print(f"Second connection closed: {mock_websocket2.is_closed}")
    
    # First connection should be closed, second should be active
    assert mock_websocket1.is_closed, "First connection should be closed"
    assert not mock_websocket2.is_closed, "Second connection should be active"
    
    # The active connection should be the second one
    active_connection = manager.connections[session_id]
    assert active_connection.websocket == mock_websocket2
    
    print("✅ Connection replacement test passed!")


async def main():
    """Run all tests."""
    print("Starting WebSocket deduplication and connection management tests...\n")
    
    try:
        await test_message_deduplication()
        await test_connection_replacement()
        print("\n🎉 All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())