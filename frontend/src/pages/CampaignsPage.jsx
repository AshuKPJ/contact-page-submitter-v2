// src/pages/CampaignsPage.jsx - Complete End-to-End Fixed Version
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus, Search, Filter, MoreVertical, Play, Pause, Square, Copy, Trash2, Eye,
  Download, TrendingUp, Clock, CheckCircle, XCircle, Globe, BarChart3
} from 'lucide-react';
import { toast } from 'react-hot-toast';

import apiService from '../services/api';

const CampaignsPage = () => {
  const navigate = useNavigate();
  
  // State management
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedCampaigns, setSelectedCampaigns] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [stats, setStats] = useState({
    totalCampaigns: 0,
    activeCampaigns: 0,
    completedCampaigns: 0,
    successRate: 0
  });

  // Load campaigns on mount
  useEffect(() => {
    loadCampaigns();
    loadStats();
  }, []);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      console.log('[CAMPAIGNS] Loading campaigns...');
      
      const response = await apiService.getCampaigns({
        search: searchTerm,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        limit: 50
      });
      
      console.log('[CAMPAIGNS] Raw response:', response);
      
      // FIXED: Handle different response formats safely
      let campaignsData = [];
      if (response === null || response === undefined) {
        console.warn('[CAMPAIGNS] API returned null/undefined, using empty array');
        campaignsData = [];
      } else if (Array.isArray(response)) {
        campaignsData = response;
      } else if (response && Array.isArray(response.data)) {
        campaignsData = response.data;
      } else if (response && response.campaigns && Array.isArray(response.campaigns)) {
        campaignsData = response.campaigns;
      } else {
        console.warn('[CAMPAIGNS] Unexpected response format:', response);
        campaignsData = [];
      }
      
      // Ensure each campaign has required fields
      campaignsData = campaignsData.map(campaign => ({
        id: campaign.id || '',
        name: campaign.name || 'Untitled Campaign',
        status: campaign.status || 'DRAFT',
        csv_filename: campaign.csv_filename || campaign.file_name || '',
        total_websites: campaign.total_websites || campaign.total_urls || 0,
        processed: campaign.processed || 0,
        successful: campaign.successful || 0,
        failed: campaign.failed || 0,
        processing_duration: campaign.processing_duration || 0,
        created_at: campaign.created_at || null,
        updated_at: campaign.updated_at || null,
        ...campaign
      }));
      
      setCampaigns(campaignsData);
      console.log(`[CAMPAIGNS] Loaded ${campaignsData.length} campaigns`);
      
    } catch (error) {
      console.error('[CAMPAIGNS] Failed to load campaigns:', error);
      toast.error('Failed to load campaigns: ' + (error.message || 'Unknown error'));
      setCampaigns([]);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      console.log('[STATS] Loading user analytics...');
      
      // FIXED: Handle analytics response with proper field mapping
      let analyticsData = null;
      try {
        const response = await apiService.getUserAnalytics();
        console.log('[STATS] Analytics response:', response);
        analyticsData = response;
      } catch (error) {
        console.warn('[STATS] Analytics failed, using fallback:', error);
        analyticsData = {
          campaigns_count: 0,
          active_campaigns: 0,
          completed_campaigns: 0,
          success_rate: 0
        };
      }
      
      // FIXED: Map analytics fields correctly (backend uses campaigns_count, frontend expects totalCampaigns)
      const newStats = {
        totalCampaigns: analyticsData?.campaigns_count || analyticsData?.total_campaigns || 0,
        activeCampaigns: analyticsData?.active_campaigns || 0,
        completedCampaigns: analyticsData?.completed_campaigns || 0,
        successRate: Math.round(analyticsData?.success_rate || 0)
      };
      
      console.log('[STATS] Mapped stats:', newStats);
      setStats(newStats);
      
    } catch (error) {
      console.error('[STATS] Failed to load stats:', error);
      // Don't show error toast for stats failure
      setStats({
        totalCampaigns: 0,
        activeCampaigns: 0,
        completedCampaigns: 0,
        successRate: 0
      });
    }
  };

  // Search and filter with debouncing
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!loading) { // Only reload if not currently loading
        loadCampaigns();
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm, statusFilter]);

  // Campaign actions with better error handling
  const handleStartCampaign = async (campaignId) => {
    try {
      console.log(`[CAMPAIGN] Starting campaign: ${campaignId}`);
      const result = await apiService.startCampaign(campaignId);
      console.log('[CAMPAIGN] Start result:', result);
      toast.success('Campaign started successfully');
      loadCampaigns();
    } catch (error) {
      console.error('[CAMPAIGN] Failed to start campaign:', error);
      toast.error('Failed to start campaign: ' + (error.message || 'Unknown error'));
    }
  };

  const handlePauseCampaign = async (campaignId) => {
    try {
      console.log(`[CAMPAIGN] Pausing campaign: ${campaignId}`);
      const result = await apiService.pauseCampaign(campaignId);
      console.log('[CAMPAIGN] Pause result:', result);
      toast.success('Campaign paused successfully');
      loadCampaigns();
    } catch (error) {
      console.error('[CAMPAIGN] Failed to pause campaign:', error);
      toast.error('Failed to pause campaign: ' + (error.message || 'Unknown error'));
    }
  };

  const handleStopCampaign = async (campaignId) => {
    try {
      console.log(`[CAMPAIGN] Stopping campaign: ${campaignId}`);
      const result = await apiService.stopCampaign(campaignId);
      console.log('[CAMPAIGN] Stop result:', result);
      toast.success('Campaign stopped successfully');
      loadCampaigns();
    } catch (error) {
      console.error('[CAMPAIGN] Failed to stop campaign:', error);
      toast.error('Failed to stop campaign: ' + (error.message || 'Unknown error'));
    }
  };

  const handleDeleteCampaign = async (campaignId) => {
    if (!window.confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) {
      return;
    }

    try {
      console.log(`[CAMPAIGN] Deleting campaign: ${campaignId}`);
      const result = await apiService.deleteCampaign(campaignId);
      console.log('[CAMPAIGN] Delete result:', result);
      toast.success('Campaign deleted successfully');
      loadCampaigns();
    } catch (error) {
      console.error('[CAMPAIGN] Failed to delete campaign:', error);
      toast.error('Failed to delete campaign: ' + (error.message || 'Unknown error'));
    }
  };

  const handleDuplicateCampaign = async (campaign) => {
    const newName = prompt('Enter a name for the duplicated campaign:', `${campaign.name} (Copy)`);
    if (!newName?.trim()) return;

    try {
      console.log(`[CAMPAIGN] Duplicating campaign: ${campaign.id}`);
      const result = await apiService.duplicateCampaign(campaign.id, newName.trim());
      console.log('[CAMPAIGN] Duplicate result:', result);
      toast.success('Campaign duplicated successfully');
      loadCampaigns();
    } catch (error) {
      console.error('[CAMPAIGN] Failed to duplicate campaign:', error);
      toast.error('Failed to duplicate campaign: ' + (error.message || 'Unknown error'));
    }
  };

  const handleBulkAction = async (action) => {
    if (selectedCampaigns.length === 0) {
      toast.error('Please select campaigns first');
      return;
    }

    try {
      console.log(`[BULK] Executing ${action} on ${selectedCampaigns.length} campaigns`);
      switch (action) {
        case 'delete':
          if (!window.confirm(`Delete ${selectedCampaigns.length} selected campaigns? This action cannot be undone.`)) return;
          await apiService.batchDeleteCampaigns(selectedCampaigns);
          toast.success('Campaigns deleted successfully');
          break;
        case 'start':
          await apiService.batchUpdateCampaignStatus(selectedCampaigns, 'RUNNING');
          toast.success('Campaigns started successfully');
          break;
        case 'pause':
          await apiService.batchUpdateCampaignStatus(selectedCampaigns, 'PAUSED');
          toast.success('Campaigns paused successfully');
          break;
        default:
          throw new Error(`Unknown bulk action: ${action}`);
      }
      setSelectedCampaigns([]);
      loadCampaigns();
    } catch (error) {
      console.error(`[BULK] Failed to ${action} campaigns:`, error);
      toast.error(`Failed to ${action} campaigns: ` + (error.message || 'Unknown error'));
    }
  };

  // Utility functions with null safety
  const getStatusColor = (status) => {
    const colors = {
      'RUNNING': 'text-green-600 bg-green-100',
      'ACTIVE': 'text-green-600 bg-green-100',
      'PROCESSING': 'text-blue-600 bg-blue-100',
      'COMPLETED': 'text-blue-600 bg-blue-100',
      'PAUSED': 'text-yellow-600 bg-yellow-100',
      'FAILED': 'text-red-600 bg-red-100',
      'DRAFT': 'text-gray-600 bg-gray-100',
      'QUEUED': 'text-purple-600 bg-purple-100',
      'STOPPED': 'text-gray-600 bg-gray-100'
    };
    return colors[status] || 'text-gray-600 bg-gray-100';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (error) {
      console.warn('[DATE] Invalid date:', dateString);
      return 'Invalid Date';
    }
  };

  const calculateProgress = (campaign) => {
    if (!campaign) return 0;
    const total = campaign.total_websites || campaign.total_urls || 0;
    const processed = campaign.processed || 0;
    if (!total || total === 0) return 0;
    return Math.min(Math.round((processed / total) * 100), 100);
  };

  // FIXED: Safe filtering with comprehensive null checks
  const filteredCampaigns = (campaigns || []).filter(campaign => {
    if (!campaign || !campaign.id) return false;
    
    const campaignName = (campaign.name || '').toLowerCase();
    const csvFilename = (campaign.csv_filename || campaign.file_name || '').toLowerCase();
    const searchLower = (searchTerm || '').toLowerCase();
    
    const matchesSearch = !searchTerm || 
                         campaignName.includes(searchLower) ||
                         csvFilename.includes(searchLower);
                         
    const matchesStatus = statusFilter === 'all' || 
                         (campaign.status || '').toUpperCase() === statusFilter.toUpperCase();
                         
    return matchesSearch && matchesStatus;
  });

  // Components with null safety
  const StatusBadge = ({ status }) => (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(status)}`}>
      {status || 'UNKNOWN'}
    </span>
  );

  const ProgressBar = ({ progress, total, successful, failed }) => {
    const safeProgress = Math.min(Math.max(progress || 0, 0), 100);
    const safeTotal = total || 0;
    const safeSuccessful = successful || 0;
    const safeFailed = failed || 0;
    
    return (
      <div className="w-full">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-gray-600">{safeProgress}% complete</span>
          <span className="text-xs text-gray-500">{safeSuccessful + safeFailed}/{safeTotal}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-indigo-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${safeProgress}%` }}
          ></div>
        </div>
      </div>
    );
  };

  const CampaignActions = ({ campaign }) => {
    const [showDropdown, setShowDropdown] = useState(false);

    if (!campaign || !campaign.id) return null;

    const status = campaign.status || 'DRAFT';
    const canStart = ['DRAFT', 'PAUSED', 'STOPPED'].includes(status);
    const canPause = ['RUNNING', 'PROCESSING', 'ACTIVE'].includes(status);
    const canStop = ['RUNNING', 'PROCESSING', 'PAUSED', 'ACTIVE'].includes(status);

    return (
      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Campaign actions"
        >
          <MoreVertical className="w-4 h-4" />
        </button>

        {showDropdown && (
          <>
            {/* Backdrop to close dropdown */}
            <div 
              className="fixed inset-0 z-10" 
              onClick={() => setShowDropdown(false)}
            />
            
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-20">
              <div className="py-2">
                <button
                  onClick={() => {
                    navigate(`/campaigns/${campaign.id}`);
                    setShowDropdown(false);
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  View Details
                </button>

                {canStart && (
                  <button
                    onClick={() => {
                      handleStartCampaign(campaign.id);
                      setShowDropdown(false);
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-green-700 hover:bg-green-50"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Start Campaign
                  </button>
                )}

                {canPause && (
                  <button
                    onClick={() => {
                      handlePauseCampaign(campaign.id);
                      setShowDropdown(false);
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-yellow-700 hover:bg-yellow-50"
                  >
                    <Pause className="w-4 h-4 mr-2" />
                    Pause Campaign
                  </button>
                )}

                {canStop && (
                  <button
                    onClick={() => {
                      handleStopCampaign(campaign.id);
                      setShowDropdown(false);
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-red-50"
                  >
                    <Square className="w-4 h-4 mr-2" />
                    Stop Campaign
                  </button>
                )}

                <hr className="my-2" />

                <button
                  onClick={() => {
                    handleDuplicateCampaign(campaign);
                    setShowDropdown(false);
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Duplicate
                </button>

                <hr className="my-2" />

                <button
                  onClick={() => {
                    handleDeleteCampaign(campaign.id);
                    setShowDropdown(false);
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading campaigns...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Campaigns</h1>
            <p className="mt-2 text-gray-600">
              Manage and monitor your contact form submission campaigns
            </p>
          </div>
          
          <div className="mt-4 md:mt-0 flex items-center space-x-3">
            <button
              onClick={() => navigate('/reports')}
              className="flex items-center px-4 py-2 bg-white text-gray-700 rounded-lg shadow-sm border hover:bg-gray-50 transition-colors"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              View Reports
            </button>
            <button
              onClick={() => navigate('/form-submitter')}
              className="flex items-center px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Campaign
            </button>
          </div>
        </div>

        {/* Stats Overview with Debug Info */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Campaigns</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalCampaigns}</p>
              </div>
              <Globe className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active</p>
                <p className="text-3xl font-bold text-green-600">{stats.activeCampaigns}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Completed</p>
                <p className="text-3xl font-bold text-blue-600">{stats.completedCampaigns}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-3xl font-bold text-purple-600">{stats.successRate}%</p>
              </div>
              <BarChart3 className="w-8 h-8 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between space-y-4 md:space-y-0 md:space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search campaigns..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div className="flex items-center space-x-3">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">All Statuses</option>
                <option value="DRAFT">Draft</option>
                <option value="RUNNING">Running</option>
                <option value="PAUSED">Paused</option>
                <option value="COMPLETED">Completed</option>
                <option value="FAILED">Failed</option>
              </select>

              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </button>
            </div>
          </div>

          {selectedCampaigns.length > 0 && (
            <div className="mt-4 flex items-center justify-between bg-indigo-50 p-4 rounded-lg">
              <span className="text-sm text-indigo-700">
                {selectedCampaigns.length} campaign(s) selected
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleBulkAction('start')}
                  className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors"
                >
                  Start
                </button>
                <button
                  onClick={() => handleBulkAction('pause')}
                  className="px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700 transition-colors"
                >
                  Pause
                </button>
                <button
                  onClick={() => handleBulkAction('delete')}
                  className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Debug Info in Development */}
        {process.env.NODE_ENV === 'development' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <h4 className="font-semibold text-yellow-800 mb-2">Debug Info</h4>
            <div className="text-sm text-yellow-700">
              <p>Total campaigns loaded: {campaigns.length}</p>
              <p>Filtered campaigns: {filteredCampaigns.length}</p>
              <p>Search term: "{searchTerm}"</p>
              <p>Status filter: {statusFilter}</p>
              <p>Stats: {JSON.stringify(stats)}</p>
            </div>
          </div>
        )}

        {/* Campaigns List */}
        <div className="space-y-4">
          {filteredCampaigns.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="text-center py-12">
                <Globe className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {campaigns.length === 0 ? 'No campaigns found' : 'No matching campaigns'}
                </h3>
                <p className="text-gray-500 mb-6">
                  {searchTerm || statusFilter !== 'all' 
                    ? 'Try adjusting your search or filters' 
                    : 'Get started by creating your first campaign'}
                </p>
                {!searchTerm && statusFilter === 'all' && campaigns.length === 0 && (
                  <button
                    onClick={() => navigate('/form-submitter')}
                    className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Create Campaign
                  </button>
                )}
              </div>
            </div>
          ) : (
            filteredCampaigns.map((campaign) => (
              <div key={campaign.id} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={selectedCampaigns.includes(campaign.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedCampaigns([...selectedCampaigns, campaign.id]);
                          } else {
                            setSelectedCampaigns(selectedCampaigns.filter(id => id !== campaign.id));
                          }
                        }}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {campaign.name}
                        </h3>
                        <div className="flex items-center space-x-4 mt-1">
                          <StatusBadge status={campaign.status} />
                          <span className="text-sm text-gray-500">
                            Created {formatDate(campaign.created_at)}
                          </span>
                          {campaign.csv_filename && (
                            <span className="text-sm text-gray-500">
                              File: {campaign.csv_filename}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <CampaignActions campaign={campaign} />
                  </div>

                  {/* Campaign Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div className="flex items-center space-x-3">
                      <Globe className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Websites</p>
                        <p className="font-medium">{campaign.total_websites}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                      <div>
                        <p className="text-sm text-gray-500">Successful</p>
                        <p className="font-medium text-green-600">{campaign.successful}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <XCircle className="w-5 h-5 text-red-500" />
                      <div>
                        <p className="text-sm text-gray-500">Failed</p>
                        <p className="font-medium text-red-600">{campaign.failed}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <Clock className="w-5 h-5 text-blue-500" />
                      <div>
                        <p className="text-sm text-gray-500">Duration</p>
                        <p className="font-medium">
                          {campaign.processing_duration 
                            ? `${Math.round(campaign.processing_duration / 60)}m` 
                            : '0m'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  {campaign.total_websites > 0 && (
                    <div className="mb-4">
                      <ProgressBar
                        progress={calculateProgress(campaign)}
                        total={campaign.total_websites}
                        successful={campaign.successful}
                        failed={campaign.failed}
                      />
                    </div>
                  )}

                  {/* Quick Actions */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {['DRAFT', 'PAUSED', 'STOPPED'].includes(campaign.status) && (
                        <button
                          onClick={() => handleStartCampaign(campaign.id)}
                          className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm"
                        >
                          <Play className="w-3 h-3 mr-1" />
                          Start
                        </button>
                      )}
                      
                      {['RUNNING', 'PROCESSING', 'ACTIVE'].includes(campaign.status) && (
                        <button
                          onClick={() => handlePauseCampaign(campaign.id)}
                          className="flex items-center px-3 py-1 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors text-sm"
                        >
                          <Pause className="w-3 h-3 mr-1" />
                          Pause
                        </button>
                      )}
                      
                      <button
                        onClick={() => navigate(`/campaigns/${campaign.id}`)}
                        className="flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm"
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        View Details
                      </button>
                    </div>
                    
                    <div className="text-sm text-gray-500">
                      Updated {formatDate(campaign.updated_at)}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Load More Button */}
        {filteredCampaigns.length >= 50 && (
          <div className="text-center mt-8">
            <button
              onClick={loadCampaigns}
              className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Load More Campaigns
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CampaignsPage;