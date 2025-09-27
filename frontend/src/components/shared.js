// src/components/shared.js - Shared Components and Utility Functions
import React from 'react';
import { CheckCircle, XCircle, Clock, AlertTriangle, Pause, Play } from 'lucide-react';

// ============ UTILITY FUNCTIONS ============

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatDateShort = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

export const formatNumber = (value) => {
  if (!value && value !== 0) return '0';
  return value.toLocaleString();
};

export const formatPercentage = (value) => {
  return `${Math.round(value || 0)}%`;
};

export const calculateSuccessRate = (successful, total) => {
  if (!total) return 0;
  return Math.round((successful / total) * 100);
};

export const calculateProgress = (processed, total) => {
  if (!total) return 0;
  return Math.round((processed / total) * 100);
};

export const formatDuration = (seconds) => {
  if (!seconds) return '0s';
  
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  } else if (seconds < 3600) {
    return `${Math.round(seconds / 60)}m`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.round((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
};

export const getTimeAgo = (dateString) => {
  if (!dateString) return 'N/A';
  
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return formatDateShort(dateString);
};

// ============ STATUS CONFIGURATIONS ============

export const getStatusConfig = (status) => {
  const configs = {
    'RUNNING': {
      color: 'text-green-600 bg-green-100',
      icon: Play,
      label: 'Running'
    },
    'COMPLETED': {
      color: 'text-blue-600 bg-blue-100',
      icon: CheckCircle,
      label: 'Completed'
    },
    'PAUSED': {
      color: 'text-yellow-600 bg-yellow-100',
      icon: Pause,
      label: 'Paused'
    },
    'FAILED': {
      color: 'text-red-600 bg-red-100',
      icon: XCircle,
      label: 'Failed'
    },
    'DRAFT': {
      color: 'text-gray-600 bg-gray-100',
      icon: Clock,
      label: 'Draft'
    },
    'QUEUED': {
      color: 'text-purple-600 bg-purple-100',
      icon: Clock,
      label: 'Queued'
    },
    'PROCESSING': {
      color: 'text-indigo-600 bg-indigo-100',
      icon: Clock,
      label: 'Processing'
    },
    'STOPPED': {
      color: 'text-gray-600 bg-gray-100',
      icon: XCircle,
      label: 'Stopped'
    },
    'CANCELLED': {
      color: 'text-red-600 bg-red-100',
      icon: XCircle,
      label: 'Cancelled'
    }
  };
  
  return configs[status] || {
    color: 'text-gray-600 bg-gray-100',
    icon: AlertTriangle,
    label: status || 'Unknown'
  };
};

// ============ SHARED COMPONENTS ============

export const StatusBadge = ({ status, showIcon = false, className = '' }) => {
  const config = getStatusConfig(status);
  const Icon = config.icon;
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color} ${className}`}>
      {showIcon && <Icon className="w-3 h-3 mr-1" />}
      {config.label}
    </span>
  );
};

export const ProgressBar = ({ 
  progress, 
  total, 
  successful = 0, 
  failed = 0, 
  showStats = true,
  height = 'h-2',
  className = ''
}) => {
  const percentage = calculateProgress(progress, total);
  
  return (
    <div className={`w-full ${className}`}>
      {showStats && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs text-gray-600">{percentage}% complete</span>
          <span className="text-xs text-gray-500">{progress}/{total}</span>
        </div>
      )}
      
      <div className={`w-full bg-gray-200 rounded-full ${height}`}>
        <div
          className={`bg-gradient-to-r from-blue-500 to-indigo-600 ${height} rounded-full transition-all duration-300`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        ></div>
      </div>
      
      {showStats && (successful > 0 || failed > 0) && (
        <div className="flex items-center space-x-4 mt-2">
          {successful > 0 && (
            <div className="flex items-center text-xs text-gray-600">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
              Success: {successful}
            </div>
          )}
          {failed > 0 && (
            <div className="flex items-center text-xs text-gray-600">
              <div className="w-2 h-2 bg-red-500 rounded-full mr-1"></div>
              Failed: {failed}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const CampaignStats = ({ campaign, className = '' }) => {
  const stats = [
    {
      label: 'Websites',
      value: formatNumber(campaign.total_websites || 0),
      icon: '🌐'
    },
    {
      label: 'Successful', 
      value: formatNumber(campaign.successful || 0),
      icon: '✅',
      color: 'text-green-600'
    },
    {
      label: 'Failed',
      value: formatNumber(campaign.failed || 0), 
      icon: '❌',
      color: 'text-red-600'
    },
    {
      label: 'Success Rate',
      value: formatPercentage(calculateSuccessRate(campaign.successful, campaign.total_websites)),
      icon: '📊',
      color: 'text-blue-600'
    }
  ];
  
  return (
    <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 ${className}`}>
      {stats.map((stat, index) => (
        <div key={index} className="text-center">
          <div className="text-xs text-gray-500 mb-1">{stat.label}</div>
          <div className={`font-semibold ${stat.color || 'text-gray-900'}`}>
            {stat.value}
          </div>
        </div>
      ))}
    </div>
  );
};

