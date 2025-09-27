// src/services/systemLogger.js
import api from './api';

/**
 * System logger for tracking user actions
 */
export const logSystemAction = async (action, details = {}) => {
  try {
    await api.post('/system-logs', {
      action,
      details: typeof details === 'string' ? details : JSON.stringify(details),
      user_agent: navigator.userAgent,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to log system action:', error);
  }
};

/**
 * Log authentication events
 */
export const logAuthEvent = async (event, data = {}) => {
  return logSystemAction(`AUTH_${event}`, data);
};

/**
 * Log campaign events
 */
export const logCampaignEvent = async (event, campaignId, data = {}) => {
  return logSystemAction(`CAMPAIGN_${event}`, {
    campaign_id: campaignId,
    ...data
  });
};

/**
 * Log submission events
 */
export const logSubmissionEvent = async (event, submissionId, data = {}) => {
  return logSystemAction(`SUBMISSION_${event}`, {
    submission_id: submissionId,
    ...data
  });
};