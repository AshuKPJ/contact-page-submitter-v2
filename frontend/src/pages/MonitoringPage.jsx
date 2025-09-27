import React, { useState, useEffect } from 'react';
import { 
  Activity, Server, Database, Cpu, HardDrive, Wifi, Shield,
  AlertTriangle, CheckCircle, XCircle, Clock, RefreshCw,
  TrendingUp, TrendingDown, Zap, Globe, Users, Package,
  BarChart3, Terminal, Cloud, Lock, AlertCircle, Info,
  Play, Pause, Settings, Download, ChevronRight, MoreVertical,
  ArrowUpRight, ArrowDownRight
} from 'lucide-react';

const MonitoringPage = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');

  // System metrics
  const systemStatus = {
    overall: 'operational',
    uptime: '99.98%',
    lastIncident: '15 days ago',
    activeAlerts: 2
  };

  const serverMetrics = [
    {
      name: 'API Server',
      status: 'operational',
      cpu: 45,
      memory: 62,
      disk: 38,
      responseTime: 42,
      requestsPerSec: 1250
    },
    {
      name: 'Database Primary',
      status: 'operational',
      cpu: 38,
      memory: 71,
      disk: 54,
      connections: 89,
      queryTime: 1.2
    },
    {
      name: 'Queue Server',
      status: 'operational',
      cpu: 22,
      memory: 45,
      disk: 31,
      jobsProcessed: 4532,
      queueLength: 23
    },
    {
      name: 'Cache Server',
      status: 'degraded',
      cpu: 78,
      memory: 85,
      disk: 42,
      hitRate: 94.5,
      evictions: 234
    }
  ];

  const services = [
    { name: 'API Gateway', status: 'operational', latency: 12, uptime: 99.99 },
    { name: 'Authentication', status: 'operational', latency: 8, uptime: 100 },
    { name: 'Form Processor', status: 'operational', latency: 45, uptime: 99.95 },
    { name: 'CAPTCHA Solver', status: 'operational', latency: 120, uptime: 99.8 },
    { name: 'Webhook Service', status: 'degraded', latency: 250, uptime: 98.5 },
    { name: 'Email Service', status: 'operational', latency: 35, uptime: 99.9 }
  ];

  const recentIncidents = [
    {
      id: 1,
      severity: 'warning',
      title: 'High Memory Usage on Cache Server',
      time: '10 minutes ago',
      status: 'investigating'
    },
    {
      id: 2,
      severity: 'info',
      title: 'Scheduled Maintenance Window',
      time: 'In 2 hours',
      status: 'scheduled'
    },
    {
      id: 3,
      severity: 'resolved',
      title: 'API Rate Limit Spike',
      time: '3 hours ago',
      status: 'resolved'
    }
  ];

  const performanceData = [
    { time: '00:00', cpu: 35, memory: 45, requests: 890 },
    { time: '04:00', cpu: 28, memory: 42, requests: 650 },
    { time: '08:00', cpu: 52, memory: 58, requests: 1450 },
    { time: '12:00', cpu: 68, memory: 72, requests: 2100 },
    { time: '16:00', cpu: 61, memory: 65, requests: 1890 },
    { time: '20:00', cpu: 45, memory: 52, requests: 1350 }
  ];

  const getStatusColor = (status) => {
    const colors = {
      operational: 'bg-green-100 text-green-700',
      degraded: 'bg-yellow-100 text-yellow-700',
      outage: 'bg-red-100 text-red-700',
      maintenance: 'bg-blue-100 text-blue-700'
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  const getMetricColor = (value) => {
    if (value < 60) return 'text-green-600';
    if (value < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getProgressBarColor = (value) => {
    if (value < 60) return 'bg-green-500';
    if (value < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        // Simulate data refresh
        console.log('Refreshing data...');
      }, refreshInterval * 1000);
      
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                System Monitoring
              </h1>
              <p className="text-gray-600 mt-1">Real-time system health and performance metrics</p>
            </div>
            <div className="flex items-center gap-3">
              {/* Auto Refresh Toggle */}
              <div className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-xl">
                <label className="text-sm text-gray-700">Auto-refresh</label>
                <button
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    autoRefresh ? 'bg-purple-600' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      autoRefresh ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="px-4 py-2 bg-white border border-gray-300 rounded-xl text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="5m">Last 5 min</option>
                <option value="1h">Last hour</option>
                <option value="24h">Last 24h</option>
                <option value="7d">Last 7 days</option>
              </select>
              <button className="p-2 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors">
                <RefreshCw className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className={`${
        systemStatus.overall === 'operational' ? 'bg-green-500' : 'bg-yellow-500'
      } text-white`}>
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {systemStatus.overall === 'operational' ? (
                <CheckCircle className="w-5 h-5" />
              ) : (
                <AlertTriangle className="w-5 h-5" />
              )}
              <span className="font-medium">
                System Status: {systemStatus.overall === 'operational' ? 'All Systems Operational' : 'Partial Outage'}
              </span>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <span>Uptime: {systemStatus.uptime}</span>
              <span>Last incident: {systemStatus.lastIncident}</span>
              {systemStatus.activeAlerts > 0 && (
                <span className="px-2 py-1 bg-white/20 rounded-full">
                  {systemStatus.activeAlerts} active alerts
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-6 pt-8">
        <div className="flex gap-2 mb-8">
          {['overview', 'servers', 'services', 'incidents'].map((tab) => (
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

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div>
            {/* Quick Stats */}
            <div className="grid grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <Cpu className="w-5 h-5 text-purple-600" />
                  <span className="text-2xl font-bold text-gray-900">52%</span>
                </div>
                <p className="text-sm text-gray-600">CPU Usage</p>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div className="h-2 bg-green-500 rounded-full transition-all duration-300" style={{ width: '52%' }}></div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <HardDrive className="w-5 h-5 text-purple-600" />
                  <span className="text-2xl font-bold text-gray-900">67%</span>
                </div>
                <p className="text-sm text-gray-600">Memory Usage</p>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div className="h-2 bg-yellow-500 rounded-full transition-all duration-300" style={{ width: '67%' }}></div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <Database className="w-5 h-5 text-purple-600" />
                  <span className="text-2xl font-bold text-gray-900">41%</span>
                </div>
                <p className="text-sm text-gray-600">Disk Usage</p>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div className="h-2 bg-green-500 rounded-full transition-all duration-300" style={{ width: '41%' }}></div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <Wifi className="w-5 h-5 text-purple-600" />
                  <span className="text-2xl font-bold text-gray-900">1.2K</span>
                </div>
                <p className="text-sm text-gray-600">Requests/sec</p>
                <div className="flex items-center gap-1 mt-2">
                  <ArrowUpRight className="w-3 h-3 text-green-600" />
                  <span className="text-xs text-green-600">+15%</span>
                </div>
              </div>
            </div>

            {/* Performance Chart */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">System Performance</h3>
              <div className="h-64 flex items-end justify-between gap-4">
                {performanceData.map((data, idx) => (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                    <div className="w-full flex flex-col gap-1" style={{ height: '200px' }}>
                      <div className="relative flex-1 flex items-end">
                        <div 
                          className="w-full bg-purple-600 rounded-t-lg hover:bg-purple-700 transition-colors cursor-pointer"
                          style={{ height: `${data.cpu}%` }}
                        >
                          <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-semibold text-gray-700 opacity-0 hover:opacity-100 transition-opacity">
                            {data.cpu}%
                          </div>
                        </div>
                      </div>
                    </div>
                    <span className="text-sm text-gray-600">{data.time}</span>
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-center gap-4 mt-4">
                <span className="text-sm text-gray-600">CPU Usage Over Time</span>
              </div>
            </div>

            {/* Active Incidents */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Incidents</h3>
              <div className="space-y-3">
                {recentIncidents.map((incident) => (
                  <div key={incident.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="flex items-center gap-3">
                      {incident.severity === 'warning' && (
                        <AlertTriangle className="w-5 h-5 text-yellow-600" />
                      )}
                      {incident.severity === 'info' && (
                        <Info className="w-5 h-5 text-blue-600" />
                      )}
                      {incident.severity === 'resolved' && (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      )}
                      <div>
                        <p className="font-medium text-gray-900">{incident.title}</p>
                        <p className="text-sm text-gray-600">{incident.time}</p>
                      </div>
                    </div>
                    <span className={`px-3 py-1 text-xs rounded-full font-medium ${
                      incident.status === 'investigating' ? 'bg-yellow-100 text-yellow-700' :
                      incident.status === 'resolved' ? 'bg-green-100 text-green-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {incident.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Servers Tab */}
        {activeTab === 'servers' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {serverMetrics.map((server, idx) => (
              <div key={idx} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Server className="w-5 h-5 text-purple-600" />
                    <h3 className="font-semibold text-gray-900">{server.name}</h3>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(server.status)}`}>
                    {server.status}
                  </span>
                </div>

                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-600">CPU</span>
                      <span className={`text-sm font-medium ${getMetricColor(server.cpu)}`}>{server.cpu}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(server.cpu)}`} style={{ width: `${server.cpu}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-600">Memory</span>
                      <span className={`text-sm font-medium ${getMetricColor(server.memory)}`}>{server.memory}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(server.memory)}`} style={{ width: `${server.memory}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-600">Disk</span>
                      <span className={`text-sm font-medium ${getMetricColor(server.disk)}`}>{server.disk}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(server.disk)}`} style={{ width: `${server.disk}%` }}></div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between text-sm">
                  <button className="text-purple-600 hover:text-purple-700 font-medium">View Details</button>
                  <button className="text-gray-600 hover:text-gray-700">
                    <Settings className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Services Tab */}
        {activeTab === 'services' && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Service Health</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr className="border-b border-gray-200">
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Service</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Latency</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Uptime</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {services.map((service, idx) => (
                    <tr key={idx} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{service.name}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(service.status)}`}>
                          {service.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">{service.latency}ms</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{service.uptime}%</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                            <Play className="w-4 h-4 text-gray-600" />
                          </button>
                          <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                            <RefreshCw className="w-4 h-4 text-gray-600" />
                          </button>
                          <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                            <MoreVertical className="w-4 h-4 text-gray-600" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Incidents Tab */}
        {activeTab === 'incidents' && (
          <div className="space-y-6">
            {/* Incident Timeline */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">Incident Timeline</h3>
              <div className="space-y-6">
                {[
                  { date: 'Today', incidents: 2, details: 'Cache server memory spike, API rate limit warning', color: 'yellow' },
                  { date: 'Yesterday', incidents: 0, details: 'No incidents reported', color: 'green' },
                  { date: 'Sep 10', incidents: 1, details: 'Database connection pool exhausted', color: 'yellow' },
                  { date: 'Sep 8', incidents: 3, details: 'DDoS attack mitigated, Service degradation, Backup completed', color: 'red' }
                ].map((day, idx) => (
                  <div key={idx} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="w-24 text-sm font-medium text-gray-700">{day.date}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {day.incidents === 0 ? (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        ) : day.color === 'red' ? (
                          <XCircle className="w-5 h-5 text-red-500" />
                        ) : (
                          <AlertCircle className="w-5 h-5 text-yellow-500" />
                        )}
                        <span className="font-medium text-gray-900">
                          {day.incidents === 0 ? 'No incidents' : `${day.incidents} incident${day.incidents > 1 ? 's' : ''}`}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{day.details}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Incident Statistics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  <span className="text-2xl font-bold text-gray-900">6</span>
                </div>
                <p className="text-sm text-gray-600">This Week</p>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <Clock className="w-5 h-5 text-blue-600" />
                  <span className="text-2xl font-bold text-gray-900">1.2h</span>
                </div>
                <p className="text-sm text-gray-600">Avg Resolution Time</p>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="text-2xl font-bold text-gray-900">94%</span>
                </div>
                <p className="text-sm text-gray-600">Resolution Rate</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MonitoringPage;