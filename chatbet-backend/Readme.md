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

# ChatBet Assistant Backend

A FastAPI-based conversational AI backend for sports betting insights and recommendations.

## Overview

ChatBet Assistant is an intelligent conversational API that provides real-time sports betting information, odds analysis, and betting recommendations. Built with FastAPI, it integrates with external sports APIs and uses Google Gemini AI for natural language processing.

## Features

- Real-time sports data integration
- Betting odds analysis and recommendations
- WebSocket support for live chat
- Intent classification and conversation management
- Tournament and fixture information
- User authentication and session management
- Comprehensive error handling and fallback responses

## Technology Stack

- **Framework**: FastAPI
- **AI/LLM**: Google Gemini AI
- **Language**: Python 3.11+
- **Database**: Redis (for caching)
- **WebSocket**: FastAPI WebSocket support
- **External API**: ChatBet Sports API
- **Deployment**: Docker

## Project Structure

```
backend/
├── app/
│   ├── api/                 # API route handlers
│   ├── core/               # Core functionality (config, auth, logging)
│   ├── models/             # Pydantic models
│   ├── services/           # Business logic services
│   ├── routes/             # Legacy route handlers
│   └── utils/              # Utility functions
├── Dockerfile              # Docker configuration
├── requirements.txt        # Python dependencies
├── main.py                # Application entry point
└── start.sh               # Development startup script
```

## Installation

### Prerequisites

- Python 3.11 or higher
- Redis server
- Google AI API key

### Setup

1. Clone the repository
2. Navigate to the backend directory
3. Run the setup script:

```bash
chmod +x setup-env.sh
./setup-env.sh
```

4. Create a `.env` file with your configuration:

```bash
GOOGLE_API_KEY=your_google_ai_api_key
REDIS_HOST=localhost
REDIS_PORT=6379
DEBUG=true
ENVIRONMENT=development
```

5. Start the development server:

```bash
chmod +x start.sh
./start.sh
```

## API Endpoints

### REST API

- `GET /` - API information
- `GET /health/` - Health check
- `POST /api/v1/chat/message` - Send chat message
- `GET /api/v1/chat/history/{session_id}` - Get conversation history

### WebSocket

- `ws://localhost:8000/ws/chat` - Real-time chat
- `ws://localhost:8000/ws/sports-updates` - Live sports updates
- `ws://localhost:8000/ws/test` - WebSocket test page

## Usage

### REST API Example

```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are today'\''s Premier League matches?",
    "user_id": "user123",
    "session_id": "session456"
  }'
```

### WebSocket Example

Connect to `ws://localhost:8000/ws/chat` and send:

```json
{
  "type": "user_message",
  "content": "Show me Champions League fixtures",
  "session_id": "your-session-id",
  "user_id": "your-user-id"
}
```

## Configuration

Key configuration options in `.env`:

- `GOOGLE_API_KEY` - Google AI API key (required)
- `CHATBET_API_BASE_URL` - External sports API URL
- `REDIS_HOST` - Redis server host
- `DEBUG` - Enable debug mode
- `CORS_ORIGINS` - Allowed CORS origins

## Development

### Running Tests

```bash
python -m pytest test_basic.py
python test_conversation_fix.py
```

### Code Structure

- **Services**: Business logic separated into focused services
- **Models**: Pydantic models for type safety and validation
- **API Layers**: Clean separation between REST and WebSocket APIs
- **Error Handling**: Comprehensive error handling with fallback responses

## Docker Deployment

```bash
docker build -t chatbet-backend .
docker run -p 8000:8000 --env-file .env chatbet-backend
```

## Monitoring

- Health endpoint: `GET /health/ping`
- WebSocket status: `GET /ws/status`
- Performance metrics available through logging

## Contributing

1. Follow Python PEP 8 style guidelines
2. Add tests for new features
3. Update documentation for API changes
4. Ensure all tests pass before submitting

## Known Issues and Solutions

### Multiple WebSocket Responses Issue

**Problem**: ChatBet sending multiple responses to a single user message (e.g., "hi" generating 3 different responses).

**Root Causes**:
1. **Multiple WebSocket Connections**: Frontend connecting to both `/ws/chat` and `/ws/chat/{session_id}` endpoints
2. **Session ID Conflicts**: Same session ID used across multiple connections
3. **Message Duplication**: Same message processed multiple times due to race conditions
4. **Null Session Handling**: `session_id` being `None` causing processing issues

**Solutions Implemented**:

#### 1. WebSocket Level Deduplication
- **Message ID Tracking**: Each message gets a unique ID and is tracked to prevent duplicate processing
- **Connection Conflict Resolution**: New connections automatically close existing connections with the same session ID
- **10-minute cleanup window**: Old processed message IDs are automatically cleaned up

#### 2. Conversation Level Deduplication
- **Content-based Hashing**: Messages are hashed based on content, user ID, and session ID
- **2-second processing window**: Same message content blocked if received within 2 seconds
- **Graceful acknowledgment**: Returns "still processing" message instead of generating new response

#### 3. Session ID Handling
- **Automatic Generation**: `None` or empty session IDs are automatically replaced with UUIDs
- **Consistent Usage**: All methods ensure valid session IDs before processing

#### 4. Enhanced Logging
- **Processing Tracking**: Detailed logs for message processing start/completion
- **Duplicate Detection**: Warning logs when duplicates are detected and blocked
- **Performance Metrics**: Response time and content length tracking

**Configuration**:
```python
# WebSocket Manager
self.message_cleanup_interval = timedelta(minutes=10)

# Conversation Manager  
self.dedup_window_minutes = 0.03  # 2 seconds in decimal minutes
```

**Testing**:
- Use `test_websocket_deduplication.py` to verify WebSocket-level fixes
- Use `test_session_id.py` to verify session ID handling
- Monitor logs for "Duplicate message detected and blocked" warnings

**Frontend Recommendations**:
1. **Single Connection**: Connect to only one WebSocket endpoint (either `/ws/chat` or `/ws/chat/{session_id}`)
2. **Unique Message IDs**: Ensure each message has a unique `message_id` 
3. **Session Management**: Maintain consistent session IDs across page reloads
4. **Error Handling**: Handle "still processing" responses gracefully

### WebSocket Connection Management
- Only one active connection per session ID is allowed
- Existing connections are automatically closed when a new connection uses the same session ID
- Message processing includes deduplication to prevent multiple responses

## License

This project is part of a technical assessment.

## Support

For issues and questions, refer to the code documentation and error logs.

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
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.0-flash` |
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


## 🔗 Related Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [Google AI Documentation](https://ai.google.dev/)
- [Redis Documentation](https://redis.io/documentation)
- [Pydantic Documentation](https://docs.pydantic.dev/)
