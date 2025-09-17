import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { apiCall } from '../utils/api';
import { 
  Users, 
  Plus, 
  Edit2, 
  Trash2, 
  LogIn, 
  LogOut, 
  Settings, 
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  Ban
} from 'lucide-react';

const TelegramAccountManager = () => {
  const [accounts, setAccounts] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [loginModal, setLoginModal] = useState(null);

  const [accountForm, setAccountForm] = useState({
    name: '',
    phone_number: '',
    api_id: '',
    api_hash: '',
    max_daily_requests: 100,
    notes: '',
    proxy_enabled: false,
    proxy_type: 'http',
    proxy_url: '',
    proxy_username: '',
    proxy_password: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      const [accountsResponse, statsResponse] = await Promise.all([
        apiCall('/api/admin/telegram-accounts', 'GET'),
        apiCall('/api/admin/telegram-accounts/stats', 'GET')
      ]);

      setAccounts(accountsResponse || []);
      setStatistics(statsResponse || {});
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to fetch Telegram accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const accountData = {
        name: accountForm.name.trim(),
        phone_number: accountForm.phone_number.trim(),
        api_id: accountForm.api_id.trim(),
        api_hash: accountForm.api_hash.trim(),
        max_daily_requests: parseInt(accountForm.max_daily_requests) || 100,
        notes: accountForm.notes.trim()
      };

      // Add proxy configuration if enabled
      if (accountForm.proxy_enabled) {
        accountData.proxy_config = {
          enabled: true,
          type: accountForm.proxy_type,
          url: accountForm.proxy_url.trim(),
          username: accountForm.proxy_username?.trim() || null,
          password: accountForm.proxy_password?.trim() || null
        };
      }

      if (editingAccount) {
        // Update existing account
        await apiCall(`/api/admin/telegram-accounts/${editingAccount._id}`, 'PUT', accountData);
        toast.success(`✅ Telegram account "${accountData.name}" berhasil diupdate`);
      } else {
        // Create new account
        await apiCall('/api/admin/telegram-accounts', 'POST', accountData);
        toast.success(`✅ Telegram account "${accountData.name}" berhasil dibuat`);
      }

      closeModal();
      await fetchData();
      
    } catch (error) {
      console.error('❌ Account save error:', error);
      
      if (error.response?.status === 400) {
        const errorMsg = error.response?.data?.detail || 'Data tidak valid';
        toast.error(`❌ ${errorMsg} - periksa form`);
      } else if (error.response?.status === 403) {
        toast.error('❌ Akses ditolak - login sebagai admin');
      } else if (error.response?.status === 409) {
        toast.error('❌ Account dengan nomor tersebut sudah ada');
      } else if (error.response?.status === 500) {
        toast.error('⚠️ Server error - tunggu beberapa saat dan coba lagi');
      } else if (error.message?.includes('Network Error')) {
        toast.error('🌐 Koneksi terputus - periksa internet dan coba lagi');
      } else {
        toast.error('❌ Gagal menyimpan account - coba lagi');
      }
    }
  };

  const handleLogin = async (accountId) => {
    console.log('🔐 Starting Telegram login for account:', accountId);
    
    try {
      setLoginModal(accountId);
      
      toast.loading('🔄 Memulai proses login Telegram...');
      
      const result = await apiCall(`/api/admin/telegram-accounts/${accountId}/login`, 'POST');
      
      console.log('📊 Login API response:', result);
      
      if (result.success) {
        toast.success('✅ Telegram account sudah login - siap digunakan');
        await fetchData();
      } else {
        toast.error(`❌ ${result.message}`);
        
        if (result.instructions) {
          result.instructions.forEach(instruction => {
            toast(instruction, { duration: 5000 });
          });
        }
      }
      
      setLoginModal(null);
      
    } catch (error) {
      console.error('❌ Login error:', error);
      
      if (error.response?.status === 500) {
        toast.error('⚠️ Server error - tunggu beberapa saat dan coba lagi');
      } else if (error.message?.includes('timeout')) {
        toast.error('⏱️ Timeout - coba lagi dengan koneksi yang lebih stabil');
      } else {
        toast.error('❌ Login gagal - periksa konfigurasi account');
      }
      
      setLoginModal(null);
    }
  };

  const handleLogout = async (accountId) => {
    try {
      const result = await apiCall(`/api/admin/telegram-accounts/${accountId}/logout`, 'POST');
      toast.success('✅ Account berhasil logout');
      await fetchData();
    } catch (error) {
      toast.error('❌ Logout gagal');
    }
  };

  const handleEdit = (account) => {
    setEditingAccount(account);
    setAccountForm({
      name: account.name || '',
      phone_number: account.phone_number || '',
      api_id: account.api_id || '',
      api_hash: account.api_hash || '',
      max_daily_requests: account.max_daily_requests || 100,
      notes: account.notes || '',
      proxy_enabled: account.proxy_config?.enabled || false,
      proxy_type: account.proxy_config?.type || 'http',
      proxy_url: account.proxy_config?.url || '',
      proxy_username: account.proxy_config?.username || '',
      proxy_password: account.proxy_config?.password || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (accountId, accountName) => {
    if (window.confirm(`Apakah Anda yakin ingin menghapus account "${accountName}"?`)) {
      try {
        await apiCall(`/api/admin/telegram-accounts/${accountId}`, 'DELETE');
        toast.success(`✅ Account "${accountName}" berhasil dihapus`);
        await fetchData();
      } catch (error) {
        toast.error('❌ Gagal menghapus account');
      }
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingAccount(null);
    setAccountForm({
      name: '',
      phone_number: '',
      api_id: '',
      api_hash: '',
      max_daily_requests: 100,
      notes: '',
      proxy_enabled: false,
      proxy_type: 'http',
      proxy_url: '',
      proxy_username: '',
      proxy_password: ''
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'logged_out':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'banned':
        return <Ban className="h-4 w-4 text-red-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    
    switch (status) {
      case 'active':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'logged_out':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'banned':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'error':
        return `${baseClasses} bg-red-100 text-red-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}  
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="h-6 w-6" />
            Telegram Account Management
          </h1>
          <p className="text-gray-600 mt-1">
            Kelola akun Telegram untuk validasi MTP
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Account
        </button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Accounts</p>
              <p className="text-2xl font-bold text-gray-900">
                {statistics.total_accounts || 0}
              </p>
            </div>
            <Users className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active</p>
              <p className="text-2xl font-bold text-green-600">
                {statistics.active_accounts || 0}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Available</p>
              <p className="text-2xl font-bold text-blue-600">
                {statistics.available_for_use || 0}
              </p>
            </div>
            <Activity className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Sessions</p>
              <p className="text-2xl font-bold text-purple-600">
                {statistics.session_pool?.total_sessions || 0}
              </p>
            </div>
            <Settings className="h-8 w-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Accounts Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Telegram Accounts</h2>
        </div>
        
        {accounts.length === 0 ? (
          <div className="p-8 text-center">
            <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">Belum ada akun Telegram yang ditambahkan</p>
            <button
              onClick={() => setShowModal(true)}
              className="mt-2 text-blue-600 hover:text-blue-800"
            >
              Tambah akun pertama
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Account
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usage
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Used
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {accounts.map((account) => (
                  <tr key={account._id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {account.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {account.phone_number}
                        </div>
                        {account.proxy_config?.enabled && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 mt-1">
                            🌐 Proxy
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(account.status)}
                        <span className={getStatusBadge(account.status)}>
                          {account.status?.toUpperCase() || 'UNKNOWN'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div>Daily: {account.daily_usage || 0}/{account.max_daily_requests || 100}</div>
                        <div className="text-gray-500">Total: {account.usage_count || 0}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {account.last_used ? new Date(account.last_used).toLocaleString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        {account.status === 'logged_out' ? (
                          <button
                            onClick={() => handleLogin(account._id)}
                            disabled={loginModal === account._id}
                            className={`p-1 ${
                              loginModal === account._id
                                ? 'text-gray-400 cursor-not-allowed'
                                : 'text-green-600 hover:text-green-700'
                            }`}
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
                          onClick={() => handleEdit(account)}
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
          </div>
        )}
      </div>

      {/* Add/Edit Account Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">
              {editingAccount ? 'Edit Telegram Account' : 'Add New Telegram Account'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account Name *
                </label>
                <input
                  type="text"
                  value={accountForm.name}
                  onChange={(e) => setAccountForm({...accountForm, name: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Main Account"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone Number *
                </label>
                <input
                  type="text"
                  value={accountForm.phone_number}
                  onChange={(e) => setAccountForm({...accountForm, phone_number: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="+6281234567890"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API ID *
                </label>
                <input
                  type="text"
                  value={accountForm.api_id}
                  onChange={(e) => setAccountForm({...accountForm, api_id: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Get from https://my.telegram.org/apps"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Hash *
                </label>
                <input
                  type="text"
                  value={accountForm.api_hash}
                  onChange={(e) => setAccountForm({...accountForm, api_hash: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Get from https://my.telegram.org/apps"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Daily Request Limit
                </label>
                <input
                  type="number"
                  value={accountForm.max_daily_requests}
                  onChange={(e) => setAccountForm({...accountForm, max_daily_requests: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  min="1"
                  max="1000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  value={accountForm.notes}
                  onChange={(e) => setAccountForm({...accountForm, notes: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="2"
                  placeholder="Optional notes..."
                />
              </div>

              {/* Proxy Configuration */}
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={accountForm.proxy_enabled}
                    onChange={(e) => setAccountForm({...accountForm, proxy_enabled: e.target.checked})}
                    className="rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">Enable Proxy</span>
                </label>
              </div>

              {accountForm.proxy_enabled && (
                <div className="space-y-3 pl-4 border-l-2 border-gray-200">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Proxy Type
                    </label>
                    <select
                      value={accountForm.proxy_type}
                      onChange={(e) => setAccountForm({...accountForm, proxy_type: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="http">HTTP</option>
                      <option value="socks5">SOCKS5</option>
                      <option value="socks4">SOCKS4</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Proxy URL
                    </label>
                    <input
                      type="text"
                      value={accountForm.proxy_url}
                      onChange={(e) => setAccountForm({...accountForm, proxy_url: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="proxy.example.com:8080"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Username (Optional)
                    </label>
                    <input
                      type="text"
                      value={accountForm.proxy_username}
                      onChange={(e) => setAccountForm({...accountForm, proxy_username: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password (Optional)
                    </label>
                    <input
                      type="password"
                      value={accountForm.proxy_password}
                      onChange={(e) => setAccountForm({...accountForm, proxy_password: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded transition-colors"
                >
                  {editingAccount ? 'Update Account' : 'Create Account'}
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TelegramAccountManager;