import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Home, 
  Zap, 
  Upload, 
  History, 
  Settings, 
  CreditCard, 
  Users, 
  Shield,
  User,
  X,
  Menu,
  Smartphone,
  Monitor,
  UserPlus,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  Activity,
  FileText,
  TrendingUp
} from 'lucide-react';

const Sidebar = ({ isOpen, setSidebarOpen }) => {
  const location = useLocation();
  const { user } = useAuth();
  const [isMinimized, setIsMinimized] = useState(false);

  const menuItems = [];

  // Admin gets different navigation (monitoring & management focused)
  if (user?.role === 'admin') {
    menuItems.push(
      {
        name: 'Dashboard Admin',
        path: '/admin',
        icon: Home,
        description: 'Monitoring & analytics sistem'
      },
      {
        name: 'User Management',
        path: '/admin/users',
        icon: Users,
        description: 'Kelola pengguna & tambah user'
      },
      {
        name: 'Payment Management',
        path: '/admin/payments',
        icon: CreditCard,
        description: 'Kelola sistem pembayaran'
      },
      {
        name: 'System Health',
        path: '/admin/system-health',
        icon: Monitor,
        description: 'Monitor sistem & performance'
      },
      {
        name: 'Audit Logs',
        path: '/admin/audit-logs',
        icon: Shield,
        description: 'Track admin & user activities'
      },
      {
        name: 'Bulk Operations',
        path: '/admin/bulk-operations',
        icon: UserPlus,
        description: 'Import users & bulk management'
      },
      {
        name: 'Advanced Analytics',
        path: '/admin/analytics',
        icon: TrendingUp,
        description: 'Deep insights & performance metrics'
      },
      {
        name: 'Admin Settings',
        path: '/admin/settings',
        icon: Settings,
        description: 'Pengaturan platform'
      }
    );
  } else {
    // Regular users get validation tools
    menuItems.push(
      {
        name: 'Dashboard',
        path: '/dashboard',
        icon: Home,
        description: 'Ringkasan aktivitas'
      },
      {
        name: 'Quick Check',
        path: '/quick-check',
        icon: Zap,
        description: 'Validasi cepat satu nomor'
      },
      {
        name: 'Bulk Check',
        path: '/bulk-check',
        icon: Upload,
        description: 'Validasi massal dari file'
      },
      {
        name: 'Job History',
        path: '/job-history',
        icon: History,
        description: 'Riwayat pekerjaan'
      },
      {
        name: 'Credit Top-up',
        path: '/credit-topup',
        icon: CreditCard,
        description: 'Beli kredit validasi'
      },
      {
        name: 'Profile',
        path: '/profile',
        icon: User,
        description: 'Pengaturan profil'
      }
    );
  }

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 h-full bg-white dark:bg-gray-800 shadow-lg transform transition-all duration-300 z-30
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        ${isMinimized ? 'w-16' : 'w-64'}
      `}>
        {/* Logo */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-gray-700">
          {!isMinimized ? (
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <Smartphone className="h-5 w-5 text-white" />
                </div>
              </div>
              <div className="ml-3">
                <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Webtools
                </h1>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {user?.role === 'admin' ? 'Admin Control' : 'Validasi Nomor'}
                </p>
              </div>
            </div>
          ) : (
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center mx-auto">
              <Smartphone className="h-5 w-5 text-white" />
            </div>
          )}
          
          {/* Toggle Minimize Button */}
          {!isMinimized && (
            <button
              onClick={() => setIsMinimized(true)}
              className="p-1 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Minimize Sidebar"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* User Info - Only show when not minimized */}
        {!isMinimized && (
          <div className="px-4 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                <span className="text-primary-600 dark:text-primary-400 font-medium text-sm">
                  {user?.username?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {user?.username}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {user?.role === 'admin' ? 'Administrator' : 'User'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Expand Button - Only show when minimized */}
        {isMinimized && (
          <div className="px-2 py-4 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setIsMinimized(false)}
              className="w-full p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center justify-center"
              title="Expand Sidebar"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        )}

        {/* Navigation */}
        <nav className={`${isMinimized ? 'px-2 py-4' : 'px-4 py-4'} space-y-1 flex-1 overflow-y-auto`}>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            if (isMinimized) {
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    relative group flex items-center justify-center w-12 h-12 rounded-lg transition-colors
                    ${isActive 
                      ? 'bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400' 
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }
                  `}
                  title={item.name}
                >
                  <Icon className="h-6 w-6" />
                  
                  {/* Tooltip */}
                  <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 dark:bg-gray-700 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                    {item.name}
                  </div>
                </Link>
              );
            }
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  sidebar-item group flex items-center px-3 py-2 rounded-lg transition-colors
                  ${isActive 
                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400' 
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
              >
                <Icon className="h-5 w-5 mr-3 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">
                    {item.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors truncate">
                    {item.description}
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Footer - Only show when not minimized and move up to avoid overlap */}
        {!isMinimized && (
          <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 mt-auto">
            <div className="text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Webtools v1.0
              </p>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default Sidebar;