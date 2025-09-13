import React, { useState } from 'react';
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
  Loader2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { id } from 'date-fns/locale';

const QuickCheck = () => {
  const { user, updateUser } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!phoneNumber.trim()) {
      toast.error('Masukkan nomor telepon');
      return;
    }

    if (user?.credits < 2) {
      toast.error('Kredit tidak mencukupi. Minimal 2 kredit diperlukan.');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const data = await apiCall('/api/validation/quick-check', 'POST', {
        phone_number: phoneNumber.trim()
      });

      setResult(data);
      
      // Update user credits
      const newCredits = user.credits - 2;
      updateUser({ ...user, credits: newCredits });
      
      // Add to history
      setHistory(prev => [data, ...prev.slice(0, 4)]);
      
      toast.success('Validasi berhasil!');
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
        return 'Tidak Diketahui';
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-6 text-white">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-white/20 rounded-lg mr-4">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Quick Check</h1>
            <p className="text-primary-100">
              Validasi satu nomor telepon secara instan
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
            Biaya: 2 kredit per validasi
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
              Masukkan Nomor Telepon
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Nomor Telepon
                </label>
                <div className="relative">
                  <input
                    type="text"
                    id="phone"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="Contoh: +628123456789 atau 08123456789"
                    className="input-field pl-10"
                    disabled={loading}
                  />
                  <Smartphone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Format yang didukung: +62xxx, 08xxx, atau 62xxx
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || !phoneNumber.trim() || (user?.credits < 2)}
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
                    Validasi Sekarang
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
                    onClick={() => copyToClipboard(JSON.stringify(result, null, 2))}
                    className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    title="Salin hasil"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                {/* Phone Number */}
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Nomor Telepon
                      </p>
                      <p className="text-lg font-medium text-gray-900 dark:text-white">
                        {result.phone_number}
                      </p>
                    </div>
                    <button
                      onClick={() => copyToClipboard(result.phone_number)}
                      className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* WhatsApp Result */}
                <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mr-3">
                        <span className="text-green-600 dark:text-green-400 font-semibold text-sm">W</span>
                      </div>
                      <span className="font-medium text-gray-900 dark:text-white">WhatsApp</span>
                    </div>
                    <div className="flex items-center">
                      {getStatusIcon(result.whatsapp.status)}
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(result.whatsapp.status)}`}>
                        {getStatusText(result.whatsapp.status)}
                      </span>
                    </div>
                  </div>
                  
                  {result.whatsapp.details && (
                    <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                      <p>• Foto Profil: {result.whatsapp.details.profile_picture ? 'Ada' : 'Tidak ada'}</p>
                      <p>• Terakhir Dilihat: {result.whatsapp.details.last_seen}</p>
                    </div>
                  )}
                </div>

                {/* Telegram Result */}
                <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mr-3">
                        <span className="text-blue-600 dark:text-blue-400 font-semibold text-sm">T</span>
                      </div>
                      <span className="font-medium text-gray-900 dark:text-white">Telegram</span>
                    </div>
                    <div className="flex items-center">
                      {getStatusIcon(result.telegram.status)}
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(result.telegram.status)}`}>
                        {getStatusText(result.telegram.status)}
                      </span>
                    </div>
                  </div>
                  
                  {result.telegram.details && (
                    <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                      {result.telegram.details.username && (
                        <p>• Username: @{result.telegram.details.username}</p>
                      )}
                      <p>• Premium: {result.telegram.details.is_premium ? 'Ya' : 'Tidak'}</p>
                    </div>
                  )}
                </div>

                {/* Results Summary */}
                {result && result.providers_used && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-600 pt-3 mt-3">
                    <div className="flex justify-between">
                      <span>Providers: WA: {result.providers_used.whatsapp}, TG: {result.providers_used.telegram}</span>
                      <span>{result.cached ? 'Dari cache' : 'Real-time'}</span>
                    </div>
                  </div>
                )}

                {/* Metadata */}
                <div className="text-xs text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-600 pt-3">
                  <div className="flex justify-between">
                    <span>Dicek pada: {format(new Date(result.checked_at), 'dd MMM yyyy HH:mm:ss', { locale: id })}</span>
                    <span>{result.cached ? 'Dari cache' : 'Real-time'}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Credit Info */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Informasi Kredit
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Kredit tersisa</span>
                <span className="font-bold text-green-600 dark:text-green-400">
                  {user?.credits || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Biaya per validasi</span>
                <span className="font-medium text-gray-900 dark:text-white">2 kredit</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Estimasi validasi</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {Math.floor((user?.credits || 0) / 2)} kali
                </span>
              </div>
            </div>
            <button className="w-full btn-primary mt-4">
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
                    <p className="font-medium text-gray-900 dark:text-white text-sm mb-1">
                      {item.phone_number}
                    </p>
                    <div className="flex items-center space-x-2 text-xs">
                      <span className={`px-2 py-1 rounded ${getStatusBadgeClass(item.whatsapp.status)}`}>
                        WA: {getStatusText(item.whatsapp.status)}
                      </span>
                      <span className={`px-2 py-1 rounded ${getStatusBadgeClass(item.telegram.status)}`}>
                        TG: {getStatusText(item.telegram.status)}
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
              <li>• Gunakan Bulk Check untuk validasi banyak nomor</li>
              <li>• Kredit hanya terpotong jika validasi berhasil</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickCheck;