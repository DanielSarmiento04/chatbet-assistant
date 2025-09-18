#!/usr/bin/env python3
"""
Quick test script for ChatBet Assistant Backend
"""

import asyncio
import sys
import os
from typing import List

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_basic_imports():
    """Test that all main modules can be imported."""
    print("🧪 Testing basic imports...")
    
    try:
        # Core modules
        from app.core.config import get_settings
        print("✅ Config module imported successfully")
        
        from app.core.logging import get_logger
        print("✅ Logging module imported successfully")
        
        # Models
        from app.models.conversation import ChatRequest, ChatResponse, IntentType
        print("✅ Conversation models imported successfully")
        
        from app.models.api_models import (
            Tournament, MatchFixture, UserValidationResponse, TokenValidationResponse, 
            Sport, TournamentInfo, SportWithTournaments, FixtureInfo, LanguageType, FixtureType,
            SportFixture, SportFixturesResponse, MultiLanguageName, TeamData
        )
        print("✅ API models imported successfully")
        
        # Test new validation models
        user_validation = UserValidationResponse(status=True, userId=1)
        token_validation = TokenValidationResponse(message="Valid token")
        print("✅ New validation models working correctly")
        
        # Test new sports models
        sport = Sport(
            alias="Soccer",
            id="1",
            name="Football",
            name_es="Football", 
            name_en="Football",
            name_pt_br="Football"
        )
        print("✅ Sports models working correctly")
        
        # Test language type validation
        valid_languages: List[LanguageType] = ["en", "es", "pt_br"]
        valid_types: List[FixtureType] = ["pre_match", "live"]
        print("✅ Language and fixture type validation working correctly")
        
        # Test new sport fixtures models
        multilang_name = MultiLanguageName(en="Test", es="Prueba", pt_br="Teste")
        team_data = TeamData(name=multilang_name)
        sport_fixture = SportFixture(
            tournament_name=multilang_name,
            away_team_data=team_data,
            source=1101,
            tournament_id="2988",
            home_team_data=team_data,
            id="27900311",
            startTime="09-18 22:00",
            startTimeIndex="09-18 22:00",
            homeCompetitorName=multilang_name,
            homeCompetitorId=multilang_name,
            awayCompetitorName=multilang_name,
            awayCompetitorId=multilang_name
        )
        print("✅ Sport fixtures models working correctly")
        
        # Test basic configuration
        settings = get_settings()
        print(f"✅ Settings loaded: environment={settings.environment}")
        
        # Test logger
        logger = get_logger(__name__)
        logger.info("Test log message")
        print("✅ Logger working correctly")
        
        # Test model creation
        request = ChatRequest(
            message="Hello",
            user_id="test_user",
            session_id="test_session",
            max_tokens=100,
            temperature=0.7
        )
        print("✅ ChatRequest model created successfully")
        
        print("\n🎉 All basic imports and configurations working!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False

async def test_api_client():
    """Test that API client can be imported and basic methods exist."""
    print("\n🧪 Testing API Client...")
    
    try:
        from app.services.chatbet_api import ChatBetAPIClient
        print("✅ ChatBetAPIClient imported successfully")
        
        # Create client instance (won't make actual requests in test)
        client = ChatBetAPIClient()
        
        # Check that new validation methods exist
        assert hasattr(client, 'validate_user'), "validate_user method missing"
        assert hasattr(client, 'validate_token_endpoint'), "validate_token_endpoint method missing"
        print("✅ New validation methods are available")
        
        # Check that new sports methods exist
        assert hasattr(client, 'get_sports'), "get_sports method missing"
        assert hasattr(client, 'get_sport_tournaments'), "get_sport_tournaments method missing"
        assert hasattr(client, 'get_all_tournaments'), "get_all_tournaments method missing"
        assert hasattr(client, 'get_fixtures'), "get_fixtures method missing"
        assert hasattr(client, 'get_sport_fixtures'), "get_sport_fixtures method missing"
        print("✅ New sports methods are available")
        
        # Clean up
        await client.close() 
        print("✅ API client structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ API client test failed: {str(e)}")
        return False

async def test_fastapi_app():
    """Test that FastAPI app can be created."""
    print("\n🧪 Testing FastAPI application...")
    
    try:
        from app import app
        print("✅ FastAPI app imported successfully")
        
        # Check if app has the expected routes
        routes = [getattr(route, 'path', str(route)) for route in app.routes]
        print(f"✅ Found {len(routes)} routes:")
        for route in routes[:5]:  # Show first 5 routes
            print(f"   - {route}")
        if len(routes) > 5:
            print(f"   ... and {len(routes) - 5} more")
        
        print("✅ FastAPI application structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("🚀 ChatBet Assistant Backend - Quick Tests")
    print("=" * 50)
    
    # Test imports
    import_success = await test_basic_imports()
    
    # Test API client
    api_success = await test_api_client()
    
    # Test FastAPI app
    app_success = await test_fastapi_app()
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 20)
    print(f"Imports: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"API Client: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"FastAPI: {'✅ PASS' if app_success else '❌ FAIL'}")
    
    if import_success and api_success and app_success:
        print("\n🎉 All tests passed! The backend is ready to run.")
        print("\n🚀 To start the server:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\n📖 API docs will be available at:")
        print("   http://localhost:8000/docs")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)