import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { 
  Settings, 
  Toggle,
  CreditCard,
  Users,
  DollarSign,
  TrendingUp,
  Plus,
  Minus,
  Edit2,
  Save,
  X,
  Shield
} from 'lucide-react';
import toast from 'react-hot-toast';

const AdminSettings = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [platformSettings, setPlatformSettings] = useState({
    whatsapp_enabled: true,
    telegram_enabled: true
  });
  const [creditStats, setCreditStats] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [creditAction, setCreditAction] = useState({
    action: 'add',
    amount: 0,
    reason: ''
  });

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchPlatformSettings();
      fetchCreditStats();
    }
  }, [user]);

  const fetchPlatformSettings = async () => {
    try {
      const settings = await apiCall('/api/admin/platform-settings');
      setPlatformSettings(settings);
    } catch (error) {
      console.error('Error fetching platform settings:', error);
      toast.error('Failed to load platform settings');
    }
  };

  const fetchCreditStats = async () => {
    try {
      const stats = await apiCall('/api/admin/credit-management');
      setCreditStats(stats);
    } catch (error) {
      console.error('Error fetching credit stats:', error);
      toast.error('Failed to load credit statistics');
    } finally {
      setLoading(false);
    }
  };

  const updatePlatformSettings = async (whatsappEnabled, telegramEnabled) => {
    try {
      await apiCall('/api/admin/platform-settings', 'PUT', {
        whatsapp_enabled: whatsappEnabled,
        telegram_enabled: telegramEnabled
      });
      
      setPlatformSettings({
        whatsapp_enabled: whatsappEnabled,
        telegram_enabled: telegramEnabled
      });
      
      toast.success('Platform settings updated successfully');
    } catch (error) {
      console.error('Error updating platform settings:', error);
      toast.error('Failed to update platform settings');
    }
  };

  const manageCreditAction = async () => {
    if (!selectedUser || !creditAction.amount || !creditAction.reason) {
      toast.error('Please fill all required fields');
      return;
    }

    try {
      await apiCall(`/api/admin/users/${selectedUser._id}/credits`, 'POST', {
        action: creditAction.action,
        amount: parseInt(creditAction.amount),
        reason: creditAction.reason
      });

      toast.success(`Successfully ${creditAction.action}ed ${creditAction.amount} credits`);
      setShowCreditModal(false);
      setCreditAction({ action: 'add', amount: 0, reason: '' });
      setSelectedUser(null);
      
      // Refresh credit stats
      fetchCreditStats();
    } catch (error) {
      console.error('Error managing credits:', error);
      const message = error.response?.data?.detail || 'Failed to manage credits';
      toast.error(message);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (user?.role !== 'admin') {
    return (
      <div className="card p-12 text-center">
        <Shield className="h-16 w-16 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Access Denied
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          You do not have permission to access admin settings
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading admin settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 rounded-lg p-6 text-white">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-white/20 rounded-lg mr-4">
            <Settings className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Admin Settings</h1>
            <p className="text-indigo-100">
              Manage platform settings and credit system
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Platform Settings */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
              Platform Visibility Controls
            </h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                    <img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/whatsapp.svg" alt="WhatsApp" className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">WhatsApp Validation</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Enable/disable WhatsApp number validation for all users
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => updatePlatformSettings(!platformSettings.whatsapp_enabled, platformSettings.telegram_enabled)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                    platformSettings.whatsapp_enabled ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      platformSettings.whatsapp_enabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                    <img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/telegram.svg" alt="Telegram" className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">Telegram Validation</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Enable/disable Telegram number validation for all users
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => updatePlatformSettings(platformSettings.whatsapp_enabled, !platformSettings.telegram_enabled)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                    platformSettings.telegram_enabled ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      platformSettings.telegram_enabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                ⚠️ <strong>Note:</strong> Disabling a platform will hide it from all users. 
                Existing validations will remain in history, but new validations for that platform will be blocked.
              </p>
            </div>
          </div>

          {/* Credit Management */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Credit Management System
              </h2>
            </div>
            
            {creditStats && (
              <>
                {/* Credit Stats Overview */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {creditStats.total_credits_in_system.toLocaleString()}
                    </p>
                    <p className="text-sm text-green-600 dark:text-green-400">Total Credits in System</p>
                  </div>
                  
                  <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                      {creditStats.total_credits_used.toLocaleString()}
                    </p>
                    <p className="text-sm text-red-600 dark:text-red-400">Credits Used</p>
                  </div>
                  
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {creditStats.total_usage_transactions.toLocaleString()}
                    </p>
                    <p className="text-sm text-blue-600 dark:text-blue-400">Total Transactions</p>
                  </div>
                </div>

                {/* Top Credit Users */}
                <div className="mb-6">
                  <h3 className="text-md font-semibold text-gray-900 dark:text-white mb-4">
                    Top Credit Users
                  </h3>
                  <div className="space-y-2">
                    {creditStats.top_credit_users.slice(0, 5).map((user, index) => (
                      <div key={user._id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <span className="flex items-center justify-center w-6 h-6 bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full text-xs font-medium">
                            {index + 1}
                          </span>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">{user.username}</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{user.email}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-gray-900 dark:text-white">
                            {user.credits.toLocaleString()} credits
                          </p>
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setShowCreditModal(true);
                            }}
                            className="text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                          >
                            Manage Credits
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Transactions */}
                <div>
                  <h3 className="text-md font-semibold text-gray-900 dark:text-white mb-4">
                    Recent Credit Purchases
                  </h3>
                  <div className="space-y-2">
                    {creditStats.recent_transactions.slice(0, 5).map((transaction) => (
                      <div key={transaction._id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {transaction.package_name}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {formatDate(transaction.completed_at || transaction.created_at)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-gray-900 dark:text-white">
                            +{transaction.credits_amount.toLocaleString()} credits
                          </p>
                          <p className="text-sm text-green-600 dark:text-green-400">
                            {formatCurrency(transaction.amount)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Quick Actions
            </h3>
            <div className="space-y-3">
              <button
                onClick={() => window.location.href = '/admin/users'}
                className="w-full btn-secondary flex items-center justify-center"
              >
                <Users className="h-4 w-4 mr-2" />
                Manage Users
              </button>
              
              <button
                onClick={() => window.location.href = '/admin'}
                className="w-full btn-secondary flex items-center justify-center"
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                View Analytics
              </button>
              
              <button
                onClick={() => setShowCreditModal(true)}
                className="w-full btn-primary flex items-center justify-center"
              >
                <CreditCard className="h-4 w-4 mr-2" />
                Manage Credits
              </button>
            </div>
          </div>

          {/* System Status */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              System Status
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">WhatsApp API</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  platformSettings.whatsapp_enabled 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}>
                  {platformSettings.whatsapp_enabled ? 'Active' : 'Disabled'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Telegram API</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  platformSettings.telegram_enabled 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}>
                  {platformSettings.telegram_enabled ? 'Active' : 'Disabled'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Payment System</span>
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  Active
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Credit Management Modal */}
      {showCreditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full">
            <div className="p-6 border-b border-gray-200 dark:border-gray-600">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Manage User Credits
                </h2>
                <button
                  onClick={() => {
                    setShowCreditModal(false);
                    setSelectedUser(null);
                    setCreditAction({ action: 'add', amount: 0, reason: '' });
                  }}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              {selectedUser && (
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <p className="font-medium text-gray-900 dark:text-white">{selectedUser.username}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{selectedUser.email}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Current Credits: <span className="font-medium">{selectedUser.credits.toLocaleString()}</span>
                  </p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Action
                </label>
                <select
                  value={creditAction.action}
                  onChange={(e) => setCreditAction({ ...creditAction, action: e.target.value })}
                  className="input-field"
                >
                  <option value="add">Add Credits</option>
                  <option value="subtract">Subtract Credits</option>
                  <option value="set">Set Credits</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Amount
                </label>
                <input
                  type="number"
                  min="0"
                  value={creditAction.amount}
                  onChange={(e) => setCreditAction({ ...creditAction, amount: e.target.value })}
                  className="input-field"
                  placeholder="Enter credit amount"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Reason
                </label>
                <textarea
                  value={creditAction.reason}
                  onChange={(e) => setCreditAction({ ...creditAction, reason: e.target.value })}
                  className="input-field"
                  rows="3"
                  placeholder="Enter reason for credit adjustment"
                />
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 dark:border-gray-600">
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowCreditModal(false);
                    setSelectedUser(null);
                    setCreditAction({ action: 'add', amount: 0, reason: '' });
                  }}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={manageCreditAction}
                  className="btn-primary"
                >
                  Apply Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminSettings;