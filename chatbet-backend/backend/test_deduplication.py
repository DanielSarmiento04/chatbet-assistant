#!/usr/bin/env python3
"""
Test script to verify message deduplication is working correctly.
"""

import asyncio
import time
from app.services.conversation_manager import ConversationManager
from app.models.conversation import ChatRequest


async def test_message_deduplication():
    """Test that duplicate messages are handled correctly."""
    print("Testing message deduplication...")
    
    # Initialize conversation manager
    manager = ConversationManager()
    
    # Create a test request
    request = ChatRequest(
        message="hi",
        user_id="test_user",
        session_id="test_session",
        max_tokens=None,
        temperature=None
    )
    
    print(f"Sending first message: '{request.message}'")
    start_time = time.time()
    
    try:
        # Send the first message
        response1 = await manager.process_message(request)
        print(f"First response: {response1.message[:100]}...")
        
        # Immediately send the same message again (should be blocked)
        print("Sending duplicate message immediately...")
        response2 = await manager.process_message(request)
        print(f"Second response: {response2.message[:100]}...")
        
        # Check if the responses are different (indicating deduplication worked)
        if "still processing" in response2.message.lower():
            print("✅ PASS: Duplicate message was correctly blocked!")
        else:
            print("❌ FAIL: Duplicate message was not blocked!")
            
        # Wait a bit and try again
        print("Waiting 2 seconds and trying again...")
        await asyncio.sleep(2)
        
        response3 = await manager.process_message(request)
        print(f"Third response: {response3.message[:100]}...")
        
        if "still processing" not in response3.message.lower():
            print("✅ PASS: Message after delay was processed normally!")
        else:
            print("❌ FAIL: Message after delay was still blocked!")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    end_time = time.time()
    print(f"Test completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(test_message_deduplication())