// API Configuration
export const API_CONFIG = {
  // Redis messages API polling configuration
  redisMessages: {
    // Server-triggered polling (primary method)
    serverTriggered: {
      enabled: true,
      timeout: 5000, // 5 seconds timeout for server notifications
    },
    // Fallback polling (secondary method)
    fallback: {
      enabled: true,
      pollingInterval: 30000, // 30 seconds fallback interval
      maxRetries: 3,
      retryDelay: 5000, // 5 seconds between retries
    },
    // Legacy continuous polling (for backward compatibility)
    continuous: {
      enabled: false, // Disabled in favor of hybrid approach
      pollingInterval: 2000,
    }
  },
  
  // Metrics API polling interval (in milliseconds)
  metrics: {
    pollingInterval: 30000, // 30 seconds (increased for more stable metrics)
    enabled: true,
  },
  
  // Message history configuration
  messageHistory: {
    maxMessages: 1000, // Maximum number of messages to display (increased from 100)
    enableLimit: true, // Whether to apply the message limit
  },
  
  // API endpoints
  endpoints: {
    redisMessages: (sessionId: string) => `/chat/api/sessions/${sessionId}/messages/`,
    metrics: '/metrics',
  },
  
  // Request settings
  request: {
    timeout: 10000, // 10 seconds
    retries: 3,
    retryDelay: 1000, // 1 second
  },
};

// Helper function to get Redis messages polling interval
export const getRedisMessagesPollingInterval = () => API_CONFIG.redisMessages.continuous.pollingInterval;

// Helper function to get fallback polling interval
export const getFallbackPollingInterval = () => API_CONFIG.redisMessages.fallback.pollingInterval;

// Helper function to get metrics polling interval
export const getMetricsPollingInterval = () => API_CONFIG.metrics.pollingInterval;

// Helper function to check if Redis messages polling is enabled
export const isRedisMessagesPollingEnabled = () => API_CONFIG.redisMessages.continuous.enabled;

// Helper function to check if server-triggered polling is enabled
export const isServerTriggeredPollingEnabled = () => API_CONFIG.redisMessages.serverTriggered.enabled;

// Helper function to check if fallback polling is enabled
export const isFallbackPollingEnabled = () => API_CONFIG.redisMessages.fallback.enabled;

// Helper function to check if metrics polling is enabled
export const isMetricsPollingEnabled = () => API_CONFIG.metrics.enabled;

// Helper function to get message history limit
export const getMessageHistoryLimit = () => API_CONFIG.messageHistory.maxMessages;

// Helper function to check if message history limit is enabled
export const isMessageHistoryLimitEnabled = () => API_CONFIG.messageHistory.enableLimit;
