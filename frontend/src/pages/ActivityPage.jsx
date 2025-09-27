import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, Download, Filter, Activity, AlertCircle, Calendar, Search, 
  Clock, X, Check, CheckCircle, AlertTriangle, Info, Server, Smartphone, Upload, 
  FileText, ExternalLink, ChevronDown, ChevronRight, Star, MoreVertical,
  TrendingUp, Users, Globe, Shield, Zap, Eye, Hash, ArrowUpRight,
  BarChart3, Target, Bell, Settings, Sparkles, Database, Cpu
} from 'lucide-react';

const defaultFilters = {
  me: true,
  source: '',
  level: '',
  action: '',
  status: '',
  q: '',
  date_from: '',
  date_to: '',
  page: 1,
  page_size: 25,
};

const ActivityPage = () => {
  const [filters, setFilters] = useState(defaultFilters);
  const [resp, setResp] = useState({ items: [], total: 0, page: 1, pages: 1 });
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [expandedGroups, setExpandedGroups] = useState(new Set());
  const [pinnedItems, setPinnedItems] = useState(new Set());
  const [viewMode, setViewMode] = useState('timeline'); // timeline, grid, compact
  const [selectedTimeRange, setSelectedTimeRange] = useState('today');

  // Mock enhanced stats
  const mockStats = {
    total: 2847,
    today: 342,
    trend: '+12.5%',
    by_level: {
      INFO: 2100,
      WARN: 547,
      ERROR: 200
    },
    by_source: {
      system: 1200,
      app: 947,
      submission: 700
    },
    performance: {
      avgResponseTime: '235ms',
      successRate: '96.8%',
      activeProcesses: 23
    }
  };

  useEffect(() => {
    // Simulate loading
    setStats(mockStats);
  }, []);

  const setField = (k, v) => setFilters((f) => ({ ...f, [k]: v }));

  const getSourceIcon = (source) => {
    const icons = {
      'system': { icon: Server, color: 'text-purple-600', bg: 'bg-purple-100' },
      'app': { icon: Smartphone, color: 'text-blue-600', bg: 'bg-blue-100' },
      'submission': { icon: Upload, color: 'text-green-600', bg: 'bg-green-100' },
      'default': { icon: FileText, color: 'text-gray-600', bg: 'bg-gray-100' }
    };
    return icons[source] || icons.default;
  };

  const getLevelStyle = (level) => {
    const styles = {
      'ERROR': { color: 'text-red-700', bg: 'bg-red-100', border: 'border-red-200', dot: 'bg-red-500' },
      'WARN': { color: 'text-amber-700', bg: 'bg-amber-100', border: 'border-amber-200', dot: 'bg-amber-500' },
      'INFO': { color: 'text-blue-700', bg: 'bg-blue-100', border: 'border-blue-200', dot: 'bg-blue-500' },
      'default': { color: 'text-gray-700', bg: 'bg-gray-100', border: 'border-gray-200', dot: 'bg-gray-500' }
    };
    return styles[level] || styles.default;
  };

  // Enhanced mock data
  const mockActivities = [
    {
      id: 1,
      timestamp: new Date().toISOString(),
      level: 'INFO',
      source: 'system',
      action: 'Campaign Started',
      message: 'Campaign "Tech Startups Q1" has been initiated',
      details: 'Processing 2,500 websites with AI-powered form detection',
      target_url: 'https://app.example.com/campaigns/abc123',
      user: 'John Doe',
      impact: 'low'
    },
    {
      id: 2,
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      level: 'WARN',
      source: 'app',
      action: 'Rate Limit Warning',
      message: 'Approaching API rate limit threshold',
      details: '85% of hourly limit reached (850/1000 requests)',
      user: 'System',
      impact: 'medium'
    },
    {
      id: 3,
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      level: 'ERROR',
      source: 'submission',
      action: 'Submission Failed',
      message: 'Failed to submit form on example.com',
      details: 'CAPTCHA validation failed after 3 attempts',
      target_url: 'https://example.com/contact',
      user: 'Jane Smith',
      impact: 'high'
    }
  ];

  const groupActivitiesByDate = (activities) => {
    const groups = {};
    activities.forEach(activity => {
      const date = new Date(activity.timestamp).toDateString();
      if (!groups[date]) groups[date] = [];
      groups[date].push(activity);
    });
    return groups;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date().toDateString();
    const yesterday = new Date(Date.now() - 86400000).toDateString();
    
    if (date.toDateString() === today) return 'Today';
    if (date.toDateString() === yesterday) return 'Yesterday';
    return date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
  };

  const TimelineItem = ({ activity, isLast }) => {
    const sourceStyle = getSourceIcon(activity.source);
    const levelStyle = getLevelStyle(activity.level);
    const SourceIcon = sourceStyle.icon;
    const isPinned = pinnedItems.has(activity.id);

    return (
      <div className="group flex">
        {/* Timeline Line */}
        <div className="flex flex-col items-center mr-4">
          <div className={`w-3 h-3 rounded-full ${levelStyle.dot} ring-4 ring-white shadow-sm`} />
          {!isLast && <div className="w-px h-full bg-gray-200 mt-2" />}
        </div>
        
        {/* Enhanced Content Card */}
        <div className="flex-1 pb-8">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:scale-[1.01]">
            {/* Card Header */}
            <div className="p-5 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl ${sourceStyle.bg}`}>
                    <SourceIcon className={`w-5 h-5 ${sourceStyle.color}`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-gray-900">
                        {activity.action || activity.source}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${levelStyle.bg} ${levelStyle.color} ${levelStyle.border} border`}>
                        {activity.level}
                      </span>
                      {activity.impact && (
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          activity.impact === 'high' ? 'bg-red-100 text-red-700' :
                          activity.impact === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-green-100 text-green-700'
                        }`}>
                          {activity.impact} impact
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(activity.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      {activity.user && (
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {activity.user}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPinnedItems(prev => 
                      prev.has(activity.id) 
                        ? new Set([...prev].filter(id => id !== activity.id))
                        : new Set([...prev, activity.id])
                    )}
                    className={`p-2 rounded-lg transition-all ${
                      isPinned 
                        ? 'bg-amber-100 text-amber-600' 
                        : 'hover:bg-gray-100 text-gray-400'
                    }`}
                  >
                    <Star className={`w-4 h-4 ${isPinned ? 'fill-current' : ''}`} />
                  </button>
                  <button className="p-2 hover:bg-gray-100 rounded-lg text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            
            {/* Card Body */}
            <div className="p-5">
              {activity.message && (
                <p className="text-gray-700 mb-3 leading-relaxed">{activity.message}</p>
              )}
              
              {activity.details && (
                <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-4 text-sm text-gray-600 mb-3 border border-gray-200">
                  <div className="flex items-start gap-2">
                    <Info className="w-4 h-4 text-gray-400 mt-0.5" />
                    <span>{activity.details}</span>
                  </div>
                </div>
              )}
              
              {activity.target_url && (
                <a
                  href={activity.target_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm font-medium bg-blue-50 px-3 py-1.5 rounded-lg transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  View Resource
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const groupedActivities = groupActivitiesByDate(mockActivities);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      {/* Modern Header */}
      <div className="bg-white border-b border-gray-100 sticky top-16 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Activity Timeline</h1>
              <p className="text-gray-600">Monitor all system events and user activities</p>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
              </select>
              <button
                onClick={() => {}}
                disabled={loading}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <button className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg">
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Enhanced Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-100 rounded-xl">
                <Activity className="w-6 h-6 text-blue-600" />
              </div>
              <span className="text-sm font-medium text-green-600 flex items-center">
                <TrendingUp className="w-3 h-3 mr-1" />
                {stats?.trend}
              </span>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-2">{stats?.total.toLocaleString()}</div>
            <div className="text-gray-600 text-sm">Total Activities</div>
            <div className="text-xs text-gray-400 mt-1">{stats?.today} today</div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-100 rounded-xl">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <span className="text-xs text-gray-500">Success Rate</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-2">{stats?.performance?.successRate}</div>
            <div className="text-gray-600 text-sm">Performance</div>
            <div className="text-xs text-gray-400 mt-1">{stats?.performance?.avgResponseTime} avg</div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-amber-100 rounded-xl">
                <AlertTriangle className="w-6 h-6 text-amber-600" />
              </div>
              <span className="text-xs text-gray-500">Warnings</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-2">{stats?.by_level?.WARN}</div>
            <div className="text-gray-600 text-sm">Attention Needed</div>
            <div className="text-xs text-gray-400 mt-1">{stats?.by_level?.ERROR} errors</div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-100 rounded-xl">
                <Cpu className="w-6 h-6 text-purple-600" />
              </div>
              <span className="text-xs text-gray-500">System</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-2">{stats?.performance?.activeProcesses}</div>
            <div className="text-gray-600 text-sm">Active Processes</div>
            <div className="text-xs text-gray-400 mt-1">Running now</div>
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            {['timeline', 'grid', 'compact'].map(mode => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all capitalize ${
                  viewMode === mode
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-300'
                }`}
              >
                {mode} View
              </button>
            ))}
          </div>
          
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search activities..."
                value={filters.q}
                onChange={(e) => setField('q', e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button className="p-2 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors">
              <Filter className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Enhanced Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Quick Filters */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Filter className="w-5 h-5 text-gray-400" />
                Quick Filters
              </h3>
              <div className="space-y-3">
                <select
                  value={filters.source}
                  onChange={(e) => setField('source', e.target.value)}
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm"
                >
                  <option value="">All Sources</option>
                  <option value="system">System</option>
                  <option value="app">Application</option>
                  <option value="submission">Submission</option>
                </select>
                
                <select
                  value={filters.level}
                  onChange={(e) => setField('level', e.target.value)}
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm"
                >
                  <option value="">All Levels</option>
                  <option value="INFO">Info</option>
                  <option value="WARN">Warning</option>
                  <option value="ERROR">Error</option>
                </select>

                <button className="w-full bg-blue-600 text-white rounded-xl py-2 hover:bg-blue-700 transition-colors font-medium">
                  Apply Filters
                </button>
              </div>
            </div>

            {/* Activity Summary */}
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl border border-blue-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Activity Breakdown</h3>
              <div className="space-y-4">
                {Object.entries(stats?.by_level || {}).map(([level, count]) => {
                  const style = getLevelStyle(level);
                  const percentage = (count / stats.total * 100).toFixed(1);
                  return (
                    <div key={level}>
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-sm font-medium ${style.color}`}>{level}</span>
                        <span className="text-sm text-gray-600">{count}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${style.dot}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Main Timeline */}
          <div className="lg:col-span-3">
            {loading && (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
              </div>
            )}
            
            {!loading && Object.keys(groupedActivities).length === 0 && (
              <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center">
                <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No Activities Found</h3>
                <p className="text-gray-600 mb-6">Try adjusting your filters or check back later.</p>
                <button className="px-6 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors">
                  Clear Filters
                </button>
              </div>
            )}

            {!loading && Object.keys(groupedActivities).length > 0 && (
              <div className="space-y-8">
                {Object.entries(groupedActivities).map(([date, activities]) => (
                  <div key={date}>
                    <div className="sticky top-32 z-10 mb-6">
                      <div className="bg-white rounded-xl border border-gray-200 px-4 py-2 shadow-sm inline-flex items-center gap-3">
                        <button
                          onClick={() => setExpandedGroups(prev => 
                            prev.has(date) 
                              ? new Set([...prev].filter(d => d !== date))
                              : new Set([...prev, date])
                          )}
                          className="flex items-center gap-2"
                        >
                          {expandedGroups.has(date) ? 
                            <ChevronDown className="w-4 h-4 text-gray-500" /> : 
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                          }
                          <h2 className="font-semibold text-gray-900">{formatDate(date)}</h2>
                        </button>
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                          {activities.length} activities
                        </span>
                      </div>
                    </div>

                    {(!expandedGroups.size || expandedGroups.has(date)) && (
                      <div className="pl-4">
                        {activities.map((activity, index) => (
                          <TimelineItem 
                            key={activity.id}
                            activity={activity}
                            isLast={index === activities.length - 1}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActivityPage;