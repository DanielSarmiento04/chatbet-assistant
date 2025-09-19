/**
 * Development environment configuration for ChatBet frontend.
 */

export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000/ws',
  enableLogging: true,
  enableAnalytics: false,

  // Feature flags for development
  features: {
    voiceInput: true,
    darkMode: true,
    realTimeUpdates: true,
    pushNotifications: false,
    betSimulation: true,
    advancedAnalytics: true
  },

  // Development specific settings
  debugMode: true,
  mockData: false, // Set to true to use mock data instead of API
  refreshInterval: 30000, // 30 seconds for live data updates

  // Cache settings
  cache: {
    defaultTtl: 5 * 60 * 1000, // 5 minutes
    matchDataTtl: 2 * 60 * 1000, // 2 minutes for match data
    oddsDataTtl: 30 * 1000, // 30 seconds for odds
    userDataTtl: 10 * 60 * 1000 // 10 minutes for user data
  },

  // Authentication
  auth: {
    tokenKey: 'chatbet_token',
    refreshTokenKey: 'chatbet_refresh_token',
    tokenExpiryBuffer: 5 * 60 * 1000 // 5 minutes buffer
  },

  // WebSocket configuration
  websocket: {
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
    heartbeatInterval: 30000,
    connectionTimeout: 10000
  },

  // UI configuration
  ui: {
    pageSize: 20,
    animationDuration: 300,
    toastDuration: 5000,
    typingIndicatorDelay: 1000,
    maxMessageLength: 2000
  },

  // Sports data configuration
  sports: {
    defaultSport: 'football',
    maxOddsAge: 15 * 60 * 1000, // 15 minutes
    maxMatchesPerPage: 50,
    popularLeagues: [
      'premier-league',
      'la-liga',
      'bundesliga',
      'serie-a',
      'ligue-1',
      'champions-league'
    ]
  },

  // Betting configuration
  betting: {
    minStake: 1,
    maxStake: 1000,
    defaultStake: 10,
    currencies: ['EUR', 'USD', 'GBP'],
    defaultCurrency: 'EUR',
    oddsFormat: 'decimal' // 'decimal', 'fractional', 'american'
  },

  // Analytics and monitoring
  analytics: {
    trackPageViews: true,
    trackUserInteractions: true,
    trackErrors: true,
    batchSize: 10,
    flushInterval: 30000
  }
};
