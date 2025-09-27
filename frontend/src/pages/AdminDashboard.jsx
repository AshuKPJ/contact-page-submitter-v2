import React, { useState } from "react";
import {
  TrendingUp, Users, FileText, Shield, Activity, DollarSign,
  Clock, Mail, Database, Server, HardDrive, Cpu, CheckCircle,
  AlertCircle, Settings, RefreshCw, Download, Filter, Search,
  Calendar, MoreVertical, BarChart3, Target, Zap, Globe,
  UserCheck, AlertTriangle, ArrowUpRight, ArrowDownRight,
  Eye, Edit3, Trash2, Plus, ChevronRight, Star, Award,
  Sparkles, Bell, Lock, Key, CreditCard, Package
} from "lucide-react";

const AdminDashboard = () => {
  const [selectedPeriod, setSelectedPeriod] = useState("month");
  const [activeTab, setActiveTab] = useState("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState("users");

  // Enhanced stats with gradient colors and more detail
  const stats = [
    {
      label: "Total Users",
      value: "412",
      icon: Users,
      trend: "+12.5%",
      trendUp: true,
      color: "from-blue-500 to-cyan-500",
      lightColor: "bg-blue-100",
      iconColor: "text-blue-600",
      description: "Active accounts",
      sparkline: [40, 45, 42, 48, 52, 58, 55, 60],
      details: { new: 47, inactive: 23, premium: 156 }
    },
    {
      label: "Active Campaigns",
      value: "8,243",
      icon: Activity,
      trend: "+8.2%",
      trendUp: true,
      color: "from-purple-500 to-pink-500",
      lightColor: "bg-purple-100",
      iconColor: "text-purple-600",
      description: "Running now",
      sparkline: [820, 850, 890, 920, 960, 1000, 980, 1050],
      details: { processing: 3421, completed: 4822, failed: 0 }
    },
    {
      label: "Form Submissions",
      value: "211K",
      icon: FileText,
      trend: "+23.1%",
      trendUp: true,
      color: "from-green-500 to-emerald-500",
      lightColor: "bg-green-100",
      iconColor: "text-green-600",
      description: "This month",
      sparkline: [18, 22, 20, 25, 28, 32, 30, 35],
      details: { successful: 198000, failed: 13000, pending: 0 }
    },
    {
      label: "Success Rate",
      value: "96.8%",
      icon: Target,
      trend: "+2.4%",
      trendUp: true,
      color: "from-orange-500 to-red-500",
      lightColor: "bg-orange-100",
      iconColor: "text-orange-600",
      description: "Average rate",
      sparkline: [94, 95, 94.5, 95.5, 96, 96.5, 96.8, 97],
      details: { best: "99.2%", worst: "89.3%", median: "96.5%" }
    }
  ];

  // Database health metrics
  const dbMetrics = {
    status: "healthy",
    tables: 24,
    totalRecords: "394.5K",
    dbSize: "1.2 GB",
    avgQueryTime: "23ms",
    activeConnections: 18,
    maxConnections: 100,
    cacheHitRate: 94.7,
    uptime: "99.99%",
    lastBackup: "2 hours ago",
    nextMaintenance: "In 5 days"
  };

  // Monthly data for charts
  const monthlyData = [
    { month: "Jan", users: 280, campaigns: 1200, submissions: 18500, revenue: 32000 },
    { month: "Feb", users: 320, campaigns: 1900, submissions: 24300, revenue: 36000 },
    { month: "Mar", users: 340, campaigns: 2400, submissions: 31200, revenue: 41000 },
    { month: "Apr", users: 360, campaigns: 2100, submissions: 28900, revenue: 38000 },
    { month: "May", users: 380, campaigns: 2800, submissions: 38400, revenue: 45000 },
    { month: "Jun", users: 412, campaigns: 3200, submissions: 42100, revenue: 52000 },
  ];

  // Recent activity with enhanced details
  const recentActivity = [
    {
      type: "user",
      message: "New enterprise user registered",
      detail: "john.doe@techcorp.com - Enterprise Plan",
      time: "2 minutes ago",
      icon: UserCheck,
      color: "text-green-600",
      bgColor: "bg-green-100",
      importance: "high"
    },
    {
      type: "campaign",
      message: "Large campaign started",
      detail: "Campaign #8243 - 5,000 URLs processing",
      time: "5 minutes ago",
      icon: Activity,
      color: "text-blue-600",
      bgColor: "bg-blue-100",
      importance: "medium"
    },
    {
      type: "error",
      message: "CAPTCHA service issue detected",
      detail: "3 failed validations in the last hour",
      time: "12 minutes ago",
      icon: AlertTriangle,
      color: "text-red-600",
      bgColor: "bg-red-100",
      importance: "high"
    },
    {
      type: "system",
      message: "Database optimization completed",
      detail: "Performance improved by 15%",
      time: "1 hour ago",
      icon: Database,
      color: "text-purple-600",
      bgColor: "bg-purple-100",
      importance: "low"
    }
  ];

  // User management table data
  const users = [
    {
      id: 1,
      name: "Sarah Johnson",
      email: "sarah@company.com",
      plan: "Enterprise",
      status: "active",
      campaigns: 42,
      submissions: 12500,
      successRate: 98.2,
      lastActive: "2 min ago",
      avatar: "SJ"
    },
    {
      id: 2,
      name: "Mike Chen",
      email: "mike@startup.io",
      plan: "Professional",
      status: "active",
      campaigns: 28,
      submissions: 8300,
      successRate: 95.7,
      lastActive: "1 hour ago",
      avatar: "MC"
    },
    {
      id: 3,
      name: "Emma Davis",
      email: "emma@agency.co",
      plan: "Business",
      status: "inactive",
      campaigns: 15,
      submissions: 4200,
      successRate: 93.4,
      lastActive: "3 days ago",
      avatar: "ED"
    }
  ];

  // Sparkline component
  const Sparkline = ({ data, color }) => {
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min;
    
    return (
      <div className="flex items-end gap-0.5 h-8">
        {data.map((value, idx) => {
          const height = ((value - min) / range) * 100;
          return (
            <div
              key={idx}
              className={`w-1 bg-gradient-to-t ${color} rounded-full transition-all hover:opacity-80`}
              style={{ height: `${height}%`, minHeight: '3px' }}
            />
          );
        })}
      </div>
    );
  };

  const StatCard = ({ stat, index }) => {
    const Icon = stat.icon;
    const isSelected = selectedMetric === stat.label.toLowerCase().replace(' ', '-');
    
    return (
      <div
        onClick={() => setSelectedMetric(stat.label.toLowerCase().replace(' ', '-'))}
        className={`bg-white rounded-2xl border p-6 cursor-pointer transition-all duration-300 ${
          isSelected 
            ? 'border-blue-500 shadow-xl scale-[1.02] ring-2 ring-blue-200' 
            : 'border-gray-200 hover:shadow-lg hover:scale-[1.01]'
        }`}
      >
        <div className="flex items-start justify-between mb-4">
          <div className={`${stat.lightColor} p-3 rounded-xl`}>
            <Icon className={`w-6 h-6 ${stat.iconColor}`} />
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-bold flex items-center ${
              stat.trendUp ? 'text-green-600' : 'text-red-600'
            }`}>
              {stat.trendUp ? (
                <ArrowUpRight className="w-3 h-3 mr-0.5" />
              ) : (
                <ArrowDownRight className="w-3 h-3 mr-0.5" />
              )}
              {stat.trend}
            </span>
            <button className="p-1 hover:bg-gray-100 rounded-lg opacity-0 hover:opacity-100 transition-opacity">
              <MoreVertical className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>
        
        <p className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</p>
        <p className="text-sm text-gray-500 mb-3">{stat.label}</p>
        
        {/* Sparkline */}
        <div className="mb-3">
          <Sparkline data={stat.sparkline} color={stat.color} />
        </div>
        
        <p className="text-xs text-gray-400">{stat.description}</p>
        
        {/* Quick stats */}
        {isSelected && (
          <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-3 gap-2">
            {Object.entries(stat.details).map(([key, value]) => (
              <div key={key} className="text-center">
                <p className="text-xs text-gray-500 capitalize">{key}</p>
                <p className="text-sm font-semibold text-gray-900">{value}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 sticky top-16 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
              <p className="text-gray-600">System overview and management controls</p>
            </div>
            <div className="flex items-center space-x-3">
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="year">This Year</option>
              </select>
              <button 
                onClick={() => setRefreshing(true)}
                className="p-2 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors"
              >
                <RefreshCw className={`w-5 h-5 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
              <button className="px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all shadow-md hover:shadow-lg flex items-center space-x-2">
                <Download className="w-4 h-4" />
                <span>Export Data</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* System Status Bar */}
        <div className={`rounded-2xl p-5 mb-8 text-white bg-gradient-to-r ${
          dbMetrics.status === "healthy" 
            ? "from-green-500 to-emerald-500" 
            : "from-yellow-500 to-orange-500"
        } shadow-lg`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">System Status: All Services Operational</h3>
                <p className="text-white/80 text-sm mt-1">Last checked: just now • Uptime: {dbMetrics.uptime}</p>
              </div>
            </div>
            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <Server className="w-4 h-4" />
                <span>{dbMetrics.activeConnections}/{dbMetrics.maxConnections} connections</span>
              </div>
              <div className="flex items-center space-x-2">
                <HardDrive className="w-4 h-4" />
                <span>{dbMetrics.dbSize} used</span>
              </div>
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4" />
                <span>{dbMetrics.avgQueryTime} avg</span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, idx) => (
            <StatCard key={idx} stat={stat} index={idx} />
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Charts Section */}
          <div className="lg:col-span-2 space-y-8">
            {/* Activity Chart */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2 text-indigo-600" />
                  Monthly Activity
                </h3>
                <div className="flex items-center gap-2">
                  <button className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
                    Users
                  </button>
                  <button className="px-3 py-1 text-sm bg-indigo-600 text-white rounded-lg">
                    Campaigns
                  </button>
                  <button className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
                    Revenue
                  </button>
                </div>
              </div>
              
              <div className="relative h-64">
                <div className="absolute inset-0 flex items-end justify-around">
                  {monthlyData.map((item, idx) => (
                    <div key={idx} className="flex-1 flex flex-col items-center mx-1 group">
                      <div className="relative w-full flex justify-center">
                        <div
                          className="w-12 bg-gradient-to-t from-indigo-600 to-indigo-400 rounded-t-lg hover:from-indigo-700 hover:to-indigo-500 transition-all cursor-pointer shadow-sm"
                          style={{
                            height: `${(item.campaigns / 3500) * 200}px`,
                          }}
                        >
                          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                            {item.campaigns.toLocaleString()} campaigns
                          </div>
                        </div>
                      </div>
                      <span className="text-sm text-gray-600 mt-2 font-medium">{item.month}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* User Management Table */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow">
              <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-white border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Users className="w-5 h-5 mr-2 text-indigo-600" />
                  User Management
                </h3>
                <button className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-xl hover:bg-indigo-700 transition-colors flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  Add User
                </button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Plan</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Activity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Performance</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-semibold">
                              {user.avatar}
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">{user.name}</div>
                              <div className="text-xs text-gray-500">{user.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700">
                            {user.plan}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                          <div>
                            <p className="font-medium">{user.campaigns} campaigns</p>
                            <p className="text-xs text-gray-500">{user.submissions.toLocaleString()} submissions</p>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-gray-900">{user.successRate}%</span>
                            <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${
                                  user.successRate >= 95 ? 'bg-green-500' :
                                  user.successRate >= 90 ? 'bg-blue-500' : 'bg-yellow-500'
                                }`}
                                style={{ width: `${user.successRate}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-full ${
                            user.status === 'active' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            <span className={`w-2 h-2 rounded-full mr-1.5 ${
                              user.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
                            }`}></span>
                            {user.status}
                          </span>
                          <p className="text-xs text-gray-500 mt-1">{user.lastActive}</p>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="flex items-center space-x-2">
                            <button className="text-indigo-600 hover:text-indigo-700">
                              <Eye className="w-4 h-4" />
                            </button>
                            <button className="text-gray-600 hover:text-gray-700">
                              <Edit3 className="w-4 h-4" />
                            </button>
                            <button className="text-red-600 hover:text-red-700">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-8">
            {/* Recent Activity */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-indigo-600" />
                Recent Activity
              </h3>
              <div className="space-y-3">
                {recentActivity.map((activity, idx) => {
                  const Icon = activity.icon;
                  return (
                    <div
                      key={idx}
                      className="flex items-start space-x-3 p-3 rounded-xl hover:bg-gray-50 transition-colors border border-gray-100 hover:border-gray-200"
                    >
                      <div className={`p-2 rounded-lg ${activity.bgColor}`}>
                        <Icon className={`w-4 h-4 ${activity.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-gray-900">{activity.message}</p>
                          {activity.importance === 'high' && (
                            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{activity.detail}</p>
                        <p className="text-xs text-gray-400 mt-1">{activity.time}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
              <button className="w-full mt-4 px-4 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors text-sm font-medium">
                View All Activity
              </button>
            </div>

            {/* Database Health */}
            <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Database className="w-5 h-5 mr-2 text-indigo-600" />
                Database Health
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Cache Hit Rate</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-green-500 to-emerald-500"
                        style={{ width: `${dbMetrics.cacheHitRate}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-gray-900">{dbMetrics.cacheHitRate}%</span>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white/70 backdrop-blur-sm rounded-xl p-3">
                    <p className="text-xs text-gray-500">Tables</p>
                    <p className="text-lg font-semibold text-gray-900">{dbMetrics.tables}</p>
                  </div>
                  <div className="bg-white/70 backdrop-blur-sm rounded-xl p-3">
                    <p className="text-xs text-gray-500">Records</p>
                    <p className="text-lg font-semibold text-gray-900">{dbMetrics.totalRecords}</p>
                  </div>
                  <div className="bg-white/70 backdrop-blur-sm rounded-xl p-3">
                    <p className="text-xs text-gray-500">Query Time</p>
                    <p className="text-lg font-semibold text-gray-900">{dbMetrics.avgQueryTime}</p>
                  </div>
                  <div className="bg-white/70 backdrop-blur-sm rounded-xl p-3">
                    <p className="text-xs text-gray-500">Size</p>
                    <p className="text-lg font-semibold text-gray-900">{dbMetrics.dbSize}</p>
                  </div>
                </div>
                
                <div className="pt-3 border-t border-indigo-200">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Last Backup</span>
                    <span className="font-medium text-gray-900">{dbMetrics.lastBackup}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-2">
                    <span className="text-gray-600">Next Maintenance</span>
                    <span className="font-medium text-gray-900">{dbMetrics.nextMaintenance}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="grid grid-cols-2 gap-3">
                <button className="p-3 bg-gray-100 hover:bg-gray-200 rounded-xl text-gray-700 text-sm font-medium transition-colors flex flex-col items-center gap-2">
                  <Users className="w-5 h-5" />
                  Manage Users
                </button>
                <button className="p-3 bg-gray-100 hover:bg-gray-200 rounded-xl text-gray-700 text-sm font-medium transition-colors flex flex-col items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Settings
                </button>
                <button className="p-3 bg-gray-100 hover:bg-gray-200 rounded-xl text-gray-700 text-sm font-medium transition-colors flex flex-col items-center gap-2">
                  <Database className="w-5 h-5" />
                  Backup
                </button>
                <button className="p-3 bg-gray-100 hover:bg-gray-200 rounded-xl text-gray-700 text-sm font-medium transition-colors flex flex-col items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Security
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;