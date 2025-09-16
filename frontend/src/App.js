import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Components
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import QuickCheck from './components/QuickCheck';
import BulkCheck from './components/BulkCheck';
import JobHistory from './components/JobHistory';
import AdminPanel from './components/AdminPanel';
import CreditTopup from './components/CreditTopup';
import UserManagement from './components/UserManagement';
import UserProfile from './components/UserProfile';
import AdminSettings from './components/AdminSettings';
import PaymentManagement from './components/PaymentManagementClean';
import SystemHealth from './components/SystemHealth';
import AuditLogs from './components/AuditLogs';
import BulkUserOperations from './components/BulkUserOperations';
import AdvancedAnalytics from './components/AdvancedAnalytics';
import WhatsAppAccountManager from './components/WhatsAppAccountManager';

// Context
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider, useTheme } from './context/ThemeContext';

// Utils
import { apiCall } from './utils/api';

function AppContent() {
  const { user, loading } = useAuth();
  const { darkMode } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarMinimized, setSidebarMinimized] = useState(false);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Memuat aplikasi...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="flex">
        {/* Sidebar */}
        <Sidebar 
          isOpen={sidebarOpen} 
          setSidebarOpen={setSidebarOpen}
          isMinimized={sidebarMinimized}
          setIsMinimized={setSidebarMinimized}
        />
        
        {/* Main Content */}
        <div className={`flex-1 transition-all duration-300 ${
          sidebarOpen 
            ? sidebarMinimized 
              ? 'lg:ml-16' 
              : 'lg:ml-64' 
            : 'ml-0'
        }`}>
          {/* Header */}
          <Header 
            sidebarOpen={sidebarOpen}
            setSidebarOpen={setSidebarOpen}
          />
          
          {/* Page Content */}
          <main className="p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/quick-check" element={<QuickCheck />} />
              <Route path="/bulk-check" element={<BulkCheck />} />
              <Route path="/job-history" element={<JobHistory />} />
              <Route path="/credit-topup" element={<CreditTopup />} />
              <Route path="/profile" element={<UserProfile />} />
              {user.role === 'admin' && (
                <>
                  <Route path="/admin" element={<AdminPanel />} />
                  <Route path="/admin/users" element={<UserManagement />} />
                  <Route path="/admin/payments" element={<PaymentManagement />} />
                  <Route path="/admin/settings" element={<AdminSettings />} />
                  <Route path="/admin/system-health" element={<SystemHealth />} />
              <Route path="/admin/audit-logs" element={<AuditLogs />} />
              <Route path="/admin/bulk-operations" element={<BulkUserOperations />} />
              <Route path="/admin/analytics" element={<AdvancedAnalytics />} />
              <Route path="/admin/whatsapp-accounts" element={<WhatsAppAccountManager />} />
                </>
              )}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <div className="App">
            <AppContent />
            <Toaster 
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: 'var(--toast-bg)',
                  color: 'var(--toast-color)',
                },
                success: {
                  iconTheme: {
                    primary: '#10b981',
                    secondary: '#ffffff',
                  },
                },
                error: {
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#ffffff',
                  },
                },
              }}
            />
          </div>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;