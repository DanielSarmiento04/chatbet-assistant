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
    // Cleanup handled by services
  }

  ngAfterViewChecked(): void {
    // Auto-scroll to bottom when new messages arrive
    if (this.shouldScrollToBottom()) {
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

  // Scroll event handler to disable auto-scroll when user scrolls up
  onScroll(): void {
    if (this.messagesContainer) {
      const element = this.messagesContainer.nativeElement;
      const isScrolledToBottom = element.scrollHeight - element.scrollTop <= element.clientHeight + 50;
      this.shouldScrollToBottom.set(isScrolledToBottom);
    }
  }
}
