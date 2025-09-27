// frontend/src/pages/DashboardPage.jsx - Enhanced Complete Version
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import AdminDashboard from './AdminDashboard';
import OwnerDashboard from './OwnerDashboard';
import UserDashboard from './UserDashboard';
import { Loader } from 'lucide-react';

const DashboardPage = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  // Redirect if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      navigate('/');
    }
  }, [user, loading, navigate]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <Loader className="w-16 h-16 text-indigo-600 animate-spin mx-auto" />
            <div className="absolute inset-0 w-16 h-16 border-4 border-indigo-200 rounded-full mx-auto animate-pulse"></div>
          </div>
          <p className="text-gray-600 mt-4 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  // Route to appropriate dashboard based on user role
  switch (user.role) {
    case 'admin':
      return <AdminDashboard />;
    
    case 'owner':
      return <OwnerDashboard />;
    
    case 'user':
    default:
      return <UserDashboard />;
  }
};

export default DashboardPage;