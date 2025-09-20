import { Component, inject, signal, OnInit } from '@angular/core';
import { ChatInterfaceComponent } from '../../components/chat-interface/chat-interface.component';
import { AuthService } from '../../services/auth.service';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    CommonModule,
    ChatInterfaceComponent,
    MatProgressBarModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule
  ],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent implements OnInit {
  private readonly authService = inject(AuthService);

  // UI state signals
  readonly isInitializing = signal(true);
  readonly initializationError = signal<string | null>(null);

  // Auth state from service
  readonly isAuthenticated = this.authService.isAuthenticated;
  readonly isAuthLoading = this.authService.isLoading;
  readonly authError = this.authService.authError;

  async ngOnInit() {
    await this.initializeAuthentication();
  }

  /**
   * Initialize authentication for chat functionality
   */
  private async initializeAuthentication(): Promise<void> {
    try {
      this.isInitializing.set(true);
      this.initializationError.set(null);

      // Check if already authenticated
      if (this.isAuthenticated()) {
        console.log('User already authenticated');
        return;
      }

      // Generate authentication token for ChatBet API
      console.log('Generating authentication token...');
      const success = await this.authService.generateAuthToken();

      if (!success) {
        throw new Error('Failed to generate authentication token');
      }

      console.log('Authentication token generated successfully');

    } catch (error) {
      console.error('Authentication initialization failed:', error);
      const errorMessage = error instanceof Error ? error.message : 'Authentication failed';
      this.initializationError.set(errorMessage);

    } finally {
      this.isInitializing.set(false);
    }
  }

  /**
   * Retry authentication
   */
  async retryAuthentication(): Promise<void> {
    await this.initializeAuthentication();
  }
}
