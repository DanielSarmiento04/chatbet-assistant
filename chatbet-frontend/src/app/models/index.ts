/**
 * Re-export all models for easy importing throughout the application.
 */

// Chat and conversation models
export * from './chat.models';

// Sports and betting models
export * from './sports.models';

// Import specific types for type guards
import type { ChatMessage } from './chat.models';
import type { Match } from './sports.models';

// Additional utility types
export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: Date;
}

export interface ApiErrorResponse {
  error: {
    message: string;
    code?: string;
    details?: Record<string, unknown>;
  };
  success: false;
  timestamp: Date;
}

// Configuration types
export interface AppConfig {
  apiUrl: string;
  wsUrl: string;
  enableLogging: boolean;
  environment: 'development' | 'production' | 'test';
  features: {
    voiceInput: boolean;
    darkMode: boolean;
    realTimeUpdates: boolean;
    pushNotifications: boolean;
  };
}

// Theme types
export interface ThemeConfig {
  primary: string;
  accent: string;
  warn: string;
  background: string;
  surface: string;
  mode: 'light' | 'dark';
}

// Loading states
export interface LoadingState {
  isLoading: boolean;
  operation?: string;
  progress?: number;
}

// Form validation types
export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

export interface FormState<T> {
  data: T;
  errors: ValidationError[];
  isValid: boolean;
  isDirty: boolean;
  isSubmitting: boolean;
}

// Navigation types
export interface NavigationItem {
  label: string;
  path: string;
  icon?: string;
  badge?: string | number;
  children?: NavigationItem[];
  isActive?: boolean;
  requiresAuth?: boolean;
}

// Notification types
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  duration?: number;
  actions?: NotificationAction[];
  timestamp: Date;
}

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary';
}

// Search types
export interface SearchResult<T> {
  items: T[];
  query: string;
  totalResults: number;
  searchTime: number;
  suggestions?: string[];
}

export interface SearchFilter {
  field: string;
  operator: 'equals' | 'contains' | 'startsWith' | 'endsWith' | 'greaterThan' | 'lessThan';
  value: unknown;
}

// Cache types
export interface CacheItem<T> {
  data: T;
  timestamp: Date;
  expiresAt: Date;
  key: string;
}

export interface CacheConfig {
  ttl: number; // Time to live in milliseconds
  maxSize?: number;
  keyPrefix?: string;
}

// Analytics types
export interface AnalyticsEvent {
  name: string;
  properties?: Record<string, unknown>;
  timestamp: Date;
  userId?: string;
  sessionId?: string;
}

// Feature flag types
export interface FeatureFlag {
  name: string;
  enabled: boolean;
  variant?: string;
  config?: Record<string, unknown>;
}

// Performance monitoring
export interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  timestamp: Date;
  labels?: Record<string, string>;
}

// Type guards
export const isApiError = (response: unknown): response is ApiErrorResponse => {
  return typeof response === 'object' &&
         response !== null &&
         'success' in response &&
         (response as { success: unknown }).success === false;
};

export const isChatMessage = (obj: unknown): obj is ChatMessage => {
  return typeof obj === 'object' &&
         obj !== null &&
         'id' in obj &&
         'content' in obj &&
         'role' in obj &&
         'timestamp' in obj;
};

export const isMatch = (obj: unknown): obj is Match => {
  return typeof obj === 'object' &&
         obj !== null &&
         'id' in obj &&
         'homeTeam' in obj &&
         'awayTeam' in obj &&
         'date' in obj;
};

// Utility functions for type conversion
export const convertToDate = (value: string | Date): Date => {
  return value instanceof Date ? value : new Date(value);
};

export const ensureArray = <T>(value: T | T[]): T[] => {
  return Array.isArray(value) ? value : [value];
};

export const safeParseJson = <T>(json: string, fallback: T): T => {
  try {
    return JSON.parse(json) as T;
  } catch {
    return fallback;
  }
};
