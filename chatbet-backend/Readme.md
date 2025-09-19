# ChatBet Assistant Backend

An intelligent conversational chatbot backend that integrates with sports betting APIs to provide insights, recommendations, and real-time data analysis.

## 🏗️ Architecture Overview

This backend is built using enterprise-level patterns with a focus on scalability, maintainability, and production readiness.

### Core Technologies

- **FastAPI**: Modern, fast web framework for building APIs with Python
- **Google Gemini AI**: Advanced language model for intelligent conversations and intent classification
- **LangChain**: Conversation management and memory handling
- **Redis**: High-performance caching and session storage
- **Pydantic v2**: Data validation and serialization
- **Docker**: Containerization for consistent deployment

### Project Structure

```
backend/
├── app/
│   ├── api/                 # FastAPI route handlers
│   │   ├── chat.py         # Chat endpoints
│   │   └── health.py       # Health check endpoints
│   ├── core/               # Core configuration and utilities
│   │   ├── config.py       # Application settings
│   │   ├── logging.py      # Structured logging setup
│   │   └── security.py     # Authentication and security
│   ├── models/             # Pydantic data models
│   │   ├── api_models.py   # External API models
│   │   ├── betting.py      # Betting-related models
│   │   └── conversation.py # Conversation models
│   ├── services/           # Business logic services
│   │   ├── chatbet_api.py  # External API integration
│   │   ├── conversation_manager.py # Conversation orchestration
│   │   └── llm_service.py  # AI/LLM integration
│   ├── utils/              # Utility modules
│   │   ├── cache.py        # Redis caching utilities
│   │   ├── exceptions.py   # Custom exception handling
│   │   └── parsers.py      # Text parsing and entity extraction
│   └── main.py             # FastAPI application entry point
├── Dockerfile              # Container configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Features

### Conversation Management
- **Intent Classification**: Automatically detects user intentions (betting info, match queries, recommendations)
- **Context Awareness**: Maintains conversation history and context using LangChain memory
- **Multi-session Support**: Handles multiple concurrent user sessions
- **Streaming Responses**: Real-time response streaming for better user experience

### Sports Betting Integration
- **Live Data**: Real-time sports data and odds from ChatBet API
- **Bet Recommendations**: AI-powered betting suggestions based on analysis
- **Risk Assessment**: Intelligent betting strategy recommendations
- **Portfolio Analysis**: Track and analyze betting performance

### Enterprise Features
- **Caching Strategy**: Multi-tier Redis caching (tournaments: 24h, fixtures: 4h, odds: 30s)
- **Error Handling**: Comprehensive exception handling with circuit breaker patterns
- **Logging**: Structured JSON logging with correlation IDs
- **Health Monitoring**: Detailed health checks for all dependencies
- **Rate Limiting**: IP-based rate limiting for API protection
- **Security**: API key authentication and CORS configuration

## 🛠️ Setup and Installation

### Prerequisites

- Python 3.11+
- Redis server
- Google AI API key
- ChatBet API access

### Local Development

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   Create a `.env` file:
   ```env
   # Application
   ENVIRONMENT=development
   DEBUG=true
   
   # Google AI
   GOOGLE_API_KEY=your_google_ai_api_key_here
   GEMINI_MODEL=gemini-2.0-flash-exp
   
   # ChatBet API
   CHATBET_API_BASE_URL=https://api.chatbet.com/v1
   CHATBET_API_KEY=your_chatbet_api_key_here
   
   # Redis
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   
   # Security
   SECRET_KEY=your_secret_key_here
   CORS_ORIGINS=http://localhost:3000,http://localhost:8080
   ```

5. **Start Redis server**
   ```bash
   redis-server
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t chatbet-backend .
   ```

2. **Run with Docker Compose**
   ```bash
   cd ..  # Go to project root
   docker-compose up -d
   ```

## 📡 API Endpoints

### Chat Endpoints

#### Send Message
```http
POST /api/v1/chat/message
Content-Type: application/json

