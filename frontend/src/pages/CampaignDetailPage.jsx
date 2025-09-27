// src/pages/CampaignDetailPage.jsx - Fixed Import Version
import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { 
  ArrowLeft, 
  Play, 
  Pause, 
  Square, 
  Trash2, 
  Download, 
  RefreshCw,
  Globe,
  Mail,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  TrendingUp,
  BarChart3,
  Settings,
  Eye,
  Copy
} from 'lucide-react';
import { toast } from 'react-hot-toast';

// FIXED: Import only apiService, no separate service objects
import apiService from '../services/api';

const CampaignDetailPage = ({ showResultsView = false }) => {
  const { campaignId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  
  // State management
  const [campaign, setCampaign] = useState(null);
  const [websites, setWebsites] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [activity, setActivity] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(showResultsView ? 'results' : 'overview');
  const [websocket, setWebsocket] = useState(null);

  // Pagination states
  const [websitesPage, setWebsitesPage] = useState(1);
  const [submissionsPage, setSubmissionsPage] = useState(1);
  const [activityPage, setActivityPage] = useState(1);

  // Load campaign data
  useEffect(() => {
    if (campaignId) {
      loadCampaignData();
      connectToWebSocket();
    }

    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [campaignId]);

  const loadCampaignData = async () => {
    try {
      setLoading(true);

      // FIXED: Use apiService methods directly
      const [campaignRes, websitesRes, submissionsRes, activityRes, analyticsRes] = await Promise.allSettled([
        apiService.getCampaign(campaignId),
        apiService.getWebsites(campaignId, { page: 1, limit: 20 }),
        apiService.getSubmissions(campaignId, { page: 1, limit: 20 }),
        apiService.getCampaignActivity(campaignId, 50),
        apiService.getCampaignAnalytics(campaignId, 7)
      ]);

      if (campaignRes.status === 'fulfilled') setCampaign(campaignRes.value);
      if (websitesRes.status === 'fulfilled') setWebsites(websitesRes.value.data || websitesRes.value);
      if (submissionsRes.status === 'fulfilled') setSubmissions(submissionsRes.value.data || submissionsRes.value);
      if (activityRes.status === 'fulfilled') setActivity(activityRes.value.data || activityRes.value);
      if (analyticsRes.status === 'fulfilled') setAnalytics(analyticsRes.value);

    } catch (error) {
      console.error('Failed to load campaign data:', error);
      toast.error('Failed to load campaign details');
    } finally {
      setLoading(false);
    }
  };

  const connectToWebSocket = () => {
    try {
      // FIXED: Use apiService WebSocket method
      const ws = apiService.connectWebSocket(
        (data) => {
          if (data.type === 'campaign_update' && data.campaign_id === campaignId) {
            setCampaign(prev => ({ ...prev, ...data.updates }));
          } else if (data.type === 'submission_update' && data.campaign_id === campaignId) {
            setSubmissions(prev => prev.map(sub => 
              sub.id === data.submission_id ? { ...sub, ...data.updates } : sub
            ));
          }
        },
        (error) => console.error('WebSocket error:', error),
        () => console.log('WebSocket disconnected')
      );
      
      setWebsocket(ws);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

  // Campaign actions
  const handleStartCampaign = async () => {
    try {
      await apiService.startCampaign(campaignId);
      toast.success('Campaign started successfully');
      loadCampaignData();
    } catch (error) {
      toast.error('Failed to start campaign');
    }
  };

  const handlePauseCampaign = async () => {
    try {
      await apiService.pauseCampaign(campaignId);
      toast.success('Campaign paused successfully');
      loadCampaignData();
    } catch (error) {
      toast.error('Failed to pause campaign');
    }
  };

  const handleStopCampaign = async () => {
    try {
      await apiService.stopCampaign(campaignId);
      toast.success('Campaign stopped successfully');
      loadCampaignData();
    } catch (error) {
      toast.error('Failed to stop campaign');
    }
  };

  const handleDeleteCampaign = async () => {
    if (!window.confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) {
      return;
    }

    try {
      await apiService.deleteCampaign(campaignId);
      toast.success('Campaign deleted successfully');
      navigate('/campaigns');
    } catch (error) {
      toast.error('Failed to delete campaign');
    }
  };

  const handleDuplicateCampaign = async () => {
    const newName = prompt('Enter a name for the duplicated campaign:', `${campaign?.name} (Copy)`);
    if (!newName) return;

    try {
      const newCampaign = await apiService.duplicateCampaign(campaignId, newName);
      toast.success('Campaign duplicated successfully');
      navigate(`/campaigns/${newCampaign.id}`);
    } catch (error) {
      toast.error('Failed to duplicate campaign');
    }
  };

  const handleExportData = async (format = 'csv') => {
    try {
      const blob = await apiService.exportCampaignData(campaignId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `campaign-${campaign?.name}-data.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success(`Data exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Failed to export data');
    }
  };

  // Load more data for pagination
  const loadMoreWebsites = async () => {
    try {
      const nextPage = websitesPage + 1;
      const response = await apiService.getWebsites(campaignId, { page: nextPage, limit: 20 });
      setWebsites(prev => [...prev, ...(response.data || response)]);
      setWebsitesPage(nextPage);
    } catch (error) {
      console.error('Failed to load more websites:', error);
    }
  };

  const loadMoreSubmissions = async () => {
    try {
      const nextPage = submissionsPage + 1;
      const response = await apiService.getSubmissions(campaignId, { page: nextPage, limit: 20 });
      setSubmissions(prev => [...prev, ...(response.data || response)]);
      setSubmissionsPage(nextPage);
    } catch (error) {
      console.error('Failed to load more submissions:', error);
    }
  };

  // Retry failed submission
  const handleRetrySubmission = async (submissionId) => {
    try {
      await apiService.retrySubmission(submissionId);
      toast.success('Submission queued for retry');
      loadCampaignData();
    } catch (error) {
      toast.error('Failed to retry submission');
    }
  };

  // Utility functions
  const getStatusColor = (status) => {
    const colors = {
      'RUNNING': 'text-green-600 bg-green-100',
      'COMPLETED': 'text-blue-600 bg-blue-100',
      'PAUSED': 'text-yellow-600 bg-yellow-100',
      'FAILED': 'text-red-600 bg-red-100',
      'DRAFT': 'text-gray-600 bg-gray-100',
      'QUEUED': 'text-purple-600 bg-purple-100'
    };
    return colors[status] || 'text-gray-600 bg-gray-100';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateSuccessRate = (successful, total) => {
    if (!total) return 0;
    return Math.round((successful / total) * 100);
  };

  // Computed values
  const canStartCampaign = campaign && ['DRAFT', 'PAUSED', 'STOPPED'].includes(campaign.status);
  const canPauseCampaign = campaign && ['RUNNING', 'PROCESSING'].includes(campaign.status);
  const canStopCampaign = campaign && ['RUNNING', 'PROCESSING', 'PAUSED'].includes(campaign.status);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading campaign details...</p>
        </div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Campaign Not Found</h1>
          <p className="text-gray-600 mb-6">The campaign you're looking for doesn't exist or has been deleted.</p>
          <button
            onClick={() => navigate('/campaigns')}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Back to Campaigns
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/campaigns')}
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                Back to Campaigns
              </button>
              <div className="h-6 border-l border-gray-300"></div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{campaign.name}</h1>
                <p className="text-sm text-gray-500 mt-1">
                  Created {formatDate(campaign.created_at)} • ID: {campaign.id.slice(0, 8)}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(campaign.status)}`}>
                {campaign.status}
              </span>
              
              <div className="flex items-center space-x-2">
                {canStartCampaign && (
                  <button
                    onClick={handleStartCampaign}
                    className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Start
                  </button>
                )}
                
                {canPauseCampaign && (
                  <button
                    onClick={handlePauseCampaign}
                    className="flex items-center px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                  >
                    <Pause className="w-4 h-4 mr-2" />
                    Pause
                  </button>
                )}
                
                {canStopCampaign && (
                  <button
                    onClick={handleStopCampaign}
                    className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <Square className="w-4 h-4 mr-2" />
                    Stop
                  </button>
                )}
                
                <button
                  onClick={() => handleExportData('csv')}
                  className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </button>
                
                <div className="relative group">
                  <button className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                    <Settings className="w-4 h-4 mr-2" />
                    Actions
                  </button>
                  
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                    <div className="py-2">
                      <button
                        onClick={handleDuplicateCampaign}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        <Copy className="w-4 h-4 mr-2" />
                        Duplicate Campaign
                      </button>
                      <button
                        onClick={() => navigate(`/reports?campaign=${campaignId}`)}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        <BarChart3 className="w-4 h-4 mr-2" />
                        View in Reports
                      </button>
                      <hr className="my-1" />
                      <button
                        onClick={handleDeleteCampaign}
                        className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete Campaign
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Websites</p>
                <p className="text-3xl font-bold text-gray-900">{campaign.total_websites || 0}</p>
              </div>
              <Globe className="w-8 h-8 text-blue-500" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-500">
                <span>Processing: {campaign.processed || 0}</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Successful</p>
                <p className="text-3xl font-bold text-green-600">{campaign.successful || 0}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-500">
                <span>Success Rate: {calculateSuccessRate(campaign.successful, campaign.total_websites)}%</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Failed</p>
                <p className="text-3xl font-bold text-red-600">{campaign.failed || 0}</p>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-500">
                <span>Email Fallback: {campaign.email_fallback || 0}</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Duration</p>
                <p className="text-3xl font-bold text-gray-900">
                  {campaign.processing_duration 
                    ? `${Math.round(campaign.processing_duration / 60)}m` 
                    : '0m'}
                </p>
              </div>
              <Clock className="w-8 h-8 text-purple-500" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-500">
                <span>Started: {formatDate(campaign.started_at)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        {campaign.total_websites > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-sm border mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Campaign Progress</h3>
              <span className="text-sm text-gray-500">
                {campaign.processed || 0} / {campaign.total_websites} websites processed
              </span>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-blue-500 to-indigo-600 h-3 rounded-full transition-all duration-500"
                style={{ 
                  width: `${Math.min(((campaign.processed || 0) / campaign.total_websites) * 100, 100)}%` 
                }}
              ></div>
            </div>
            
            <div className="flex justify-between items-center mt-4">
              <div className="flex space-x-6">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm text-gray-600">Successful ({campaign.successful || 0})</span>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                  <span className="text-sm text-gray-600">Failed ({campaign.failed || 0})</span>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                  <span className="text-sm text-gray-600">Email Fallback ({campaign.email_fallback || 0})</span>
                </div>
              </div>
              
              <div className="text-sm text-gray-500">
                {Math.round(((campaign.processed || 0) / campaign.total_websites) * 100)}% Complete
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', label: 'Overview', icon: Eye },
                { id: 'websites', label: 'Websites', icon: Globe },
                { id: 'results', label: 'Submissions', icon: Mail },
                { id: 'activity', label: 'Activity', icon: Clock },
                { id: 'settings', label: 'Settings', icon: Settings }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } transition-colors`}
                >
                  <tab.icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Campaign Details */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Campaign Details</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Campaign Name</label>
                        <p className="mt-1 text-sm text-gray-900">{campaign.name || 'Unnamed Campaign'}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Status</label>
                        <span className={`mt-1 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(campaign.status)}`}>
                          {campaign.status}
                        </span>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">File Name</label>
                        <p className="mt-1 text-sm text-gray-900">{campaign.csv_filename || campaign.file_name || 'N/A'}</p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Created</label>
                        <p className="mt-1 text-sm text-gray-900">{formatDate(campaign.created_at)}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Last Updated</label>
                        <p className="mt-1 text-sm text-gray-900">{formatDate(campaign.updated_at)}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">CAPTCHA Enabled</label>
                        <p className="mt-1 text-sm text-gray-900">
                          {campaign.use_captcha ? 'Yes' : 'No'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Message Template */}
                {campaign.message && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Message Template</h3>
                    <div className="bg-gray-50 border rounded-lg p-4">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{campaign.message}</p>
                    </div>
                  </div>
                )}

                {/* Analytics Summary */}
                {analytics && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Analytics</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-blue-600">Average Success Rate</p>
                            <p className="text-2xl font-bold text-blue-700">
                              {analytics.success_rate ? `${analytics.success_rate}%` : 'N/A'}
                            </p>
                          </div>
                          <TrendingUp className="w-8 h-8 text-blue-500" />
                        </div>
                      </div>
                      
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-green-600">Processing Speed</p>
                            <p className="text-2xl font-bold text-green-700">
                              {analytics.processing_speed ? `${analytics.processing_speed}/min` : 'N/A'}
                            </p>
                          </div>
                          <BarChart3 className="w-8 h-8 text-green-500" />
                        </div>
                      </div>
                      
                      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-orange-600">CAPTCHA Encounters</p>
                            <p className="text-2xl font-bold text-orange-700">
                              {analytics.captcha_count || 0}
                            </p>
                          </div>
                          <AlertTriangle className="w-8 h-8 text-orange-500" />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Websites Tab */}
            {activeTab === 'websites' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">Websites ({websites.length})</h3>
                  <button
                    onClick={loadMoreWebsites}
                    className="flex items-center px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Load More
                  </button>
                </div>

                <div className="space-y-4">
                  {websites.map((website) => (
                    <div key={website.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h4 className="font-medium text-gray-900">{website.domain}</h4>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(website.status)}`}>
                              {website.status}
                            </span>
                            {website.form_detected && (
                              <span className="px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-full">
                                Form Detected
                              </span>
                            )}
                            {website.has_captcha && (
                              <span className="px-2 py-1 text-xs font-medium text-orange-700 bg-orange-100 rounded-full">
                                CAPTCHA
                              </span>
                            )}
                          </div>
                          
                          {website.contact_url && (
                            <a
                              href={website.contact_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:text-blue-800 mt-1 block"
                            >
                              {website.contact_url}
                            </a>
                          )}
                          
                          {website.failure_reason && (
                            <p className="text-sm text-red-600 mt-1">
                              Error: {website.failure_reason}
                            </p>
                          )}
                        </div>
                        
                        <div className="text-right">
                          {website.form_field_count && (
                            <p className="text-sm text-gray-500">
                              {website.form_field_count} fields
                            </p>
                          )}
                          <p className="text-xs text-gray-400">
                            {formatDate(website.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {websites.length === 0 && (
                    <div className="text-center py-12">
                      <Globe className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No websites found</h3>
                      <p className="text-gray-500">
                        Websites will appear here once the campaign is processed.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Submissions Tab */}
            {activeTab === 'results' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">Submissions ({submissions.length})</h3>
                  <button
                    onClick={loadMoreSubmissions}
                    className="flex items-center px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Load More
                  </button>
                </div>

                <div className="space-y-4">
                  {submissions.map((submission) => (
                    <div key={submission.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h4 className="font-medium text-gray-900">
                              {submission.url ? new URL(submission.url).hostname : 'Unknown Website'}
                            </h4>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              submission.success 
                                ? 'text-green-700 bg-green-100' 
                                : submission.status === 'failed'
                                  ? 'text-red-700 bg-red-100'
                                  : 'text-yellow-700 bg-yellow-100'
                            }`}>
                              {submission.success ? 'Success' : submission.status}
                            </span>
                            <span className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full">
                              {submission.contact_method_display || submission.contact_method}
                            </span>
                            {submission.captcha_solved && (
                              <span className="px-2 py-1 text-xs font-medium text-purple-700 bg-purple-100 rounded-full">
                                CAPTCHA Solved
                              </span>
                            )}
                          </div>
                          
                          {submission.error_message && (
                            <p className="text-sm text-red-600 mt-1">
                              Error: {submission.error_message}
                            </p>
                          )}
                          
                          {submission.email_extracted && (
                            <p className="text-sm text-gray-600 mt-1">
                              Email found: {submission.email_extracted}
                            </p>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {submission.retry_count > 0 && (
                            <span className="text-xs text-gray-500">
                              Retried {submission.retry_count}x
                            </span>
                          )}
                          
                          {!submission.success && submission.status === 'failed' && (
                            <button
                              onClick={() => handleRetrySubmission(submission.id)}
                              className="px-3 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition-colors"
                            >
                              Retry
                            </button>
                          )}
                          
                          <div className="text-right text-xs text-gray-400">
                            {submission.processing_time && (
                              <p>{submission.processing_time}s</p>
                            )}
                            <p>{formatDate(submission.submitted_at || submission.created_at)}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {submissions.length === 0 && (
                    <div className="text-center py-12">
                      <Mail className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No submissions yet</h3>
                      <p className="text-gray-500">
                        Submissions will appear here once the campaign is running.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Activity Tab */}
            {activeTab === 'activity' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">Activity Log ({activity.length})</h3>
                  <button
                    onClick={loadCampaignData}
                    className="flex items-center px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Refresh
                  </button>
                </div>

                <div className="space-y-4">
                  {activity.map((log, index) => (
                    <div key={index} className="flex items-start space-x-4 py-3 border-b border-gray-100 last:border-b-0">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                          <Clock className="w-4 h-4 text-gray-600" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{log.action || log.message}</p>
                        {log.details && (
                          <p className="text-sm text-gray-600 mt-1">{log.details}</p>
                        )}
                        <p className="text-xs text-gray-400 mt-1">
                          {formatDate(log.timestamp || log.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                  
                  {activity.length === 0 && (
                    <div className="text-center py-12">
                      <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No activity yet</h3>
                      <p className="text-gray-500">
                        Activity logs will appear here as the campaign progresses.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-6">Campaign Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Campaign Name
                      </label>
                      <input
                        type="text"
                        value={campaign.name || ''}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        readOnly
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Status
                      </label>
                      <span className={`px-3 py-2 text-sm font-medium rounded-lg ${getStatusColor(campaign.status)}`}>
                        {campaign.status}
                      </span>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        CAPTCHA Enabled
                      </label>
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={campaign.use_captcha || false}
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                          readOnly
                        />
                        <label className="ml-2 text-sm text-gray-900">
                          Use CAPTCHA solving service
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Proxy Configuration
                      </label>
                      <input
                        type="text"
                        value={campaign.proxy || ''}
                        placeholder="No proxy configured"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        readOnly
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        CSV File
                      </label>
                      <input
                        type="text"
                        value={campaign.csv_filename || campaign.file_name || ''}
                        placeholder="No file uploaded"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        readOnly
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Created
                      </label>
                      <input
                        type="text"
                        value={formatDate(campaign.created_at)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                        readOnly
                      />
                    </div>
                  </div>
                </div>
                
                {campaign.message && (
                  <div className="mt-8">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Message Template
                    </label>
                    <textarea
                      value={campaign.message}
                      rows={8}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      readOnly
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CampaignDetailPage;