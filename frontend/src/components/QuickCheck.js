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
  const [validationMethod, setValidationMethod] = useState('standard'); // 'standard' or 'deeplink_profile'
  const [telegramValidationMethod, setTelegramValidationMethod] = useState('standard'); // 'standard', 'mtp', or 'mtp_profile'
  const [platformSettings, setPlatformSettings] = useState({
    whatsapp_enabled: true,
    telegram_enabled: true
  });

  // Persistent data states
  const [persistentStats, setPersistentStats] = useState(() => initializePersistentData().stats);
  const [validationHistory, setValidationHistory] = useState(() => initializePersistentData().history);
  const [history, setHistory] = useState([]);

  // Save to localStorage whenever states change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.VALIDATION_STATS, JSON.stringify(persistentStats));
  }, [persistentStats]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.VALIDATION_HISTORY, JSON.stringify(validationHistory));
  }, [validationHistory]);

  useEffect(() => {
    fetchPlatformSettings();
  }, []);

  // Update persistent stats with new validation results
  const updatePersistentStats = useCallback((newResult) => {
    setPersistentStats(prevStats => ({
      whatsapp_active: prevStats.whatsapp_active + (newResult.summary.whatsapp_active || 0),
      telegram_active: prevStats.telegram_active + (newResult.summary.telegram_active || 0),
      whatsapp_business: prevStats.whatsapp_business + (newResult.summary.whatsapp_business || 0),
      total_processed: prevStats.total_processed + (newResult.summary.total_processed || 0)
    }));
  }, []);

  // Add new validations to history (newest first)
  const addToValidationHistory = useCallback((newResult) => {
    const timestamp = new Date().toISOString();
    const newEntries = newResult.details.map(detail => ({
      id: `${timestamp}-${detail.phone_number}`,
      phone_number: detail.phone_number,
      identifier: detail.identifier,
      whatsapp: detail.whatsapp,
      telegram: detail.telegram,
      validated_at: timestamp
    }));

    setValidationHistory(prevHistory => {
      const updatedHistory = [...newEntries, ...prevHistory];
      // Keep only last 100 entries for performance
      return updatedHistory.slice(0, 100);
    });
  }, []);

  // Copy individual phone number
  const copyPhoneNumber = useCallback((phoneNumber) => {
    navigator.clipboard.writeText(phoneNumber).then(() => {
      toast.success(`Nomor ${phoneNumber} berhasil disalin!`);
    }).catch(() => {
      toast.error('Gagal menyalin nomor');
    });
  }, []);

  // Clear persistent data
  const clearPersistentData = useCallback(() => {
    setPersistentStats({
      whatsapp_active: 0,
      telegram_active: 0,
      whatsapp_business: 0,
      total_processed: 0
    });
    setValidationHistory([]);
    toast.success('Data riwayat berhasil dibersihkan');
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
    
    if (validateWhatsapp) {
      // Standard method: 1 credit, Deep Link Profile: 3 credits
      creditsPerNumber += validationMethod === 'deeplink_profile' ? 3 : 1;
      
      // Add Telegram credits
      if (validateTelegram) {
        if (telegramValidationMethod === 'mtp_profile') {
          creditsPerNumber += 3;
        } else if (telegramValidationMethod === 'mtp') {
          creditsPerNumber += 2;
        } else {
          creditsPerNumber += 1;
        }
      }
    }
    if (validateTelegram) {
      creditsPerNumber += 1; // Telegram always 1 credit
    }
    
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
        validate_telegram: validateTelegram,
        validation_method: validationMethod, // Pass WhatsApp validation method to backend
        telegram_validation_method: telegramValidationMethod // Pass Telegram validation method to backend
      });

      setResult(data);
      
      // Update persistent stats and history
      updatePersistentStats(data);
      addToValidationHistory(data);
      
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

    const blob = new Blob([csvContent], { type: 'text/csv' }); // eslint-disable-line no-undef
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
            
            <div className="space-y-4 mb-6">
              {/* WhatsApp Section */}
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
                    <span className="text-green-600">🟢</span>
                    <span className="ml-1">WhatsApp</span>
                    {!platformSettings.whatsapp_enabled && (
                      <span className="ml-2 text-xs text-red-500">(Disabled)</span>
                    )}
                  </span>
                </label>
              </div>

              {/* WhatsApp Method Selection */}
              {validateWhatsapp && (
                <div className="ml-6 space-y-3 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">Pilih Metode WhatsApp:</p>
                  
                  <div className="space-y-2">
                    <div className="flex items-center">
                      <input
                        type="radio"
                        id="standard"
                        name="whatsapp_method"
                        value="standard"
                        checked={validationMethod === 'standard'}
                        onChange={(e) => setValidationMethod(e.target.value)}
                        className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                      <label htmlFor="standard" className="ml-2 text-sm text-gray-900 dark:text-gray-300">
                        <div className="flex items-center justify-between w-full">
                          <span>
                            <strong>Standard Check</strong>
                            <span className="text-gray-500 dark:text-gray-400 block text-xs">
                              Validasi akurat menggunakan CheckNumber.ai
                            </span>
                          </span>
                          <span className="text-primary-600 font-medium text-sm">1 kredit</span>
                        </div>
                      </label>
                    </div>
                    
                    <div className="flex items-center">
                      <input
                        type="radio"
                        id="deeplink_profile"
                        name="whatsapp_method"
                        value="deeplink_profile"
                        checked={validationMethod === 'deeplink_profile'}
                        onChange={(e) => setValidationMethod(e.target.value)}
                        className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                      <label htmlFor="deeplink_profile" className="ml-2 text-sm text-gray-900 dark:text-gray-300">
                        <div className="flex items-center justify-between w-full">
                          <span>
                            <strong>Deep Link Profile</strong> 
                            <span className="inline-block bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-2 py-0.5 rounded-full ml-1">PREMIUM</span>
                            <span className="text-gray-500 dark:text-gray-400 block text-xs">
                              Info profil detail: foto, last seen, akun bisnis
                            </span>
                          </span>
                          <span className="text-purple-600 font-medium text-sm">3 kredit</span>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {/* Telegram Section */}
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
                    <span className="text-blue-600">🔵</span>
                    <span className="ml-1">Telegram</span>
                    {!platformSettings.telegram_enabled && (
                      <span className="ml-2 text-xs text-red-500">(Disabled)</span>
                    )}
                  </span>
                </label>
              </div>

              {/* Telegram Method Selection */}
              {validateTelegram && (
                <div className="ml-6 space-y-3 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">Pilih Metode Telegram:</p>
                  
                  <div className="space-y-2">
                    <div className="flex items-center">
                      <input
                        type="radio"
                        id="telegram_standard"
                        name="telegram_method"
                        value="standard"
                        checked={telegramValidationMethod === 'standard'}
                        onChange={(e) => setTelegramValidationMethod(e.target.value)}
                        className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                      <label htmlFor="telegram_standard" className="ml-2 text-sm text-gray-900 dark:text-gray-300">
                        <div className="flex items-center justify-between w-full">
                          <span>
                            <strong>Standard Check</strong>
                            <span className="text-gray-500 dark:text-gray-400 block text-xs">
                              Username validation menggunakan Bot API
                            </span>
                          </span>
                          <span className="text-primary-600 font-medium text-sm">1 kredit</span>
                        </div>
                      </label>
                    </div>

                    <div className="flex items-center">
                      <input
                        type="radio"
                        id="telegram_mtp"
                        name="telegram_method"
                        value="mtp"
                        checked={telegramValidationMethod === 'mtp'}
                        onChange={(e) => setTelegramValidationMethod(e.target.value)}
                        className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                      <label htmlFor="telegram_mtp" className="ml-2 text-sm text-gray-900 dark:text-gray-300">
                        <div className="flex items-center justify-between w-full">
                          <span>
                            <strong>MTP Validation</strong>
                            <span className="inline-block bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-xs px-2 py-0.5 rounded-full ml-1">MTP</span>
                            <span className="text-gray-500 dark:text-gray-400 block text-xs">
                              Phone + Username validation via native client
                            </span>
                          </span>
                          <span className="text-primary-600 font-medium text-sm">2 kredit</span>
                        </div>
                      </label>
                    </div>
                    
                    <div className="flex items-center">
                      <input
                        type="radio"
                        id="telegram_mtp_profile"
                        name="telegram_method"
                        value="mtp_profile"
                        checked={telegramValidationMethod === 'mtp_profile'}
                        onChange={(e) => setTelegramValidationMethod(e.target.value)}
                        className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      />
                      <label htmlFor="telegram_mtp_profile" className="ml-2 text-sm text-gray-900 dark:text-gray-300">
                        <div className="flex items-center justify-between w-full">
                          <span>
                            <strong>MTP Profile Deep</strong>
                            <span className="inline-block bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-2 py-0.5 rounded-full ml-1">PREMIUM</span>
                            <span className="text-gray-500 dark:text-gray-400 block text-xs">
                              Full profile: foto, bio, last seen, privacy settings
                            </span>
                          </span>
                          <span className="text-primary-600 font-medium text-sm">3 kredit</span>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>
              )}
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

          {/* Persistent Results & Stats */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                📊 Statistik Validasi
              </h2>
              <div className="flex items-center space-x-2">
                <button
                  onClick={downloadResults}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="Download CSV"
                >
                  <Download className="h-4 w-4" />
                </button>
                <button
                  onClick={clearPersistentData}
                  className="p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-200 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
                  title="Bersihkan Data"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Persistent Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-4 text-center border border-green-200 dark:border-green-800">
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {persistentStats.whatsapp_active}
                </p>
                <p className="text-sm font-medium text-green-600 dark:text-green-400">WhatsApp Aktif</p>
              </div>
              
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl p-4 text-center border border-blue-200 dark:border-blue-800">
                <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {persistentStats.telegram_active}
                </p>
                <p className="text-sm font-medium text-blue-600 dark:text-blue-400">Telegram Aktif</p>
              </div>
              
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl p-4 text-center border border-purple-200 dark:border-purple-800">
                <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                  {persistentStats.whatsapp_business}
                </p>
                <p className="text-sm font-medium text-purple-600 dark:text-purple-400">WA Business</p>
              </div>
              
              <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-700/20 dark:to-gray-600/20 rounded-xl p-4 text-center border border-gray-200 dark:border-gray-600">
                <p className="text-3xl font-bold text-gray-600 dark:text-gray-400">
                  {persistentStats.total_processed}
                </p>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Diproses</p>
              </div>
            </div>

            {/* Validation History */}
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  📋 Riwayat Validasi ({validationHistory.length})
                </h3>
                {loading && (
                  <div className="flex items-center text-primary-600 dark:text-primary-400">
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    <span className="text-sm">Memproses...</span>
                  </div>
                )}
              </div>

              {validationHistory.length > 0 ? (
                <div className="overflow-x-auto">
                  <div className="max-h-96 overflow-y-auto">
                    <table className="w-full border-collapse">
                      <thead className="sticky top-0 bg-white dark:bg-gray-800 z-10">
                        <tr className="border-b-2 border-gray-200 dark:border-gray-600">
                          <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Nomor</th>
                          <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Nama</th>
                          <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">WhatsApp</th>
                          <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Telegram</th>
                          <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Waktu</th>
                          <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Aksi</th>
                        </tr>
                      </thead>
                      <tbody>
                        {validationHistory.map((entry, index) => (
                          <tr key={entry.id} className={`border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${index === 0 ? 'bg-green-50/50 dark:bg-green-900/10' : ''}`}>
                            <td className="py-3 px-4">
                              <div className="flex items-center space-x-2">
                                <span className="font-mono text-sm text-gray-900 dark:text-white">
                                  {entry.phone_number}
                                </span>
                                {index === 0 && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                                    Baru
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 px-4">
                              {entry.identifier ? (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                                  {entry.identifier}
                                </span>
                              ) : (
                                <span className="text-gray-400 text-sm">—</span>
                              )}
                            </td>
                            <td className="py-3 px-4">
                              {entry.whatsapp ? (
                                <div className="flex items-center space-x-2">
                                  {getStatusIcon(entry.whatsapp.status)}
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(entry.whatsapp.status)}`}>
                                    {entry.whatsapp.status === 'active' 
                                      ? getWhatsAppType(entry.whatsapp.details)
                                      : getStatusText(entry.whatsapp.status)
                                    }
                                  </span>
                                </div>
                              ) : (
                                <span className="text-gray-400 text-xs">—</span>
                              )}
                            </td>
                            <td className="py-3 px-4">
                              {entry.telegram ? (
                                <div className="flex items-center space-x-2">
                                  {getStatusIcon(entry.telegram.status)}
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(entry.telegram.status)}`}>
                                    {entry.telegram.status === 'active' && entry.telegram.details?.username
                                      ? `@${entry.telegram.details.username}`
                                      : getStatusText(entry.telegram.status)
                                    }
                                  </span>
                                </div>
                              ) : (
                                <span className="text-gray-400 text-xs">—</span>
                              )}
                            </td>
                            <td className="py-3 px-4">
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {format(new Date(entry.validated_at), 'HH:mm:ss', { locale: id })}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <button
                                onClick={() => copyPhoneNumber(entry.phone_number)}
                                className="p-1.5 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 rounded-lg hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
                                title="Salin nomor"
                              >
                                <Copy className="h-3.5 w-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full mb-4">
                    <Smartphone className="h-8 w-8 text-gray-400" />
                  </div>
                  <p className="text-gray-500 dark:text-gray-400">
                    Belum ada riwayat validasi. Mulai validasi nomor untuk melihat riwayat.
                  </p>
                </div>
              )}
            </div>
          </div>
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