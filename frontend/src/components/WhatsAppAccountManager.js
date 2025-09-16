import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
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
  const [qrCodeModal, setQrCodeModal] = useState(null); // For QR code display
  const [qrCodeData, setQrCodeData] = useState(null); // QR code image data
  
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
        // Update existing account
        console.log('📝 Updating WhatsApp account:', editingAccount._id);
        
        const updateData = {
          name: accountForm.name,
          phone_number: accountForm.phone_number,
          login_method: accountForm.login_method,
          max_daily_requests: accountForm.max_daily_requests,
          notes: accountForm.notes
        };

        // Add proxy configuration only if enabled
        if (accountForm.proxy_enabled) {
          updateData.proxy_config = {
            enabled: true,
            type: accountForm.proxy_type,
            url: accountForm.proxy_url,
            username: accountForm.proxy_username || null,
            password: accountForm.proxy_password || null
          };
        }

        const result = await apiCall(`/api/admin/whatsapp-accounts/${editingAccount._id}`, 'PUT', updateData);
        console.log('✅ Account update successful:', result);
        
        toast.success('WhatsApp account updated successfully');
        await fetchData();
        closeModal();
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

        // Create new account (reverted to simple approach)
        console.log('🚀 Creating WhatsApp account with data:', accountData);
        
        const result = await apiCall('/api/admin/whatsapp-accounts', 'POST', accountData);
        
        console.log('✅ Account creation successful:', result);
        
        toast.success('WhatsApp account created successfully');
        await fetchData();
        closeModal();
      }
    } catch (error) {
      console.error('❌ Account save error:', error);
      
      // Simplified error handling
      if (error.response?.status === 400) {
        toast.error('Data tidak valid - periksa form');
      } else if (error.response?.status === 403) {
        toast.error('Akses ditolak - login sebagai admin');
      } else if (error.response?.status === 500) {
        toast.error('Server error - coba lagi nanti');
      } else {
        toast.error('Gagal menyimpan account - coba lagi');
      }
    }
  };

  const handleLogin = async (accountId) => {
    console.log('🔐 Starting login for account:', accountId);
    
    try {
      setLoginModal(accountId);
      setQrCodeModal(null); // Clear any existing QR modal
      setQrCodeData(null);
      
      console.log('📡 Calling login API...');
      const result = await apiCall(`/api/admin/whatsapp-accounts/${accountId}/login`, 'POST');
      
      console.log('📊 Login API response:', result);
      
      if (result.success && result.already_logged_in) {
        toast.success('Account sudah login - siap digunakan');
        await fetchData();
        setLoginModal(null);
      } else if (result.success && result.method === 'phone_verification') {
        // Phone verification initiated
        toast.success('SMS verification dikirim ke nomor WhatsApp');
        toast.info('Periksa SMS dan masukkan kode verifikasi di WhatsApp Web');
        setLoginModal(null);
        
        // Auto-refresh to check login status
        setTimeout(async () => {
          console.log('📱 Checking login status after phone verification...');
          await fetchData();
        }, 30000); // Check after 30 seconds
        
      } else if (result.success && result.qr_code) {
        // Show QR code modal (fallback method)
        console.log('📱 Displaying QR code modal (fallback method)');
        setQrCodeData(result.qr_code);
        setQrCodeModal(accountId);
        setLoginModal(null);
        toast.info('QR Code di-generate sebagai fallback - coba scan');
        
        // Auto-close QR modal after expiry
        setTimeout(async () => {
          console.log('⏰ QR Code expired, cleaning up...');
          setQrCodeModal(null);
          setQrCodeData(null);
          await fetchData();
        }, (result.expires_in || 240) * 1000);
        
      } else {
        console.log('❌ Login failed:', result);
        toast.error(result.message || 'Login gagal');
        setLoginModal(null);
      }
    } catch (error) {
      console.error('❌ Login error details:', error);
      
      // Enhanced error handling
      if (error.message && error.message.includes('timeout')) {
        toast.error('Timeout - browser automation gagal');
      } else if (error.response?.status === 500) {
        toast.error('Server error - coba lagi nanti');
      } else {
        toast.error('Login gagal - coba lagi');
      }
      
      setLoginModal(null);
    }
  };

  const handleLogout = async (accountId) => {
    try {
      await apiCall(`/api/admin/whatsapp-accounts/${accountId}/logout`, 'POST');
      toast.success('Account logged out successfully');
      await fetchData();
    } catch (error) {
      toast.error('Failed to logout account');
      console.error('Logout Error:', error);
    }
  };

  const handleDelete = async (accountId, accountName) => {
    console.log('🗑️ Attempting to delete account:', accountId, accountName);
    
    if (!window.confirm(`Yakin hapus account "${accountName}"?`)) {
      return;
    }

    try {
      console.log('📡 Calling delete API...');
      const result = await apiCall(`/api/admin/whatsapp-accounts/${accountId}`, 'DELETE');
      
      console.log('✅ Delete successful:', result);
      toast.success('Account berhasil dihapus');
      await fetchData();
    } catch (error) {
      console.error('❌ Delete error:', error);
      
      if (error.response?.status === 404) {
        toast.error('Account tidak ditemukan');
      } else if (error.response?.status === 403) {
        toast.error('Akses ditolak');
      } else {
        toast.error('Gagal hapus account - coba lagi');
      }
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

      {/* QR Code Modal */}
      {qrCodeModal && qrCodeData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 text-center">
              📱 Scan QR Code untuk Login WhatsApp
            </h3>
            
            <div className="text-center space-y-4">
              {/* QR Code Image */}
              <div className="flex justify-center">
                <img 
                  src={qrCodeData} 
                  alt="WhatsApp QR Code"
                  className="border-2 border-gray-300 rounded-lg bg-white p-2"
                  style={{ maxWidth: '300px', maxHeight: '300px' }}
                />
              </div>
              
              {/* Instructions */}
              <div className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <p className="font-medium">📋 Langkah-langkah:</p>
                <ol className="text-left space-y-1">
                  <li>1. Buka WhatsApp di HP Anda</li>
                  <li>2. Tap Menu (⋮) → Linked Devices</li>
                  <li>3. Tap "Link a Device"</li>
                  <li>4. Scan QR code di atas</li>
                </ol>
              </div>
              
              {/* Status */}
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  ⏳ Menunggu scan... QR code akan expired dalam 5 menit
                </p>
              </div>
              
              {/* Troubleshooting */}
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-left">
                <p className="text-xs text-yellow-700 dark:text-yellow-300">
                  <strong>⚠️ Jika scan gagal:</strong>
                </p>
                <ul className="text-xs text-yellow-600 dark:text-yellow-400 mt-1 space-y-1">
                  <li>• Tunggu 10-15 menit sebelum coba lagi</li>
                  <li>• Pastikan WhatsApp mobile up-to-date</li>
                  <li>• Coba gunakan nomor WhatsApp yang berbeda</li>
                  <li>• Pastikan device limit tidak terlampaui (max 4 linked devices)</li>
                </ul>
              </div>
              
              {/* Close Button */}
              <div className="flex justify-center pt-4">
                <button
                  onClick={() => {
                    setQrCodeModal(null);
                    setQrCodeData(null);
                  }}
                  className="btn-secondary"
                >
                  Tutup
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WhatsAppAccountManager;