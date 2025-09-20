# ChatBet Assistant - Conversational AI Sports Betting Platform

## 🎯 Project Overview

**ChatBet Assistant** is a comprehensive conversational AI platform designed for sports betting information, real-time odds comparison, and personalized betting recommendations. Built with modern technologies including FastAPI backend with Google Gemini AI integration and Angular 19 frontend with Material Design 3.

**Key Features:**
- 🤖 **Intelligent Conversation**: Natural language interaction with Google Gemini 2.5-Flash AI
- ⚡ **Real-time Data**: Live sports data streaming via WebSocket
- 🎨 **Modern UI**: Angular 19 with signals-based state management and Material Design 3
- 🔐 **Secure Architecture**: JWT authentication with Redis session management
- 🐳 **Containerized Deployment**: Full Docker support with orchestration
- 🌐 **Bilingual Support**: Complete English and Spanish documentation
- 📱 **Responsive Design**: Mobile-first approach with PWA capabilities

## 🎬 Demo

Watch the ChatBet Assistant in action! The demo showcases the complete conversational AI experience including real-time chat interaction, sports data streaming, and intelligent betting recommendations.

**Demo Video**: `output_o.mp4`

<video width="320" height="240" controls>
  <source src="./output_o.mp4" type="video/mp4">
</video>

The demonstration includes:
- 💬 **Natural Language Chat**: Seamless conversation with the AI assistant
- 🏈 **Sports Data Queries**: Real-time sports information and statistics
- 📊 **Betting Odds Display**: Live odds comparison and analysis
- ⚡ **WebSocket Communication**: Instant message delivery and responses
- 📱 **Responsive Interface**: Mobile and desktop experience
- 🎯 **AI Recommendations**: Intelligent betting suggestions based on user queries

## 🏗️ Architecture Overview

### System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     ChatBet Platform                        │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Angular 19)          │  Backend (FastAPI)        │
│  ├── Signals State Management   │  ├── Google Gemini AI     │
│  ├── Material Design 3 UI       │  ├── Redis Caching        │
│  ├── WebSocket Client           │  ├── JWT Authentication   │
│  ├── PWA Capabilities           │  ├── Sports API Streaming │
│  └── Responsive Design          │  └── WebSocket Server     │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure                             │
│  ├── Docker Containers          │  ├── Network Isolation    │
│  ├── Redis Database             │  ├── Environment Config   │
│  └── Multi-service Orchestration│  └── Health Monitoring    │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- **Framework**: FastAPI (Python 3.11+)
- **AI Engine**: Google Gemini 2.5-Flash with LangChain
- **Database**: Redis for caching and sessions
- **Communication**: WebSocket for real-time updates
- **Authentication**: JWT with secure token management
- **Containerization**: Docker with multi-stage builds

**Frontend:**
- **Framework**: Angular 19 with standalone components
- **State Management**: Angular Signals + RxJS patterns
- **UI Library**: Angular Material 19 with Material Design 3
- **Real-time**: Socket.IO client for WebSocket communication
- **Language**: TypeScript 5.6+ with strict type checking
- **Build System**: Angular CLI with esbuild optimization

**Infrastructure:**
- **Orchestration**: Docker Compose with service networking
- **Caching**: Redis with TTL-based invalidation
- **Deployment**: Multi-environment configuration support
- **Monitoring**: Health checks and logging integration

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose**: Latest versions
- **Node.js**: 18.19+ or 20.9+ (for frontend development)
- **Python**: 3.11+ (for backend development)
- **Git**: For version control

### Option 1: Docker Deployment (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd chatbet-assistant

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:4200
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

### Option 2: Development Setup

#### Backend Setup
```bash
cd chatbet-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/env.example.sh backend/env.sh
# Edit env.sh with your configuration

# Start development server
source backend/env.sh
python backend/main.py
```

#### Frontend Setup
```bash
cd chatbet-frontend

# Install dependencies (recommended: use bun for faster installs)
bun install
# or npm install

# Start development server
bun run start
# or ng serve

# Access at http://localhost:4200
```

### Environment Configuration

Create environment files based on your setup:

**Backend Environment** (`chatbet-backend/backend/env.sh`):
```bash
export GEMINI_API_KEY="your-gemini-api-key"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET_KEY="your-secure-jwt-secret"
export CORS_ORIGINS="http://localhost:4200"
export LOG_LEVEL="INFO"
```

**Frontend Environment** (`chatbet-frontend/src/environments/environment.ts`):
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000/ws/chat',
  enableLogging: true
};
```

## 📁 Project Structure

```
chatbet-assistant/
├── README.md                    # This file - project overview
├── README_ES.md                 # Spanish version of project overview
├── docker-compose.yml           # Multi-service orchestration
├── chatbet-backend/            # FastAPI backend service
│   ├── README.md               # Backend-specific documentation
│   ├── README_ES.md            # Spanish backend documentation
│   ├── docker-compose.yml      # Backend service configuration
│   └── backend/                # Python application code
│       ├── main.py             # FastAPI application entry point
│       ├── requirements.txt    # Python dependencies
│       ├── app/                # Application modules
│       │   ├── api/            # API route definitions
│       │   ├── core/           # Core functionality (auth, config)
│       │   ├── models/         # Data models and schemas
│       │   ├── services/       # Business logic services
│       │   └── utils/          # Utility functions
│       └── tests/              # Test suite
└── chatbet-frontend/           # Angular frontend application
    ├── README.md               # Frontend-specific documentation
    ├── README_ES.md            # Spanish frontend documentation
    ├── docker-compose.yml      # Frontend service configuration
    ├── angular.json            # Angular CLI configuration
    ├── package.json            # Node.js dependencies
    └── src/                    # Angular application source
        ├── app/                # Application components and services
        │   ├── components/     # Reusable UI components
        │   ├── pages/          # Route-based page components
        │   ├── services/       # Angular services
        │   └── models/         # TypeScript type definitions
        └── environments/       # Environment configurations
```

## 🔧 Development Workflow

### Backend Development
```bash
cd chatbet-backend

# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Run tests
python -m pytest backend/test_*.py

# Start development server with hot reload
python backend/main.py

# API documentation available at http://localhost:8000/docs
```

### Frontend Development
```bash
cd chatbet-frontend

# Install dependencies
bun install

# Start development server
bun run start

# Run tests
bun run test

# Build for production
bun run build:prod

# Lint code
bun run lint
```

### Docker Development
```bash
# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild specific service
docker-compose up --build chatbet-backend
```

## 🌐 API Documentation

### Core Endpoints

**Health Check:**
```bash
GET /api/v1/health
# Response: {"status": "healthy", "timestamp": "2025-09-19T10:00:00Z"}
```

**Authentication:**
```bash
POST /api/v1/auth/login
# Body: {"username": "user", "password": "pass"}
# Response: {"access_token": "jwt-token", "token_type": "bearer"}
```

**Chat Conversation:**
```bash
POST /api/v1/chat/message
# Headers: Authorization: Bearer <token>
# Body: {"message": "What are today's football matches?", "session_id": "uuid"}
```

**WebSocket Connection:**
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/chat');

// Send message
ws.send(JSON.stringify({
  type: 'message',
  data: {
    content: 'Show me betting odds for Lakers vs Warriors',
    session_id: 'session-uuid'
  }
}));
```

### Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Security Features

### Backend Security
- **JWT Authentication**: Secure token-based authentication
- **CORS Protection**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic model validation for all inputs
- **Rate Limiting**: Protection against API abuse
- **Secure Headers**: Security headers for all responses

### Frontend Security
- **XSS Protection**: Input sanitization and safe rendering
- **CSRF Protection**: Token-based request validation
- **Secure Storage**: Secure token storage and management
- **Content Security Policy**: Strict CSP headers
- **HTTPS Enforcement**: Secure communication in production

## 📊 Performance & Monitoring

### Performance Metrics
- **Backend Response Time**: < 200ms for API calls
- **WebSocket Latency**: < 50ms for real-time messages
- **Frontend Load Time**: < 1.5s initial page load
- **Bundle Size**: < 2MB optimized production build

### Monitoring & Logging
```bash
# View application logs
docker-compose logs -f chatbet-backend
docker-compose logs -f chatbet-frontend

# Monitor Redis performance
docker-compose exec redis redis-cli monitor

# Health check endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:4200/health
```

## 🚧 Troubleshooting

### Common Issues

**Backend Won't Start:**
```bash
# Check environment variables
source backend/env.sh
echo $GEMINI_API_KEY

# Verify Redis connection
docker-compose exec redis redis-cli ping

# Check port availability
lsof -i :8000
```

**Frontend Build Fails:**
```bash
# Clear cache and reinstall
rm -rf node_modules bun.lockb
bun install

# Check Angular CLI version
ng version

# Verify TypeScript compilation
npx tsc --noEmit
```

**WebSocket Connection Issues:**
```bash
# Test WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8000/ws/chat
```

**Docker Issues:**
```bash
# Rebuild all services
docker-compose down -v
docker-compose up --build

# Check service status
docker-compose ps

# View detailed logs
docker-compose logs --details chatbet-backend
```

## 🌍 Internationalization

This project provides complete bilingual documentation:

### English Documentation
- `README.md` - Global project overview (this file)
- `chatbet-backend/README.md` - Backend technical documentation
- `chatbet-frontend/README.md` - Frontend technical documentation

### Spanish Documentation
- `README_ES.md` - Global project overview in Spanish
- `chatbet-backend/README_ES.md` - Backend documentation in Spanish
- `chatbet-frontend/README_ES.md` - Frontend documentation in Spanish

All documentation maintains feature parity across languages with appropriate technical terminology and cultural localization.

## 🤝 Contributing

### Development Guidelines
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the coding standards
4. Run tests: `bun run test` (frontend) or `pytest` (backend)
5. Commit your changes: `git commit -m "Add amazing feature"`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Coding Standards
- **Backend**: Follow PEP 8 with Black formatting
- **Frontend**: Follow Angular style guide with ESLint
- **TypeScript**: Strict mode enabled with complete type coverage
- **Testing**: Minimum 80% code coverage required
- **Documentation**: Update relevant README files for changes

## 📄 License

This project is part of a technical evaluation for ChatBet.

## 🙋‍♂️ Support & Contact

For questions, issues, or support:

### Documentation
- Backend API: http://localhost:8000/docs
- Frontend Components: Refer to Angular documentation
- Docker Setup: See docker-compose.yml configuration

### Development Resources
- **Angular 19**: https://angular.dev/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Google Gemini**: https://ai.google.dev/
- **Redis**: https://redis.io/documentation
- **Material Design 3**: https://material.angular.io/

### Troubleshooting
- Check service logs: `docker-compose logs -f`
- Verify environment configuration
- Ensure all prerequisites are installed
- Review network connectivity between services

---

**Built with ❤️ by Daniel Sarmiento**  
*Senior Full-Stack Developer & AI Integration Specialist*

**Project Status**: Active Development  
**Version**: 1.0.0  
**Last Updated**: September 19, 2025