import React, { useState, useRef, useEffect } from 'react';
import { 
  Upload, FileText, CheckCircle, Loader2, X, AlertCircle, 
  ArrowLeft, Clock, Globe, ChevronRight, Info, BarChart3, 
  Sparkles, Zap, Shield, Activity, Target, Rocket, Database, 
  Eye, RefreshCw, Plus, Play, Pause, Hash, Calendar, Building2,
  Users, TrendingUp, Award, Server, ArrowUpRight, Edit3, Copy
} from 'lucide-react';

// Shared Components (eliminates duplication)
const StatusBadge = ({ status }) => {
  const configs = {
    'ACTIVE': { bg: 'bg-blue-100', text: 'text-blue-700', icon: Play },
    'PROCESSING': { bg: 'bg-blue-100', text: 'text-blue-700', icon: Activity },
    'COMPLETED': { bg: 'bg-green-100', text: 'text-green-700', icon: CheckCircle },
    'PAUSED': { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: Pause },
    'FAILED': { bg: 'bg-red-100', text: 'text-red-700', icon: AlertCircle }
  };
  
  const config = configs[status?.toUpperCase()] || configs['PAUSED'];
  const Icon = config.icon;
  
  return (
    <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium ${config.bg} ${config.text}`}>
      <Icon className="w-4 h-4 mr-1.5" />
      {status}
    </span>
  );
};

const ProgressBar = ({ current, total, className = "" }) => {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  return (
    <div className={`w-full bg-gray-200 rounded-full h-3 ${className}`}>
      <div 
        className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-1000"
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

const CampaignStatsGrid = ({ campaign }) => {
  const successRate = campaign.processed > 0 ? ((campaign.successful / campaign.processed) * 100).toFixed(1) : 0;
  
  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="text-center p-3 bg-blue-50 rounded-lg">
        <div className="text-xl font-bold text-blue-600">{campaign.successful || 0}</div>
        <div className="text-xs text-gray-500">Successful</div>
      </div>
      <div className="text-center p-3 bg-red-50 rounded-lg">
        <div className="text-xl font-bold text-red-600">{campaign.failed || 0}</div>
        <div className="text-xs text-gray-500">Failed</div>
      </div>
      <div className="text-center p-3 bg-green-50 rounded-lg">
        <div className="text-xl font-bold text-green-600">{successRate}%</div>
        <div className="text-xs text-gray-500">Success Rate</div>
      </div>
      <div className="text-center p-3 bg-purple-50 rounded-lg">
        <div className="text-xl font-bold text-purple-600">{campaign.processed || 0}</div>
        <div className="text-xs text-gray-500">Processed</div>
      </div>
    </div>
  );
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diffHours = Math.floor((now - date) / (1000 * 60 * 60));
  
  if (diffHours < 1) return 'Just now';
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
};

const ConsolidatedCampaignsHub = () => {
  const navigate = (path) => console.log('Navigate to:', path);
  const [activeTab, setActiveTab] = useState('overview');
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [csvFile, setCsvFile] = useState(null);
  const [csvPreview, setCsvPreview] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [monitoringCampaign, setMonitoringCampaign] = useState(null);
  const fileInputRef = useRef(null);

  // Mock data
  const mockCampaigns = [
    {
      id: 'camp-001',
      name: 'SaaS Companies Q4 2024',
      status: 'ACTIVE',
      total_urls: 1250,
      processed: 456,
      successful: 387,
      failed: 69,
      created_at: '2024-09-10T14:20:00Z',
      csv_filename: 'saas_companies_q4.csv'
    },
    {
      id: 'camp-002', 
      name: 'Tech Startups Directory',
      status: 'COMPLETED',
      total_urls: 890,
      processed: 890,
      successful: 742,
      failed: 148,
      created_at: '2024-09-01T10:00:00Z',
      csv_filename: 'tech_startups_2024.csv'
    }
  ];

  useEffect(() => {
    setCampaigns(mockCampaigns);
  }, []);

  const runningCampaigns = campaigns.filter(c => c.status === 'ACTIVE' || c.status === 'PROCESSING');
  const completedCampaigns = campaigns.filter(c => c.status !== 'ACTIVE' && c.status !== 'PROCESSING');

  const handleFileUpload = async (file) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Please upload a CSV file');
      return;
    }
    
    setCsvFile(file);
    const text = await file.text();
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    setCsvPreview({
      headers,
      totalRows: lines.length - 1,
      filename: file.name
    });
  };

  const handleCampaignSubmit = () => {
    setSubmitting(true);
    // Simulate campaign creation
    setTimeout(() => {
      const newCampaign = {
        id: 'camp-new',
        name: csvFile.name.replace('.csv', ''),
        status: 'ACTIVE',
        total_urls: csvPreview.totalRows,
        processed: 0,
        successful: 0,
        failed: 0,
        created_at: new Date().toISOString(),
        csv_filename: csvFile.name
      };
      setCampaigns([newCampaign, ...campaigns]);
      setMonitoringCampaign(newCampaign);
      setActiveTab('monitor');
      setSubmitting(false);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-16 z-30">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-lg">
                  <Rocket className="w-6 h-6 text-white" />
                </div>
                Campaign Hub
              </h1>
              <p className="text-gray-600 mt-1">Create, manage, and monitor all your campaigns</p>
            </div>
            <div className="flex items-center gap-3">
              <button 
                onClick={() => navigate('/reports')}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
              >
                <BarChart3 className="w-4 h-4" />
                Analytics
              </button>
              <button 
                onClick={() => setActiveTab('create')}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                New Campaign
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex">
            {[
              { id: 'overview', label: 'All Campaigns', icon: BarChart3, count: campaigns.length },
              { id: 'create', label: 'Create New', icon: Plus },
              { id: 'monitor', label: 'Active Monitoring', icon: Activity, count: runningCampaigns.length, disabled: runningCampaigns.length === 0 }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => !tab.disabled && setActiveTab(tab.id)}
                  disabled={tab.disabled}
                  className={`relative py-4 px-6 font-medium text-sm transition-all flex items-center gap-2 ${
                    activeTab === tab.id
                      ? 'text-indigo-600'
                      : tab.disabled 
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                  {tab.count !== undefined && (
                    <span className={`ml-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                      activeTab === tab.id 
                        ? 'bg-indigo-100 text-indigo-700' 
                        : tab.disabled
                          ? 'bg-gray-100 text-gray-500'
                          : 'bg-gray-100 text-gray-600'
                    }`}>
                      {tab.count}
                    </span>
                  )}
                  {activeTab === tab.id && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-indigo-600 to-purple-600"></div>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Overview Tab - All Campaigns */}
        {activeTab === 'overview' && (
          <div>
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-blue-100 rounded-xl">
                    <Database className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{campaigns.length}</p>
                    <p className="text-sm text-gray-600">Total Campaigns</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-green-100 rounded-xl">
                    <Activity className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{runningCampaigns.length}</p>
                    <p className="text-sm text-gray-600">Active Now</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-purple-100 rounded-xl">
                    <Globe className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">
                      {campaigns.reduce((sum, c) => sum + c.total_urls, 0).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-600">Total URLs</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-orange-100 rounded-xl">
                    <Target className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">
                      {campaigns.length > 0 ? 
                        (campaigns.reduce((sum, c) => sum + (c.processed > 0 ? (c.successful / c.processed) * 100 : 0), 0) / campaigns.length).toFixed(1)
                        : 0}%
                    </p>
                    <p className="text-sm text-gray-600">Avg Success Rate</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Running Campaigns */}
            {runningCampaigns.length > 0 && (
              <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Currently Running</h2>
                <div className="space-y-4">
                  {runningCampaigns.map((campaign) => (
                    <div key={campaign.id} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-all">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{campaign.name}</h3>
                          <p className="text-sm text-gray-500">
                            {campaign.csv_filename} • Started {formatDate(campaign.created_at)}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <StatusBadge status={campaign.status} />
                          <button
                            onClick={() => navigate(`/campaigns/${campaign.id}`)}
                            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                          >
                            View Details
                          </button>
                        </div>
                      </div>
                      
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-gray-600">Progress</span>
                          <span className="text-sm font-medium">
                            {campaign.processed}/{campaign.total_urls} ({Math.round((campaign.processed / campaign.total_urls) * 100)}%)
                          </span>
                        </div>
                        <ProgressBar current={campaign.processed} total={campaign.total_urls} />
                      </div>
                      
                      <CampaignStatsGrid campaign={campaign} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* All Campaigns */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">All Campaigns</h2>
              <div className="grid gap-6">
                {campaigns.map((campaign) => (
                  <div key={campaign.id} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-all">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">{campaign.name}</h3>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <FileText className="w-4 h-4" />
                            {campaign.csv_filename}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {formatDate(campaign.created_at)}
                          </span>
                          <span className="flex items-center gap-1">
                            <Globe className="w-4 h-4" />
                            {campaign.total_urls} URLs
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <StatusBadge status={campaign.status} />
                        <button
                          onClick={() => navigate(`/campaigns/${campaign.id}`)}
                          className="p-2 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    
                    <CampaignStatsGrid campaign={campaign} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Create Tab */}
        {activeTab === 'create' && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
              <div className="p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Campaign</h2>
                
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="relative rounded-2xl border-2 border-dashed border-gray-300 hover:border-indigo-400 hover:bg-gray-50 transition-all cursor-pointer p-12 text-center"
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                    className="hidden"
                  />
                  
                  {csvFile ? (
                    <>
                      <FileText className="w-16 h-16 text-green-500 mx-auto mb-4" />
                      <p className="text-xl font-semibold text-gray-900">{csvFile.name}</p>
                      <p className="text-gray-600 mt-2">{csvPreview?.totalRows || 0} URLs ready to process</p>
                    </>
                  ) : (
                    <>
                      <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-xl font-medium text-gray-900">Upload your CSV file</p>
                      <p className="text-gray-500 mt-2">Drag and drop or click to browse</p>
                    </>
                  )}
                </div>

                {csvPreview && (
                  <div className="mt-6 flex items-center justify-between">
                    <div className="text-gray-600">
                      Ready to process <span className="font-semibold">{csvPreview.totalRows} websites</span>
                    </div>
                    <button
                      onClick={handleCampaignSubmit}
                      disabled={submitting}
                      className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:shadow-xl transition-all disabled:opacity-50"
                    >
                      {submitting ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin mr-2 inline" />
                          Launching...
                        </>
                      ) : (
                        'Launch Campaign'
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Monitor Tab */}
        {activeTab === 'monitor' && runningCampaigns.length > 0 && (
          <div className="max-w-4xl mx-auto">
            {runningCampaigns.map(campaign => (
              <div key={campaign.id} className="bg-white rounded-2xl shadow-xl p-8">
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Monitoring: {campaign.name}</h2>
                  <p className="text-gray-600">Processing {campaign.processed} of {campaign.total_urls} URLs</p>
                </div>

                <div className="mb-8">
                  <div className="flex justify-between mb-3">
                    <span className="text-sm font-medium text-gray-700">Progress</span>
                    <span className="text-sm font-bold text-gray-900">
                      {Math.round((campaign.processed / campaign.total_urls) * 100)}%
                    </span>
                  </div>
                  <ProgressBar current={campaign.processed} total={campaign.total_urls} className="h-4" />
                </div>

                <CampaignStatsGrid campaign={campaign} />

                <div className="flex justify-center gap-4 mt-8">
                  <button 
                    onClick={() => navigate(`/campaigns/${campaign.id}`)}
                    className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-all"
                  >
                    View Details
                  </button>
                  <button 
                    onClick={() => setActiveTab('create')}
                    className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:shadow-lg transition-all"
                  >
                    Create Another
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ConsolidatedCampaignsHub;