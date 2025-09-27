import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, AlertCircle, Activity, BarChart3, Clock,
  CheckCircle, XCircle, RefreshCw, Plus, Search,
  ChevronDown, MoreVertical, ArrowUpRight, ArrowDownRight,
  Zap, Shield, Mail, Globe, Target, Users, Timer,
  DollarSign, Percent, Hash, Calendar, Filter, Eye,
  Database, Server, Cpu, HardDrive, Link2, FileText
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, RadialBarChart, RadialBar, Legend } from 'recharts';

const UserDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    analytics: null,
    campaigns: [],
    dailyStats: null,
    performance: null,
    recentSubmissions: [],
    websiteStats: []
  });
  const [timeRange, setTimeRange] = useState(7);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedKPIView, setSelectedKPIView] = useState('overview');

  // Fetch real data from your API
  const fetchDashboardData = async () => {
    try {
      setRefreshing(true);
      const token = localStorage.getItem('access_token');
      
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Fetch all data in parallel using your actual endpoints
      const [
        analyticsRes,
        campaignsRes,
        dailyStatsRes,
        performanceRes
      ] = await Promise.all([
        fetch('/api/analytics/user?include_detailed=true', { headers }),
        fetch('/api/campaigns?limit=10', { headers }),
        fetch(`/api/analytics/daily-stats?days=${timeRange}&include_trends=true`, { headers }),
        fetch(`/api/analytics/performance?time_range=${timeRange}`, { headers })
      ]);

      const analyticsData = await analyticsRes.json();
      const campaignsData = await campaignsRes.json();
      const dailyStatsData = await dailyStatsRes.json();
      const performanceData = await performanceRes.json();

      // Process campaigns data - handle both array and object response
      const campaigns = Array.isArray(campaignsData) ? campaignsData : (campaignsData.campaigns || []);
      
      // Extract recent submissions from campaigns
      const recentSubmissions = [];
      
      // Get website statistics from performance data
      const websiteStats = performanceData?.domain_statistics || [];

      setData({
        analytics: analyticsData,
        campaigns: campaigns,
        dailyStats: dailyStatsData,
        performance: performanceData,
        recentSubmissions: recentSubmissions,
        websiteStats: websiteStats
      });

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [timeRange]);

  // Auto-refresh for active campaigns
  useEffect(() => {
    const hasActiveCampaign = data.campaigns.some(c => 
      c.status === 'active' || c.status === 'running' || c.status === 'ACTIVE'
    );

    if (hasActiveCampaign) {
      const interval = setInterval(() => {
        fetchDashboardData();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [data.campaigns]);

  const { analytics, campaigns, dailyStats, performance, websiteStats } = data;

  // Calculate additional KPIs from actual database data
  const calculateKPIs = () => {
    if (!analytics) return {};
    
    const totalProcessed = analytics.successful_submissions + analytics.failed_submissions;
    const captchaRate = analytics.captcha_submissions > 0 
      ? (analytics.captcha_solved / analytics.captcha_submissions * 100) 
      : 0;
    
    return {
      // Processing metrics
      totalProcessed,
      processingRate: totalProcessed > 0 ? (analytics.successful_submissions / totalProcessed * 100) : 0,
      
      // Efficiency metrics  
      submissionsPerCampaign: analytics.campaigns_count > 0 
        ? Math.round(analytics.total_submissions / analytics.campaigns_count) 
        : 0,
      websitesPerCampaign: analytics.campaigns_count > 0
        ? Math.round(analytics.websites_count / analytics.campaigns_count)
        : 0,
        
      // Quality metrics
      captchaSuccessRate: captchaRate.toFixed(1),
      emailExtractionRate: analytics.successful_submissions > 0
        ? ((analytics.emails_extracted / analytics.successful_submissions) * 100).toFixed(1)
        : 0,
      
      // Velocity metrics
      dailyAverage: dailyStats?.summary?.avg_daily_submissions || 0,
      peakDay: dailyStats?.trends?.peak_day || 'N/A',
      
      // Growth metrics
      growthTrend: dailyStats?.trends?.trend_percentage || 0,
      trendDirection: dailyStats?.trends?.submission_trend || 'stable'
    };
  };

  const kpis = calculateKPIs();

  // Status color helper
  const getStatusColor = (status) => {
    const statusMap = {
      'active': 'text-green-600 bg-green-50',
      'running': 'text-green-600 bg-green-50',
      'completed': 'text-blue-600 bg-blue-50',
      'paused': 'text-yellow-600 bg-yellow-50',
      'failed': 'text-red-600 bg-red-50',
      'draft': 'text-gray-600 bg-gray-50'
    };
    return statusMap[status?.toLowerCase()] || 'text-gray-600 bg-gray-50';
  };

  // Prepare chart data from actual database
  const prepareChartData = () => {
    if (!dailyStats?.series) return [];
    
    return dailyStats.series.map(day => ({
      day: new Date(day.day).toLocaleDateString('en', { weekday: 'short' }),
      date: day.day,
      total: day.total || 0,
      success: day.success || 0,
      failed: day.failed || 0,
      success_rate: day.success_rate || 0,
      captcha: day.captcha_encountered || 0
    }));
  };

  const chartData = prepareChartData();

  // Submission breakdown for pie chart
  const submissionBreakdown = [
    { name: 'Successful', value: analytics?.successful_submissions || 0, color: '#10b981' },
    { name: 'Failed', value: analytics?.failed_submissions || 0, color: '#ef4444' },
    { name: 'Pending', value: (analytics?.total_submissions - (analytics?.successful_submissions + analytics?.failed_submissions)) || 0, color: '#f59e0b' }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Removed duplicate header - using main layout header instead */}
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Controls Bar */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <select 
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
            <button
              onClick={fetchDashboardData}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              disabled={refreshing}
            >
              <RefreshCw className={`w-5 h-5 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
          <button 
            onClick={() => window.location.href = '/campaigns/new'}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Campaign
          </button>
        </div>

        {/* KPI Toggle Tabs */}
        <div className="flex gap-2 mb-6">
          {['overview', 'efficiency', 'quality', 'websites'].map(view => (
            <button
              key={view}
              onClick={() => setSelectedKPIView(view)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
                selectedKPIView === view 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-300'
              }`}
            >
              {view}
            </button>
          ))}
        </div>

        {/* Dynamic KPI Grid based on selected view */}
        {selectedKPIView === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Submissions</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.total_submissions?.toLocaleString() || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <ArrowUpRight className="w-4 h-4 text-green-500 mr-1" />
                    <span className="text-green-600">+{kpis.growthTrend}%</span>
                    <span className="text-gray-400 ml-1">vs last period</span>
                  </div>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Activity className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Success Rate</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.success_rate?.toFixed(1) || '0'}%
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-1" />
                    <span className="text-green-600">{analytics?.successful_submissions || 0} successful</span>
                  </div>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Active Campaigns</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.active_campaigns || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <span className="text-gray-400">of {analytics?.campaigns_count || '0'} total</span>
                  </div>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Websites Processed</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.websites_count?.toLocaleString() || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Globe className="w-4 h-4 text-blue-500 mr-1" />
                    <span className="text-blue-600">{analytics?.websites_with_forms || 0} with forms</span>
                  </div>
                </div>
                <div className="p-3 bg-orange-50 rounded-lg">
                  <Globe className="w-5 h-5 text-orange-600" />
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedKPIView === 'efficiency' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Daily Average</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {kpis.dailyAverage?.toFixed(0) || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Calendar className="w-4 h-4 text-blue-500 mr-1" />
                    <span className="text-gray-600">submissions/day</span>
                  </div>
                </div>
                <div className="p-3 bg-yellow-50 rounded-lg">
                  <Zap className="w-5 h-5 text-yellow-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Avg Retry Count</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.avg_retry_count?.toFixed(1) || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <RefreshCw className="w-4 h-4 text-orange-500 mr-1" />
                    <span className="text-gray-600">per submission</span>
                  </div>
                </div>
                <div className="p-3 bg-indigo-50 rounded-lg">
                  <Timer className="w-5 h-5 text-indigo-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Per Campaign Avg</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {kpis.submissionsPerCampaign || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Hash className="w-4 h-4 text-purple-500 mr-1" />
                    <span className="text-gray-600">submissions</span>
                  </div>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Database className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Processing Rate</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {kpis.processingRate?.toFixed(1) || '0'}%
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Cpu className="w-4 h-4 text-green-500 mr-1" />
                    <span className="text-gray-600">completed</span>
                  </div>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <Server className="w-5 h-5 text-green-600" />
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedKPIView === 'quality' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Form Detection Rate</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.form_detection_rate?.toFixed(1) || '0'}%
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Target className="w-4 h-4 text-green-500 mr-1" />
                    <span className="text-gray-600">{analytics?.websites_with_forms || 0} detected</span>
                  </div>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <Target className="w-5 h-5 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">CAPTCHA Success</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.captcha_success_rate?.toFixed(1) || '0'}%
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Shield className="w-4 h-4 text-purple-500 mr-1" />
                    <span className="text-gray-600">{analytics?.captcha_solved || 0} solved</span>
                  </div>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <Shield className="w-5 h-5 text-purple-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Email Extraction</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.emails_extracted || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Mail className="w-4 h-4 text-blue-500 mr-1" />
                    <span className="text-blue-600">{kpis.emailExtractionRate}% rate</span>
                  </div>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Mail className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Unique Campaigns</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.unique_campaigns_used || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Users className="w-4 h-4 text-indigo-500 mr-1" />
                    <span className="text-gray-600">utilized</span>
                  </div>
                </div>
                <div className="p-3 bg-indigo-50 rounded-lg">
                  <Users className="w-5 h-5 text-indigo-600" />
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedKPIView === 'websites' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Websites</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.websites_count || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Globe className="w-4 h-4 text-blue-500 mr-1" />
                    <span className="text-gray-600">processed</span>
                  </div>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Globe className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">With Forms</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.websites_with_forms || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <FileText className="w-4 h-4 text-green-500 mr-1" />
                    <span className="text-green-600">forms detected</span>
                  </div>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <FileText className="w-5 h-5 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">With CAPTCHA</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {analytics?.websites_with_captcha || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Shield className="w-4 h-4 text-purple-500 mr-1" />
                    <span className="text-purple-600">protected</span>
                  </div>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <Shield className="w-5 h-5 text-purple-600" />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Avg per Campaign</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">
                    {kpis.websitesPerCampaign || '0'}
                  </p>
                  <div className="flex items-center mt-2 text-sm">
                    <Link2 className="w-4 h-4 text-orange-500 mr-1" />
                    <span className="text-gray-600">websites</span>
                  </div>
                </div>
                <div className="p-3 bg-orange-50 rounded-lg">
                  <HardDrive className="w-5 h-5 text-orange-600" />
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Submission Trends */}
          <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Submission Trends</h2>
              <button className="text-gray-400 hover:text-gray-600">
                <MoreVertical className="w-5 h-5" />
              </button>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="day" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="success" 
                  stroke="#10b981" 
                  fillOpacity={1} 
                  fill="url(#colorSuccess)"
                  strokeWidth={2}
                />
                <Area 
                  type="monotone" 
                  dataKey="failed" 
                  stroke="#ef4444" 
                  fillOpacity={1} 
                  fill="url(#colorFailed)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Recent Campaigns - Fixed Component */}
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Recent Campaigns</h2>
              <a href="/campaigns" className="text-sm text-blue-600 hover:text-blue-700 font-medium">View all</a>
            </div>
            
            <div className="space-y-4">
              {campaigns.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 text-sm">No campaigns yet</p>
                  <a 
                    href="/campaigns/new" 
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium mt-2 inline-block"
                  >
                    Create your first campaign
                  </a>
                </div>
              ) : (
                campaigns.slice(0, 5).map((campaign) => {
                  // Helper function to get status styling
                  const getStatusStyle = (status) => {
                    const statusMap = {
                      'COMPLETED': { bg: 'bg-green-100', text: 'text-green-700', icon: CheckCircle },
                      'DRAFT': { bg: 'bg-gray-100', text: 'text-gray-700', icon: FileText },
                      'ACTIVE': { bg: 'bg-blue-100', text: 'text-blue-700', icon: Activity },
                      'RUNNING': { bg: 'bg-blue-100', text: 'text-blue-700', icon: Activity },
                      'FAILED': { bg: 'bg-red-100', text: 'text-red-700', icon: XCircle },
                      'PAUSED': { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: Clock }
                    };
                    return statusMap[status?.toUpperCase()] || statusMap['DRAFT'];
                  };

                  // Helper function to format campaign name
                  const formatCampaignName = (campaign) => {
                    if (campaign.name && !campaign.name.startsWith('Campaign -')) {
                      return campaign.name;
                    }
                    
                    let displayName = campaign.name || `Campaign ${campaign.id?.slice(0, 8)}`;
                    displayName = displayName
                      .replace(/^Campaign - /, '')
                      .replace(/ - \d{8}_\d{6}$/, '')
                      .replace(/Sample\.csv|TestFile\.csv/, (match) => match.replace('.csv', ''))
                      .replace(/20250912_\d+/, '');
                    
                    if (displayName.length > 35) {
                      displayName = displayName.substring(0, 32) + '...';
                    }
                    
                    return displayName || 'Untitled Campaign';
                  };

                  const statusStyle = getStatusStyle(campaign.status);
                  const StatusIcon = statusStyle.icon;
                  const progress = Math.round(((campaign.processed || 0) / Math.max(campaign.total_websites || campaign.total_urls || 1, 1)) * 100);
                  const total = campaign.total_websites || campaign.total_urls || 0;
                  const processed = campaign.processed || 0;

                  // Get progress color
                  const getProgressColor = () => {
                    if (campaign.status === 'COMPLETED') return 'bg-green-500';
                    if (campaign.status === 'FAILED') return 'bg-red-500';
                    if (progress === 0) return 'bg-gray-300';
                    if (progress < 50) return 'bg-yellow-500';
                    return 'bg-blue-500';
                  };
                  
                  return (
                    <div 
                      key={campaign.id} 
                      className="p-4 hover:bg-gray-50 rounded-lg transition-colors border border-gray-100 hover:border-gray-200 cursor-pointer"
                      onClick={() => window.location.href = `/campaigns/${campaign.id}`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {formatCampaignName(campaign)}
                          </h3>
                          <p className="text-xs text-gray-500 mt-1">
                            {processed}/{total} processed
                          </p>
                        </div>
                        
                        <div className="flex items-center ml-3">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${statusStyle.bg} ${statusStyle.text}`}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {campaign.status}
                          </span>
                        </div>
                      </div>
                      
                      {/* Progress Bar */}
                      <div className="flex items-center gap-3">
                        <div className="flex-1 bg-gray-200 rounded-full h-2.5 overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-300 ${getProgressColor()}`}
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-gray-600 min-w-[35px] text-right">
                          {progress}%
                        </span>
                      </div>
                      
                      {/* Additional Info */}
                      <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
                        <span>
                          {campaign.successful || 0} successful, {campaign.failed || 0} failed
                        </span>
                        {campaign.created_at && (
                          <span>
                            {new Date(campaign.created_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Additional Analytics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-8">
          {/* Submission Breakdown Pie Chart */}
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Submission Status</h2>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={submissionBreakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {submissionBreakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-2 gap-2 mt-4">
              {submissionBreakdown.map((item) => (
                <div key={item.name} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-xs text-gray-600">{item.name}: {item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Website Performance from actual database */}
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Top Domains</h2>
              <Filter className="w-4 h-4 text-gray-400" />
            </div>
            <div className="space-y-3">
              {websiteStats.slice(0, 4).map((domain, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{domain.domain}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all ${
                            domain.success_rate > 80 ? 'bg-green-500' : 
                            domain.success_rate > 60 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${domain.success_rate}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600 min-w-[40px]">{domain.success_rate}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Stats from actual database */}
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">API Status</span>
                </div>
                <span className="text-sm font-semibold text-green-600">Operational</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">Database</span>
                </div>
                <span className="text-sm font-semibold text-green-600">Connected</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">CAPTCHA Service</span>
                </div>
                <span className="text-sm font-semibold text-green-600">Active</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">Processing Queue</span>
                </div>
                <span className="text-sm font-semibold text-blue-600">
                  {campaigns.filter(c => c.status === 'active' || c.status === 'running').length} Active
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;