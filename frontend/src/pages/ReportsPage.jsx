// src/pages/ReportsPage.jsx - Fixed Import Version
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  BarChart3,
  TrendingUp,
  TrendingDown,
  Calendar,
  Download,
  Filter,
  RefreshCw,
  Globe,
  Mail,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Eye,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { toast } from 'react-hot-toast';

// FIXED: Import only apiService
import apiService from '../services/api';

const ReportsPage = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State management
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(searchParams.get('timeRange') || '30');
  const [selectedCampaign, setSelectedCampaign] = useState(searchParams.get('campaign') || 'all');
  const [reportData, setReportData] = useState({
    overview: {},
    campaigns: [],
    trends: [],
    failures: [],
    performance: {},
    captcha: {}
  });
  const [campaigns, setCampaigns] = useState([]);

  // Load data on mount and when filters change
  useEffect(() => {
    loadReportData();
    loadCampaignsList();
  }, [timeRange, selectedCampaign]);

  // Update URL params when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    if (timeRange !== '30') params.set('timeRange', timeRange);
    if (selectedCampaign !== 'all') params.set('campaign', selectedCampaign);
    setSearchParams(params);
  }, [timeRange, selectedCampaign, setSearchParams]);

  const loadReportData = async () => {
    try {
      setLoading(true);

      // FIXED: Use apiService methods directly
      const promises = [
        apiService.getPerformanceMetrics(parseInt(timeRange)),
        apiService.getTrendAnalytics('submissions', parseInt(timeRange)),
        apiService.getFailureAnalytics(parseInt(timeRange)),
        apiService.getCaptchaAnalytics(parseInt(timeRange))
      ];

      // Add campaign-specific analytics if a campaign is selected
      if (selectedCampaign && selectedCampaign !== 'all') {
        promises.push(apiService.getCampaignAnalytics(selectedCampaign, parseInt(timeRange)));
      } else {
        promises.push(apiService.getUserAnalytics());
      }

      const [performance, trends, failures, captcha, overview] = await Promise.allSettled(promises);

      // Process results
      const processedData = {
        overview: overview.status === 'fulfilled' ? overview.value : {},
        trends: trends.status === 'fulfilled' ? trends.value.data || [] : [],
        failures: failures.status === 'fulfilled' ? failures.value.data || [] : [],
        performance: performance.status === 'fulfilled' ? performance.value : {},
        captcha: captcha.status === 'fulfilled' ? captcha.value : {}
      };

      // Load campaigns data for comparison table
      if (selectedCampaign === 'all') {
        const campaignsResponse = await apiService.getCampaigns({ 
          limit: 10, 
          sort: 'updated_at',
          include_stats: true 
        });
        processedData.campaigns = campaignsResponse.data || campaignsResponse || [];
      }

      setReportData(processedData);

    } catch (error) {
      console.error('Failed to load report data:', error);
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const loadCampaignsList = async () => {
    try {
      // FIXED: Use apiService directly
      const response = await apiService.getCampaigns({ limit: 100 });
      setCampaigns(response.data || response || []);
    } catch (error) {
      console.error('Failed to load campaigns list:', error);
    }
  };

  const handleExportReport = async (format = 'csv') => {
    try {
      // FIXED: Use apiService directly
      const blob = await apiService.exportAnalyticsData(parseInt(timeRange), format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-report-${timeRange}days.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success(`Report exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Failed to export report');
    }
  };

  // Computed values
  const overviewStats = useMemo(() => {
    const overview = reportData.overview;
    return {
      totalCampaigns: overview.total_campaigns || 0,
      totalSubmissions: overview.total_submissions || 0,
      successfulSubmissions: overview.successful_submissions || 0,
      averageSuccessRate: overview.average_success_rate || 0,
      totalWebsites: overview.total_websites || 0,
      activeCapatigns: overview.active_campaigns || 0
    };
  }, [reportData.overview]);

  const trendData = useMemo(() => {
    return reportData.trends.map(item => ({
      date: item.date || item.timestamp,
      submissions: item.submissions || 0,
      successful: item.successful || 0,
      failed: item.failed || 0,
      successRate: item.success_rate || 0
    }));
  }, [reportData.trends]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatPercentage = (value) => {
    return `${Math.round(value || 0)}%`;
  };

  const formatNumber = (value) => {
    if (!value && value !== 0) return '0';
    return value.toLocaleString();
  };

  // Components
  const StatCard = ({ title, value, icon: Icon, color, trend, trendValue }) => (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-3xl font-bold ${color}`}>{value}</p>
          {trend && (
            <div className="flex items-center mt-2">
              {trend === 'up' ? (
                <ArrowUpRight className="w-4 h-4 text-green-500" />
              ) : trend === 'down' ? (
                <ArrowDownRight className="w-4 h-4 text-red-500" />
              ) : null}
              <span className={`text-sm ml-1 ${
                trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'
              }`}>
                {trendValue}
              </span>
            </div>
          )}
        </div>
        <Icon className={`w-8 h-8 ${color.replace('text-', 'text-').replace('-600', '-500')}`} />
      </div>
    </div>
  );

  const FailureInsightCard = ({ failure }) => (
    <div className="bg-white p-4 rounded-lg border-l-4 border-l-red-400">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-medium text-gray-900">{failure.error_type || 'Unknown Error'}</h4>
          <p className="text-sm text-gray-600 mt-1">{failure.description || failure.message}</p>
          <div className="flex items-center mt-2 space-x-4">
            <span className="text-xs text-gray-500">
              Occurrences: {failure.count || 0}
            </span>
            <span className="text-xs text-gray-500">
              Impact: {formatPercentage(failure.impact || 0)}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
            (failure.severity || 'medium') === 'high' 
              ? 'text-red-700 bg-red-100'
              : (failure.severity || 'medium') === 'medium'
                ? 'text-yellow-700 bg-yellow-100'
                : 'text-gray-700 bg-gray-100'
          }`}>
            {failure.severity || 'Medium'}
          </span>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics data...</p>
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
            <h1 className="text-3xl font-bold text-gray-900">Analytics & Reports</h1>
            <p className="mt-2 text-gray-600">
              Comprehensive insights into your campaign performance and system metrics
            </p>
          </div>
          
          <div className="mt-4 md:mt-0 flex items-center space-x-3">
            <button
              onClick={loadReportData}
              className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
            <button
              onClick={() => handleExportReport('csv')}
              className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Report
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow-sm border mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between space-y-4 md:space-y-0">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Calendar className="w-5 h-5 text-gray-400" />
                <label htmlFor="timeRange" className="text-sm font-medium text-gray-700">
                  Time Range:
                </label>
                <select
                  id="timeRange"
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="7">Last 7 days</option>
                  <option value="14">Last 2 weeks</option>
                  <option value="30">Last 30 days</option>
                  <option value="90">Last 3 months</option>
                  <option value="365">Last year</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <Filter className="w-5 h-5 text-gray-400" />
                <label htmlFor="campaign" className="text-sm font-medium text-gray-700">
                  Campaign:
                </label>
                <select
                  id="campaign"
                  value={selectedCampaign}
                  onChange={(e) => setSelectedCampaign(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Campaigns</option>
                  {campaigns.map((campaign) => (
                    <option key={campaign.id} value={campaign.id}>
                      {campaign.name || `Campaign ${campaign.id.slice(0, 8)}`}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="text-sm text-gray-500">
              {selectedCampaign !== 'all' && (
                <button
                  onClick={() => {
                    const campaign = campaigns.find(c => c.id === selectedCampaign);
                    if (campaign) navigate(`/campaigns/${campaign.id}`);
                  }}
                  className="flex items-center text-indigo-600 hover:text-indigo-800"
                >
                  <Eye className="w-4 h-4 mr-1" />
                  View Campaign Details
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Campaigns"
            value={formatNumber(overviewStats.totalCampaigns)}
            icon={BarChart3}
            color="text-blue-600"
          />
          <StatCard
            title="Total Submissions"
            value={formatNumber(overviewStats.totalSubmissions)}
            icon={Mail}
            color="text-green-600"
          />
          <StatCard
            title="Success Rate"
            value={formatPercentage(overviewStats.averageSuccessRate)}
            icon={CheckCircle}
            color="text-purple-600"
          />
          <StatCard
            title="Websites Processed"
            value={formatNumber(overviewStats.totalWebsites)}
            icon={Globe}
            color="text-indigo-600"
          />
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          
          {/* Success Rate Trend */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Success Rate Trend</h3>
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                <span className="text-sm text-gray-600">
                  {trendData.length > 1 && trendData[trendData.length - 1]?.successRate > trendData[0]?.successRate 
                    ? 'Trending Up' 
                    : 'Stable'}
                </span>
              </div>
            </div>
            
            {trendData.length > 0 ? (
              <div className="space-y-4">
                {trendData.slice(-7).map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{formatDate(item.date)}</span>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-medium">{item.successful}/{item.submissions}</span>
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${item.successRate}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium text-green-600 w-12 text-right">
                        {formatPercentage(item.successRate)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                No trend data available for the selected period
              </div>
            )}
          </div>

          {/* Performance Summary */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Performance Summary</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="text-sm font-medium text-gray-700">Average Processing Time</span>
                <span className="text-sm font-bold">
                  {reportData.performance.avg_processing_time ? 
                    `${Math.round(reportData.performance.avg_processing_time)}s` : 
                    'N/A'
                  }
                </span>
              </div>
              
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="text-sm font-medium text-gray-700">Processing Speed</span>
                <span className="text-sm font-bold">
                  {reportData.performance.processing_speed ? 
                    `${reportData.performance.processing_speed}/min` : 
                    'N/A'
                  }
                </span>
              </div>
              
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="text-sm font-medium text-gray-700">Email Fallback Rate</span>
                <span className="text-sm font-bold">
                  {formatPercentage(reportData.performance.email_fallback_rate || 0)}
                </span>
              </div>
              
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="text-sm font-medium text-gray-700">Retry Rate</span>
                <span className="text-sm font-bold">
                  {formatPercentage(reportData.performance.retry_rate || 0)}
                </span>
              </div>
              
              <div className="flex items-center justify-between py-2">
                <span className="text-sm font-medium text-gray-700">Peak Processing Hour</span>
                <span className="text-sm font-bold">
                  {reportData.performance.peak_hour || 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Failure Analysis */}
        <div className="bg-white p-6 rounded-lg shadow-sm border mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Failure Analysis</h3>
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              <span className="text-sm text-gray-600">
                {reportData.failures.length} failure type(s) identified
              </span>
            </div>
          </div>
          
          {reportData.failures.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reportData.failures.slice(0, 6).map((failure, index) => (
                <FailureInsightCard key={index} failure={failure} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">No Major Issues Found</h4>
              <p className="text-gray-500">
                Your campaigns are running smoothly with minimal errors
              </p>
            </div>
          )}
        </div>

        {/* CAPTCHA Analytics */}
        <div className="bg-white p-6 rounded-lg shadow-sm border mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">CAPTCHA Analytics</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600 mb-2">
                {formatNumber(reportData.captcha.total_encountered || 0)}
              </div>
              <p className="text-sm text-gray-600">CAPTCHAs Encountered</p>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 mb-2">
                {formatNumber(reportData.captcha.total_solved || 0)}
              </div>
              <p className="text-sm text-gray-600">Successfully Solved</p>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600 mb-2">
                {formatPercentage(reportData.captcha.solve_rate || 0)}
              </div>
              <p className="text-sm text-gray-600">Solve Rate</p>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600 mb-2">
                {reportData.captcha.avg_solve_time ? 
                  `${Math.round(reportData.captcha.avg_solve_time)}s` : 
                  'N/A'
                }
              </div>
              <p className="text-sm text-gray-600">Avg Solve Time</p>
            </div>
          </div>
          
          {reportData.captcha.types && reportData.captcha.types.length > 0 && (
            <div className="mt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">CAPTCHA Types Distribution</h4>
              <div className="space-y-2">
                {reportData.captcha.types.map((type, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 capitalize">{type.type || 'Unknown'}</span>
                    <div className="flex items-center space-x-4">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-indigo-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${(type.count / reportData.captcha.total_encountered) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium text-gray-900 w-12 text-right">
                        {type.count}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Campaign Comparison */}
        {selectedCampaign === 'all' && reportData.campaigns.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Campaign Comparison</h3>
              <button
                onClick={() => navigate('/campaigns')}
                className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center"
              >
                View All Campaigns
                <ArrowUpRight className="w-4 h-4 ml-1" />
              </button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Campaign
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Websites
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Success Rate
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Updated
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {reportData.campaigns.map((campaign) => (
                    <tr key={campaign.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {campaign.name || `Campaign ${campaign.id.slice(0, 8)}`}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          campaign.status === 'COMPLETED' 
                            ? 'text-green-800 bg-green-100'
                            : campaign.status === 'RUNNING'
                              ? 'text-blue-800 bg-blue-100'
                              : campaign.status === 'FAILED'
                                ? 'text-red-800 bg-red-100'
                                : 'text-gray-800 bg-gray-100'
                        }`}>
                          {campaign.status}
                        </span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatNumber(campaign.total_websites || 0)}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-3">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ 
                                width: `${campaign.total_websites > 0 
                                  ? Math.round((campaign.successful / campaign.total_websites) * 100) 
                                  : 0}%` 
                              }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium">
                            {campaign.total_websites > 0 
                              ? formatPercentage((campaign.successful / campaign.total_websites) * 100)
                              : '0%'
                            }
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(campaign.updated_at)}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => navigate(`/campaigns/${campaign.id}`)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportsPage;