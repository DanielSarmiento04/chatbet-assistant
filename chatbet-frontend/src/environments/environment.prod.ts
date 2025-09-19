/**
 * Production environment configuration for ChatBet frontend.
 */

export const environment = {
  production: true,
  apiUrl: '/api',
  wsUrl: 'wss://your-domain.com/ws',
  enableLogging: false,
  enableAnalytics: true,

  // Feature flags for production
  features: {
    voiceInput: true,
    darkMode: true,
    realTimeUpdates: true,
    pushNotifications: true,
    betSimulation: false, // Disabled in production
    advancedAnalytics: true
  },

  // Production specific settings
  debugMode: false,
  mockData: false,
  refreshInterval: 60000, // 1 minute for live data updates

  // Cache settings (longer TTL for production)
  cache: {
    defaultTtl: 15 * 60 * 1000, // 15 minutes
    matchDataTtl: 5 * 60 * 1000, // 5 minutes for match data
    oddsDataTtl: 60 * 1000, // 1 minute for odds
    userDataTtl: 30 * 60 * 1000 // 30 minutes for user data
  },

  // Authentication
  auth: {
    tokenKey: 'chatbet_token',
    refreshTokenKey: 'chatbet_refresh_token',
    tokenExpiryBuffer: 5 * 60 * 1000 // 5 minutes buffer
  },

  // WebSocket configuration
  websocket: {
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    heartbeatInterval: 45000,
    connectionTimeout: 15000
  },

  // UI configuration
  ui: {
    pageSize: 20,
    animationDuration: 200, // Shorter for better performance
    toastDuration: 4000,
    typingIndicatorDelay: 800,
    maxMessageLength: 2000
  },

  // Sports data configuration
  sports: {
    defaultSport: 'football',
    maxOddsAge: 10 * 60 * 1000, // 10 minutes
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
    batchSize: 25,
    flushInterval: 60000
  }
};
