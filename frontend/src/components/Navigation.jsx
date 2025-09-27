// src/components/Navigation.jsx
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart3, FileText, Rocket, Settings } from 'lucide-react';
import useAuth from '../hooks/useAuth';
import UserMenu from './UserMenu';

const Navigation = () => {
  const location = useLocation();
  const { user } = useAuth();

  const navigation = [
    { name: 'Activity', href: '/activity', icon: FileText }, // NEW
    { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
    { name: 'Campaigns', href: '/campaigns', icon: Rocket },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/dashboard" className="text-lg font-semibold">CPS</Link>
            <div className="hidden sm:flex sm:space-x-4">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = location.pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`inline-flex items-center px-3 py-2 text-sm rounded-md ${
                      active
                        ? 'bg-gray-100 text-gray-900'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="flex items-center">
            <UserMenu
              name={`${user?.first_name || ''} ${user?.last_name || ''}`.trim() || user?.email}
              role={user?.role}
              email={user?.email}
              onLogout={() => { localStorage.removeItem('access_token'); window.location.href = '/'; }}
            />
          </div>
        </div>
      </div>

      {/* Mobile */}
      <div className="sm:hidden">
        <div className="pt-2 pb-3 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = location.pathname.startsWith(item.href);
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium ${
                  active
                    ? 'bg-gray-50 border-indigo-500 text-indigo-700'
                    : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'
                }`}
              >
                <Icon className="w-4 h-4 inline mr-2" />
                {item.name}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
