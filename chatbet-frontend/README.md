# ChatBet Frontend

A modern, real-time sports betting conversational interface built with Angular 19 and Material Design. ChatBet provides an intuitive chat experience for sports betting inquiries, odds checking, and match information.

![Angular](https://img.shields.io/badge/Angular-19.0-red)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue)
![Material](https://img.shields.io/badge/Material-19.2-green)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-orange)

## 🚀 Features

### Core Functionality
- **Real-time Chat Interface** - Instant messaging with WebSocket connectivity
- **Sports Betting Assistant** - AI-powered conversational betting guidance
- **Live Odds Integration** - Real-time sports odds and match information
- **Authentication System** - Secure user authentication and session management
- **Responsive Design** - Mobile-first responsive UI with Material Design

### Chat Features
- **Smart Auto-scroll** - Intelligent scroll management with user interaction detection
- **Typing Indicators** - Real-time typing status from the bot
- **Message Formatting** - Rich text support with markdown rendering
- **Quick Actions** - Pre-defined prompts for common queries
- **Message History** - Persistent conversation history
- **Error Handling** - Graceful error states and retry mechanisms

### UI/UX Features
- **Material Design 3** - Modern Google Material Design theming
- **Dark/Light Theme** - Automatic theme switching
- **Connection Status** - Visual WebSocket connection indicators
- **Loading States** - Smooth loading animations and progress indicators
- **Accessibility** - WCAG compliant with keyboard navigation support

## 🏗️ Architecture

### Technology Stack
- **Framework**: Angular 19 (Standalone Components)
- **UI Library**: Angular Material 19.2
- **State Management**: Angular Signals (Modern Reactive State)
- **Real-time Communication**: WebSocket with Socket.IO
- **Styling**: SCSS with Material Design tokens
- **Package Manager**: Bun (Fast JavaScript runtime)
- **Build System**: Angular CLI with esbuild

### Project Structure
```
src/
├── app/
│   ├── components/           # Reusable UI components
│   │   ├── chat-interface/   # Main chat interface
│   │   ├── chat-input/       # Message input component
│   │   ├── message-bubble/   # Individual message display
│   │   ├── header/          # Application header
│   │   └── sidebar/         # Navigation sidebar
│   ├── services/            # Business logic and data services
│   │   ├── auth.service.ts  # Authentication management
│   │   ├── chat.service.ts  # Chat state and message handling
│   │   ├── websocket.service.ts # WebSocket communication
│   │   └── api.service.ts   # HTTP API interactions
│   ├── models/              # TypeScript interfaces and types
│   │   ├── chat.models.ts   # Chat and conversation models
│   │   └── sports.models.ts # Sports and betting data models
│   ├── pages/               # Route components
│   │   ├── chat/           # Chat page container
│   │   └── home/           # Landing page
│   └── utils/              # Utility functions and helpers
├── assets/                 # Static assets (images, icons)
└── environments/           # Environment configurations
```

## 🔧 Installation & Setup

### Prerequisites
- **Node.js** (v18+)
- **Bun** (v1.1.0+) - Fast JavaScript runtime
- **Git** for version control

### Quick Start
```bash
# Clone the repository
git clone https://github.com/DanielSarmiento04/chatbet-assistant.git
cd chatbet-assistant/chatbet-frontend

# Install dependencies
bun install

# Start development server
bun run start

# Open browser to http://localhost:4200
```

### Available Scripts
```bash
# Development
bun run start          # Start dev server with hot reload
bun run watch          # Build and watch for changes

# Building
bun run build          # Build for development
bun run build:prod     # Build for production

# Testing & Quality
bun run test           # Run unit tests
bun run lint           # Run ESLint
bun run e2e            # Run end-to-end tests

# Production
bun run serve:ssr      # Serve production build
```

## 🔌 Backend Integration

### WebSocket Connection
The frontend connects to the ChatBet backend via WebSocket for real-time communication:

```typescript
// WebSocket endpoint
const WEBSOCKET_URL = 'ws://localhost:8000/ws/chat'

// Message protocol
interface WebSocketMessage {
  type: 'message' | 'typing' | 'error' | 'connection_ack'
  data: any
  session_id?: string
  message_id?: string
}
```

### API Endpoints
```typescript
// REST API base URL
const API_BASE_URL = 'http://localhost:8000/api'

// Available endpoints
GET    /api/health              # Health check
POST   /api/auth/login          # User authentication
GET    /api/chat/sessions       # Get chat sessions
POST   /api/chat/message        # Send message (fallback)
```

## 🎨 UI Components

### ChatInterface Component
Main chat interface with real-time messaging capabilities.

**Features:**
- Real-time message streaming
- Smart scroll management
- Typing indicators
- Connection status
- Error handling

**Usage:**
```html
<app-chat-interface></app-chat-interface>
```

### MessageBubble Component
Individual message display with rich formatting.

**Features:**
- Role-based styling (user/bot)
- Markdown rendering
- Timestamp formatting
- Loading states

### ChatInput Component
Message input with send functionality.

**Features:**
- Auto-resize textarea
- Send on Enter key
- Disabled states
- Character limits

## 🔐 Authentication

### Authentication Flow
1. User visits the application
2. Authentication service checks for existing session
3. If authenticated, WebSocket connection is established
4. Chat interface becomes available

### Auth Service Features
```typescript
// Authentication methods
isAuthenticated(): boolean
login(credentials): Promise<void>
logout(): void
getCurrentUser(): User | null
```

## 🌐 WebSocket Communication

### Connection Management
```typescript
// Connection lifecycle
connect()           # Establish WebSocket connection
disconnect()        # Close connection gracefully
reconnect()         # Automatic reconnection with backoff
isConnected()       # Check connection status
```

### Message Protocol
```typescript
// Outgoing messages
{
  type: 'message',
  data: {
    content: string,
    session_id: string
  }
}

// Incoming messages
{
  type: 'response',
  data: {
    content: string,
    message_id: string,
    is_final: boolean
  }
}
```

## 🎯 State Management

### Signal-based Architecture
The application uses Angular's modern Signals for reactive state management:

```typescript
// Service signals
messages = signal<ChatMessage[]>([])
isProcessing = signal<boolean>(false)
isConnected = signal<boolean>(false)

// Computed values
hasMessages = computed(() => this.messages().length > 0)
```

### Chat State
- **Messages**: Array of chat messages
- **Session**: Current conversation session
- **Connection**: WebSocket connection status
- **UI State**: Loading, typing, error states

## 🔄 Message Flow

### Sending Messages
1. User types message in chat input
2. Message is validated and added to local state
3. WebSocket service sends message to backend
4. UI shows loading state
5. Response is received and displayed

### Receiving Messages
1. Backend sends message via WebSocket
2. WebSocket service processes incoming data
3. Chat service updates message state
4. UI reactively updates to show new message
5. Auto-scroll triggers if user is at bottom

## 🎨 Theming & Styling

### Material Design 3
The application uses Angular Material with custom theming:

```scss
// Custom theme configuration
@use '@angular/material' as mat;

$primary-palette: mat.define-palette(mat.$green-palette);
$accent-palette: mat.define-palette(mat.$blue-palette);
$theme: mat.define-light-theme(...);
```

### Responsive Design
- **Mobile First**: Optimized for mobile devices
- **Breakpoints**: Material Design breakpoint system
- **Flexible Layouts**: CSS Grid and Flexbox

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
bun run test

# Run specific test file
bun run test -- --include="**/chat.service.spec.ts"

# Run with coverage
bun run test -- --coverage
```

### Test Structure
- **Services**: Business logic testing
- **Components**: UI behavior testing
- **Integration**: WebSocket communication testing

## 🚀 Deployment

### Production Build
```bash
# Create optimized production build
bun run build:prod

# Files are generated in dist/ directory
# Serve with any static file server
```

### Environment Configuration
```typescript
// src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://api.chatbet.com',
  wsUrl: 'wss://api.chatbet.com/ws'
};
```

### Docker Support
```dockerfile
# Build stage
FROM oven/bun:1 AS builder
WORKDIR /app
COPY package.json bun.lockb ./
RUN bun install
COPY . .
RUN bun run build:prod

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist/chatbet-frontend /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

## 🔧 Configuration

### Environment Variables
```bash
# Development
NG_API_URL=http://localhost:8000
NG_WS_URL=ws://localhost:8000/ws

# Production
NG_API_URL=https://api.chatbet.com
NG_WS_URL=wss://api.chatbet.com/ws
```

### Build Configuration
Angular CLI configuration in `angular.json`:
- Development: Fast builds with source maps
- Production: Optimized builds with minification

## 🐛 Troubleshooting

### Common Issues

#### WebSocket Connection Failed
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Verify WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8000/ws/chat
```

#### Build Errors
```bash
# Clear node modules and reinstall
rm -rf node_modules bun.lockb
bun install

# Clear Angular cache
bun run ng cache clean
```

#### Authentication Issues
```bash
# Check auth service configuration
# Verify API endpoints are accessible
# Check browser network tab for 401/403 errors
```

## 📊 Performance

### Optimization Features
- **Lazy Loading**: Route-based code splitting
- **OnPush Strategy**: Optimized change detection
- **Signals**: Efficient reactive updates
- **Bundle Optimization**: Tree-shaking and minification

### Performance Metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **WebSocket Connection**: < 100ms
- **Message Latency**: < 50ms

## 🔒 Security

### Security Features
- **HTTPS**: Encrypted communication
- **WSS**: Secure WebSocket connections
- **Authentication**: JWT-based auth tokens
- **CORS**: Proper cross-origin configuration
- **Input Sanitization**: XSS prevention

## 📈 Monitoring

### Error Tracking
```typescript
// Global error handler
export class GlobalErrorHandler implements ErrorHandler {
  handleError(error: any): void {
    console.error('Global error:', error);
    // Send to monitoring service
  }
}
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built with ❤️ by the Daniel Sarmiento 
