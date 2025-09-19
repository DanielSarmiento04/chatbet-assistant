import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, BehaviorSubject, throwError, of } from 'rxjs';
import { map, catchError, tap, switchMap } from 'rxjs/operators';
import { Router } from '@angular/router';
import {
  User,
  UserPreferences,
  ApiResponse,
  ApiErrorResponse
} from '../models';
import { ApiService } from './api.service';
import { environment } from '../../environments/environment';

/**
 * Authentication service for ChatBet application.
 * Manages user authentication, session, and profile using Angular 19 signals.
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiService = inject(ApiService);
  private readonly router = inject(Router);

  // Authentication state signals
  private readonly userSignal = signal<User | null>(null);
  private readonly tokenSignal = signal<string | null>(null);
  private readonly isLoadingSignal = signal<boolean>(false);
  private readonly authErrorSignal = signal<string | null>(null);

  // Readonly accessors
  readonly user = this.userSignal.asReadonly();
  readonly token = this.tokenSignal.asReadonly();
  readonly isLoading = this.isLoadingSignal.asReadonly();
  readonly authError = this.authErrorSignal.asReadonly();

  // Computed values
  readonly isAuthenticated = computed(() => this.userSignal() !== null && this.tokenSignal() !== null);
  readonly userId = computed(() => this.userSignal()?.id);
  readonly username = computed(() => this.userSignal()?.username);
  readonly userEmail = computed(() => this.userSignal()?.email);
  readonly userBalance = computed(() => this.userSignal()?.balance || 0);
  readonly userCurrency = computed(() => this.userSignal()?.currency || 'EUR');
  readonly isVerified = computed(() => this.userSignal()?.isVerified || false);
  readonly userPreferences = computed(() => this.userSignal()?.preferences);

  constructor() {
    // Initialize from stored token on app start
    this.initializeFromStorage();
  }

  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<boolean> {
    try {
      this.isLoadingSignal.set(true);
      this.authErrorSignal.set(null);

      const response = await this.apiService.auth.login({ email, password }).toPromise();

      if (response) {
        this.setAuthData(response.user, response.token);
        return true;
      }

      return false;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      this.authErrorSignal.set(errorMessage);
      return false;

    } finally {
      this.isLoadingSignal.set(false);
    }
  }

  /**
   * Register new user account
   */
  async register(email: string, password: string, username: string): Promise<boolean> {
    try {
      this.isLoadingSignal.set(true);
      this.authErrorSignal.set(null);

      const response = await this.apiService.auth.register({ email, password, username }).toPromise();

      if (response) {
        this.setAuthData(response.user, response.token);
        return true;
      }

      return false;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      this.authErrorSignal.set(errorMessage);
      return false;

    } finally {
      this.isLoadingSignal.set(false);
    }
  }

  /**
   * Logout user and clear session
   */
  async logout(): Promise<void> {
    try {
      this.isLoadingSignal.set(true);

      // Call logout API if user is authenticated
      if (this.isAuthenticated()) {
        await this.apiService.auth.logout().toPromise();
      }

    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);

    } finally {
      this.clearAuthData();
      this.isLoadingSignal.set(false);

      // Redirect to home page
      this.router.navigate(['/']);
    }
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<boolean> {
    try {
      if (!this.tokenSignal()) {
        return false;
      }

      const response = await this.apiService.auth.refreshToken().toPromise();

      if (response?.token) {
        this.tokenSignal.set(response.token);
        this.storeToken(response.token);
        return true;
      }

      return false;

    } catch (error) {
      // Clear auth data if refresh fails
      this.clearAuthData();
      return false;
    }
  }

  /**
   * Load user profile
   */
  async loadProfile(): Promise<void> {
    try {
      if (!this.isAuthenticated()) {
        return;
      }

      this.isLoadingSignal.set(true);

      const user = await this.apiService.auth.getProfile().toPromise();

      if (user) {
        this.userSignal.set(user);
        this.storeUser(user);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load profile';
      this.authErrorSignal.set(errorMessage);

    } finally {
      this.isLoadingSignal.set(false);
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(updates: Partial<User>): Promise<boolean> {
    try {
      if (!this.isAuthenticated()) {
        return false;
      }

      this.isLoadingSignal.set(true);
      this.authErrorSignal.set(null);

      const updatedUser = await this.apiService.auth.updateProfile(updates).toPromise();

      if (updatedUser) {
        this.userSignal.set(updatedUser);
        this.storeUser(updatedUser);
        return true;
      }

      return false;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update profile';
      this.authErrorSignal.set(errorMessage);
      return false;

    } finally {
      this.isLoadingSignal.set(false);
    }
  }

  /**
   * Update user preferences
   */
  async updatePreferences(preferences: Partial<UserPreferences>): Promise<boolean> {
    const currentUser = this.userSignal();

    if (!currentUser) {
      return false;
    }

    const updatedPreferences = { ...currentUser.preferences, ...preferences };
    const updates = { preferences: updatedPreferences };

    return this.updateProfile(updates);
  }

  /**
   * Get current user balance
   */
  async refreshBalance(): Promise<void> {
    try {
      if (!this.isAuthenticated()) {
        return;
      }

      const balanceData = await this.apiService.auth.getBalance().toPromise();

      if (balanceData) {
        this.userSignal.update(user => {
          if (user) {
            return { ...user, balance: balanceData.balance, currency: balanceData.currency };
          }
          return user;
        });
      }

    } catch (error) {
      console.warn('Failed to refresh balance:', error);
    }
  }

  /**
   * Check if token is expired or about to expire
   */
  isTokenExpired(): boolean {
    const token = this.tokenSignal();

    if (!token) {
      return true;
    }

    try {
      // Decode JWT token to check expiration
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      const now = Date.now();
      const buffer = environment.auth.tokenExpiryBuffer;

      return now >= (exp - buffer);

    } catch (error) {
      // If we can't decode the token, consider it expired
      return true;
    }
  }

  /**
   * Clear authentication error
   */
  clearError(): void {
    this.authErrorSignal.set(null);
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(permission: string): boolean {
    const user = this.userSignal();
    // This would be implemented based on your permission system
    // For now, just return true for authenticated users
    return !!user;
  }

  /**
   * Set authentication data
   */
  private setAuthData(user: User, token: string): void {
    this.userSignal.set(user);
    this.tokenSignal.set(token);

    // Store in localStorage
    this.storeUser(user);
    this.storeToken(token);

    // Clear any previous errors
    this.authErrorSignal.set(null);
  }

  /**
   * Clear authentication data
   */
  private clearAuthData(): void {
    this.userSignal.set(null);
    this.tokenSignal.set(null);

    // Clear from localStorage
    this.clearStorage();

    // Clear errors
    this.authErrorSignal.set(null);
  }

  /**
   * Initialize authentication from stored data
   */
  private initializeFromStorage(): void {
    try {
      const storedToken = localStorage.getItem(environment.auth.tokenKey);
      const storedUserData = localStorage.getItem('chatbet_user');

      if (storedToken && storedUserData) {
        const user = JSON.parse(storedUserData) as User;

        // Check if token is expired
        if (!this.isTokenExpiredStatic(storedToken)) {
          this.userSignal.set(user);
          this.tokenSignal.set(storedToken);
        } else {
          // Clear expired data
          this.clearStorage();
        }
      }

    } catch (error) {
      console.warn('Failed to initialize auth from storage:', error);
      this.clearStorage();
    }
  }

  /**
   * Store user data in localStorage
   */
  private storeUser(user: User): void {
    try {
      localStorage.setItem('chatbet_user', JSON.stringify(user));
    } catch (error) {
      console.warn('Failed to store user data:', error);
    }
  }

  /**
   * Store token in localStorage
   */
  private storeToken(token: string): void {
    try {
      localStorage.setItem(environment.auth.tokenKey, token);
    } catch (error) {
      console.warn('Failed to store token:', error);
    }
  }

  /**
   * Clear all stored authentication data
   */
  private clearStorage(): void {
    try {
      localStorage.removeItem(environment.auth.tokenKey);
      localStorage.removeItem(environment.auth.refreshTokenKey);
      localStorage.removeItem('chatbet_user');
    } catch (error) {
      console.warn('Failed to clear storage:', error);
    }
  }

  /**
   * Static method to check if token is expired (for initialization)
   */
  private isTokenExpiredStatic(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000;
      const now = Date.now();
      const buffer = environment.auth.tokenExpiryBuffer;

      return now >= (exp - buffer);

    } catch (error) {
      return true;
    }
  }

  /**
   * Get auth header for HTTP requests
   */
  getAuthHeader(): { Authorization: string } | {} {
    const token = this.tokenSignal();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  /**
   * Check if current user is guest (not authenticated)
   */
  isGuest(): boolean {
    return !this.isAuthenticated();
  }

  /**
   * Get user avatar URL or generate placeholder
   */
  getUserAvatar(): string {
    const user = this.userSignal();

    if (user?.avatar) {
      return user.avatar;
    }

    // Generate placeholder avatar based on username
    const username = user?.username || 'Guest';
    const initials = username.substring(0, 2).toUpperCase();
    return `https://ui-avatars.com/api/?name=${initials}&background=random&size=40`;
  }
}
