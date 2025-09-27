import React, { useState } from 'react';
import { 
  Link2, Zap, Globe, Settings, Plus, Check, X, AlertCircle,
  ChevronRight, ExternalLink, RefreshCw, Shield, Clock,
  Code, Terminal, Database, Server, Cloud, Package,
  Send, Download, Upload, Copy, Eye, EyeOff, 
  Activity, CheckCircle, XCircle, Info, Edit2, Trash2,
  Play, Pause, ArrowRight, Webhook, Bot, Mail,
  MessageSquare, Calendar, FileText, BarChart3
} from 'lucide-react';

const IntegrationsPage = () => {
  const [activeTab, setActiveTab] = useState('connected');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showWebhookModal, setShowWebhookModal] = useState(false);
  const [testingWebhook, setTestingWebhook] = useState(null);

  const connectedIntegrations = [
    {
      id: 1,
      name: 'Slack',
      description: 'Get notifications in your Slack workspace',
      icon: MessageSquare,
      status: 'connected',
      lastSync: '2 minutes ago',
      color: 'from-purple-500 to-pink-500',
      events: ['campaign.completed', 'submission.failed'],
      usage: '1,234 messages sent'
    },
    {
      id: 2,
      name: 'Google Sheets',
      description: 'Export data to Google Sheets automatically',
      icon: FileText,
      status: 'connected',
      lastSync: '1 hour ago',
      color: 'from-green-500 to-emerald-500',
      events: ['data.export'],
      usage: '56 sheets updated'
    },
    {
      id: 3,
      name: 'Zapier',
      description: 'Connect with 5000+ apps',
      icon: Zap,
      status: 'connected',
      lastSync: '3 hours ago',
      color: 'from-orange-500 to-red-500',
      events: ['all'],
      usage: '892 zaps triggered'
    }
  ];

  const availableIntegrations = [
    {
      id: 4,
      name: 'Salesforce',
      description: 'Sync contacts and campaigns with Salesforce CRM',
      icon: Cloud,
      category: 'crm',
      color: 'from-blue-500 to-cyan-500',
      popular: true
    },
    {
      id: 5,
      name: 'HubSpot',
      description: 'Manage leads and track conversions',
      icon: Database,
      category: 'crm',
      color: 'from-orange-500 to-amber-500',
      popular: true
    },
    {
      id: 6,
      name: 'Microsoft Teams',
      description: 'Collaborate with your team',
      icon: MessageSquare,
      category: 'communication',
      color: 'from-blue-600 to-indigo-600',
      popular: false
    },
    {
      id: 7,
      name: 'Webhook',
      description: 'Send data to any URL',
      icon: Globe,
      category: 'developer',
      color: 'from-gray-600 to-gray-800',
      popular: false
    },
    {
      id: 8,
      name: 'Mailchimp',
      description: 'Sync subscribers and campaigns',
      icon: Mail,
      category: 'marketing',
      color: 'from-yellow-500 to-orange-500',
      popular: true
    },
    {
      id: 9,
      name: 'Google Analytics',
      description: 'Track campaign performance',
      icon: BarChart3,
      category: 'analytics',
      color: 'from-indigo-500 to-purple-500',
      popular: false
    }
  ];

  const webhooks = [
    {
      id: 1,
      name: 'Production Webhook',
      url: 'https://api.example.com/webhooks/campaigns',
      events: ['campaign.completed', 'campaign.failed'],
      status: 'active',
      lastTriggered: '5 minutes ago',
      successRate: 99.8
    },
    {
      id: 2,
      name: 'Development Webhook',
      url: 'https://dev.example.com/webhooks/test',
      events: ['submission.created', 'submission.updated'],
      status: 'active',
      lastTriggered: '2 hours ago',
      successRate: 95.2
    },
    {
      id: 3,
      name: 'Backup Webhook',
      url: 'https://backup.example.com/webhooks',
      events: ['all'],
      status: 'paused',
      lastTriggered: '3 days ago',
      successRate: 100
    }
  ];

  const webhookEvents = [
    { id: 'campaign.created', name: 'Campaign Created', category: 'Campaigns' },
    { id: 'campaign.started', name: 'Campaign Started', category: 'Campaigns' },
    { id: 'campaign.completed', name: 'Campaign Completed', category: 'Campaigns' },
    { id: 'campaign.failed', name: 'Campaign Failed', category: 'Campaigns' },
    { id: 'submission.created', name: 'Submission Created', category: 'Submissions' },
    { id: 'submission.success', name: 'Submission Successful', category: 'Submissions' },
    { id: 'submission.failed', name: 'Submission Failed', category: 'Submissions' },
    { id: 'user.added', name: 'User Added', category: 'Team' },
    { id: 'user.removed', name: 'User Removed', category: 'Team' }
  ];

  const categories = [
    { id: 'all', name: 'All', count: availableIntegrations.length },
    { id: 'crm', name: 'CRM', count: 2 },
    { id: 'communication', name: 'Communication', count: 1 },
    { id: 'marketing', name: 'Marketing', count: 1 },
    { id: 'analytics', name: 'Analytics', count: 1 },
    { id: 'developer', name: 'Developer', count: 1 }
  ];

  const filteredIntegrations = selectedCategory === 'all' 
    ? availableIntegrations 
    : availableIntegrations.filter(i => i.category === selectedCategory);

  const handleTestWebhook = (webhookId) => {
    setTestingWebhook(webhookId);
    setTimeout(() => setTestingWebhook(null), 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
                  <Link2 className="w-6 h-6 text-white" />
                </div>
                Integration Hub
              </h1>
              <p className="text-gray-600 mt-1">Connect your favorite tools and services</p>
            </div>
            <button className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Add Integration
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-6 pt-8">
        <div className="flex gap-2 mb-8">
          {['connected', 'available', 'webhooks', 'logs'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 rounded-xl font-medium capitalize transition-all ${
                activeTab === tab
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Connected Integrations */}
        {activeTab === 'connected' && (
          <div>
            {connectedIntegrations.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {connectedIntegrations.map((integration) => {
                  const Icon = integration.icon;
                  return (
                    <div key={integration.id} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-all">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 bg-gradient-to-br ${integration.color} rounded-xl flex items-center justify-center`}>
                            <Icon className="w-6 h-6 text-white" />
                          </div>
                          <div>
                            <h3 className="text-lg font-semibold text-gray-900">{integration.name}</h3>
                            <p className="text-sm text-gray-600">{integration.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                          <span className="text-xs text-green-600 font-medium">Connected</span>
                        </div>
                      </div>

                      <div className="space-y-3 mb-4">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Last sync</span>
                          <span className="text-gray-900 font-medium">{integration.lastSync}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Usage</span>
                          <span className="text-gray-900 font-medium">{integration.usage}</span>
                        </div>
                        <div>
                          <span className="text-sm text-gray-600">Events:</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {integration.events.map(event => (
                              <span key={event} className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                                {event}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <button className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium">
                          Configure
                        </button>
                        <button className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                          <RefreshCw className="w-4 h-4" />
                        </button>
                        <button className="px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
                <Link2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No integrations connected</h3>
                <p className="text-gray-600 mb-4">Connect your first integration to get started</p>
                <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                  Browse Integrations
                </button>
              </div>
            )}
          </div>
        )}

        {/* Available Integrations */}
        {activeTab === 'available' && (
          <div>
            {/* Category Filter */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
              <div className="flex items-center gap-2">
                {categories.map(category => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedCategory === category.id
                        ? 'bg-purple-100 text-purple-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {category.name}
                    <span className="ml-2 text-xs bg-gray-100 px-2 py-0.5 rounded-full">
                      {category.count}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Integration Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredIntegrations.map((integration) => {
                const Icon = integration.icon;
                return (
                  <div key={integration.id} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-all cursor-pointer">
                    <div className="flex items-start justify-between mb-4">
                      <div className={`w-12 h-12 bg-gradient-to-br ${integration.color} rounded-xl flex items-center justify-center`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      {integration.popular && (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full font-medium">
                          Popular
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{integration.name}</h3>
                    <p className="text-sm text-gray-600 mb-4">{integration.description}</p>
                    <button className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center justify-center gap-2">
                      <Plus className="w-4 h-4" />
                      Connect
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Webhooks */}
        {activeTab === 'webhooks' && (
          <div>
            {/* Webhook List */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Webhook Endpoints</h3>
                  <button 
                    onClick={() => setShowWebhookModal(true)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add Webhook
                  </button>
                </div>
              </div>

              <div className="divide-y divide-gray-200">
                {webhooks.map((webhook) => (
                  <div key={webhook.id} className="p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-1">{webhook.name}</h4>
                        <code className="text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                          {webhook.url}
                        </code>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleTestWebhook(webhook.id)}
                          className="px-3 py-1 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium hover:bg-purple-200 transition-colors flex items-center gap-1"
                        >
                          {testingWebhook === webhook.id ? (
                            <>
                              <RefreshCw className="w-3 h-3 animate-spin" />
                              Testing...
                            </>
                          ) : (
                            <>
                              <Play className="w-3 h-3" />
                              Test
                            </>
                          )}
                        </button>
                        <button className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                          webhook.status === 'active' 
                            ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}>
                          {webhook.status === 'active' ? (
                            <>
                              <Pause className="w-3 h-3 inline mr-1" />
                              Active
                            </>
                          ) : (
                            <>
                              <Play className="w-3 h-3 inline mr-1" />
                              Paused
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-6 text-sm">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">Last triggered: {webhook.lastTriggered}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">Success rate: </span>
                        <span className={`font-medium ${
                          webhook.successRate > 95 ? 'text-green-600' : 'text-yellow-600'
                        }`}>
                          {webhook.successRate}%
                        </span>
                      </div>
                    </div>

                    <div className="mt-3">
                      <span className="text-sm text-gray-600">Events:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {webhook.events.map(event => (
                          <span key={event} className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                            {event}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Webhook Events Reference */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Events</h3>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {webhookEvents.map((event) => (
                  <div key={event.id} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{event.name}</p>
                      <p className="text-xs text-gray-500">{event.category}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Logs */}
        {activeTab === 'logs' && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Integration Activity Logs</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {[
                { time: '2 minutes ago', integration: 'Slack', event: 'campaign.completed', status: 'success', message: 'Notification sent successfully' },
                { time: '15 minutes ago', integration: 'Google Sheets', event: 'data.export', status: 'success', message: 'Data exported to sheet' },
                { time: '1 hour ago', integration: 'Webhook', event: 'submission.failed', status: 'error', message: 'Connection timeout' },
                { time: '2 hours ago', integration: 'Zapier', event: 'campaign.started', status: 'success', message: 'Zap triggered' },
                { time: '3 hours ago', integration: 'Slack', event: 'user.added', status: 'success', message: 'Welcome message sent' }
              ].map((log, idx) => (
                <div key={idx} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {log.status === 'success' ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {log.integration} • {log.event}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">{log.message}</p>
                      </div>
                    </div>
                    <span className="text-xs text-gray-500">{log.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntegrationsPage;