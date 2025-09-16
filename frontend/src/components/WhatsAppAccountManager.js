import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { 
  Plus, 
  Edit2, 
  Trash2, 
  Power, 
  PowerOff, 
  Smartphone, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Users,
  Activity,
  QrCode,
  LogIn,
  LogOut
} from 'lucide-react';
import { apiCall } from '../utils/api';

const WhatsAppAccountManager = () => {
  const [accounts, setAccounts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [loginModal, setLoginModal] = useState(null);
  
  const [accountForm, setAccountForm] = useState({
    name: '',
    phone_number: '',
    login_method: 'qr_code',
    max_daily_requests: 100,
    notes: '',
    // Proxy configuration
    proxy_enabled: false,
    proxy_url: '',
    proxy_username: '',
    proxy_password: '',
    proxy_type: 'http' // http, socks5, socks4
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [accountsData, statsData] = await Promise.all([
        apiCall('/api/admin/whatsapp-accounts'),
        apiCall('/api/admin/whatsapp-accounts/stats')
      ]);
      
      setAccounts(accountsData);
      setStats(statsData);
    } catch (error) {
      toast.error('Failed to load WhatsApp accounts');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const openModal = (account = null) => {
    if (account) {
      setEditingAccount(account);
      const proxyConfig = account.proxy_config || {};
      setAccountForm({
        name: account.name || '',
        phone_number: account.phone_number || '',
        login_method: account.login_method || 'qr_code',
        max_daily_requests: account.max_daily_requests || 100,
        notes: account.notes || '',
        // Proxy configuration
        proxy_enabled: proxyConfig.enabled || false,
        proxy_url: proxyConfig.url || '',
        proxy_username: proxyConfig.username || '',
        proxy_password: proxyConfig.password || '',
        proxy_type: proxyConfig.type || 'http'
      });
    } else {
      setEditingAccount(null);
      setAccountForm({
        name: '',
        phone_number: '',
        login_method: 'qr_code',
        max_daily_requests: 100,
        notes: '',
        // Proxy configuration
        proxy_enabled: false,
        proxy_url: '',
        proxy_username: '',
        proxy_password: '',
        proxy_type: 'http'
      });
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingAccount(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (editingAccount) {
        // Update existing account (not implemented in backend yet)
        toast.info('Account update functionality coming soon');
      } else {
        // Prepare account data with proxy configuration
        const accountData = {
          name: accountForm.name,
          phone_number: accountForm.phone_number,
          login_method: accountForm.login_method,
          max_daily_requests: accountForm.max_daily_requests,
          notes: accountForm.notes
        };

        // Add proxy configuration only if enabled
        if (accountForm.proxy_enabled) {
          accountData.proxy_config = {
            enabled: true,
            type: accountForm.proxy_type,
            url: accountForm.proxy_url,
            username: accountForm.proxy_username || null,
            password: accountForm.proxy_password || null
          };
        }

        // Create new account using direct fetch (workaround for apiCall issue)
        console.log('🚀 Creating WhatsApp account with data:', accountData);
        
        // Get token from localStorage
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('Authentication token not found');
        }
        
        // Use direct fetch instead of apiCall
        const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
        const response = await fetch(`${backendUrl}/api/admin/whatsapp-accounts`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(accountData)
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(`API Error ${response.status}: ${errorData.detail || response.statusText}`);
        }
        
        const result = await response.json();
        console.log('✅ Account creation successful:', result);
        
        toast.success('WhatsApp account created successfully');
        await fetchData();
        closeModal();
      }
    } catch (error) {
      // Enhanced error logging for debugging
      console.error('🔍 WhatsApp Account Creation Error Details:', {
        error: error,
        message: error.message,
        response: error.response,
        status: error.response?.status,
        data: error.response?.data,
        config: error.config
      });
      
      // More specific error messages
      if (error.response?.status === 400) {
        toast.error(`Validation Error: ${error.response?.data?.detail || 'Invalid data'}`);
      } else if (error.response?.status === 403) {
        toast.error('Access denied - Admin permission required');
      } else if (error.response?.status === 500) {
        toast.error(`Server Error: ${error.response?.data?.detail || 'Internal server error'}`);
      } else if (error.code === 'NETWORK_ERROR') {
        toast.error('Network error - Check your connection');
      } else {
        toast.error(`Failed to save account: ${error.message || 'Unknown error'}`);
      }
      
      console.error('Error:', error);
    }
  };

  const handleLogin = async (accountId) => {
    try {
      setLoginModal(accountId);
      
      // Use direct fetch for login (consistent with create account fix)
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/admin/whatsapp-accounts/${accountId}/login`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Login failed: ${errorData.detail || response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        toast.success('Account logged in successfully');
        await fetchData();
      } else if (result.qr_code) {
        // Show QR code for scanning
        toast.info('QR Code generated - scan with WhatsApp mobile app');
        // TODO: Implement QR code display modal
      } else {
        toast.error(result.message || 'Login failed');
      }
    } catch (error) {
      toast.error('Failed to login account');
      console.error('Login Error:', error);
    } finally {
      setLoginModal(null);
    }
  };

  const handleLogout = async (accountId) => {
    try {
      // Use direct fetch for logout (consistent fix)
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/admin/whatsapp-accounts/${accountId}/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Logout failed: ${errorData.detail || response.statusText}`);
      }
      
      toast.success('Account logged out successfully');
      await fetchData();
    } catch (error) {
      toast.error('Failed to logout account');
      console.error('Logout Error:', error);
    }
  };

  const handleDelete = async (accountId, accountName) => {
    if (!window.confirm(`Are you sure you want to delete account "${accountName}"?`)) {
      return;
    }

    try {
      // Use direct fetch for delete (consistent fix)
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/admin/whatsapp-accounts/${accountId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Delete failed: ${errorData.detail || response.statusText}`);
      }
      
      toast.success('Account deleted successfully');
      await fetchData();
    } catch (error) {
      toast.error('Failed to delete account');
      console.error('Delete Error:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'banned':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'logged_out':
        return <PowerOff className="h-4 w-4 text-gray-500" />;
      case 'rate_limited':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'banned':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'logged_out':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
      case 'rate_limited':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            WhatsApp Account Management
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Manage WhatsApp accounts for deep link validation
          </p>
        </div>
        <button
          onClick={() => openModal()}
          className="btn-primary flex items-center"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Account
        </button>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card p-4">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-blue-500 mr-3" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Accounts</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.total_accounts}
                </p>
              </div>
            </div>
          </div>
          
          <div className="card p-4">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-500 mr-3" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Active</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.status_breakdown?.active || 0}
                </p>
              </div>
            </div>
          </div>
          
          <div className="card p-4">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-orange-500 mr-3" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Available</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.available_for_use}
                </p>
              </div>
            </div>
          </div>
          
          <div className="card p-4">
            <div className="flex items-center">
              <XCircle className="h-8 w-8 text-red-500 mr-3" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Issues</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {(stats.status_breakdown?.banned || 0) + (stats.status_breakdown?.error || 0)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Accounts List */}
      <div className="card">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            WhatsApp Accounts
          </h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Account
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status & Proxy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Usage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Last Used
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {accounts.map((account) => (
                <tr key={account._id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Smartphone className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {account.name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {account.phone_number}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <div className="flex items-center">
                        {getStatusIcon(account.status)}
                        <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(account.status)}`}>
                          {account.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      {account.proxy_config?.enabled && (
                        <div className="flex items-center">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                            🌐 Proxy
                          </span>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    <div>
                      <div>Daily: {account.daily_usage || 0}/{account.max_daily_requests || 100}</div>
                      <div className="text-xs text-gray-500">Total: {account.usage_count || 0}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {account.last_used ? new Date(account.last_used).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      {account.status === 'logged_out' ? (
                        <button
                          onClick={() => handleLogin(account._id)}
                          disabled={loginModal === account._id}
                          className="text-green-600 hover:text-green-700 p-1"
                          title="Login Account"
                        >
                          {loginModal === account._id ? (
                            <div className="loading-spinner w-4 h-4"></div>
                          ) : (
                            <LogIn className="h-4 w-4" />
                          )}
                        </button>
                      ) : account.status === 'active' ? (
                        <button
                          onClick={() => handleLogout(account._id)}
                          className="text-orange-600 hover:text-orange-700 p-1"
                          title="Logout Account"
                        >
                          <LogOut className="h-4 w-4" />
                        </button>
                      ) : null}
                      
                      <button
                        onClick={() => openModal(account)}
                        className="text-blue-600 hover:text-blue-700 p-1"
                        title="Edit Account"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => handleDelete(account._id, account.name)}
                        className="text-red-600 hover:text-red-700 p-1"
                        title="Delete Account"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {accounts.length === 0 && (
            <div className="text-center py-12">
              <Smartphone className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                No WhatsApp accounts
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Add your first WhatsApp account to start using deep link validation.
              </p>
              <div className="mt-6">
                <button
                  onClick={() => openModal()}
                  className="btn-primary"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add WhatsApp Account
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Account Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {editingAccount ? 'Edit WhatsApp Account' : 'Add WhatsApp Account'}
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Account Name *
                </label>
                <input
                  type="text"
                  required
                  value={accountForm.name}
                  onChange={(e) => setAccountForm({ ...accountForm, name: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Main Account, Backup Account"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Phone Number *
                </label>
                <input
                  type="tel"
                  required
                  value={accountForm.phone_number}
                  onChange={(e) => setAccountForm({ ...accountForm, phone_number: e.target.value })}
                  className="input-field"
                  placeholder="+6281234567890"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Login Method
                </label>
                <select
                  value={accountForm.login_method}
                  onChange={(e) => setAccountForm({ ...accountForm, login_method: e.target.value })}
                  className="input-field"
                >
                  <option value="qr_code">QR Code Scan</option>
                  <option value="phone_verification">Phone Verification</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Daily Request Limit
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={accountForm.max_daily_requests}
                  onChange={(e) => setAccountForm({ ...accountForm, max_daily_requests: parseInt(e.target.value) })}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Notes
                </label>
                <textarea
                  value={accountForm.notes}
                  onChange={(e) => setAccountForm({ ...accountForm, notes: e.target.value })}
                  className="input-field"
                  rows="2"
                  placeholder="Optional notes about this account"
                />
              </div>
              
              {/* Proxy Configuration Section */}
              <div className="border-t border-gray-200 dark:border-gray-600 pt-4">
                <div className="flex items-center mb-4">
                  <input
                    type="checkbox"
                    id="proxy_enabled"
                    checked={accountForm.proxy_enabled}
                    onChange={(e) => setAccountForm({ ...accountForm, proxy_enabled: e.target.checked })}
                    className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label htmlFor="proxy_enabled" className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                    🌐 Enable Proxy (Optional)
                    <span className="block text-xs text-gray-500">Use proxy for IP diversity and security</span>
                  </label>
                </div>
                
                {accountForm.proxy_enabled && (
                  <div className="space-y-4 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Proxy Type
                        </label>
                        <select
                          value={accountForm.proxy_type}
                          onChange={(e) => setAccountForm({ ...accountForm, proxy_type: e.target.value })}
                          className="input-field"
                        >
                          <option value="http">HTTP/HTTPS</option>
                          <option value="socks5">SOCKS5</option>
                          <option value="socks4">SOCKS4</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Proxy URL *
                        </label>
                        <input
                          type="text"
                          required={accountForm.proxy_enabled}
                          value={accountForm.proxy_url}
                          onChange={(e) => setAccountForm({ ...accountForm, proxy_url: e.target.value })}
                          className="input-field"
                          placeholder="http://proxy-server:port"
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Username (Optional)
                        </label>
                        <input
                          type="text"
                          value={accountForm.proxy_username}
                          onChange={(e) => setAccountForm({ ...accountForm, proxy_username: e.target.value })}
                          className="input-field"
                          placeholder="proxy username"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Password (Optional)
                        </label>
                        <input
                          type="password"
                          value={accountForm.proxy_password}
                          onChange={(e) => setAccountForm({ ...accountForm, proxy_password: e.target.value })}
                          className="input-field"
                          placeholder="proxy password"
                        />
                      </div>
                    </div>
                    
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      💡 <strong>Tips:</strong> Gunakan proxy dari provider berbeda untuk setiap account agar IP lebih diverse dan mengurangi risiko detection.
                    </div>
                  </div>
                )}
              </div>
              
              <div className="flex justify-end space-x-2 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                >
                  {editingAccount ? 'Update' : 'Create'} Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default WhatsAppAccountManager;