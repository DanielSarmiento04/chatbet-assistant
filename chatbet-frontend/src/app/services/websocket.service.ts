import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, Subject, BehaviorSubject, fromEvent, NEVER, interval } from 'rxjs';
import { map, filter, tap, retry, delay, catchError, takeWhile } from 'rxjs/operators';
import {
  WebSocketMessage,
  ChatMessage,
  TypingIndicator,
  MessageRole,
  MessageType
} from '../models';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';
import { generateUUID } from '../utils/common.utils';

export enum WebSocketStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

interface WebSocketEventData {
  [key: string]: unknown;
}

/**
 * WebSocket service for real-time communication with ChatBet backend.
 * Uses native WebSocket with reconnection logic and message handling.
 */
@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private readonly authService = inject(AuthService);

  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;

  // Connection state signals
  private readonly statusSignal = signal<WebSocketStatus>(WebSocketStatus.DISCONNECTED);
  private readonly lastErrorSignal = signal<string | null>(null);
  private readonly connectionTimeSignal = signal<Date | null>(null);

  // Message handling subjects
  private readonly messageSubject = new Subject<ChatMessage>();
  private readonly typingSubject = new Subject<TypingIndicator>();
  private readonly systemSubject = new Subject<WebSocketMessage>();

  // Readonly accessors
  readonly status = this.statusSignal.asReadonly();
  readonly lastError = this.lastErrorSignal.asReadonly();
  readonly connectionTime = this.connectionTimeSignal.asReadonly();

  // Computed values
  readonly isConnected = computed(() => this.statusSignal() === WebSocketStatus.CONNECTED);
  readonly isConnecting = computed(() =>
    this.statusSignal() === WebSocketStatus.CONNECTING ||
    this.statusSignal() === WebSocketStatus.RECONNECTING
  );
  readonly canSendMessages = computed(() => this.isConnected());

  // Public observables
  readonly message$ = this.messageSubject.asObservable();
  readonly typing$ = this.typingSubject.asObservable();
  readonly system$ = this.systemSubject.asObservable();

  constructor() {
    // Note: Don't auto-connect here to avoid duplicate connections
    // Connection will be initiated by components when needed
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    this.statusSignal.set(WebSocketStatus.CONNECTING);
    this.lastErrorSignal.set(null);

    try {
      // Build WebSocket URL with auth token
      const wsUrl = this.buildWebSocketUrl();
      this.socket = new WebSocket(wsUrl);

      this.setupSocketEventHandlers();

    } catch (error) {
      this.handleConnectionError(error instanceof Error ? error.message : 'Connection failed');
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.clearTimers();

    if (this.socket) {
      this.socket.close(1000, 'Manual disconnect');
      this.socket = null;
    }

    this.statusSignal.set(WebSocketStatus.DISCONNECTED);
    this.connectionTimeSignal.set(null);
    this.reconnectAttempts = 0;
  }

  /**
   * Send a chat message through WebSocket
   */
  sendMessage(content: string, sessionId: string, userId?: string): void {
    if (!this.canSendMessages()) {
      throw new Error('WebSocket not connected');
    }

    // Send message using backend WSUserMessage structure
    const message = {
      type: 'user_message',
      content,
      user_id: userId,
      timestamp: new Date().toISOString(),
      session_id: sessionId,
      message_id: generateUUID(),
      metadata: {}
    };

    if (environment.enableLogging) {
      console.log('Sending WebSocket message:', message);
    }

    this.sendWebSocketMessage(message);
  }

  /**
   * Send typing indicator
   */
  sendTyping(isTyping: boolean, sessionId: string, userId?: string): void {
    if (!this.canSendMessages()) {
      return;
    }

    // Send typing using backend WSTypingIndicator structure
    const message = {
      type: 'typing',
      is_typing: isTyping,
      timestamp: new Date().toISOString(),
      session_id: sessionId,
      message_id: generateUUID(),
      estimated_time_seconds: null
    };

    this.sendWebSocketMessage(message);
  }

  /**
   * Join a specific session room
   * Note: Session management is handled automatically by the backend
   */
  joinSession(sessionId: string): void {
    // Backend handles session management automatically
    // No explicit join message needed
    if (environment.enableLogging) {
      console.log('Session will be managed automatically by backend:', sessionId);
    }
  }

  /**
   * Leave a session room
   * Note: Session management is handled automatically by the backend
   */
  leaveSession(sessionId: string): void {
    // Backend handles session management automatically
    // No explicit leave message needed
    if (environment.enableLogging) {
      console.log('Session cleanup will be managed automatically by backend:', sessionId);
    }
  }

  /**
   * Request conversation history
   * Note: History requests may be handled through HTTP API instead
   */
  requestHistory(sessionId: string, limit = 20): void {
    // TODO: Implement history request through appropriate backend endpoint
    // Backend may handle history through HTTP API or dedicated WebSocket message type
    if (environment.enableLogging) {
      console.log('History request for session:', sessionId, 'limit:', limit);
    }
  }

  /**
   * Build WebSocket URL with authentication
   */
  private buildWebSocketUrl(): string {
    const baseUrl = environment.wsUrl.replace('http', 'ws');

    // For now, connect without token since backend WebSocket doesn't expect it yet
    // In future iterations, we can add: ?token=${encodeURIComponent(token)}
    // when backend WebSocket endpoint is updated to handle token authentication

    return baseUrl;
  }

  /**
   * Setup socket event handlers
   */
  private setupSocketEventHandlers(): void {
    if (!this.socket) return;

    this.socket.onopen = () => {
      this.statusSignal.set(WebSocketStatus.CONNECTED);
      this.connectionTimeSignal.set(new Date());
      this.reconnectAttempts = 0;
      this.lastErrorSignal.set(null);

      // Start heartbeat
      this.startHeartbeat();

      if (environment.enableLogging) {
        console.log('WebSocket connected');
      }
    };

    this.socket.onclose = (event) => {
      this.statusSignal.set(WebSocketStatus.DISCONNECTED);
      this.connectionTimeSignal.set(null);
      this.clearTimers();

      if (environment.enableLogging) {
        console.log('WebSocket disconnected:', event.code, event.reason);
      }

      // Only attempt reconnection if it wasn't a manual disconnect
      if (event.code !== 1000) {
        this.attemptReconnection();
      }
    };

    this.socket.onerror = (error) => {
      this.handleConnectionError('WebSocket connection error');
    };

    this.socket.onmessage = (event) => {
      this.handleIncomingMessage(event.data);
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleIncomingMessage(data: string): void {
    try {
      const message = JSON.parse(data);

      if (environment.enableLogging) {
        console.log('Received WebSocket message:', message);
      }

      // Handle backend message format (direct properties)
      switch (message.type) {
        case 'bot_response':
          const chatMessage: ChatMessage = {
            id: message.message_id || generateUUID(),
            role: MessageRole.ASSISTANT,
            content: message.content,
            timestamp: new Date(message.timestamp),
            messageType: MessageType.TEXT,
            sessionId: message.session_id,
            responseTimeMs: message.response_time_ms || 0
          };
          this.messageSubject.next(chatMessage);
          break;

        case 'streaming_response':
          // Handle streaming messages
          const streamingMessage: ChatMessage = {
            id: message.message_id || generateUUID(),
            role: MessageRole.ASSISTANT,
            content: message.content,
            timestamp: new Date(message.timestamp),
            messageType: MessageType.TEXT,
            sessionId: message.session_id,
            responseTimeMs: 0
          };
          this.messageSubject.next(streamingMessage);
          break;

        case 'typing':
          const typingIndicator: TypingIndicator = {
            userId: message.user_id || 'unknown',
            isTyping: message.is_typing,
            sessionId: message.session_id
          };
          this.typingSubject.next(typingIndicator);
          break;

        case 'pong':
          // Handle pong responses
          if (environment.enableLogging) {
            console.log('Received pong:', message);
          }
          break;

        case 'connection_ack':
          // Handle connection acknowledgment
          if (environment.enableLogging) {
            console.log('Connection acknowledged:', message);
          }
          break;

        case 'error':
          // Handle error messages
          console.error('WebSocket error:', message);
          this.lastErrorSignal.set(message.content || 'Unknown error');
          this.systemSubject.next(message);
          break;

        case 'message':
          // Legacy frontend format support (fallback)
          const legacyMessage = this.parseIncomingMessage(message.data);
          if (legacyMessage) {
            this.messageSubject.next(legacyMessage);
          }
          break;

        case 'connection':
        case 'disconnect':
          this.systemSubject.next(message);
          break;

        default:
          if (environment.enableLogging) {
            console.log('Unknown WebSocket message type:', message.type);
          }
      }

    } catch (error) {
      console.warn('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Parse incoming message data into ChatMessage format
   */
  private parseIncomingMessage(data: unknown): ChatMessage | null {
    try {
      if (typeof data !== 'object' || !data) {
        return null;
      }

      const messageData = data as WebSocketEventData;

      return {
        id: (messageData['id'] || messageData['messageId'] || generateUUID()) as string,
        role: MessageRole.ASSISTANT,
        content: (messageData['message'] || messageData['content'] || '') as string,
        timestamp: messageData['timestamp'] ? new Date(messageData['timestamp'] as string) : new Date(),
        messageType: MessageType.TEXT,
        sessionId: messageData['sessionId'] as string,
        detectedIntent: messageData['detected_intent'] as any,
        intentConfidence: messageData['intent_confidence'] as number,
        responseTimeMs: messageData['response_time_ms'] as number,
        isLoading: false,
        hasError: false
      };

    } catch (error) {
      console.warn('Failed to parse incoming message:', error);
      return null;
    }
  }

  /**
   * Send message through WebSocket
   */
  private sendWebSocketMessage(message: WebSocketMessage | any): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      if (environment.enableLogging) {
        console.log('Sending to WebSocket:', JSON.stringify(message));
      }
      this.socket.send(JSON.stringify(message));
    } else {
      if (environment.enableLogging) {
        console.error('Cannot send message: WebSocket not open. State:', this.socket?.readyState);
      }
    }
  }

  /**
   * Handle connection errors
   */
  private handleConnectionError(errorMessage: string): void {
    this.statusSignal.set(WebSocketStatus.ERROR);
    this.lastErrorSignal.set(errorMessage);

    if (environment.enableLogging) {
      console.error('WebSocket connection error:', errorMessage);
    }

    this.attemptReconnection();
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnection(): void {
    if (this.reconnectAttempts >= environment.websocket.maxReconnectAttempts) {
      this.statusSignal.set(WebSocketStatus.ERROR);
      this.lastErrorSignal.set('Max reconnection attempts reached');
      return;
    }

    this.statusSignal.set(WebSocketStatus.RECONNECTING);
    this.reconnectAttempts++;

    const delay = Math.min(
      environment.websocket.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Max 30 seconds
    );

    if (environment.enableLogging) {
      console.log(`Attempting reconnection ${this.reconnectAttempts}/${environment.websocket.maxReconnectAttempts} in ${delay}ms`);
    }

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        // Send ping message with required fields to match backend WSPing model
        const sessionId = this.getCurrentSessionId();
        this.socket.send(JSON.stringify({
          type: 'ping',
          timestamp: new Date().toISOString(),
          session_id: sessionId || 'heartbeat',
          message_id: generateUUID()
        }));
      }
    }, environment.websocket.heartbeatInterval);
  }

  /**
   * Get current session ID (we might need to track this)
   */
  private getCurrentSessionId(): string | null {
    // For now, return a default session ID
    // In the future, this should track the actual session
    return 'default-session';
  }

  /**
   * Clear all timers
   */
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Get connection statistics
   */
  getConnectionStats(): {
    status: WebSocketStatus;
    connectedAt: Date | null;
    reconnectAttempts: number;
    lastError: string | null;
  } {
    return {
      status: this.statusSignal(),
      connectedAt: this.connectionTimeSignal(),
      reconnectAttempts: this.reconnectAttempts,
      lastError: this.lastErrorSignal()
    };
  }

  /**
   * Force reconnection
   */
  forceReconnect(): void {
    this.disconnect();
    this.reconnectAttempts = 0;
    setTimeout(() => this.connect(), 1000);
  }

  /**
   * Check if WebSocket is supported
   */
  isWebSocketSupported(): boolean {
    return 'WebSocket' in window;
  }
}
