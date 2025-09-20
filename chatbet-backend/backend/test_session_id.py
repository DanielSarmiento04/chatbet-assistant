#!/usr/bin/env python3
"""
Test script to verify session ID handling in conversation manager.
"""

import asyncio
from app.services.conversation_manager import ConversationManager
from app.models.conversation import ChatRequest


async def test_session_id_handling():
    """Test that None session_id is properly handled."""
    print("Testing session ID handling...")
    
    manager = ConversationManager()
    
    # Test with None session_id
    request = ChatRequest(
        message="hello",
        user_id="test_user",
        session_id=None,  # This should be handled gracefully
        max_tokens=None,
        temperature=None
    )
    
    try:
        response = await manager.process_message(request)
        print(f"✅ Success! Response session_id: {response.session_id}")
        print(f"Response: {response.message[:50]}...")
        
        # Session ID should not be None
        assert response.session_id is not None
        assert response.session_id != ""
        
        print("✅ Session ID handling test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


async def test_empty_session_id():
    """Test with empty string session_id."""
    print("\nTesting empty session ID handling...")
    
    manager = ConversationManager()
    
    # Test with empty session_id
    request = ChatRequest(
        message="hello again",
        user_id="test_user",
        session_id="",  # Empty string should also be handled
        max_tokens=None,
        temperature=None
    )
    
    try:
        response = await manager.process_message(request)
        print(f"✅ Success! Response session_id: {response.session_id}")
        print(f"Response: {response.message[:50]}...")
        
        # Session ID should not be empty
        assert response.session_id is not None
        assert response.session_id != ""
        
        print("✅ Empty session ID handling test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


async def main():
    """Run all tests."""
    print("Starting session ID handling tests...\n")
    
    try:
        await test_session_id_handling()
        await test_empty_session_id()
        print("\n🎉 All session ID tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Tests failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())