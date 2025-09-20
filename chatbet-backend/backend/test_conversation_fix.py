#!/usr/bin/env python3
"""
Test script to verify the conversation flow fixes.

This script simulates the exact conversation scenario that was failing
to ensure our fixes work properly.
"""

import asyncio
import json
from app.services.conversation_manager import get_conversation_manager
from app.models.conversation import ChatRequest
from app.core.config import settings

async def test_conversation_scenarios():
    """Test the conversation scenarios that were failing."""
    
    print("🧪 Testing ChatBet Conversation Flow")
    print("=" * 50)
    
    conversation_manager = get_conversation_manager()
    
    # Test scenarios that were failing
    test_cases = [
        {
            "message": "give me all tournaments available",
            "expected_behavior": "Should list available tournaments"
        },
        {
            "message": "give me all teams in UEFA",
            "expected_behavior": "Should explain limitation and suggest alternatives"
        },
        {
            "message": "give me all matches in UEFA",
            "expected_behavior": "Should try UEFA Champions League (566) and explain if no matches"
        },
        {
            "message": "give me all matches in League Two",
            "expected_behavior": "Should find League Two matches (tournament 1844)"
        },
        {
            "message": "Which match do you recommend I bet on?",
            "expected_behavior": "Should ask for clarification about preferences"
        }
    ]
    
    session_id = "test_session_fix"
    user_id = "test_user"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['message']}")
        print(f"Expected: {test_case['expected_behavior']}")
        print("-" * 40)
        
        try:
            # Create chat request
            request = ChatRequest(
                message=test_case['message'],
                user_id=user_id,
                session_id=session_id,
                max_tokens=None,
                temperature=None
            )
            
            # Process the message
            response = await conversation_manager.process_message(request)
            
            # Print response
            print(f"✅ Response: {response.message}")
            print(f"Intent: {response.detected_intent}")
            print(f"Confidence: {response.intent_confidence}")
            print(f"Response Time: {response.response_time_ms}ms")
            
            if response.suggested_actions:
                print(f"Suggested Actions: {', '.join(response.suggested_actions)}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()
    
    # Test specific tournament query that should work
    print("\n🎯 Testing Specific Working Scenario")
    print("-" * 40)
    
    try:
        request = ChatRequest(
            message="Show me League Two matches for tomorrow",
            user_id=user_id,
            session_id=session_id,
            max_tokens=None,
            temperature=None
        )
        
        response = await conversation_manager.process_message(request)
        print(f"✅ Response: {response.message}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_api_integration():
    """Test the API integration directly."""
    
    print("\n🔧 Testing API Integration")
    print("=" * 50)
    
    from app.services.chatbet_api import get_api_client
    
    try:
        api_client = await get_api_client()
        
        # Test authentication
        print("Testing authentication...")
        auth_result = await api_client.test_authentication()
        print(f"Auth test: {'✅ Passed' if auth_result else '❌ Failed'}")
        
        # Test tournaments
        print("\nTesting tournaments...")
        tournaments = await api_client.get_tournaments()
        print(f"Tournaments found: {len(tournaments)}")
        
        if tournaments:
            print("Available tournaments:")
            for t in tournaments[:5]:  # Show first 5
                print(f"  - {t.name} (ID: {t.id})")
        
        # Test fixtures for League Two (ID: 1844)
        print("\nTesting League Two fixtures...")
        fixtures_response = await api_client.get_fixtures(
            tournament_id="1844",
            fixture_type="pre_match"
        )
        
        print(f"League Two fixtures: {len(fixtures_response.fixtures)}")
        if fixtures_response.fixtures:
            print("Sample fixtures:")
            for f in fixtures_response.fixtures[:3]:  # Show first 3
                print(f"  - {f.homeCompetitor.name} vs {f.awayCompetitor.name} at {f.startTime}")
        
        await api_client.close()
        
    except Exception as e:
        print(f"❌ API Test Error: {str(e)}")

if __name__ == "__main__":
    # Set up basic configuration
    import os
    os.environ.setdefault("GOOGLE_API_KEY", "test-key")
    
    async def main():
        await test_api_integration()
        await test_conversation_scenarios()
    
    asyncio.run(main())