import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Home, 
  Zap, 
  Upload, 
  History, 
  Settings, 
  Smartphone,
  Shield,
  CreditCard,
  User,
  Users
} from 'lucide-react';

const Sidebar = ({ isOpen }) => {
  const location = useLocation();
  const { user } = useAuth();

  const menuItems = [
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
    }
  ];

  // Add admin menu for admin users
  if (user?.role === 'admin') {
    menuItems.push({
      name: 'Admin Panel',
      path: '/admin',
      icon: Shield,
      description: 'Panel administrasi'
    });
  }

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={() => {}}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 h-full w-64 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 z-30
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}>
        {/* Logo */}
        <div className="flex items-center px-6 py-4 border-b border-gray-200 dark:border-gray-700">
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
              Validasi Nomor
            </p>
          </div>
        </div>

        {/* User Info */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
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
                {user?.credits || 0} kredit tersisa
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="px-4 py-4 space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  sidebar-item group
                  ${isActive ? 'active' : ''}
                `}
              >
                <Icon className="h-5 w-5 mr-3 flex-shrink-0" />
                <div className="flex-1">
                  <div className="text-sm font-medium">
                    {item.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors">
                    {item.description}
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Webtools Validation v1.0
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
              Multi-Tenant Platform
            </p>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;