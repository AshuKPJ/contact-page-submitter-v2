// src/config/environment.js - Environment Configuration

const getEnvironmentVariable = (key, defaultValue) => {
  // Try different ways to get environment variables
  
  // 1. Create React App (process.env)
  if (typeof process !== 'undefined' && process.env && process.env[key]) {
    return process.env[key];
  }
  
  // 2. Vite (import.meta.env)
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env[key]) {
    return import.meta.env[key];
  }
  
  // 3. Window global (for runtime config)
  if (typeof window !== 'undefined' && window.ENV && window.ENV[key]) {
    return window.ENV[key];
  }
  
  // 4. Default value
  return defaultValue;
};

// Development vs Production detection
const isDevelopment = () => {
  if (typeof process !== 'undefined' && process.env) {
    return process.env.NODE_ENV === 'development';
  }
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    return import.meta.env.DEV;
  }
  return window.location.hostname === 'localhost';
};

// Environment configuration
const environment = {
  // API Configuration
  API_URL: getEnvironmentVariable('REACT_APP_API_URL', 
    isDevelopment() ? 'http://localhost:8000' : 'https://api.yourapp.com'
  ),
  
  // WebSocket URL (auto-generated from API URL)
  WS_URL: (() => {
    const apiUrl = getEnvironmentVariable('REACT_APP_API_URL', 'http://localhost:8000');
    return apiUrl.replace('http', 'ws').replace('https', 'wss');
  })(),
  
  // Feature Flags
  ENABLE_WEBSOCKET: getEnvironmentVariable('REACT_APP_ENABLE_WEBSOCKET', 'true') === 'true',
  ENABLE_DEBUG: getEnvironmentVariable('REACT_APP_DEBUG', isDevelopment() ? 'true' : 'false') === 'true',
  
  // App Configuration
  APP_NAME: getEnvironmentVariable('REACT_APP_NAME', 'Campaign Manager'),
  APP_VERSION: getEnvironmentVariable('REACT_APP_VERSION', '1.0.0'),
  
  // Auth Configuration
  AUTH_TOKEN_KEY: 'auth_token',
  AUTH_REFRESH_KEY: 'refresh_token',
  
  // Pagination
  DEFAULT_PAGE_SIZE: parseInt(getEnvironmentVariable('REACT_APP_PAGE_SIZE', '50')),
  
  // Timeouts (in milliseconds)
  API_TIMEOUT: parseInt(getEnvironmentVariable('REACT_APP_API_TIMEOUT', '30000')),
  POLL_INTERVAL: parseInt(getEnvironmentVariable('REACT_APP_POLL_INTERVAL', '2000')),
  
  // Environment Type
  IS_DEVELOPMENT: isDevelopment(),
  IS_PRODUCTION: !isDevelopment(),
};

// Log configuration in development
if (environment.ENABLE_DEBUG) {
  console.log('Environment Configuration:', {
    API_URL: environment.API_URL,
    WS_URL: environment.WS_URL,
    IS_DEVELOPMENT: environment.IS_DEVELOPMENT
  });
}

export default environment;