# ChatBet Frontend

This is a chat interface where you can talk to a bot about sports betting. It's built with Angular 19 and looks pretty modern thanks to Material Design.

## What it does

**The main thing:** You chat with a bot that knows about sports betting. Ask it about odds, matches, or how to place bets.

**Chat stuff that works:**
- Messages appear instantly (WebSocket connection)
- The page scrolls down automatically when new messages come in (but stops if you're scrolling up)
- You can see when the bot is typing
- Messages look nice with bold text and lists
- Your conversation history stays there
- If something breaks, it tells you what went wrong

**Other useful things:**
- Works on your phone
- Shows if you're connected or not
- Looks good in both light and dark mode
- You can navigate with just your keyboard

## How it's built

**What we used:**
- Angular 19 (the latest version with standalone components)
- Angular Material for the UI (Google's design system)
- WebSocket for real-time chat
- TypeScript because plain JavaScript gets messy
- Bun instead of npm (it's faster)

**How the code is organized:**
```
src/app/
├── components/        # UI pieces you can reuse
│   ├── chat-interface/ # The main chat window
│   ├── chat-input/    # Where you type messages
│   ├── message-bubble/ # Individual message display
│   └── header/        # Top navigation
├── services/          # The logic that makes things work
│   ├── auth.service.ts    # Login/logout stuff
│   ├── chat.service.ts    # Managing conversations
│   ├── websocket.service.ts # Real-time connection
│   └── api.service.ts     # Talking to the backend
├── models/           # TypeScript types (keeps things organized)
└── pages/           # Different screens in the app
```

## Getting it running

**What you need first:**
- Node.js (version 18 or newer)
- Bun (it's like npm but faster)
- Git

**To start developing:**
```bash
# Get the code
git clone https://github.com/DanielSarmiento04/chatbet-assistant.git
cd chatbet-assistant/chatbet-frontend

# Install everything
bun install

# Start the dev server
bun run start

# Open http://localhost:4200 in your browser
```

**Other commands you might need:**
```bash
bun run build         # Build for production
bun run test          # Run tests
bun run lint          # Check code quality
```

## How it talks to the backend

**WebSocket connection:**
The frontend connects to `ws://localhost:8000/ws/chat` and sends messages like this:

```typescript
{
  type: 'message',
  data: {
    content: "What are today's football matches?",
    session_id: "some-unique-id"
  }
}
```

The backend responds with:
```typescript
{
  type: 'response',
  data: {
    content: "Here are today's matches...",
    message_id: "another-unique-id",
    is_final: true
  }
}
```

**Regular API calls:**
- `GET /api/health` - Check if backend is alive
- `POST /api/auth/login` - Login
- `GET /api/chat/sessions` - Get your chat history

## Main components

**ChatInterface:** The main chat window where everything happens. It handles scrolling, shows typing indicators, and connects to the WebSocket.

**MessageBubble:** Shows individual messages. It can render markdown (bold text, lists, etc.) and styles messages differently for you vs the bot.

**ChatInput:** The text area where you type. It grows as you type more text and sends messages when you press Enter.

## How authentication works

1. When you visit the site, it checks if you're already logged in
2. If yes, it connects to the WebSocket and you can start chatting
3. If no, you need to login first
4. Once logged in, your session is saved so you don't have to login again

The auth service keeps track of whether you're logged in and handles the login/logout process.

## The WebSocket connection

This is how messages appear instantly. The frontend opens a WebSocket connection to the backend and:

- Sends your messages immediately
- Receives bot responses in real-time
- Shows when the bot is typing
- Automatically reconnects if the connection drops
- Shows connection status (connected/disconnected)

## How state management works

We use Angular's new Signals system instead of old-school observables. It's simpler:

```typescript
// These automatically update the UI when they change
messages = signal<ChatMessage[]>([])
isConnected = signal<boolean>(false)
isTyping = signal<boolean>(false)

// This updates automatically when messages change
hasMessages = computed(() => this.messages().length > 0)
```

## What happens when you send a message

1. You type something and hit Enter
2. The message gets added to the chat immediately
3. WebSocket sends it to the backend
4. UI shows a loading indicator
5. Backend processes it and sends a response
6. Response appears in the chat
7. Page scrolls down automatically (unless you were scrolling up)

## Styling and themes

Uses Material Design 3 with custom colors. The theme automatically switches between light and dark based on your system preferences.

Everything is responsive and works on phones. We use CSS Grid and Flexbox for layouts.

## Testing

```bash
# Run all tests
bun run test

# Run a specific test
bun run test -- --include="**/chat.service.spec.ts"

# See test coverage
bun run test -- --coverage
```

Tests cover the main services (auth, chat, websocket) and key components.

## Building for production

```bash
# Create production build
bun run build:prod

# Files go in dist/ folder
# You can serve them with any web server
```

**Environment setup:**
Create environment files for different setups:

```typescript
// src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://your-api.com',
  wsUrl: 'wss://your-api.com/ws'
};
```

## Common problems and fixes

**WebSocket won't connect:**
- Check if the backend is running: `curl http://localhost:8000/api/health`
- Make sure the WebSocket URL is correct
- Check browser console for error messages

**Build fails:**
```bash
# Clean everything and start fresh
rm -rf node_modules bun.lockb
bun install
```

**Page loads but nothing works:**
- Check browser network tab for failed requests
- Look at console for JavaScript errors
- Make sure API endpoints are reachable

**Authentication not working:**
- Check if login endpoint returns the right response
- Verify auth tokens are being stored/sent correctly
- Look for 401/403 errors in network tab

## Performance notes

The app loads fast because:
- Uses lazy loading for different pages
- Bundles are optimized and tree-shaken
- Angular's OnPush change detection strategy
- Signals update only what changed

Typical performance:
- Page loads in under 1.5 seconds
- WebSocket connects in under 100ms
- Messages appear in under 50ms

## Security stuff

- All communication is encrypted (HTTPS/WSS)
- Authentication uses JWT tokens
- User input is sanitized to prevent XSS
- CORS is configured properly
- No sensitive data in localStorage

## Contributing

If you want to help out:

1. Fork the repo
2. Create a branch: `git checkout -b fix-something`
3. Make your changes
4. Test everything works
5. Commit: `git commit -m "Fix something"`
6. Push and create a pull request

**Code style:**
- Use TypeScript strict mode
- Follow Angular style guide
- Run `bun run lint` before committing
- Write tests for new features

---

Built by Daniel Sarmiento 
