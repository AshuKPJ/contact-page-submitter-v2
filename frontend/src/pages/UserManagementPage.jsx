import React, { useState } from 'react';
import { 
  Users, UserPlus, Shield, Key, Mail, Phone, Globe, Activity,
  MoreVertical, Edit2, Trash2, Lock, Unlock, CheckCircle, XCircle,
  Clock, AlertCircle, Search, Filter, Download, RefreshCw,
  ChevronDown, Star, Award, TrendingUp, Eye, Copy, Send,
  UserCheck, UserX, Settings, Database, Zap, Package,
  CreditCard, Calendar, BarChart3, Target, Sparkles, Plus, Code
} from 'lucide-react';

const UserManagementPage = () => {
  const [activeTab, setActiveTab] = useState('team');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState('all');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [selectedUsers, setSelectedUsers] = useState([]);

  // Mock data
  const teamMembers = [
    {
      id: 1,
      name: 'Sarah Johnson',
      email: 'sarah@example.com',
      role: 'Admin',
      status: 'active',
      lastActive: '2 min ago',
      campaigns: 45,
      submissions: 12847,
      successRate: 94,
      avatar: 'SJ',
      joinedDate: '2024-03-15',
      permissions: ['full_access']
    },
    {
      id: 2,
      name: 'Mike Chen',
      email: 'mike@example.com',
      role: 'Manager',
      status: 'active',
      lastActive: '1 hour ago',
      campaigns: 32,
      submissions: 8923,
      successRate: 91,
      avatar: 'MC',
      joinedDate: '2024-05-20',
      permissions: ['create_campaigns', 'view_analytics', 'manage_team']
    },
    {
      id: 3,
      name: 'Emily Davis',
      email: 'emily@example.com',
      role: 'User',
      status: 'inactive',
      lastActive: '3 days ago',
      campaigns: 18,
      submissions: 4562,
      successRate: 88,
      avatar: 'ED',
      joinedDate: '2024-07-10',
      permissions: ['create_campaigns', 'view_own']
    },
    {
      id: 4,
      name: 'Alex Rivera',
      email: 'alex@example.com',
      role: 'User',
      status: 'pending',
      lastActive: 'Never',
      campaigns: 0,
      submissions: 0,
      successRate: 0,
      avatar: 'AR',
      joinedDate: '2024-09-10',
      permissions: ['view_own']
    }
  ];

  const roles = [
    {
      name: 'Admin',
      color: 'from-purple-500 to-pink-500',
      description: 'Full system access',
      permissions: ['All permissions'],
      userCount: 2
    },
    {
      name: 'Manager',
      color: 'from-blue-500 to-cyan-500',
      description: 'Team and campaign management',
      permissions: ['Create campaigns', 'View analytics', 'Manage team'],
      userCount: 3
    },
    {
      name: 'User',
      color: 'from-green-500 to-emerald-500',
      description: 'Basic campaign access',
      permissions: ['Create campaigns', 'View own data'],
      userCount: 8
    },
    {
      name: 'Viewer',
      color: 'from-gray-500 to-gray-600',
      description: 'Read-only access',
      permissions: ['View campaigns', 'View reports'],
      userCount: 5
    }
  ];

  const permissions = [
    { id: 'full_access', name: 'Full Access', category: 'System', icon: Shield },
    { id: 'create_campaigns', name: 'Create Campaigns', category: 'Campaigns', icon: Plus },
    { id: 'edit_campaigns', name: 'Edit Campaigns', category: 'Campaigns', icon: Edit2 },
    { id: 'delete_campaigns', name: 'Delete Campaigns', category: 'Campaigns', icon: Trash2 },
    { id: 'view_analytics', name: 'View Analytics', category: 'Analytics', icon: BarChart3 },
    { id: 'export_data', name: 'Export Data', category: 'Analytics', icon: Download },
    { id: 'manage_team', name: 'Manage Team', category: 'Team', icon: Users },
    { id: 'manage_billing', name: 'Manage Billing', category: 'Billing', icon: CreditCard },
    { id: 'api_access', name: 'API Access', category: 'Developer', icon: Code }
  ];

  const getStatusColor = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-700',
      inactive: 'bg-gray-100 text-gray-700',
      pending: 'bg-yellow-100 text-yellow-700',
      suspended: 'bg-red-100 text-red-700'
    };
    return colors[status] || colors.inactive;
  };

  const getRoleGradient = (role) => {
    const gradients = {
      Admin: 'from-purple-500 to-pink-500',
      Manager: 'from-blue-500 to-cyan-500',
      User: 'from-green-500 to-emerald-500',
      Viewer: 'from-gray-500 to-gray-600'
    };
    return gradients[role] || gradients.User;
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
                  <Users className="w-6 h-6 text-white" />
                </div>
                Team Management
              </h1>
              <p className="text-gray-600 mt-1">Manage users, roles, and permissions</p>
            </div>
            <button
              onClick={() => setShowInviteModal(true)}
              className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:shadow-lg transition-all duration-300 flex items-center gap-2 font-medium"
            >
              <UserPlus className="w-4 h-4" />
              Invite User
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-6 pt-8">
        <div className="flex gap-2 mb-8">
          {['team', 'roles', 'permissions', 'activity'].map((tab) => (
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

        {/* Team Members Tab */}
        {activeTab === 'team' && (
          <div>
            {/* Filters */}
            <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-6 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search team members..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="px-4 py-3 bg-white border border-gray-300 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="all">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="user">User</option>
                  <option value="viewer">Viewer</option>
                </select>
                <button className="p-3 bg-white border border-gray-300 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors">
                  <Filter className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Team Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {teamMembers.map((member) => (
                <div key={member.id} className="bg-white border border-gray-200 rounded-2xl p-6 hover:shadow-lg transition-all">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${getRoleGradient(member.role)} flex items-center justify-center text-white font-bold text-lg`}>
                        {member.avatar}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{member.name}</h3>
                        <p className="text-gray-600 text-sm">{member.email}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className={`px-2 py-1 rounded-lg text-xs font-medium ${getStatusColor(member.status)}`}>
                            {member.status}
                          </span>
                          <span className="text-xs text-gray-500">{member.lastActive}</span>
                        </div>
                      </div>
                    </div>
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                      <MoreVertical className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>

                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-gray-900">{member.campaigns}</p>
                      <p className="text-xs text-gray-500">Campaigns</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-gray-900">{member.submissions.toLocaleString()}</p>
                      <p className="text-xs text-gray-500">Submissions</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-gray-900">{member.successRate}%</p>
                      <p className="text-xs text-gray-500">Success</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <span className={`px-3 py-1.5 rounded-lg bg-gradient-to-r ${getRoleGradient(member.role)} text-white text-sm font-medium`}>
                      {member.role}
                    </span>
                    <div className="flex items-center gap-2">
                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600">
                        <Mail className="w-4 h-4" />
                      </button>
                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600">
                        <Key className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Roles Tab */}
        {activeTab === 'roles' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {roles.map((role, idx) => (
              <div key={idx} className="bg-white border border-gray-200 rounded-2xl p-6 hover:shadow-lg transition-all">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${role.color} flex items-center justify-center`}>
                      <Shield className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900">{role.name}</h3>
                      <p className="text-gray-600 text-sm">{role.description}</p>
                    </div>
                  </div>
                  <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                    <Edit2 className="w-4 h-4 text-gray-400" />
                  </button>
                </div>

                <div className="space-y-2 mb-4">
                  {role.permissions.map((perm, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-gray-700">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>{perm}</span>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <span className="text-sm text-gray-600">
                    {role.userCount} users
                  </span>
                  <button className="text-sm text-purple-600 hover:text-purple-700 transition-colors font-medium">
                    View Users →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Permissions Tab */}
        {activeTab === 'permissions' && (
          <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
            <div className="p-6 border-b border-gray-200 bg-gray-50">
              <h3 className="text-xl font-semibold text-gray-900">Permission Matrix</h3>
              <p className="text-gray-600 mt-1">Configure role-based access control</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr className="border-b border-gray-200">
                    <th className="px-6 py-4 text-left text-sm font-medium text-gray-700">Permission</th>
                    <th className="px-6 py-4 text-center text-sm font-medium text-gray-700">Admin</th>
                    <th className="px-6 py-4 text-center text-sm font-medium text-gray-700">Manager</th>
                    <th className="px-6 py-4 text-center text-sm font-medium text-gray-700">User</th>
                    <th className="px-6 py-4 text-center text-sm font-medium text-gray-700">Viewer</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {permissions.map((perm) => (
                    <tr key={perm.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="flex items-center gap-3">
                          <perm.icon className="w-4 h-4 text-gray-400" />
                          <div>
                            <p className="font-medium">{perm.name}</p>
                            <p className="text-xs text-gray-500">{perm.category}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                      </td>
                      <td className="px-6 py-4 text-center">
                        {['create_campaigns', 'edit_campaigns', 'view_analytics', 'manage_team'].includes(perm.id) ? (
                          <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-400 mx-auto" />
                        )}
                      </td>
                      <td className="px-6 py-4 text-center">
                        {['create_campaigns', 'view_analytics'].includes(perm.id) ? (
                          <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-400 mx-auto" />
                        )}
                      </td>
                      <td className="px-6 py-4 text-center">
                        {['view_analytics'].includes(perm.id) ? (
                          <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-400 mx-auto" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="space-y-4">
              {[
                { user: 'Sarah Johnson', action: 'Created new campaign', target: 'Summer Sale 2025', time: '2 minutes ago', icon: Plus },
                { user: 'Mike Chen', action: 'Updated role permissions', target: 'Manager Role', time: '1 hour ago', icon: Shield },
                { user: 'Emily Davis', action: 'Invited new user', target: 'alex@example.com', time: '3 hours ago', icon: UserPlus },
                { user: 'System', action: 'Automated backup completed', target: 'All user data', time: '6 hours ago', icon: Database },
                { user: 'Sarah Johnson', action: 'Exported analytics report', target: 'Q3 Performance', time: '1 day ago', icon: Download }
              ].map((activity, idx) => {
                const Icon = activity.icon;
                return (
                  <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <p className="text-gray-900">
                          <span className="font-medium">{activity.user}</span>
                          <span className="text-gray-600"> {activity.action} </span>
                          <span className="font-medium">{activity.target}</span>
                        </p>
                        <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                      </div>
                    </div>
                    <button className="p-2 hover:bg-white rounded-lg transition-colors">
                      <Eye className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserManagementPage;