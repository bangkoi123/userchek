import React, { useState, useEffect } from 'react';
import { apiCall } from '../utils/api';
import { 
  Settings,
  CheckCircle,
  XCircle,
  AlertCircle,
  Save,
  RefreshCw,
  Key,
  Globe,
  Zap,
  DollarSign
} from 'lucide-react';
import toast from 'react-hot-toast';

const WhatsAppProviders = () => {
  const [settings, setSettings] = useState({
    provider: 'free',
    api_key: '',
    api_url: '',
    enabled: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await apiCall('/api/admin/whatsapp-provider');
      setSettings(data);
    } catch (error) {
      toast.error('Gagal memuat pengaturan provider');
      console.error('Error fetching provider settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      const payload = {
        provider: settings.provider,
        api_key: settings.api_key,
        api_url: settings.api_url,
        enabled: settings.enabled
      };

      await apiCall('/api/admin/whatsapp-provider', 'PUT', payload);
      toast.success('Pengaturan provider berhasil disimpan!');
    } catch (error) {
      const message = error.response?.data?.detail || 'Gagal menyimpan pengaturan';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const testProvider = async () => {
    try {
      setTesting(true);
      
      // Test dengan nomor sample
      const testNumber = '628123456789';
      const response = await apiCall('/api/validation/quick-check', 'POST', {
        phone_inputs: [testNumber],
        validate_whatsapp: true,
        validate_telegram: false
      });
      
      if (response.details && response.details.length > 0) {
        const result = response.details[0];
        if (result.whatsapp) {
          const provider_used = result.whatsapp.details?.provider || 'unknown';
          toast.success(`Test berhasil! Provider: ${provider_used}, Status: ${result.whatsapp.status}`);
        } else {
          toast.error('Test gagal: Tidak ada hasil WhatsApp');
        }
      } else {
        toast.error('Test gagal: Tidak ada data hasil');
      }
    } catch (error) {
      const message = error.response?.data?.detail || 'Test provider gagal';
      toast.error(message);
    } finally {
      setTesting(false);
    }
  };

  const getProviderInfo = (provider) => {
    switch (provider) {
      case 'checknumber_ai':
        return {
          name: 'CheckNumber.ai',
          description: 'API premium dengan akurasi tinggi',
          icon: <DollarSign className="h-5 w-5" />,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          accuracy: '95%+',
          cost: 'Berbayar'
        };
      case 'free':
        return {
          name: 'Free Method',
          description: 'Metode gratis dengan web scraping',
          icon: <Zap className="h-5 w-5" />,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          accuracy: '70-80%',
          cost: 'Gratis'
        };
      default:
        return {
          name: 'Unknown',
          description: 'Provider tidak dikenal',
          icon: <AlertCircle className="h-5 w-5" />,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          accuracy: 'N/A',
          cost: 'N/A'
        };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-primary-600" />
        <span className="ml-2 text-gray-600">Memuat pengaturan...</span>
      </div>
    );
  }

  const currentProviderInfo = getProviderInfo(settings.provider);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-6 text-white">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-white/20 rounded-lg mr-4">
            <Settings className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">WhatsApp Providers</h1>
            <p className="text-primary-100">
              Kelola provider validasi WhatsApp untuk akurasi optimal
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
            Provider Aktif: {currentProviderInfo.name}
          </div>
          <div className="flex items-center">
            <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
            Status: {settings.enabled ? 'Aktif' : 'Nonaktif'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Provider Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Current Provider Status */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Provider Saat Ini
            </h2>
            
            <div className={`p-4 rounded-lg ${currentProviderInfo.bgColor} border`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${currentProviderInfo.color} bg-white`}>
                    {currentProviderInfo.icon}
                  </div>
                  <div className="ml-3">
                    <h3 className="font-semibold text-gray-900">{currentProviderInfo.name}</h3>
                    <p className="text-sm text-gray-600">{currentProviderInfo.description}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${settings.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {settings.enabled ? (
                      <>
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Aktif
                      </>
                    ) : (
                      <>
                        <XCircle className="h-3 w-3 mr-1" />
                        Nonaktif
                      </>
                    )}
                  </span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Akurasi:</span>
                  <span className="ml-2 font-medium text-gray-900">{currentProviderInfo.accuracy}</span>
                </div>
                <div>
                  <span className="text-gray-600">Biaya:</span>
                  <span className="ml-2 font-medium text-gray-900">{currentProviderInfo.cost}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Provider Selection */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Pilih Provider
            </h2>
            
            <div className="space-y-4">
              {/* Free Method */}
              <div className="border rounded-lg p-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="provider"
                    value="free"
                    checked={settings.provider === 'free'}
                    onChange={(e) => setSettings(prev => ({...prev, provider: e.target.value}))}
                    className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 focus:ring-primary-500"
                  />
                  <div className="ml-3 flex-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <Zap className="h-5 w-5 text-blue-600 mr-2" />
                        <span className="font-medium text-gray-900">Free Method</span>
                        <span className="ml-2 px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">Gratis</span>
                      </div>
                      <span className="text-sm text-gray-600">70-80% akurasi</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      Metode gratis menggunakan web scraping WhatsApp. Cocok untuk testing dan volume kecil.
                    </p>
                  </div>
                </label>
              </div>

              {/* CheckNumber.ai */}
              <div className="border rounded-lg p-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="provider"
                    value="checknumber_ai"
                    checked={settings.provider === 'checknumber_ai'}
                    onChange={(e) => setSettings(prev => ({...prev, provider: e.target.value}))}
                    className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 focus:ring-primary-500"
                  />
                  <div className="ml-3 flex-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <DollarSign className="h-5 w-5 text-green-600 mr-2" />
                        <span className="font-medium text-gray-900">CheckNumber.ai</span>
                        <span className="ml-2 px-2 py-1 text-xs rounded bg-green-100 text-green-800">Premium</span>
                      </div>
                      <span className="text-sm text-gray-600">95%+ akurasi</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      API premium dengan akurasi tinggi. Cocok untuk production dan volume tinggi.
                    </p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* API Configuration */}
          {settings.provider === 'checknumber_ai' && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Konfigurasi CheckNumber.ai
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <Key className="h-4 w-4 inline mr-1" />
                    API Key
                  </label>
                  <input
                    type="password"
                    value={settings.api_key}
                    onChange={(e) => setSettings(prev => ({...prev, api_key: e.target.value}))}
                    placeholder="Masukkan API Key CheckNumber.ai"
                    className="input-field"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Dapatkan API key dari dashboard CheckNumber.ai
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <Globe className="h-4 w-4 inline mr-1" />
                    API URL
                  </label>
                  <input
                    type="url"
                    value={settings.api_url || 'https://api.ekycpro.com/v1/whatsapp'}
                    onChange={(e) => setSettings(prev => ({...prev, api_url: e.target.value}))}
                    placeholder="https://api.ekycpro.com/v1/whatsapp"
                    className="input-field"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    URL endpoint API CheckNumber.ai (gunakan default jika tidak yakin)
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Enable/Disable */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Status Provider
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Aktifkan atau nonaktifkan provider WhatsApp
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.enabled}
                  onChange={(e) => setSettings(prev => ({...prev, enabled: e.target.checked}))}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Actions */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Aksi
            </h3>
            <div className="space-y-3">
              <button
                onClick={handleSave}
                disabled={saving}
                className="w-full btn-primary disabled:opacity-50 flex items-center justify-center"
              >
                {saving ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Menyimpan...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Simpan Pengaturan
                  </>
                )}
              </button>
              
              <button
                onClick={testProvider}
                disabled={testing || !settings.enabled}
                className="w-full btn-secondary disabled:opacity-50 flex items-center justify-center"
              >
                {testing ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Test Provider
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Provider Comparison */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Perbandingan Provider
            </h3>
            <div className="space-y-4 text-sm">
              <div className="border-b pb-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">Free Method</span>
                  <span className="text-green-600">Gratis</span>
                </div>
                <div className="text-gray-600 space-y-1">
                  <div className="flex justify-between">
                    <span>Akurasi:</span>
                    <span>70-80%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Kecepatan:</span>
                    <span>Sedang</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Limit:</span>
                    <span>Tidak ada</span>
                  </div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">CheckNumber.ai</span>
                  <span className="text-orange-600">Berbayar</span>
                </div>
                <div className="text-gray-600 space-y-1">
                  <div className="flex justify-between">
                    <span>Akurasi:</span>
                    <span>95%+</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Kecepatan:</span>
                    <span>Cepat</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Limit:</span>
                    <span>Sesuai paket</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Tips */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              💡 Tips
            </h3>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
              <li>• Gunakan Free Method untuk testing</li>
              <li>• CheckNumber.ai untuk production</li>
              <li>• Test provider sebelum go-live</li>
              <li>• Monitor akurasi secara berkala</li>
              <li>• Backup ke free method jika API error</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WhatsAppProviders;