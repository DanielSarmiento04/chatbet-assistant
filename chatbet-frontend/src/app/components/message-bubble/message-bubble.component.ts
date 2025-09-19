import { Component, Input, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ChatMessage, MessageRole, MessageType } from '../../models';
import { formatDate, formatOdds } from '../../utils/common.utils';

@Component({
  selector: 'app-message-bubble',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
    MatTooltipModule
  ],
  templateUrl: './message-bubble.component.html',
  styleUrl: './message-bubble.component.scss'
})
export class MessageBubbleComponent {
  @Input({ required: true }) message!: ChatMessage;
  @Input() isLatest = false;
  @Input() showTimestamp = true;
  @Input() showAvatar = true;

  // Expose enums to template
  readonly MessageRole = MessageRole;
  readonly MessageType = MessageType;

  // Component state
  isExpanded = signal(false);
  showActions = signal(false);

  // Computed properties
  isUserMessage = computed(() => this.message.role === MessageRole.USER);
  isAssistantMessage = computed(() => this.message.role === MessageRole.ASSISTANT);
  isSystemMessage = computed(() => this.message.role === MessageRole.SYSTEM);
  isErrorMessage = computed(() => this.message.hasError || this.message.messageType === MessageType.ERROR);

  messageIcon = computed(() => {
    if (this.isUserMessage()) return 'person';
    if (this.isSystemMessage()) return 'info';
    if (this.isErrorMessage()) return 'error';
    return 'smart_toy';
  });

  messageTypeIcon = computed(() => {
    switch (this.message.messageType) {
      case MessageType.MATCH_CARD:
        return 'sports_soccer';
      case MessageType.ODDS_TABLE:
        return 'trending_up';
      case MessageType.RECOMMENDATION:
        return 'lightbulb';
      case MessageType.TOURNAMENT_INFO:
        return 'emoji_events';
      case MessageType.ERROR:
        return 'error';
      default:
        return null;
    }
  });

  formattedTimestamp = computed(() => {
    return formatDate(this.message.timestamp, 'short');
  });

  messageClasses = computed(() => {
    const classes = ['message-bubble'];

    if (this.isUserMessage()) classes.push('user-message');
    if (this.isAssistantMessage()) classes.push('assistant-message');
    if (this.isSystemMessage()) classes.push('system-message');
    if (this.isErrorMessage()) classes.push('error-message');
    if (this.message.isLoading) classes.push('loading-message');
    if (this.isLatest) classes.push('latest-message');

    return classes.join(' ');
  });

  toggleExpanded(): void {
    this.isExpanded.update(expanded => !expanded);
  }

  toggleActions(): void {
    this.showActions.update(show => !show);
  }

  copyMessage(): void {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(this.message.content).then(() => {
        // Could show a toast notification here
        console.log('Message copied to clipboard');
      }).catch(err => {
        console.error('Failed to copy message:', err);
      });
    }
  }

  retryMessage(): void {
    // Emit an event to parent component to retry sending this message
    // This would need to be implemented as an Output event
  }

  formatOddsValue(odds: number): string {
    return formatOdds(odds);
  }
}
