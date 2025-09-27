import React, { useState } from 'react';
import { 
  Bell, BellOff, Check, X, Clock, AlertCircle, Info,
  CheckCircle, XCircle, AlertTriangle, Zap, TrendingUp,
  Mail, MessageSquare, Users, Package, Settings,
  Filter, Search, Archive, Trash2, Star, MoreVertical,
  Calendar, Activity, Server, Shield, CreditCard,
  Download, Upload, RefreshCw, Eye, EyeOff, Volume2
} from 'lucide-react';

const NotificationsPage = () => {
  const [activeTab, setActiveTab] = useState('all');
  const [selectedFilters, setSelectedFilters] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [notificationSettings, setNotificationSettings] = useState({
    email: true,
    push: true,
    sms: false,
    desktop: true
  });

  // Mock notifications data
  const notifications = [
    {
      id: 1,
      type: 'success',
      title: 'Campaign Completed',
      message: 'Your campaign "Summer Sale 2025" has been completed successfully',
      time: '5 minutes ago',
      read: false,
      starred: true,
      icon: CheckCircle,
      color: 'text-green-600 bg-green-100',
      category: 'campaigns'
    },
    {
      id: 2,
      type: 'warning',
      title: 'High Traffic Alert',
      message: 'API usage is at 85% of your monthly limit',
      time: '1 hour ago',
      read: false,
      starred: false,
      icon: AlertTriangle,
      color: 'text-yellow-600 bg-yellow-100',
      category: 'system'
    },
    {
      id: 3,
      type: 'info',
      title: 'New Team Member',
      message: 'Alex Rivera has joined your team',
      time: '3 hours ago',
      read: true,
      starred: false,
      icon: Users,
      color: 'text-blue-600 bg-blue-100',
      category: 'team'
    },
    {
      id: 4,
      type: 'error',
      title: 'Payment Failed',
      message: 'Your payment method was declined. Please update your billing information',
      time: '1 day ago',
      read: true,
      starred: true,
      icon: CreditCard,
      color: 'text-red-600 bg-red-100',
      category: 'billing'
    },
    {
      id: 5,
      type: 'success',
      title: 'Export Ready',
      message: 'Your data export is ready for download',
      time: '2 days ago',
      read: true,
      starred: false,
      icon: Download,
      color: 'text-green-600 bg-green-100',
      category: 'data'
    }
  ];

  const categories = [
    { id: 'all', label: 'All', count: notifications.length },
    { id: 'campaigns', label: 'Campaigns', count: 2, icon: Activity },
    { id: 'system', label: 'System', count: 1, icon: Server },
    { id: 'team', label: 'Team', count: 1, icon: Users },
    { id: 'billing', label: 'Billing', count: 1, icon: CreditCard },
    { id: 'security', label: 'Security', count: 0, icon: Shield }
  ];

  const alertRules = [
    {
      id: 1,
      name: 'Campaign Completion',
      description: 'Notify when any campaign reaches 100% completion',
      enabled: true,
      channels: ['email', 'push'],
      icon: CheckCircle
    },
    {
      id: 2,
      name: 'Failed Submissions',
      description: 'Alert when submission failure rate exceeds 20%',
      enabled: true,
      channels: ['email', 'push', 'sms'],
      icon: XCircle
    },
    {
      id: 3,
      name: 'API Limit Warning',
      description: 'Warn when API usage reaches 80% of limit',
      enabled: true,
      channels: ['email'],
      icon: AlertTriangle
    },
    {
      id: 4,
      name: 'New Team Member',
      description: 'Notify when someone joins the team',
      enabled: false,
      channels: ['push'],
      icon: Users
    },
    {
      id: 5,
      name: 'Weekly Report',
      description: 'Send weekly performance summary every Monday',
      enabled: true,
      channels: ['email'],
      icon: TrendingUp
    }
  ];

  const handleMarkAsRead = (id) => {
    // Handle mark as read
  };

  const handleDelete = (id) => {
    // Handle delete
  };

  const handleToggleStar = (id) => {
    // Handle star toggle
  };

  const filteredNotifications = notifications.filter(n => 
    activeTab === 'all' || n.category === activeTab
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
                  <Bell className="w-6 h-6 text-white" />
                </div>
                Notifications Center
              </h1>
              <p className="text-gray-600 mt-1">Manage alerts and notification preferences</p>
            </div>
            <div className="flex items-center gap-3">
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative">
                <Bell className="w-5 h-5 text-gray-600" />
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  2
                </span>
              </button>
              <button className="px-4 py-2 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Settings
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="col-span-1">
            {/* Categories */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm mb-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Categories</h3>
              <div className="space-y-1">
                {categories.map(category => (
                  <button
                    key={category.id}
                    onClick={() => setActiveTab(category.id)}
                    className={`w-full px-3 py-2 rounded-lg text-left flex items-center justify-between transition-colors ${
                      activeTab === category.id
                        ? 'bg-purple-50 text-purple-700'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {category.icon && <category.icon className="w-4 h-4" />}
                      <span className="text-sm font-medium">{category.label}</span>
                    </div>
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded-full">
                      {category.count}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Settings */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Quick Settings</h3>
              <div className="space-y-3">
                {Object.entries(notificationSettings).map(([key, value]) => (
                  <label key={key} className="flex items-center justify-between cursor-pointer">
                    <span className="text-sm text-gray-700 capitalize">{key}</span>
                    <button
                      onClick={() => setNotificationSettings(prev => ({...prev, [key]: !value}))}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        value ? 'bg-purple-600' : 'bg-gray-300'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          value ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="col-span-3">
            {/* Filters Bar */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm mb-6">
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search notifications..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <button className="px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2 text-sm">
                    <Filter className="w-4 h-4" />
                    Filter
                  </button>
                  <button className="px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2 text-sm">
                    <Archive className="w-4 h-4" />
                    Archive All
                  </button>
                </div>
              </div>
            </div>

            {/* Notifications List */}
            <div className="space-y-3">
              {filteredNotifications.map(notification => {
                const Icon = notification.icon;
                return (
                  <div
                    key={notification.id}
                    className={`bg-white rounded-xl border ${
                      notification.read ? 'border-gray-200' : 'border-purple-200 shadow-md'
                    } p-4 hover:shadow-lg transition-all`}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`p-2 rounded-lg ${notification.color}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className={`font-semibold ${
                              notification.read ? 'text-gray-900' : 'text-gray-900'
                            }`}>
                              {notification.title}
                              {!notification.read && (
                                <span className="ml-2 inline-block w-2 h-2 bg-purple-600 rounded-full"></span>
                              )}
                            </h4>
                            <p className="text-gray-600 text-sm mt-1">{notification.message}</p>
                            <p className="text-gray-400 text-xs mt-2">{notification.time}</p>
                          </div>
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleToggleStar(notification.id)}
                              className="p-1 hover:bg-gray-100 rounded transition-colors"
                            >
                              <Star className={`w-4 h-4 ${
                                notification.starred ? 'text-yellow-500 fill-yellow-500' : 'text-gray-400'
                              }`} />
                            </button>
                            <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                              <MoreVertical className="w-4 h-4 text-gray-400" />
                            </button>
                          </div>
                        </div>
                        {!notification.read && (
                          <button
                            onClick={() => handleMarkAsRead(notification.id)}
                            className="mt-3 text-sm text-purple-600 hover:text-purple-700 font-medium"
                          >
                            Mark as read
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Alert Rules Section */}
            <div className="mt-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Alert Rules</h2>
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="divide-y divide-gray-200">
                  {alertRules.map(rule => {
                    const Icon = rule.icon;
                    return (
                      <div key={rule.id} className="p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-gray-100 rounded-lg">
                              <Icon className="w-5 h-5 text-gray-600" />
                            </div>
                            <div>
                              <h4 className="font-medium text-gray-900">{rule.name}</h4>
                              <p className="text-sm text-gray-600">{rule.description}</p>
                              <div className="flex items-center gap-2 mt-2">
                                {rule.channels.map(channel => (
                                  <span key={channel} className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                                    {channel}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                          <button
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                              rule.enabled ? 'bg-purple-600' : 'bg-gray-300'
                            }`}
                          >
                            <span
                              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                rule.enabled ? 'translate-x-6' : 'translate-x-1'
                              }`}
                            />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationsPage;