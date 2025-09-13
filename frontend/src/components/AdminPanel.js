import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { 
  Shield, 
  Settings, 
  Users, 
  Bot,
  MessageSquare,
  Monitor,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Activity,
  Database
} from 'lucide-react';
import toast from 'react-hot-toast';

const AdminPanel = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [telegramAccounts, setTelegramAccounts] = useState([]);
  const [whatsappProviders, setWhatsappProviders] = useState([]);
  const [systemStats, setSystemStats] = useState(null);
  const [jobs, setJobs] = useState([]);

  // Modal states
  const [showTelegramModal, setShowTelegramModal] = useState(false);
  const [showWhatsAppModal, setShowWhatsAppModal] = useState(false);
  const [editingTelegram, setEditingTelegram] = useState(null);
  const [editingWhatsApp, setEditingWhatsApp] = useState(null);

  // Form states
  const [telegramForm, setTelegramForm] = useState({
    name: '',
    phone_number: '',
    api_id: '',
    api_hash: '',
    bot_token: '',
    is_active: true
  });

  const [whatsAppForm, setWhatsAppForm] = useState({
    name: '',
    api_endpoint: '',
    api_key: '',
    provider_type: 'twilio',
    is_active: true
  });

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchAdminData();
    }
  }, [user]);

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      const [statsData, telegramData, whatsappData, jobsData] = await Promise.all([
        apiCall('/api/admin/analytics').catch(() => ({})),
        apiCall('/api/admin/telegram-accounts').catch(() => []),
        apiCall('/api/admin/whatsapp-providers').catch(() => []),
        apiCall('/api/admin/jobs').catch(() => [])
      ]);
      
      setSystemStats(statsData);
      setTelegramAccounts(telegramData);
      setWhatsappProviders(whatsappData);
      setJobs(jobsData);
    } catch (error) {
      console.error('Error fetching admin data:', error);
      toast.error('Gagal memuat data admin');
    } finally {
      setLoading(false);
    }
  };

  // Telegram Account Functions
  const openTelegramModal = (account = null) => {
    if (account) {
      setEditingTelegram(account);
      setTelegramForm({
        name: account.name || '',
        phone_number: account.phone_number || '',
        api_id: account.api_id || '',
        api_hash: account.api_hash || '',
        bot_token: account.bot_token || '',
        is_active: account.is_active !== false
      });
    } else {
      setEditingTelegram(null);
      setTelegramForm({
        name: '',
        phone_number: '',
        api_id: '',
        api_hash: '',
        bot_token: '',
        is_active: true
      });
    }
    setShowTelegramModal(true);
  };

  const closeTelegramModal = () => {
    setShowTelegramModal(false);
    setEditingTelegram(null);
  };

  const saveTelegramAccount = async () => {
    try {
      if (editingTelegram) {
        // Update existing account
        await apiCall(`/api/admin/telegram-accounts/${editingTelegram._id}`, 'PUT', telegramForm);
        toast.success('Akun Telegram berhasil diupdate');
      } else {
        // Create new account
        await apiCall('/api/admin/telegram-accounts', 'POST', telegramForm);
        toast.success('Akun Telegram berhasil ditambahkan');
      }
      
      closeTelegramModal();
      fetchAdminData(); // Refresh data
    } catch (error) {
      const message = error.response?.data?.detail || 'Gagal menyimpan akun Telegram';
      toast.error(message);
    }
  };

  const deleteTelegramAccount = async (accountId, accountName) => {
    if (!window.confirm(`Apakah Anda yakin ingin menghapus akun "${accountName}"?`)) {
      return;
    }

    try {
      await apiCall(`/api/admin/telegram-accounts/${accountId}`, 'DELETE');
      toast.success('Akun Telegram berhasil dihapus');
      fetchAdminData(); // Refresh data
    } catch (error) {
      const message = error.response?.data?.detail || 'Gagal menghapus akun Telegram';
      toast.error(message);
    }
  };

  // WhatsApp Provider Functions
  const openWhatsAppModal = (provider = null) => {
    if (provider) {
      setEditingWhatsApp(provider);
      setWhatsAppForm({
        name: provider.name || '',
        api_endpoint: provider.api_endpoint || '',
        api_key: provider.api_key || '',
        provider_type: provider.provider_type || 'twilio',
        is_active: provider.is_active !== false
      });
    } else {
      setEditingWhatsApp(null);
      setWhatsAppForm({
        name: '',
        api_endpoint: '',
        api_key: '',
        provider_type: 'twilio',
        is_active: true
      });
    }
    setShowWhatsAppModal(true);
  };

  const closeWhatsAppModal = () => {
    setShowWhatsAppModal(false);
    setEditingWhatsApp(null);
  };

  const saveWhatsAppProvider = async () => {
    try {
      if (editingWhatsApp) {
        // Update existing provider
        await apiCall(`/api/admin/whatsapp-providers/${editingWhatsApp._id}`, 'PUT', whatsAppForm);
        toast.success('Provider WhatsApp berhasil diupdate');
      } else {
        // Create new provider
        await apiCall('/api/admin/whatsapp-providers', 'POST', whatsAppForm);
        toast.success('Provider WhatsApp berhasil ditambahkan');
      }
      
      closeWhatsAppModal();
      fetchAdminData(); // Refresh data
    } catch (error) {
      const message = error.response?.data?.detail || 'Gagal menyimpan provider WhatsApp';
      toast.error(message);
    }
  };

  const deleteWhatsAppProvider = async (providerId, providerName) => {
    if (!window.confirm(`Apakah Anda yakin ingin menghapus provider "${providerName}"?`)) {
      return;
    }

    try {
      await apiCall(`/api/admin/whatsapp-providers/${providerId}`, 'DELETE');
      toast.success('Provider WhatsApp berhasil dihapus');
      fetchAdminData(); // Refresh data
    } catch (error) {
      const message = error.response?.data?.detail || 'Gagal menghapus provider WhatsApp';
      toast.error(message);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: Monitor },
    { id: 'telegram', name: 'Telegram Accounts', icon: MessageSquare },
    { id: 'whatsapp', name: 'WhatsApp Providers', icon: Bot },
    { id: 'jobs', name: 'Job Monitoring', icon: Activity },
    { id: 'settings', name: 'System Settings', icon: Settings }
  ];

  if (user?.role !== 'admin') {
    return (
      <div className="card p-12 text-center">
        <Shield className="h-16 w-16 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Akses Ditolak
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Anda tidak memiliki akses ke panel admin
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Memuat panel admin...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-600 to-red-700 rounded-lg p-6 text-white">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-white/20 rounded-lg mr-4">
            <Shield className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Dashboard Admin</h1>
            <p className="text-red-100">
              Monitoring sistem, provider, dan konfigurasi platform
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="card p-0 overflow-hidden">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200
                    ${activeTab === tab.id
                      ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                    }
                  `}
                >
                  <Icon className="h-5 w-5 mr-2" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'overview' && (
            <OverviewTab stats={systemStats} />
          )}
          
          {activeTab === 'telegram' && (
            <TelegramTab 
              accounts={telegramAccounts}
              onRefresh={fetchAdminData}
              openModal={openTelegramModal}
              onDelete={deleteTelegramAccount}
            />
          )}
          
          {activeTab === 'whatsapp' && (
            <WhatsAppTab 
              providers={whatsappProviders}
              onRefresh={fetchAdminData}
              openModal={openWhatsAppModal}
              onDelete={deleteWhatsAppProvider}
            />
          )}
          
          {activeTab === 'jobs' && (
            <JobsTab jobs={jobs} onRefresh={fetchAdminData} />
          )}
          
          {activeTab === 'settings' && (
            <SettingsTab />
          )}
        </div>
      </div>

      {/* Telegram Modal */}
      {showTelegramModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {editingTelegram ? 'Edit Akun Telegram' : 'Tambah Akun Telegram'}
              </h3>
              <button
                onClick={closeTelegramModal}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nama *
                </label>
                <input
                  type="text"
                  value={telegramForm.name}
                  onChange={(e) => setTelegramForm({ ...telegramForm, name: e.target.value })}
                  className="input-field"
                  placeholder="Primary Telegram Bot"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nomor Telepon *
                </label>
                <input
                  type="text"
                  value={telegramForm.phone_number}
                  onChange={(e) => setTelegramForm({ ...telegramForm, phone_number: e.target.value })}
                  className="input-field"
                  placeholder="+628123456789"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  API ID *
                </label>
                <input
                  type="text"
                  value={telegramForm.api_id}
                  onChange={(e) => setTelegramForm({ ...telegramForm, api_id: e.target.value })}
                  className="input-field"
                  placeholder="1234567"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  API Hash *
                </label>
                <input
                  type="text"
                  value={telegramForm.api_hash}
                  onChange={(e) => setTelegramForm({ ...telegramForm, api_hash: e.target.value })}
                  className="input-field"
                  placeholder="abcdef1234567890abcdef1234567890"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Bot Token (Opsional)
                </label>
                <input
                  type="text"
                  value={telegramForm.bot_token}
                  onChange={(e) => setTelegramForm({ ...telegramForm, bot_token: e.target.value })}
                  className="input-field"
                  placeholder="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="telegram-active"
                  checked={telegramForm.is_active}
                  onChange={(e) => setTelegramForm({ ...telegramForm, is_active: e.target.checked })}
                  className="mr-2"
                />
                <label htmlFor="telegram-active" className="text-sm text-gray-700 dark:text-gray-300">
                  Aktif
                </label>
              </div>
            </div>
            
            <div className="flex space-x-4 mt-6">
              <button
                onClick={closeTelegramModal}
                className="btn-secondary flex-1"
              >
                Batal
              </button>
              <button
                onClick={saveTelegramAccount}
                className="btn-primary flex-1 flex items-center justify-center"
              >
                <Save className="h-4 w-4 mr-2" />
                Simpan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* WhatsApp Modal */}
      {showWhatsAppModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {editingWhatsApp ? 'Edit Provider WhatsApp' : 'Tambah Provider WhatsApp'}
              </h3>
              <button
                onClick={closeWhatsAppModal}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nama *
                </label>
                <input
                  type="text"
                  value={whatsAppForm.name}
                  onChange={(e) => setWhatsAppForm({ ...whatsAppForm, name: e.target.value })}
                  className="input-field"
                  placeholder="Twilio WhatsApp Business"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Provider Type *
                </label>
                <select
                  value={whatsAppForm.provider_type}
                  onChange={(e) => setWhatsAppForm({ ...whatsAppForm, provider_type: e.target.value })}
                  className="input-field"
                >
                  <option value="twilio">Twilio</option>
                  <option value="vonage">Vonage</option>
                  <option value="360dialog">360Dialog</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  API Endpoint *
                </label>
                <input
                  type="url"
                  value={whatsAppForm.api_endpoint}
                  onChange={(e) => setWhatsAppForm({ ...whatsAppForm, api_endpoint: e.target.value })}
                  className="input-field"
                  placeholder="https://api.twilio.com/..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  API Key *
                </label>
                <input
                  type="text"
                  value={whatsAppForm.api_key}
                  onChange={(e) => setWhatsAppForm({ ...whatsAppForm, api_key: e.target.value })}
                  className="input-field"
                  placeholder="your-api-key-here"
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="whatsapp-active"
                  checked={whatsAppForm.is_active}
                  onChange={(e) => setWhatsAppForm({ ...whatsAppForm, is_active: e.target.checked })}
                  className="mr-2"
                />
                <label htmlFor="whatsapp-active" className="text-sm text-gray-700 dark:text-gray-300">
                  Aktif
                </label>
              </div>
            </div>
            
            <div className="flex space-x-4 mt-6">
              <button
                onClick={closeWhatsAppModal}
                className="btn-secondary flex-1"
              >
                Batal
              </button>
              <button
                onClick={saveWhatsAppProvider}
                className="btn-primary flex-1 flex items-center justify-center"
              >
                <Save className="h-4 w-4 mr-2" />
                Simpan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Overview Tab Component
const OverviewTab = ({ stats }) => {
  const formatNumber = (num) => {
    return new Intl.NumberFormat('id-ID').format(num || 0);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm">Total Users</p>
              <p className="text-2xl font-bold">{formatNumber(stats?.user_stats?.total_users)}</p>
              <p className="text-blue-200 text-xs mt-1">
                {formatNumber(stats?.user_stats?.active_users)} aktif
              </p>
            </div>
            <Users className="h-8 w-8 text-blue-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">Total Validations</p>
              <p className="text-2xl font-bold">{formatNumber(stats?.validation_stats?.total_validations)}</p>
              <p className="text-green-200 text-xs mt-1">
                {formatNumber(stats?.validation_stats?.completed_validations)} berhasil
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm">Active Jobs</p>
              <p className="text-2xl font-bold">{formatNumber(stats?.validation_stats?.active_jobs)}</p>
              <p className="text-purple-200 text-xs mt-1">
                {formatNumber(stats?.validation_stats?.failed_validations)} gagal
              </p>
            </div>
            <Activity className="h-8 w-8 text-purple-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-sm">Total Revenue</p>
              <p className="text-2xl font-bold">{formatCurrency(stats?.payment_stats?.total_revenue)}</p>
              <p className="text-orange-200 text-xs mt-1">
                {formatNumber(stats?.payment_stats?.total_transactions)} transaksi
              </p>
            </div>
            <Database className="h-8 w-8 text-orange-200" />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Aktivitas Terbaru
          </h3>
          <div className="space-y-3">
            {stats?.recent_activities?.map((activity, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {activity.message}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {activity.timestamp}
                  </p>
                </div>
              </div>
            )) || (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                Tidak ada aktivitas terbaru
              </p>
            )}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            System Health
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">Database</span>
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                <span className="text-sm font-medium text-green-600 dark:text-green-400">Healthy</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">API Services</span>
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                <span className="text-sm font-medium text-green-600 dark:text-green-400">Running</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">Job Queue</span>
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-yellow-500 mr-2" />
                <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">Monitoring</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Telegram Tab Component
const TelegramTab = ({ accounts, onRefresh, openModal, onDelete }) => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Telegram Accounts
        </h3>
        <button 
          onClick={() => openModal()}
          className="btn-primary flex items-center hover:bg-primary-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Tambah Akun
        </button>
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          💡 <strong>Info:</strong> Akun Telegram digunakan untuk validasi nomor. Pastikan akun memiliki API credentials yang valid.
        </p>
      </div>

      {accounts && accounts.length > 0 ? (
        <div className="space-y-4">
          {accounts.map((account) => (
            <div key={account._id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {account.name}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {account.phone_number}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    API ID: {account.api_id} • Bot Token: {account.bot_token ? 'Set' : 'Not Set'}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    account.is_active 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  }`}>
                    {account.is_active ? 'Aktif' : 'Tidak Aktif'}
                  </span>
                  <button 
                    onClick={() => openModal(account)}
                    className="p-1 text-blue-600 hover:text-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900 rounded transition-colors"
                    title="Edit akun"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button 
                    onClick={() => onDelete(account._id, account.name)}
                    className="p-1 text-red-600 hover:text-red-700 hover:bg-red-100 dark:hover:bg-red-900 rounded transition-colors"
                    title="Hapus akun"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400 mb-4">Belum ada akun Telegram</p>
          <button 
            onClick={() => openModal()}
            className="btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Tambah Akun Pertama
          </button>
        </div>
      )}
    </div>
  );
};

// WhatsApp Tab Component
const WhatsAppTab = ({ providers, onRefresh, openModal, onDelete }) => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          WhatsApp Providers
        </h3>
        <button 
          onClick={() => openModal()}
          className="btn-primary flex items-center hover:bg-primary-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Tambah Provider
        </button>
      </div>

      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
        <p className="text-sm text-green-800 dark:text-green-200">
          💡 <strong>Info:</strong> Provider WhatsApp adalah layanan pihak ketiga untuk validasi nomor WhatsApp. Contoh: Twilio, Vonage, dll.
        </p>
      </div>

      {providers && providers.length > 0 ? (
        <div className="space-y-4">
          {providers.map((provider) => (
            <div key={provider._id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {provider.name}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {provider.provider_type} • {provider.api_endpoint}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    API Key: {provider.api_key ? `${provider.api_key.substring(0, 8)}...` : 'Not Set'}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    provider.is_active 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  }`}>
                    {provider.is_active ? 'Aktif' : 'Tidak Aktif'}
                  </span>
                  <button 
                    onClick={() => openModal(provider)}
                    className="p-1 text-blue-600 hover:text-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900 rounded transition-colors"
                    title="Edit provider"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button 
                    onClick={() => onDelete(provider._id, provider.name)}
                    className="p-1 text-red-600 hover:text-red-700 hover:bg-red-100 dark:hover:bg-red-900 rounded transition-colors"
                    title="Hapus provider"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400 mb-4">Belum ada provider WhatsApp</p>
          <button 
            onClick={() => openModal()}
            className="btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Tambah Provider Pertama
          </button>
        </div>
      )}
    </div>
  );
};

// Jobs Tab Component
const JobsTab = ({ jobs, onRefresh }) => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Job Monitoring
        </h3>
        <button onClick={onRefresh} className="btn-secondary">
          Refresh
        </button>
      </div>

      <div className="text-center py-12">
        <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">Job monitoring akan tersedia segera</p>
      </div>
    </div>
  );
};

// Users Tab Component removed - now available via sidebar User Management

// Settings Tab Component
const SettingsTab = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          System Settings
        </h3>
      </div>

      <div className="text-center py-12">
        <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">System settings akan tersedia segera</p>
      </div>
    </div>
  );
};

export default AdminPanel;