export const LoadingSpinner = ({ size = 'medium', className = '' }) => {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-8 w-8', 
    large: 'h-12 w-12'
  };
  
  return (
    <div className={`animate-spin rounded-full border-2 border-b-transparent border-indigo-600 ${sizeClasses[size]} ${className}`}></div>
  );
};

export const EmptyState = ({ 
  icon: Icon, 
  title, 
  description, 
  action,
  className = ''
}) => (
  <div className={`text-center py-12 ${className}`}>
    {Icon && <Icon className="w-12 h-12 text-gray-400 mx-auto mb-4" />}
    <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
    <p className="text-gray-500 mb-6">{description}</p>
    {action && action}
  </div>
);

export const StatCard = ({ 
  title, 
  value, 
  icon: Icon, 
  color = 'text-blue-600', 
  trend, 
  trendValue,
  onClick,
  className = ''
}) => (
  <div 
    className={`bg-white p-6 rounded-lg shadow-sm border transition-colors ${
      onClick ? 'cursor-pointer hover:bg-gray-50' : ''
    } ${className}`}
    onClick={onClick}
  >
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className={`text-3xl font-bold ${color}`}>{value}</p>
        {trend && trendValue && (
          <div className="flex items-center mt-2">
            <span className={`text-sm ${
              trend === 'up' ? 'text-green-600' : 
              trend === 'down' ? 'text-red-600' : 
              'text-gray-600'
            }`}>
              {trend === 'up' ? '↗' : trend === 'down' ? '↘' : '→'} {trendValue}
            </span>
          </div>
        )}
      </div>
      {Icon && <Icon className={`w-8 h-8 ${color.replace('text-', 'text-').replace('-600', '-500')}`} />}
    </div>
  </div>
);

// ============ DATA VALIDATION ============

export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validateUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const validateCSVFile = (file) => {
  const errors = [];
  
  if (!file) {
    errors.push('File is required');
    return errors;
  }
  
  if (!file.name.toLowerCase().endsWith('.csv')) {
    errors.push('File must be a CSV file');
  }
  
  if (file.size > 10 * 1024 * 1024) { // 10MB
    errors.push('File size must be less than 10MB');
  }
  
  if (file.size === 0) {
    errors.push('File appears to be empty');
  }
  
  return errors;
};

// ============ LOCAL STORAGE HELPERS ============

export const setLocalStorageItem = (key, value) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('Error saving to localStorage:', error);
  }
};

export const getLocalStorageItem = (key, defaultValue = null) => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error('Error reading from localStorage:', error);
    return defaultValue;
  }
};

export const removeLocalStorageItem = (key) => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Error removing from localStorage:', error);
  }
};

// ============ DEBOUNCE HELPER ============

export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// ============ API ERROR HANDLING ============

export const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    const message = data?.detail || data?.message || 'An error occurred';
    
    switch (status) {
      case 400:
        return 'Invalid request. Please check your input.';
      case 401:
        return 'Please log in to continue.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 422:
        return message; // Validation errors
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return message;
    }
  } else if (error.code === 'ERR_NETWORK') {
    return 'Cannot connect to server. Please check your internet connection.';
  } else {
    return error.message || 'An unexpected error occurred';
  }
};

// ============ EXPORT ALL ============

export default {
  // Utility functions
  formatDate,
  formatDateShort,
  formatNumber,
  formatPercentage,
  calculateSuccessRate,
  calculateProgress,
  formatDuration,
  getTimeAgo,
  getStatusConfig,
  
  // Components
  StatusBadge,
  ProgressBar,
  CampaignStats,
  LoadingSpinner,
  EmptyState,
  StatCard,
  
  // Validation
  validateEmail,
  validateUrl,
  validateCSVFile,
  
  // Storage
  setLocalStorageItem,
  getLocalStorageItem,
  removeLocalStorageItem,
  
  // Helpers
  debounce,
  handleApiError
};