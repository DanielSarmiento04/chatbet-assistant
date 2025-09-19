import { Injectable, inject, signal, computed, effect } from '@angular/core';
import { Observable, Subject, BehaviorSubject, combineLatest } from 'rxjs';
import { map, filter, tap, switchMap, distinctUntilChanged } from 'rxjs/operators';
import { generateUUID } from '../utils/common.utils';
import {
  ChatMessage,
  ChatRequest,
  ChatResponse,
  MessageRole,
  MessageType,
  ConversationContext,
  Conversation,
  ChatUIState,
  IntentType,
  CreateMessagePayload
} from '../models';
import { ApiService } from './api.service';
import { environment } from '../../environments/environment';

/**
 * Chat service for managing conversation state and messaging.
 * Uses Angular 19 signals for reactive state management.
 */
@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly apiService = inject(ApiService);

  // Core conversation state signals
  private readonly messagesSignal = signal<ChatMessage[]>([]);
  private readonly currentSessionIdSignal = signal<string | null>(null);
  private readonly conversationContextSignal = signal<ConversationContext | null>(null);

  // UI state signals
  private readonly isTypingSignal = signal<boolean>(false);
  private readonly lastErrorSignal = signal<string | null>(null);
  private readonly suggestedPromptsSignal = signal<string[]>([]);

  // Message input state
  private readonly pendingMessageSignal = signal<string>('');
  private readonly isProcessingSignal = signal<boolean>(false);

  // Readonly accessors for external components
  readonly messages = this.messagesSignal.asReadonly();
  readonly currentSessionId = this.currentSessionIdSignal.asReadonly();
  readonly conversationContext = this.conversationContextSignal.asReadonly();
  readonly isTyping = this.isTypingSignal.asReadonly();
  readonly lastError = this.lastErrorSignal.asReadonly();
  readonly suggestedPrompts = this.suggestedPromptsSignal.asReadonly();
  readonly pendingMessage = this.pendingMessageSignal.asReadonly();
  readonly isProcessing = this.isProcessingSignal.asReadonly();

  // Computed values
  readonly hasMessages = computed(() => this.messagesSignal().length > 0);
  readonly lastMessage = computed(() => {
    const messages = this.messagesSignal();
    return messages.length > 0 ? messages[messages.length - 1] : null;
  });
  readonly lastUserMessage = computed(() => {
    const messages = this.messagesSignal();
    return messages.filter(m => m.role === MessageRole.USER).pop() || null;
  });
  readonly messageCount = computed(() => this.messagesSignal().length);
  readonly canSendMessage = computed(() => {
    return this.pendingMessageSignal().trim().length > 0 &&
           !this.isProcessingSignal() &&
           !this.isTypingSignal();
  });

  // Chat UI state computed signal
  readonly chatUIState = computed<ChatUIState>(() => ({
    isLoading: this.isProcessingSignal(),
    isConnected: this.apiService.connectionStatus() === 'connected',
    isTyping: this.isTypingSignal(),
    lastError: this.lastErrorSignal() ? {
      message: this.lastErrorSignal()!,
      timestamp: new Date()
    } : undefined,
    suggestedPrompts: this.suggestedPromptsSignal(),
    currentSessionId: this.currentSessionIdSignal() || undefined
  }));

  // Subjects for reactive streams
  private readonly messageSubject = new Subject<ChatMessage>();
  private readonly typingSubject = new Subject<boolean>();

  // Public observables
  readonly message$ = this.messageSubject.asObservable();
  readonly typing$ = this.typingSubject.asObservable();

  constructor() {
    // Initialize default suggested prompts
    this.initializeSuggestedPrompts();

    // Set up auto-session creation
    this.setupAutoSessionCreation();

    // Set up error clearing on successful operations
    this.setupErrorClearing();
  }

  /**
   * Send a message in the current conversation
   */
  async sendMessage(content: string, userId?: string): Promise<void> {
    if (!this.canSendMessage() || !content.trim()) {
      return;
    }

    const sessionId = this.ensureSession();
    const userMessage = this.createUserMessage(content, sessionId, userId);

    try {
      // Clear any previous errors
      this.lastErrorSignal.set(null);

      // Add user message to conversation
      this.addMessage(userMessage);

      // Set processing state
      this.isProcessingSignal.set(true);
      this.pendingMessageSignal.set('');

      // Emit typing indicator
      this.setTyping(true);

      // Prepare API request
      const request: ChatRequest = {
        message: content,
        sessionId,
        userId,
        includeContext: true
      };

      // Send to API
      const response = await this.apiService.chat.sendMessage(request).toPromise();

      if (response) {
        // Create assistant message from response
        const assistantMessage = this.createAssistantMessage(response, sessionId);
        this.addMessage(assistantMessage);

        // Update suggested prompts if provided
        if (response.suggestedActions.length > 0) {
          this.suggestedPromptsSignal.set(response.suggestedActions);
        }

        // Emit message event
        this.messageSubject.next(assistantMessage);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      this.lastErrorSignal.set(errorMessage);

      // Add error message to conversation
      const errorMessageObj = this.createErrorMessage(errorMessage, sessionId);
      this.addMessage(errorMessageObj);

    } finally {
      this.isProcessingSignal.set(false);
      this.setTyping(false);
    }
  }

  /**
   * Update the pending message (for input binding)
   */
  updatePendingMessage(content: string): void {
    this.pendingMessageSignal.set(content);
  }

  /**
   * Set typing indicator state
   */
  setTyping(isTyping: boolean): void {
    this.isTypingSignal.set(isTyping);
    this.typingSubject.next(isTyping);
  }

  /**
   * Start a new conversation session
   */
  startNewSession(userId?: string): void {
    const sessionId = generateUUID();
    this.currentSessionIdSignal.set(sessionId);

    // Create new conversation context
    const context: ConversationContext = {
      sessionId,
      userId,
      createdAt: new Date(),
      lastActivity: new Date(),
      preferredTeams: [],
      preferredTournaments: [],
      language: 'en',
      mentionedTeams: [],
      mentionedMatches: [],
      isAuthenticated: !!userId
    };

    this.conversationContextSignal.set(context);

    // Clear messages for new session
    this.messagesSignal.set([]);

    // Reset UI state
    this.clearError();
    this.initializeSuggestedPrompts();
  }

  /**
   * Load conversation history
   */
  async loadConversationHistory(sessionId: string, userId?: string): Promise<void> {
    try {
      this.isProcessingSignal.set(true);

      const response = await this.apiService.chat.getConversationHistory(
        userId || 'anonymous',
        sessionId,
        50,
        0
      ).toPromise();

      if (response?.data) {
        // Convert conversation summaries to messages
        // This would need to be implemented based on backend response structure
        // For now, we'll just set the session
        this.currentSessionIdSignal.set(sessionId);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load conversation history';
      this.lastErrorSignal.set(errorMessage);
    } finally {
      this.isProcessingSignal.set(false);
    }
  }

  /**
   * Clear current conversation
   */
  clearConversation(): void {
    this.messagesSignal.set([]);
    this.clearError();
    this.isProcessingSignal.set(false);
    this.isTypingSignal.set(false);
    this.pendingMessageSignal.set('');
    this.initializeSuggestedPrompts();
  }

  /**
   * Clear error state
   */
  clearError(): void {
    this.lastErrorSignal.set(null);
  }

  /**
   * Add a message to the current conversation
   */
  private addMessage(message: ChatMessage): void {
    this.messagesSignal.update(messages => [...messages, message]);

    // Update conversation context last activity
    this.conversationContextSignal.update(context => {
      if (context) {
        return { ...context, lastActivity: new Date() };
      }
      return context;
    });
  }

  /**
   * Create a user message
   */
  private createUserMessage(content: string, sessionId: string, userId?: string): ChatMessage {
    return {
      id: generateUUID(),
      role: MessageRole.USER,
      content: content.trim(),
      timestamp: new Date(),
      messageType: MessageType.TEXT,
      sessionId,
      userId,
      isLoading: false,
      hasError: false
    };
  }

  /**
   * Create an assistant message from API response
   */
  private createAssistantMessage(response: ChatResponse, sessionId: string): ChatMessage {
    return {
      id: response.messageId,
      role: MessageRole.ASSISTANT,
      content: response.message,
      timestamp: new Date(),
      messageType: this.determineMessageType(response),
      sessionId,
      detectedIntent: response.detectedIntent,
      intentConfidence: response.intentConfidence,
      responseTimeMs: response.responseTimeMs,
      tokenCount: response.tokenCount,
      isLoading: false,
      hasError: false
    };
  }

  /**
   * Create an error message
   */
  private createErrorMessage(errorText: string, sessionId: string): ChatMessage {
    return {
      id: generateUUID(),
      role: MessageRole.ASSISTANT,
      content: `Sorry, I encountered an error: ${errorText}`,
      timestamp: new Date(),
      messageType: MessageType.ERROR,
      sessionId,
      isLoading: false,
      hasError: true,
      errorMessage: errorText
    };
  }

  /**
   * Determine message type from API response
   */
  private determineMessageType(response: ChatResponse): MessageType {
    // Determine message type based on detected intent or function calls
    if (response.detectedIntent) {
      switch (response.detectedIntent) {
        case IntentType.MATCH_INQUIRY:
        case IntentType.MATCH_SCHEDULE_QUERY:
          return MessageType.MATCH_CARD;
        case IntentType.ODDS_COMPARISON:
        case IntentType.ODDS_INFORMATION_QUERY:
          return MessageType.ODDS_TABLE;
        case IntentType.BETTING_RECOMMENDATION:
          return MessageType.RECOMMENDATION;
        case IntentType.TOURNAMENT_INFO:
        case IntentType.TOURNAMENT_INFO_QUERY:
          return MessageType.TOURNAMENT_INFO;
        default:
          return MessageType.TEXT;
      }
    }

    return MessageType.TEXT;
  }

  /**
   * Ensure a session exists, create one if not
   */
  private ensureSession(): string {
    let sessionId = this.currentSessionIdSignal();

    if (!sessionId) {
      this.startNewSession();
      sessionId = this.currentSessionIdSignal();
    }

    return sessionId!;
  }

  /**
   * Initialize default suggested prompts
   */
  private initializeSuggestedPrompts(): void {
    const defaultPrompts = [
      "What are today's match fixtures?",
      "Show me betting odds for Premier League",
      "Give me betting recommendations",
      "What's the best bet for this weekend?",
      "Compare odds for Manchester United vs Liverpool"
    ];

    this.suggestedPromptsSignal.set(defaultPrompts);
  }

  /**
   * Setup auto-session creation on first message
   */
  private setupAutoSessionCreation(): void {
    effect(() => {
      const pendingMessage = this.pendingMessageSignal();
      const currentSession = this.currentSessionIdSignal();

      // Auto-create session when user starts typing and no session exists
      if (pendingMessage.length > 0 && !currentSession) {
        this.startNewSession();
      }
    });
  }

  /**
   * Setup error clearing on successful operations
   */
  private setupErrorClearing(): void {
    effect(() => {
      const hasMessages = this.hasMessages();
      const lastMessage = this.lastMessage();

      // Clear errors when new successful message is added
      if (hasMessages && lastMessage && !lastMessage.hasError) {
        this.lastErrorSignal.set(null);
      }
    });
  }

  /**
   * Get conversation as exportable object
   */
  getConversation(): Conversation | null {
    const context = this.conversationContextSignal();
    const messages = this.messagesSignal();

    if (!context) {
      return null;
    }

    return {
      id: context.sessionId,
      context,
      messages,
      title: this.generateConversationTitle(messages),
      isActive: true
    };
  }

  /**
   * Generate a title for the conversation based on messages
   */
  private generateConversationTitle(messages: ChatMessage[]): string {
    const userMessages = messages.filter(m => m.role === MessageRole.USER);

    if (userMessages.length === 0) {
      return 'New Conversation';
    }

    const firstMessage = userMessages[0].content;
    return firstMessage.length > 50
      ? `${firstMessage.substring(0, 47)}...`
      : firstMessage;
  }
}