{
  "message": "What are the odds for Barcelona vs Real Madrid?",
  "user_id": "user123",
  "session_id": "session456"
}
```

Response:
```json
{
  "message": "Based on current data, Barcelona vs Real Madrid has the following odds...",
  "session_id": "session456",
  "message_id": "msg_1234567890",
  "response_time_ms": 250,
  "token_count": 150,
  "detected_intent": "odds_information_query",
  "intent_confidence": 0.95,
  "function_calls_made": ["get_match_odds"],
  "suggested_actions": ["View full match analysis", "Get betting recommendations"]
}
```

#### Get Conversation History
```http
GET /api/v1/chat/conversations/{user_id}?session_id=session456&limit=20
```

#### Clear Conversation History
```http
DELETE /api/v1/chat/conversations/{user_id}?session_id=session456
```

#### Get Supported Intents
```http
GET /api/v1/chat/intents
```

### Health Endpoints

#### Basic Health Check
```http
GET /health/
```

#### Readiness Check (with dependency validation)
```http
GET /health/ready
```

#### Liveness Check
```http
GET /health/live
```

## 🧠 AI and Conversation Features

### Intent Classification

The system automatically classifies user messages into the following intents:

- **GENERAL_BETTING_INFO**: General betting explanations and help
- **MATCH_INQUIRY**: Questions about specific matches and fixtures
- **ODDS_COMPARISON**: Comparing odds across different markets
- **BETTING_RECOMMENDATION**: Personalized betting suggestions
- **TOURNAMENT_INFO**: Tournament schedules and information

### Entity Extraction

Automatically extracts entities from user messages:
- **Amounts**: "$100", "50 euros"
- **Dates**: "today", "next weekend", "December 15"
- **Teams**: "Barcelona", "Man United", "Lakers"
- **Betting Terms**: "over/under", "handicap", "BTTS"

### Conversation Memory

Uses LangChain's ConversationBufferWindowMemory to maintain context:
- Remembers last 10 messages by default
- Preserves conversation context across messages
- Handles multiple concurrent sessions

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Runtime environment | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `GOOGLE_API_KEY` | Google AI API key | Required |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.0-flash-exp` |
| `REDIS_HOST` | Redis server host | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `CACHE_TTL_TOURNAMENTS` | Tournament cache TTL (seconds) | `86400` |
| `CACHE_TTL_FIXTURES` | Fixtures cache TTL (seconds) | `14400` |
| `CACHE_TTL_ODDS` | Odds cache TTL (seconds) | `30` |
| `RATE_LIMIT_REQUESTS` | Requests per minute per IP | `100` |
| `CONVERSATION_MEMORY_WINDOW` | Messages to remember | `10` |

### Caching Strategy

- **Tournaments**: 24 hours (stable data)
- **Match Fixtures**: 4 hours (semi-stable data)
- **Live Odds**: 30 seconds (highly dynamic data)
- **User Sessions**: 1 hour (conversation context)

## 🏥 Monitoring and Observability

### Health Checks

The system provides comprehensive health monitoring:

- **Application Health**: Basic service availability
- **Dependency Health**: Redis, ChatBet API, conversation manager status
- **Performance Metrics**: Response times and error rates

### Logging

Structured JSON logging with:
- Correlation IDs for request tracing
- Performance metrics
- Error details with context
- Security event logging

### Error Handling

- Custom exception hierarchy for different error types
- Circuit breaker patterns for external API calls
- Graceful degradation when services are unavailable
- Detailed error responses with correlation IDs

## 🔐 Security

### Authentication
- API key authentication for production endpoints
- Bearer token support for user authentication
- Rate limiting by IP address

### CORS Configuration
- Configurable allowed origins
- Secure default settings for production

### Data Protection
- Input validation using Pydantic models
- SQL injection prevention
- XSS protection through proper encoding

## 🧪 Testing

### Running Tests
```bash
pytest tests/ -v
```

### Test Coverage
```bash
pytest --cov=app tests/
```

### Load Testing
```bash
# Using locust (install: pip install locust)
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📊 Performance Considerations

### Optimization Strategies
- Connection pooling for external APIs
- Redis caching with appropriate TTLs
- Async/await for non-blocking operations
- Circuit breaker pattern for resilience
- Request/response compression

### Scalability
- Stateless design for horizontal scaling
- Redis for shared session storage
- Background task processing for heavy operations
- Load balancing ready

## 🚨 Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```bash
   # Check Redis is running
   redis-cli ping
   # Should return "PONG"
   ```

2. **Google AI API Error**
   ```bash
   # Verify API key is set
   echo $GOOGLE_API_KEY
   # Check API quotas in Google Cloud Console
   ```

3. **Import Errors**
   ```bash
   # Ensure PYTHONPATH is set correctly
   export PYTHONPATH=/code
   ```

### Debug Mode

Enable debug mode for detailed logging:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🤝 Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Use type hints throughout the codebase
5. Follow PEP 8 coding standards

## 📄 License

This project is part of the ChatBet Technical Assessment and follows enterprise-level development practices.

## 🔗 Related Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [Google AI Documentation](https://ai.google.dev/)
- [Redis Documentation](https://redis.io/documentation)
- [Pydantic Documentation](https://docs.pydantic.dev/)
