// src/services/telemetry.js
import api from './api';

/**
 * Enhanced telemetry service for tracking events
 */
export async function trackEvent({
  level = 'INFO',
  message,
  context = {},
  campaign_id,
  website_id,
  organization_id,
}) {
  try {
    await api.post('/logs/app', {
      level,
      message,
      context,
      campaign_id,
      website_id,
      organization_id,
    });
  } catch (e) {
    // Silent fail to avoid breaking UX
    console.warn('[telemetry] failed', e?.response?.data || e.message);
  }
}

/**
 * Track system events (admin only)
 */
export async function trackSystemEvent({
  message,
  context = {},
}) {
  try {
    await api.post('/logs/system', {
      level: 'INFO',
      message,
      context,
    });
  } catch (e) {
    console.warn('[telemetry] system event failed', e?.response?.data || e.message);
  }
}

/**
 * Track user actions
 */
export async function trackUserAction(action, properties = {}) {
  return trackEvent({
    level: 'INFO',
    message: `User action: ${action}`,
    context: { action, ...properties }
  });
}

/**
 * Track errors
 */
export async function trackError(error, context = {}) {
  return trackEvent({
    level: 'ERROR',
    message: error.message || 'Unknown error',
    context: {
      error: error.toString(),
      stack: error.stack,
      ...context
    }
  });
}

/**
 * Track performance metrics
 */
export async function trackPerformance(metric, value, context = {}) {
  return trackEvent({
    level: 'INFO',
    message: `Performance: ${metric}`,
    context: {
      metric,
      value,
      ...context
    }
  });
}