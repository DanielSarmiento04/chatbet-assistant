import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError, of } from 'rxjs';
import { map, catchError, retry, timeout, shareReplay } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  ChatRequest,
  ChatResponse,
  ConversationSummary,
  Match,
  Tournament,
  OddsComparison,
  BettingRecommendation,
  User,
  ApiResponse,
  ApiErrorResponse,
  PaginatedResponse,
  isApiError
} from '../models';

/**
 * Core API service for ChatBet application.
 * Handles all HTTP communication with the backend using Angular 19 best practices.
 */
@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  // Loading state signals
  private readonly loadingRequests = signal(new Set<string>());
  readonly isLoading = this.loadingRequests.asReadonly();

  // Error state
  private readonly errorSubject = new BehaviorSubject<ApiErrorResponse | null>(null);
  readonly error$ = this.errorSubject.asObservable();

  // Connection state
  private readonly connectionState = signal<'connected' | 'disconnected' | 'connecting'>('disconnected');
  readonly connectionStatus = this.connectionState.asReadonly();

  /**
   * Chat API endpoints
   */
  readonly chat = {
    sendMessage: (request: ChatRequest): Observable<ChatResponse> => {
      return this.post<ChatResponse>('/api/v1/chat/message', request, 'sendMessage');
    },

    getConversationHistory: (
      userId: string,
      sessionId?: string,
      limit = 20,
      offset = 0
    ): Observable<PaginatedResponse<ConversationSummary>> => {
      const params = new HttpParams()
        .set('limit', limit.toString())
        .set('offset', offset.toString())
        .set('session_id', sessionId || '');

      return this.get<PaginatedResponse<ConversationSummary>>(
        `/api/v1/chat/conversations/${userId}`,
        'getConversationHistory',
        { params }
      );
    },

    clearConversationHistory: (userId: string, sessionId?: string): Observable<{ message: string }> => {
      const params = sessionId ? new HttpParams().set('session_id', sessionId) : undefined;
      return this.delete<{ message: string }>(
        `/api/v1/chat/conversations/${userId}`,
        'clearConversationHistory',
        { params }
      );
    },

    getSupportedIntents: (): Observable<{ supported_intents: unknown[]; total_count: number }> => {
      return this.get<{ supported_intents: unknown[]; total_count: number }>(
        '/api/v1/chat/intents',
        'getSupportedIntents'
      ).pipe(
        shareReplay(1) // Cache the intents
      );
    }
  };

  /**
   * Sports data API endpoints
   */
  readonly sports = {
    getMatches: (filters?: {
      sport?: string;
      league?: string;
      team?: string;
      date?: string;
      status?: string;
    }): Observable<PaginatedResponse<Match>> => {
      const params = this.buildParams(filters);
      return this.get<PaginatedResponse<Match>>('/sports/matches', 'getMatches', { params });
    },

    getMatch: (matchId: string): Observable<Match> => {
      return this.get<Match>(`/sports/matches/${matchId}`, 'getMatch');
    },

    getTournaments: (filters?: {
      sport?: string;
      country?: string;
      season?: string;
    }): Observable<PaginatedResponse<Tournament>> => {
      const params = this.buildParams(filters);
      return this.get<PaginatedResponse<Tournament>>('/sports/tournaments', 'getTournaments', { params });
    },

    getTournament: (tournamentId: string): Observable<Tournament> => {
      return this.get<Tournament>(`/sports/tournaments/${tournamentId}`, 'getTournament');
    },

    getOdds: (matchId: string): Observable<OddsComparison> => {
      return this.get<OddsComparison>(`/sports/odds/${matchId}`, 'getOdds');
    },

    getRecommendations: (userId?: string): Observable<BettingRecommendation[]> => {
      const endpoint = userId ? `/sports/recommendations/${userId}` : '/sports/recommendations';
      return this.get<BettingRecommendation[]>(endpoint, 'getRecommendations');
    }
  };

  /**
   * User authentication and profile API endpoints
   */
  readonly auth = {
    generateToken: (): Observable<{ token: string }> => {
      return this.post<{ token: string }>('/api/v1/auth/generate_token', {}, 'generateToken');
    },

    validateToken: (): Observable<{ message: string }> => {
      return this.post<{ message: string }>('/api/v1/auth/validate_token', {}, 'validateToken');
    },

    getUserInfo: (): Observable<User> => {
      return this.get<User>('/api/v1/auth/user_info', 'getUserInfo');
    },

    refreshToken: (): Observable<{ token: string }> => {
      return this.post<{ token: string }>('/api/v1/auth/refresh_token', {}, 'refreshToken');
    },

    // Legacy methods (kept for potential future use)
    login: (credentials: { email: string; password: string }): Observable<{ user: User; token: string }> => {
      return this.post<{ user: User; token: string }>('/auth/login', credentials, 'login');
    },

    register: (userData: {
      email: string;
      password: string;
      username: string;
    }): Observable<{ user: User; token: string }> => {
      return this.post<{ user: User; token: string }>('/auth/register', userData, 'register');
    },

    logout: (): Observable<{ message: string }> => {
      return this.post<{ message: string }>('/auth/logout', {}, 'logout');
    },

    getProfile: (): Observable<User> => {
      return this.get<User>('/auth/profile', 'getProfile');
    },

    updateProfile: (userData: Partial<User>): Observable<User> => {
      return this.put<User>('/auth/profile', userData, 'updateProfile');
    },

    getBalance: (): Observable<{ balance: number; currency: string }> => {
      return this.get<{ balance: number; currency: string }>('/auth/balance', 'getBalance');
    }
  };

  /**
   * Health check endpoint
   */
  healthCheck(): Observable<{ status: string; timestamp: string }> {
    return this.get<{ status: string; timestamp: string }>('/health', 'healthCheck')
      .pipe(
        timeout(5000),
        catchError(() => of({ status: 'error', timestamp: new Date().toISOString() }))
      );
  }

  /**
   * Generic HTTP methods with loading state management
   */
  private get<T>(
    endpoint: string,
    operation: string,
    options?: { params?: HttpParams }
  ): Observable<T> {
    return this.handleRequest<T>(
      this.http.get<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, options),
      operation
    );
  }

  private post<T>(endpoint: string, body: unknown, operation: string): Observable<T> {
    return this.handleRequest<T>(
      this.http.post<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, body),
      operation
    );
  }

  private put<T>(endpoint: string, body: unknown, operation: string): Observable<T> {
    return this.handleRequest<T>(
      this.http.put<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, body),
      operation
    );
  }

  private delete<T>(
    endpoint: string,
    operation: string,
    options?: { params?: HttpParams }
  ): Observable<T> {
    return this.handleRequest<T>(
      this.http.delete<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, options),
      operation
    );
  }

  /**
   * Handle HTTP requests with loading states and error handling
   */
  private handleRequest<T>(
    request: Observable<ApiResponse<T>>,
    operation: string
  ): Observable<T> {
    // Add operation to loading set
    this.addLoadingOperation(operation);

    return request.pipe(
      timeout(environment.websocket.connectionTimeout),
      retry(2),
      map(response => {
        if (isApiError(response)) {
          throw new Error(response.error.message);
        }
        return response.data;
      }),
      catchError(error => this.handleError(error, operation)),
      // Remove operation from loading set regardless of success/failure
      // Using finalize would be better but we need to handle the loading state
      shareReplay(1)
    ).pipe(
      // Use a separate subscription to handle loading state cleanup
      map(data => {
        this.removeLoadingOperation(operation);
        return data;
      }),
      catchError(error => {
        this.removeLoadingOperation(operation);
        return throwError(() => error);
      })
    );
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: HttpErrorResponse | Error, operation: string): Observable<never> {
    let apiError: ApiErrorResponse;

    if (error instanceof HttpErrorResponse) {
      // Handle HTTP errors
      apiError = {
        error: {
          message: error.error?.message || error.message || 'An unexpected error occurred',
          code: error.status?.toString(),
          details: { operation, url: error.url, status: error.status }
        },
        success: false,
        timestamp: new Date()
      };
    } else {
      // Handle other errors
      apiError = {
        error: {
          message: error.message || 'An unexpected error occurred',
          details: { operation }
        },
        success: false,
        timestamp: new Date()
      };
    }

    // Update error state
    this.errorSubject.next(apiError);

    if (environment.enableLogging) {
      console.error(`API operation failed [${operation}]:`, error);
    }

    return throwError(() => apiError);
  }

  /**
   * Build HTTP params from filters object
   */
  private buildParams(filters?: Record<string, string | undefined>): HttpParams {
    let params = new HttpParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params = params.set(key, value);
        }
      });
    }

    return params;
  }

  /**
   * Loading state management
   */
  private addLoadingOperation(operation: string): void {
    this.loadingRequests.update(current => new Set([...current, operation]));
  }

  private removeLoadingOperation(operation: string): void {
    this.loadingRequests.update(current => {
      const updated = new Set(current);
      updated.delete(operation);
      return updated;
    });
  }

  /**
   * Check if a specific operation is loading
   */
  isOperationLoading(operation: string): boolean {
    return this.loadingRequests().has(operation);
  }

  /**
   * Check if any operation is loading
   */
  get hasLoadingOperations(): boolean {
    return this.loadingRequests().size > 0;
  }

  /**
   * Clear all errors
   */
  clearError(): void {
    this.errorSubject.next(null);
  }

  /**
   * Set connection status
   */
  setConnectionStatus(status: 'connected' | 'disconnected' | 'connecting'): void {
    this.connectionState.set(status);
  }
}
