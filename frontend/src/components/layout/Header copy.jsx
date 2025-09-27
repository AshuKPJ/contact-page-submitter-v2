// src/components/layout/Header.jsx - Corrected with actual page routes
import React, { useState, useEffect, useRef } from "react";
import { 
  ChevronDown, Bell, Search, Menu, X, Zap, LogOut,
  LayoutDashboard, Rocket, BarChart3, FileText, Users, 
  Settings, Shield, Activity, Target, Globe, TrendingUp,
  Database, Mail, MessageSquare, Calendar, Briefcase,
  DollarSign, Award, Clock, CheckCircle, AlertCircle,
  UserCircle, CreditCard, Key, HelpCircle, BookOpen,
  RefreshCcw, Download, Filter, Code, Server, Monitor
} from "lucide-react";
import useAuth from "../../hooks/useAuth";
import { useNavigate, useLocation, Link } from "react-router-dom";
import toast from 'react-hot-toast';

const Header = () => {
  const [activeMenu, setActiveMenu] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const menuRef = useRef(null);
  const userMenuRef = useRef(null);
  
  // Handle scroll effect
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setActiveMenu(null);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Logout handler
  const handleLogout = async () => {
    try {
      setUserMenuOpen(false);
      setMobileMenuOpen(false);
      setActiveMenu(null);
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_id');
      navigate('/');
      toast.success('Logged out');
    }
  };

  // Mega menu structure based on user role - CORRECTED WITH ACTUAL ROUTES
  const getMegaMenuStructure = () => {
    const baseStructure = [
      {
        id: 'campaigns',
        title: 'Campaigns',
        sections: [
          {
            title: 'Campaign Management',
            items: [
              { name: 'All Campaigns', href: '/campaigns', icon: Rocket },
              { name: 'Create New', href: '/form-submitter', icon: Target },
              { name: 'Activity Log', href: '/activity', icon: Activity }
            ]
          },
          {
            title: 'Analytics',
            items: [
              { name: 'Reports', href: '/reports', icon: FileText },
              { name: 'Performance', href: '/reports', icon: BarChart3 },
              { name: 'Success Metrics', href: '/reports', icon: TrendingUp }
            ]
          },
          {
            title: 'Resources',
            items: [
              { name: 'API Documentation', href: '/api-documentation', icon: Code },
              { name: 'Help Center', href: '/help', icon: HelpCircle }
            ]
          }
        ]
      },
      {
        id: 'tools',
        title: 'Tools',
        sections: [
          {
            title: 'System',
            items: [
              { name: 'Monitoring', href: '/monitoring', icon: Monitor },
              { name: 'System Health', href: '/monitoring', icon: Server },
              { name: 'Activity Feed', href: '/activity', icon: Activity }
            ]
          },
          {
            title: 'Management',
            items: [
              { name: 'Notifications', href: '/notifications', icon: Bell },
              { name: 'Settings', href: '/settings', icon: Settings },
              { name: 'Profile', href: '/contact-info', icon: UserCircle }
            ]
          }
        ]
      }
    ];

    // Add admin section for admin/owner roles
    const userRole = user?.role?.toLowerCase() || 'user';
    if (userRole === 'admin' || userRole === 'owner') {
      baseStructure.push({
        id: 'admin',
        title: 'Admin',
        sections: [
          {
            title: 'User Management',
            items: [
              { name: 'All Users', href: '/user-management', icon: Users },
              { name: 'Roles & Permissions', href: '/user-management', icon: Shield },
              { name: 'Activity Logs', href: '/activity', icon: Activity }
            ]
          },
          {
            title: 'System',
            items: [
              { name: 'Settings', href: '/settings', icon: Settings },
              { name: 'Monitoring', href: '/monitoring', icon: Monitor },
              { name: 'Reports', href: '/reports', icon: BarChart3 }
            ]
          }
        ]
      });
    }

    return baseStructure;
  };

  const megaMenuItems = getMegaMenuStructure();

  // Get user display info
  const getUserDisplayName = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    if (user?.first_name) return user.first_name;
    if (user?.email) return user.email.split('@')[0];
    return 'User';
  };

  const getUserInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    if (user?.first_name) return user.first_name[0].toUpperCase();
    if (user?.email) return user.email[0].toUpperCase();
    return 'U';
  };

  const getUserRole = () => {
    const role = user?.role;
    if (typeof role === 'object' && role?.value) {
      return role.value;
    }
    return role || 'user';
  };

  // Guest header (not logged in)
  if (!user) {
    return (
      <header className={`fixed top-0 z-50 w-full bg-white transition-all duration-300 ${
        scrolled ? 'shadow-sm' : 'border-b border-gray-200'
      }`}>
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2">
              <img
                className="h-8 w-auto"
                alt="CPS"
                src="/assets/images/CPS_Header_Logo.png"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <div className="hidden items-center space-x-2" style={{ display: 'none' }}>
                <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-semibold text-gray-900">CPS</span>
              </div>
            </Link>
            
            <div className="flex items-center space-x-4">
              <Link to="/login" className="text-gray-600 hover:text-gray-900 font-medium">
                Sign In
              </Link>
              <Link to="/register" className="bg-indigo-600 text-white px-5 py-2 rounded-lg hover:bg-indigo-700 font-medium">
                Get Started
              </Link>
            </div>
          </div>
        </nav>
      </header>
    );
  }

  // Logged in header with mega menu
  return (
    <header className={`fixed top-0 z-50 w-full bg-white transition-all duration-300 ${
      scrolled ? 'shadow-sm' : 'border-b border-gray-200'
    }`}>
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" ref={menuRef}>
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-8">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <img
                className="h-8 w-auto"
                alt="CPS"
                src="/assets/images/CPS_Header_Logo.png"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <div className="hidden items-center space-x-2" style={{ display: 'none' }}>
                <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-semibold text-gray-900">CPS</span>
              </div>
            </Link>

            {/* Main Navigation with Mega Menu */}
            <nav className="hidden lg:flex items-center space-x-1">
              <Link
                to="/dashboard"
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  location.pathname === '/dashboard'
                    ? 'text-indigo-600 bg-indigo-50'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                Dashboard
              </Link>
              
              {megaMenuItems.map((item) => (
                <div key={item.id} className="relative">
                  <button
                    onMouseEnter={() => setActiveMenu(item.id)}
                    onClick={() => setActiveMenu(activeMenu === item.id ? null : item.id)}
                    className={`flex items-center space-x-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                      activeMenu === item.id 
                        ? 'text-indigo-600 bg-gray-50' 
                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <span>{item.title}</span>
                    <ChevronDown className={`w-4 h-4 transition-transform ${
                      activeMenu === item.id ? 'rotate-180' : ''
                    }`} />
                  </button>
                  
                  {/* Mega Menu Dropdown */}
                  {activeMenu === item.id && (
                    <div 
                      className="absolute left-0 mt-1 bg-white rounded-lg shadow-xl border border-gray-200 p-6 animate-fadeIn"
                      onMouseLeave={() => setActiveMenu(null)}
                      style={{ minWidth: '600px' }}
                    >
                      <div className="grid grid-cols-3 gap-6">
                        {item.sections.map((section, idx) => (
                          <div key={idx}>
                            <h3 className="font-semibold text-gray-900 mb-3">{section.title}</h3>
                            <ul className="space-y-2">
                              {section.items.map((subItem) => {
                                const Icon = subItem.icon;
                                return (
                                  <li key={subItem.href}>
                                    <Link
                                      to={subItem.href}
                                      className="flex items-center space-x-2 text-sm text-gray-600 hover:text-indigo-600 hover:bg-gray-50 px-2 py-1.5 rounded transition-colors"
                                      onClick={() => setActiveMenu(null)}
                                    >
                                      <Icon className="w-4 h-4" />
                                      <span>{subItem.name}</span>
                                    </Link>
                                  </li>
                                );
                              })}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              
              <Link
                to="/reports"
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  location.pathname === '/reports'
                    ? 'text-indigo-600 bg-indigo-50'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                Reports
              </Link>
              
              <Link
                to="/help"
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  location.pathname === '/help'
                    ? 'text-indigo-600 bg-indigo-50'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                Help
              </Link>
            </nav>
          </div>

          {/* Right Section */}
          <div className="flex items-center space-x-3">
            {/* Search */}
            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors">
              <Search className="w-5 h-5" />
            </button>
            
            {/* Notifications */}
            <Link 
              to="/notifications"
              className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </Link>

            {/* User Menu */}
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="h-8 w-8 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white flex items-center justify-center text-sm font-medium shadow-sm">
                  {getUserInitials()}
                </div>
                <span className="hidden sm:block text-sm font-medium text-gray-700 max-w-[150px] truncate">
                  {getUserDisplayName()}
                </span>
                <ChevronDown className={`h-4 w-4 text-gray-500 transition-transform ${
                  userMenuOpen ? "rotate-180" : ""
                }`} />
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 animate-fadeIn">
                  <div className="p-4 border-b border-gray-200">
                    <p className="font-medium text-gray-900">{getUserDisplayName()}</p>
                    <p className="text-sm text-gray-500 truncate">{user.email}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="inline-block px-2 py-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded capitalize">
                        {getUserRole()}
                      </span>
                      {user?.is_verified && (
                        <span className="inline-block px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">
                          Verified
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="py-2">
                    <Link
                      to="/contact-info"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <UserCircle className="w-4 h-4 text-gray-400" />
                        <span>Profile Settings</span>
                      </div>
                    </Link>
                    
                    <Link
                      to="/settings"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <Settings className="w-4 h-4 text-gray-400" />
                        <span>Account Settings</span>
                      </div>
                    </Link>

                    {(getUserRole() === 'admin' || getUserRole() === 'owner') && (
                      <>
                        <Link
                          to="/user-management"
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                          onClick={() => setUserMenuOpen(false)}
                        >
                          <div className="flex items-center space-x-3">
                            <Users className="w-4 h-4 text-gray-400" />
                            <span>User Management</span>
                          </div>
                        </Link>
                        <Link
                          to="/monitoring"
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                          onClick={() => setUserMenuOpen(false)}
                        >
                          <div className="flex items-center space-x-3">
                            <Monitor className="w-4 h-4 text-gray-400" />
                            <span>System Monitoring</span>
                          </div>
                        </Link>
                      </>
                    )}
                    
                    <Link
                      to="/notifications"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <Bell className="w-4 h-4 text-gray-400" />
                        <span>Notifications</span>
                      </div>
                    </Link>
                    
                    <Link
                      to="/help"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <HelpCircle className="w-4 h-4 text-gray-400" />
                        <span>Help & Support</span>
                      </div>
                    </Link>
                  </div>
                  
                  <div className="border-t border-gray-200">
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <LogOut className="w-4 h-4" />
                        <span>Sign Out</span>
                      </div>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-200 py-4 animate-slideDown">
            <Link
              to="/dashboard"
              className={`block px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                location.pathname === '/dashboard'
                  ? 'text-indigo-600 bg-indigo-50'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              Dashboard
            </Link>
            
            <Link
              to="/campaigns"
              className={`block px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                location.pathname === '/campaigns'
                  ? 'text-indigo-600 bg-indigo-50'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              Campaigns
            </Link>
            
            <Link
              to="/form-submitter"
              className={`block px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                location.pathname === '/form-submitter'
                  ? 'text-indigo-600 bg-indigo-50'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              New Campaign
            </Link>
            
            <Link
              to="/reports"
              className={`block px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                location.pathname === '/reports'
                  ? 'text-indigo-600 bg-indigo-50'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              Reports
            </Link>
            
            <Link
              to="/activity"
              className={`block px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                location.pathname === '/activity'
                  ? 'text-indigo-600 bg-indigo-50'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              Activity
            </Link>
            
            <Link
              to="/help"
              className={`block px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                location.pathname === '/help'
                  ? 'text-indigo-600 bg-indigo-50'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              Help
            </Link>

            {/* Mobile Logout Button */}
            <div className="border-t border-gray-200 mt-4 pt-4">
              <button
                onClick={handleLogout}
                className="w-full flex items-center space-x-3 px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        )}
      </nav>

      {/* Animation Styles */}
      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out;
        }

        .animate-slideDown {
          animation: slideDown 0.3s ease-out;
        }
      `}</style>
    </header>
  );
};

export default Header;