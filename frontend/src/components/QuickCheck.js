import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { 
  Smartphone, 
  Zap, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Copy,
  Download,
  Loader2,
  Plus,
  Minus,
  Settings,
  RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { id } from 'date-fns/locale';

// LocalStorage keys
const STORAGE_KEYS = {
  VALIDATION_STATS: 'quickcheck_validation_stats',
  VALIDATION_HISTORY: 'quickcheck_validation_history'
};

// Initialize persistent data
const initializePersistentData = () => {
  const savedStats = localStorage.getItem(STORAGE_KEYS.VALIDATION_STATS);
  const savedHistory = localStorage.getItem(STORAGE_KEYS.VALIDATION_HISTORY);
  
  return {
    stats: savedStats ? JSON.parse(savedStats) : {
      whatsapp_active: 0,
      telegram_active: 0,
      whatsapp_business: 0,
      total_processed: 0
    },
    history: savedHistory ? JSON.parse(savedHistory) : []
  };
};

const QuickCheck = () => {
  const { user, updateUser } = useAuth();
  const [phoneInputs, setPhoneInputs] = useState(['']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [validateWhatsapp, setValidateWhatsapp] = useState(true);
  const [validateTelegram, setValidateTelegram] = useState(true);
  const [platformSettings, setPlatformSettings] = useState({
    whatsapp_enabled: true,
    telegram_enabled: true
  });

  // Persistent data states
  const [persistentStats, setPersistentStats] = useState(() => initializePersistentData().stats);
  const [validationHistory, setValidationHistory] = useState(() => initializePersistentData().history);

  useEffect(() => {
    fetchPlatformSettings();
  }, []);

  const fetchPlatformSettings = async () => {
    try {
      const settings = await apiCall('/api/platform-settings');
      setPlatformSettings(settings);
      
      // If platform is disabled, uncheck it
      if (!settings.whatsapp_enabled) {
        setValidateWhatsapp(false);
      }
      if (!settings.telegram_enabled) {
        setValidateTelegram(false);
      }
    } catch (error) {
      console.error('Error fetching platform settings:', error);
    }
  };

  const addPhoneInput = () => {
    if (phoneInputs.length < 20) {
      setPhoneInputs([...phoneInputs, '']);
    }
  };

  const removePhoneInput = (index) => {
    if (phoneInputs.length > 1) {
      const newInputs = phoneInputs.filter((_, i) => i !== index);
      setPhoneInputs(newInputs);
    }
  };

  const updatePhoneInput = (index, value) => {
    const newInputs = [...phoneInputs];
    newInputs[index] = value;
    setPhoneInputs(newInputs);
  };

  const calculateCredits = () => {
    const validInputs = phoneInputs.filter(input => input.trim()).length;
    let creditsPerNumber = 0;
    if (validateWhatsapp) creditsPerNumber += 1;
    if (validateTelegram) creditsPerNumber += 1;
    return validInputs * creditsPerNumber;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const validInputs = phoneInputs.filter(input => input.trim());
    if (validInputs.length === 0) {
      toast.error('Masukkan minimal satu nomor telepon');
      return;
    }

    if (!validateWhatsapp && !validateTelegram) {
      toast.error('Pilih minimal satu platform untuk validasi');
      return;
    }

    const creditsNeeded = calculateCredits();
    if (user?.credits < creditsNeeded) {
      toast.error(`Kredit tidak mencukupi. Dibutuhkan ${creditsNeeded} kredit, tersisa ${user?.credits || 0}`);
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const data = await apiCall('/api/validation/quick-check', 'POST', {
        phone_inputs: validInputs,
        validate_whatsapp: validateWhatsapp,
        validate_telegram: validateTelegram
      });

      setResult(data);
      
      // Update user credits
      const newCredits = user.credits - creditsNeeded;
      updateUser({ ...user, credits: newCredits });
      
      // Add to history
      setHistory(prev => [data, ...prev.slice(0, 4)]);
      
      toast.success(`Validasi berhasil! ${validInputs.length} nomor diproses`);
    } catch (error) {
      const message = error.response?.data?.detail || 'Terjadi kesalahan saat validasi';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Disalin ke clipboard');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'inactive':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'active':
        return 'Aktif';
      case 'inactive':
        return 'Tidak Aktif';
      default:
        return 'Unknown';
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'inactive':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    }
  };

  const getWhatsAppType = (details) => {
    const type = details?.type;
    switch (type) {
      case 'business':
        return 'WA Business';
      case 'personal':
        return 'WA Basic';
      default:
        return 'WA';
    }
  };

  const downloadResults = () => {
    if (!result || !result.details) return;
    
    let csvContent = "Identifier,Phone Number,WhatsApp Status,WhatsApp Type,Telegram Status,Telegram Username\n";
    
    result.details.forEach(detail => {
      const identifier = detail.identifier || '';
      const phone = detail.phone_number;
      const waStatus = detail.whatsapp ? getStatusText(detail.whatsapp.status) : 'N/A';
      const waType = detail.whatsapp ? getWhatsAppType(detail.whatsapp.details) : 'N/A';
      const tgStatus = detail.telegram ? getStatusText(detail.telegram.status) : 'N/A';
      const tgUsername = detail.telegram?.details?.username || '';
      
      csvContent += `"${identifier}","${phone}","${waStatus}","${waType}","${tgStatus}","${tgUsername}"\n`;
    });

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quick_check_results_${new Date().getTime()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-6 text-white">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-white/20 rounded-lg mr-4">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Quick Check Multiple</h1>
            <p className="text-primary-100">
              Validasi hingga 20 nomor telepon secara bersamaan
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
            Biaya: {calculateCredits()} kredit total
          </div>
          <div className="flex items-center">
            <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
            Kredit tersisa: {user?.credits || 0}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Platform Selection
            </h2>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="whatsapp"
                  checked={validateWhatsapp}
                  onChange={(e) => setValidateWhatsapp(e.target.checked)}
                  disabled={!platformSettings.whatsapp_enabled}
                  className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <label htmlFor="whatsapp" className="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">
                  <span className="flex items-center">
                    WhatsApp (1 credit)
                    {!platformSettings.whatsapp_enabled && (
                      <span className="ml-2 text-xs text-red-500">(Disabled)</span>
                    )}
                  </span>
                </label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="telegram"
                  checked={validateTelegram}
                  onChange={(e) => setValidateTelegram(e.target.checked)}
                  disabled={!platformSettings.telegram_enabled}
                  className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <label htmlFor="telegram" className="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">
                  <span className="flex items-center">
                    Telegram (1 credit)
                    {!platformSettings.telegram_enabled && (
                      <span className="ml-2 text-xs text-red-500">(Disabled)</span>
                    )}
                  </span>
                </label>
              </div>
            </div>

            <h3 className="text-md font-semibold text-gray-900 dark:text-white mb-4">
              Masukkan Nomor Telepon (Max 20)
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {phoneInputs.map((phoneInput, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={phoneInput}
                      onChange={(e) => updatePhoneInput(index, e.target.value)}
                      placeholder={`${index + 1}. Masukkan nomor: '08123456789' atau dengan nama: 'koi 08123456789'`}
                      className="input-field pl-8"
                      disabled={loading}
                    />
                    <Smartphone className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  </div>
                  
                  {phoneInputs.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removePhoneInput(index)}
                      className="p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                      disabled={loading}
                    >
                      <Minus className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
              
              {phoneInputs.length < 20 && (
                <button
                  type="button"
                  onClick={addPhoneInput}
                  className="flex items-center text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 text-sm font-medium"
                  disabled={loading}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Tambah Nomor ({phoneInputs.length}/20)
                </button>
              )}

              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  💡 <strong>Tips:</strong> Masukkan nomor dengan format yang didukung: +62xxx, 08xxx, atau 62xxx.
                  Anda juga bisa menambahkan nama: "koi 08123456789"
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || phoneInputs.filter(p => p.trim()).length === 0 || 
                         (!validateWhatsapp && !validateTelegram) ||
                         (user?.credits < calculateCredits())}
                className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Memvalidasi...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Validasi {phoneInputs.filter(p => p.trim()).length} Nomor ({calculateCredits()} kredit)
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Results */}
          {result && (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Hasil Validasi
                </h2>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={downloadResults}
                    className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    title="Download CSV"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => copyToClipboard(JSON.stringify(result, null, 2))}
                    className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    title="Salin hasil"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {result.summary.whatsapp_active}
                  </p>
                  <p className="text-sm text-green-600 dark:text-green-400">WhatsApp Aktif</p>
                </div>
                
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {result.summary.telegram_active}
                  </p>
                  <p className="text-sm text-blue-600 dark:text-blue-400">Telegram Aktif</p>
                </div>
                
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {result.summary.whatsapp_business}
                  </p>
                  <p className="text-sm text-purple-600 dark:text-purple-400">WA Business</p>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-700/20 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                    {result.summary.total_processed}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Diproses</p>
                </div>
              </div>

              {/* Results Table */}
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-600">
                      <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Username</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Nomor</th>
                      {result.platforms_validated.whatsapp && (
                        <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">WhatsApp</th>
                      )}
                      {result.platforms_validated.telegram && (
                        <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Telegram</th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {result.details.map((detail, index) => (
                      <tr key={index} className="border-b border-gray-100 dark:border-gray-700">
                        <td className="py-3 px-4">
                          {detail.identifier ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200">
                              📝 {detail.identifier}
                            </span>
                          ) : (
                            <span className="text-gray-400 text-sm">—</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-mono text-sm">{detail.phone_number}</span>
                        </td>
                        {result.platforms_validated.whatsapp && (
                          <td className="py-3 px-4">
                            {detail.whatsapp ? (
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(detail.whatsapp.status)}
                                <div>
                                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadgeClass(detail.whatsapp.status)}`}>
                                    {detail.whatsapp.status === 'active' 
                                      ? getWhatsAppType(detail.whatsapp.details)
                                      : getStatusText(detail.whatsapp.status)
                                    }
                                  </span>
                                </div>
                              </div>
                            ) : (
                              <span className="text-gray-400">N/A</span>
                            )}
                          </td>
                        )}
                        {result.platforms_validated.telegram && (
                          <td className="py-3 px-4">
                            {detail.telegram ? (
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(detail.telegram.status)}
                                <div>
                                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadgeClass(detail.telegram.status)}`}>
                                    {detail.telegram.status === 'active' && detail.telegram.details?.username
                                      ? `@${detail.telegram.details.username}`
                                      : getStatusText(detail.telegram.status)
                                    }
                                  </span>
                                </div>
                              </div>
                            ) : (
                              <span className="text-gray-400">N/A</span>
                            )}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {result.summary.duplicates_removed > 0 && (
                <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                  <p className="text-sm text-yellow-700 dark:text-yellow-300">
                    ℹ️ {result.summary.duplicates_removed} nomor duplikat dihapus untuk menghemat kredit
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Credit Info */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              💳 Info Kredit
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Kredit per nomor</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {(validateWhatsapp ? 1 : 0) + (validateTelegram ? 1 : 0)} kredit
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Total kebutuhan</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {calculateCredits()} kredit
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Estimasi validasi</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {Math.floor((user?.credits || 0) / ((validateWhatsapp ? 1 : 0) + (validateTelegram ? 1 : 0)) || 1)} nomor
                </span>
              </div>
            </div>
            <button 
              onClick={() => window.location.href = '/credit-topup'}
              className="w-full btn-primary mt-4"
            >
              Beli Kredit
            </button>
          </div>

          {/* Recent History */}
          {history.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Riwayat Terbaru
              </h3>
              <div className="space-y-3">
                {history.map((item, index) => (
                  <div key={index} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {item.summary?.total_processed || 1} nomor divalidasi
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {format(new Date(item.checked_at), 'HH:mm', { locale: id })}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs">
                      <span className="px-2 py-1 rounded bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                        WA: {item.summary?.whatsapp_active || 0}
                      </span>
                      <span className="px-2 py-1 rounded bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                        TG: {item.summary?.telegram_active || 0}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tips */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              💡 Tips
            </h3>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
              <li>• Format nomor akan dinormalisasi otomatis</li>
              <li>• Hasil validasi di-cache selama 7 hari</li>
              <li>• Duplikat dihapus otomatis untuk hemat kredit</li>
              <li>• Gunakan Bulk Check untuk file CSV/Excel</li>
              <li>• Kredit hanya terpotong jika validasi berhasil</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickCheck;