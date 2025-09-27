// src/components/layout/AppLayout.jsx - Clean Layout with Separated Components
import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import Header from './Header';
import Footer from '../layout/Footer';

const AppLayout = () => {
  const { user } = useAuth();
  const location = useLocation();

  // Don't show navigation on landing page or if not authenticated
  const showNavigation = user && location.pathname !== '/';
  const isLandingPage = location.pathname === '/';

  if (!showNavigation) {
    return (
      <div className="min-h-screen bg-white">
        {/* Don't show Header on landing page as it has its own navigation */}
        {!isLandingPage && <Header />}
        <Outlet />
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Professional Header */}
      <Header />

      {/* Main Content Area */}
      <main className="pt-16">
        <div className="min-h-[calc(100vh-4rem)]">
          <Outlet />
        </div>
      </main>

      {/* Professional Footer */}
      <Footer />
    </div>
  );
};

export default AppLayout;