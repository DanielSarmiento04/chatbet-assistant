import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ChatService } from '../../services/chat.service';
import { WebSocketService } from '../../services/websocket.service';
import { AuthService } from '../../services/auth.service';
import { ChatMessage } from '../../models';

@Component({
  selector: 'app-chat-interface',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatToolbarModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatDividerModule,
    MatTooltipModule
  ],
  templateUrl: './chat-interface.component.html',
  styleUrl: './chat-interface.component.scss'
})
export class ChatInterfaceComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;
  @ViewChild('scrollAnchor') scrollAnchor!: ElementRef;

  // Local component state
  errorMessage = signal<string | null>(null);
  shouldScrollToBottom = signal(true);
  showChatHistory = signal(false);
  isUserScrolling = signal(false);
  scrollTimeoutId: ReturnType<typeof setTimeout> | null = null;
  lastScrollTime = 0;

  // Computed values
  getInputPlaceholder = computed(() => {
    if (!this.webSocketService.isConnected()) return 'Connecting...';
    if (this.chatService.isProcessing()) return 'Please wait...';
    if (!this.authService.isAuthenticated()) return 'Please sign in to chat';
    return 'Ask about sports, odds, or place a bet...';
  });

  constructor(
    private chatService: ChatService,
    private webSocketService: WebSocketService,
    private authService: AuthService
  ) {}

  // Signals from services (accessed as properties)
  get messages() { return this.chatService.messages; }
  get isLoading() { return this.chatService.isProcessing; }
  get isTyping() { return this.chatService.isTyping; }
  get hasMessages() { return this.chatService.hasMessages; }
  get isConnected() { return this.webSocketService.isConnected; }
  get isAuthenticated() { return this.authService.isAuthenticated; }

  ngOnInit(): void {
    // Initialize WebSocket connection
    this.initializeConnection();

    // Set up error handling
    this.setupErrorHandling();

    // Create or resume chat session
    this.initializeChatSession();
  }

  ngOnDestroy(): void {
    // Clean up scroll timeout
    if (this.scrollTimeoutId) {
      clearTimeout(this.scrollTimeoutId);
    }
    // Cleanup handled by services
  }

  ngAfterViewChecked(): void {
    // Only auto-scroll if user is not manually scrolling and we should scroll to bottom
    if (this.shouldScrollToBottom() && !this.isUserScrolling()) {
      this.scrollToBottom();
    }
  }

  private async initializeConnection(): Promise<void> {
    try {
      console.log('isAuthenticated:', this.authService.isAuthenticated());

      // Only connect if authenticated and not already connected/connecting
      if (this.authService.isAuthenticated() && !this.webSocketService.isConnected() && !this.webSocketService.isConnecting()) {
        console.log('Initiating WebSocket connection...');
        this.webSocketService.connect();
      } else {
        console.log('WebSocket connection not needed or already in progress');
      }
    } catch (error) {
      console.error('Failed to initialize connection:', error);
      this.errorMessage.set('Failed to connect to chat service');
    }
  }

  private setupErrorHandling(): void {
    // Listen for WebSocket errors using computed signal
    // Note: In a real implementation, you'd want to use effects or observables
    // For now, we'll rely on the error states in the services
  }

  private async initializeChatSession(): Promise<void> {
    if (!this.chatService.currentSessionId()) {
      this.chatService.startNewSession();
    }
  }

  async onMessageSubmit(content: string): Promise<void> {
    if (!content.trim() || !this.webSocketService.isConnected()) {
      return;
    }

    this.clearError();
    // When user sends message, reset scrolling state and enable auto-scroll
    this.isUserScrolling.set(false);
    this.shouldScrollToBottom.set(true);

    try {
      await this.chatService.sendMessage(content);
    } catch (error) {
      console.error('Failed to send message:', error);
      this.errorMessage.set('Failed to send message. Please try again.');
    }
  }

  async onInputSubmit(content: string): Promise<void> {
    await this.onMessageSubmit(content);
  }

  async sendQuickMessage(content: string): Promise<void> {
    await this.onMessageSubmit(content);
  }

  clearChat(): void {
    if (confirm('Are you sure you want to clear the chat history?')) {
      this.chatService.clearConversation();
      this.clearError();
    }
  }

  toggleChatHistory(): void {
    this.showChatHistory.update(show => !show);
    // TODO: Implement chat history sidebar
  }

  clearError(): void {
    this.errorMessage.set(null);
  }

  private scrollToBottom(): void {
    try {
      if (this.scrollAnchor) {
        this.scrollAnchor.nativeElement.scrollIntoView({
          behavior: 'smooth',
          block: 'end'
        });
      }
    } catch (error) {
      console.warn('Could not scroll to bottom:', error);
    }
  }

  // Manual scroll to bottom triggered by user button click
  scrollToBottomManual(): void {
    this.isUserScrolling.set(false); // Reset user scrolling flag
    this.shouldScrollToBottom.set(true);
    this.scrollToBottom();
  }

  // Format message content with basic markdown support
  formatMessageContent(content: string): string {
    if (!content) return '';

    // Convert basic markdown to HTML
    let formatted = content
      // Bold text: **text** or __text__
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/__(.*?)__/g, '<strong>$1</strong>')
      // Italic text: *text* or _text_ (but avoid conflicts with list markers)
      .replace(/(?<!\*)\*([^*\n]+?)\*(?!\*)/g, '<em>$1</em>')
      .replace(/(?<!_)_([^_\n]+?)_(?!_)/g, '<em>$1</em>')
      // Code: `text`
      .replace(/`(.*?)`/g, '<code>$1</code>')
      // Line breaks (preserve paragraph structure)
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      // Lists: * item or - item (improved pattern)
      .replace(/^[\*\-]\s+(.+)$/gm, '<div class="list-item">• $1</div>')
      // Numbers in lists: 1. item
      .replace(/^\d+\.\s+(.+)$/gm, '<div class="list-item numbered">$1</div>');

    // Wrap content in paragraphs if not already wrapped
    if (!formatted.includes('<p>') && !formatted.includes('<div class="list-item">')) {
      formatted = `<p>${formatted}</p>`;
    } else if (formatted.includes('<p>')) {
      formatted = `<p>${formatted}</p>`;
    }

    return formatted;
  }

  // Format message timestamp
  formatMessageTime(timestamp: Date): string {
    if (!timestamp) return '';

    const now = new Date();
    const messageDate = new Date(timestamp);
    
    // Handle invalid dates
    if (isNaN(messageDate.getTime())) {
      console.warn('Invalid timestamp provided:', timestamp);
      return '';
    }

    const diffInMs = now.getTime() - messageDate.getTime();
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    // Handle future timestamps (clock skew)
    if (diffInMs < 0) {
      return 'Just now';
    }

    // Less than 1 minute
    if (diffInMinutes < 1) {
      return 'Just now';
    }
    
    // Less than 1 hour
    if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`;
    }
    
    // Less than 24 hours (same day)
    if (diffInHours < 24 && messageDate.getDate() === now.getDate()) {
      return `${diffInHours}h ago`;
    }
    
    // Yesterday
    if (diffInDays === 1) {
      return `Yesterday ${messageDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }
    
    // Within a week
    if (diffInDays < 7) {
      const dayName = messageDate.toLocaleDateString([], { weekday: 'short' });
      const time = messageDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      return `${dayName} ${time}`;
    }
    
    // More than a week ago
    return messageDate.toLocaleDateString([], { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  // Scroll event handler to disable auto-scroll when user scrolls up
  onScroll() {
    // Throttle scroll events to prevent excessive firing
    const now = Date.now();
    if (now - this.lastScrollTime < 50) { // 50ms throttle
      return;
    }
    this.lastScrollTime = now;

    const element = this.messagesContainer?.nativeElement;
    if (!element) return;

    // Set user scrolling flag when user scrolls manually
    this.isUserScrolling.set(true);

    // Clear existing timeout
    if (this.scrollTimeoutId) {
      clearTimeout(this.scrollTimeoutId);
    }

    // Clear user scrolling flag after 150ms of no scrolling
    this.scrollTimeoutId = setTimeout(() => {
      this.isUserScrolling.set(false);
    }, 150);

    // Update should scroll to bottom based on position
    const scrollHeight = element.scrollHeight;
    const scrollTop = element.scrollTop;
    const clientHeight = element.clientHeight;

    this.shouldScrollToBottom.set(
      scrollTop + clientHeight >= scrollHeight - 10
    );
  }
}
