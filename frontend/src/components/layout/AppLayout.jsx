// src/components/layout/AppLayout.jsx - Fixed Version (No styled-jsx)
import React, { Suspense, useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import Header from './Header';
import Footer from '../layout/Footer';
import { Loader2 } from 'lucide-react';

// Loading component
const LoadingSpinner = () => (
  <div className="fixed inset-0 bg-white/80 backdrop-blur-sm z-50 flex items-center justify-center">
    <div className="flex flex-col items-center space-y-4">
      <div className="relative">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
        <div className="absolute inset-0 w-8 h-8 border-2 border-indigo-200 rounded-full animate-pulse"></div>
      </div>
      <p className="text-sm text-gray-600 animate-pulse">Loading...</p>
    </div>
  </div>
);

// Page transition wrapper
const PageTransition = ({ children }) => (
  <div className="animate-fadeIn">
    {children}
  </div>
);

const AppLayout = () => {
  const { user, loading } = useAuth();
  const location = useLocation();
  const [pageLoading, setPageLoading] = useState(false);
  const [backgroundPattern, setBackgroundPattern] = useState('dots');

  // Don't show navigation on landing page or if not authenticated
  const showNavigation = user && location.pathname !== '/';
  const isLandingPage = location.pathname === '/';
  const isDashboard = location.pathname.includes('/dashboard');

  // Handle page transitions
  useEffect(() => {
    setPageLoading(true);
    const timer = setTimeout(() => setPageLoading(false), 300);
    return () => clearTimeout(timer);
  }, [location.pathname]);

  // Dynamic background patterns based on user role
  useEffect(() => {
    if (user?.role) {
      const role = typeof user.role === 'object' ? user.role.value : user.role;
      switch (role.toLowerCase()) {
        case 'owner':
          setBackgroundPattern('executive');
          break;
        case 'admin':
          setBackgroundPattern('admin');
          break;
        default:
          setBackgroundPattern('dots');
      }
    }
  }, [user?.role]);

  // Show loading spinner during auth check
  if (loading) {
    return <LoadingSpinner />;
  }

  // Background pattern styles
  const getBackgroundStyle = () => {
    const patterns = {
      dots: `url("data:image/svg+xml,%3Csvg width='20' height='20' viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%239C92AC' fill-opacity='0.03'%3E%3Ccircle cx='3' cy='3' r='1'/%3E%3C/g%3E%3C/svg%3E")`,
      admin: `url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23E53E3E' fill-opacity='0.02'%3E%3Cpath d='M20 20L0 0v40l20-20zm0 0L40 0v40L20 20z'/%3E%3C/g%3E%3C/svg%3E")`,
      executive: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23D69E2E' fill-opacity='0.02'%3E%3Cpolygon points='30,0 60,30 30,60 0,30'/%3E%3C/g%3E%3C/svg%3E")`
    };
    return patterns[backgroundPattern] || patterns.dots;
  };

  if (!showNavigation) {
    return (
      <div className="min-h-screen bg-white relative">
        {/* Subtle background pattern for non-authenticated pages */}
        {!isLandingPage && (
          <div 
            className="absolute inset-0 opacity-30"
            style={{ backgroundImage: getBackgroundStyle() }}
          />
        )}
        
        {/* Don't show Header on landing page as it has its own navigation */}
        {!isLandingPage && <Header />}
        
        <Suspense fallback={<LoadingSpinner />}>
          <PageTransition>
            {pageLoading ? <LoadingSpinner /> : <Outlet />}
          </PageTransition>
        </Suspense>
        
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen relative overflow-x-hidden smooth-scroll">
      {/* Enhanced background with role-based patterns */}
      <div className="fixed inset-0 bg-gradient-to-br from-gray-50 via-white to-gray-100">
        <div 
          className="absolute inset-0 opacity-40"
          style={{ backgroundImage: getBackgroundStyle() }}
        />
        {isDashboard && (
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/20 via-transparent to-purple-50/20" />
        )}
      </div>

      {/* Professional Header with enhanced styling */}
      <Header />

      {/* Main Content Area with improved spacing and transitions */}
      <main className="relative pt-16 min-h-[calc(100vh-4rem)]">
        <Suspense fallback={<LoadingSpinner />}>
          <PageTransition>
            {pageLoading ? (
              <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
                <LoadingSpinner />
              </div>
            ) : (
              <div className="relative z-10">
                <Outlet />
              </div>
            )}
          </PageTransition>
        </Suspense>
      </main>

      {/* Enhanced Footer */}
      <Footer />
    </div>
  );
};

export default AppLayout;