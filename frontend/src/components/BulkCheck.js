import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { useAuth } from '../context/AuthContext';
import { uploadFile, apiCall } from '../utils/api';
import { useJobProgress } from '../hooks/useSocket';
import { 
  Upload, 
  File, 
  CheckCircle, 
  AlertCircle,
  Download,
  Trash2,
  FileSpreadsheet,
  FileText,
  Loader2,
  Info,
  Wifi,
  WifiOff
} from 'lucide-react';
import toast from 'react-hot-toast';

const BulkCheck = () => {
  const { user } = useAuth();
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [realTimeProgress, setRealTimeProgress] = useState(null);
  const [validateWhatsapp, setValidateWhatsapp] = useState(true);
  const [validateTelegram, setValidateTelegram] = useState(true);
  const [platformSettings, setPlatformSettings] = useState({
    whatsapp_enabled: true,
    telegram_enabled: true
  });
  
  // Real-time job progress hook
  const { progress, isListening, startListening, stopListening } = useJobProgress(currentJobId);

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

  // Handle real-time progress updates
  useEffect(() => {
    if (progress) {
      setRealTimeProgress(progress);
      
      if (progress.status === 'completed') {
        toast.success(`🎉 Validasi selesai! ${progress.results?.whatsapp_active || 0} WhatsApp aktif, ${progress.results?.telegram_active || 0} Telegram aktif`);
        setTimeout(() => {
          setCurrentJobId(null);
          setRealTimeProgress(null);
          stopListening();
        }, 5000); // Show completion for 5 seconds
      }
    }
  }, [progress, stopListening]);

  // Sample CSV for download
  const sampleCSV = `phone_number
+6281234567890
+6289876543210
+6285555666777
08123456789
+628111222333`;

  const downloadSampleCSV = () => {
    const element = document.createElement("a");
    const file = new Blob([sampleCSV], { type: 'text/csv' });
    element.href = URL.createObjectURL(file);
    element.download = "sample_phone_numbers.csv";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    toast.success('Sample CSV downloaded!');
  };

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      rejectedFiles.forEach(({ file, errors }) => {
        errors.forEach((error) => {
          if (error.code === 'file-too-large') {
            toast.error(`File ${file.name} terlalu besar (max 10MB)`);
          } else if (error.code === 'file-invalid-type') {
            toast.error(`File ${file.name} format tidak didukung`);
          }
        });
      });
    }

    // Handle accepted files
    acceptedFiles.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const preview = e.target.result;
        setFiles(prev => [...prev, {
          id: Date.now() + Math.random(),
          file,
          preview,
          status: 'ready',
          error: null
        }]);
      };
      reader.readAsText(file);
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: true
  });

  const removeFile = (id) => {
    setFiles(prev => prev.filter(file => file.id !== id));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileName) => {
    const extension = fileName.split('.').pop().toLowerCase();
    if (extension === 'csv') {
      return <FileText className="h-8 w-8 text-green-500" />;
    } else if (extension === 'xlsx' || extension === 'xls') {
      return <FileSpreadsheet className="h-8 w-8 text-blue-500" />;
    }
    return <File className="h-8 w-8 text-gray-500" />;
  };

  const estimateCredits = () => {
    let totalRows = 0;
    files.forEach(fileItem => {
      if (fileItem.preview) {
        const lines = fileItem.preview.split('\n').filter(line => line.trim());
        totalRows += Math.max(0, lines.length - 1); // Subtract header row
      }
    });
    
    // Calculate credits based on platform selection
    let creditsPerNumber = 0;
    if (validateWhatsapp) creditsPerNumber += 1;
    if (validateTelegram) creditsPerNumber += 1;
    
    return totalRows * creditsPerNumber;
  };

  const startValidation = async () => {
    if (files.length === 0) {
      toast.error('Pilih file terlebih dahulu');
      return;
    }

    if (!validateWhatsapp && !validateTelegram) {
      toast.error('Pilih minimal satu platform untuk validasi');
      return;
    }

    const estimatedCredits = estimateCredits();
    if (user?.credits < estimatedCredits) {
      toast.error(`Kredit tidak mencukupi. Dibutuhkan ${estimatedCredits} kredit, tersisa ${user?.credits || 0}`);
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      for (let i = 0; i < files.length; i++) {
        const fileItem = files[i];
        
        // Update file status
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id ? { ...f, status: 'uploading' } : f
        ));

        try {
          const response = await uploadFile('/api/validation/bulk-check', fileItem.file, (progress) => {
            setUploadProgress(Math.round(((i / files.length) * 100) + (progress / files.length)));
          });

          // Update file status to success
          setFiles(prev => prev.map(f => 
            f.id === fileItem.id ? { ...f, status: 'success' } : f
          ));

          toast.success(`File ${fileItem.file.name} berhasil diupload`);
          
          // Start real-time monitoring if job_id is returned
          if (response.job_id) {
            setCurrentJobId(response.job_id);
            startListening();
            toast.info('🔄 Mulai monitoring progress real-time...');
          }
          
        } catch (error) {
          // Update file status to error
          setFiles(prev => prev.map(f => 
            f.id === fileItem.id ? { 
              ...f, 
              status: 'error', 
              error: error.response?.data?.detail || 'Upload gagal' 
            } : f
          ));
          
          toast.error(`Error uploading ${fileItem.file.name}: ${error.response?.data?.detail || 'Upload gagal'}`);
        }
      }
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-lg p-6 text-white">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-white/20 rounded-lg mr-4">
            <Upload className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Bulk Check</h1>
            <p className="text-green-100">
              Upload file CSV/Excel untuk validasi massal nomor telepon
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
            Format: CSV, XLS, XLSX
          </div>
          <div className="flex items-center">
            <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
            Max: 10MB per file
          </div>
          <div className="flex items-center">
            <span className="w-2 h-2 bg-yellow-400 rounded-full mr-2"></span>
            Kredit: {user?.credits || 0}
          </div>
        </div>
      </div>

      {/* Demo Section */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          🎯 Demo Bulk Check
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Coba fitur bulk validation dengan sample nomor telepon
        </p>
        
        <div className="flex space-x-4">
          <button
            onClick={() => {
              const sampleCSV = `phone_number\n+6281234567890\n+6289876543210\n+6285555666777\n08123456789\n+628111222333`;
              const element = document.createElement("a");
              const file = new Blob([sampleCSV], { type: 'text/csv' });
              element.href = URL.createObjectURL(file);
              element.download = "sample_phone_numbers.csv";
              document.body.appendChild(element);
              element.click();
              document.body.removeChild(element);
              toast.success('Sample CSV downloaded!');
            }}
            className="btn-secondary flex items-center"
          >
            <Download className="h-4 w-4 mr-2" />
            Download Sample CSV
          </button>
          
          <button
            onClick={() => toast.info('Upload sample CSV untuk mencoba fitur bulk validation')}
            className="btn-primary flex items-center"
          >
            <FileText className="h-4 w-4 mr-2" />
            Try Demo Upload
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Upload Area */}
        <div className="lg:col-span-2 space-y-6">
          {/* File Upload */}
          <div className="card p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Upload File
              </h2>
              <button
                onClick={downloadSampleCSV}
                className="btn-secondary text-sm"
              >
                <Download className="h-4 w-4 mr-2" />
                Download Sample
              </button>
            </div>
            
            <div
              {...getRootProps()}
              className={`
                drop-zone cursor-pointer
                ${isDragActive ? 'active' : ''}
                ${uploading ? 'pointer-events-none opacity-50' : ''}
              `}
            >
              <input {...getInputProps()} />
              <div className="text-center">
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                {isDragActive ? (
                  <p className="text-lg text-primary-600 dark:text-primary-400 font-medium">
                    Lepaskan file di sini...
                  </p>
                ) : (
                  <>
                    <p className="text-lg text-gray-900 dark:text-white font-medium mb-2">
                      Drag & drop file atau klik untuk pilih
                    </p>
                    <p className="text-gray-600 dark:text-gray-400">
                      Mendukung CSV, XLS, XLSX (max 10MB)
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  File yang Dipilih ({files.length})
                </h2>
                <button
                  onClick={() => setFiles([])}
                  className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm font-medium"
                  disabled={uploading}
                >
                  Hapus Semua
                </button>
              </div>

              <div className="space-y-3">
                {files.map((fileItem) => (
                  <div key={fileItem.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getFileIcon(fileItem.file.name)}
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {fileItem.file.name}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {formatFileSize(fileItem.file.size)} • {fileItem.file.type || 'Unknown type'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        {fileItem.status === 'ready' && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded-full text-xs font-medium">
                            Siap
                          </span>
                        )}
                        {fileItem.status === 'uploading' && (
                          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded-full text-xs font-medium flex items-center">
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                            Upload...
                          </span>
                        )}
                        {fileItem.status === 'success' && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded-full text-xs font-medium flex items-center">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Berhasil
                          </span>
                        )}
                        {fileItem.status === 'error' && (
                          <span className="px-2 py-1 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-full text-xs font-medium flex items-center">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            Error
                          </span>
                        )}
                        
                        {!uploading && (
                          <button
                            onClick={() => removeFile(fileItem.id)}
                            className="p-1 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>

                    {fileItem.error && (
                      <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
                        {fileItem.error}
                      </div>
                    )}

                    {fileItem.preview && (
                      <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
                        Preview: {Math.max(0, fileItem.preview.split('\n').filter(line => line.trim()).length - 1)} baris data
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Progress Bar */}
              {uploading && (
                <div className="mt-4">
                  <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                    <span>Upload Progress</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Real-time Progress */}
              {realTimeProgress && (
                <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-blue-900 dark:text-blue-100 flex items-center">
                      <Wifi className="h-4 w-4 mr-2" />
                      Live Progress - Job {realTimeProgress.job_id?.substring(0, 8)}...
                    </h4>
                    <span className="text-sm text-blue-700 dark:text-blue-300">
                      {realTimeProgress.status === 'completed' ? '✅ Selesai' : '🔄 Memproses'}
                    </span>
                  </div>
                  
                  <div className="progress-bar mb-2">
                    <div 
                      className="progress-fill transition-all duration-500"
                      style={{ width: `${realTimeProgress.progress_percentage || 0}%` }}
                    />
                  </div>
                  
                  <div className="flex justify-between text-sm text-blue-700 dark:text-blue-300">
                    <span>
                      {realTimeProgress.processed_numbers || 0} / {realTimeProgress.total_numbers || 0} nomor
                    </span>
                    <span>{realTimeProgress.progress_percentage || 0}%</span>
                  </div>
                  
                  {realTimeProgress.current_phone && (
                    <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
                      📱 Sedang memproses: {realTimeProgress.current_phone}
                      {realTimeProgress.last_result && (
                        <span className="ml-2">
                          (WA: {realTimeProgress.last_result.whatsapp}, TG: {realTimeProgress.last_result.telegram})
                        </span>
                      )}
                    </div>
                  )}
                  
                  {realTimeProgress.status === 'completed' && realTimeProgress.results && (
                    <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div className="text-center p-2 bg-green-100 dark:bg-green-900 rounded">
                        <div className="font-bold text-green-700 dark:text-green-300">
                          {realTimeProgress.results.whatsapp_active || 0}
                        </div>
                        <div className="text-green-600 dark:text-green-400">WA Aktif</div>
                      </div>
                      <div className="text-center p-2 bg-blue-100 dark:bg-blue-900 rounded">
                        <div className="font-bold text-blue-700 dark:text-blue-300">
                          {realTimeProgress.results.telegram_active || 0}
                        </div>
                        <div className="text-blue-600 dark:text-blue-400">TG Aktif</div>
                      </div>
                      <div className="text-center p-2 bg-red-100 dark:bg-red-900 rounded">
                        <div className="font-bold text-red-700 dark:text-red-300">
                          {realTimeProgress.results.inactive || 0}
                        </div>
                        <div className="text-red-600 dark:text-red-400">Tidak Aktif</div>
                      </div>
                      <div className="text-center p-2 bg-yellow-100 dark:bg-yellow-900 rounded">
                        <div className="font-bold text-yellow-700 dark:text-yellow-300">
                          {realTimeProgress.results.errors || 0}
                        </div>
                        <div className="text-yellow-600 dark:text-yellow-400">Error</div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Action Button */}
              <button
                onClick={startValidation}
                disabled={uploading || files.length === 0 || files.some(f => f.status === 'error')}
                className="w-full btn-primary mt-4 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Memproses...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Mulai Validasi ({estimateCredits()} kredit)
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Credit & Estimation */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Estimasi Biaya
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Kredit tersisa</span>
                <span className="font-bold text-green-600 dark:text-green-400">
                  {user?.credits || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Estimasi biaya</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {estimateCredits()} kredit
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Sisa setelah validasi</span>
                <span className={`font-medium ${
                  (user?.credits || 0) - estimateCredits() >= 0 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {(user?.credits || 0) - estimateCredits()}
                </span>
              </div>
            </div>
          </div>

          {/* Format Guide */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              📋 Format File
            </h3>
            <div className="space-y-3">
              <div>
                <p className="font-medium text-gray-900 dark:text-white mb-2">CSV Format:</p>
                <div className="bg-gray-100 dark:bg-gray-700 rounded p-2 text-sm font-mono">
                  phone_number<br/>
                  +628123456789<br/>
                  08234567890<br/>
                  628345678901
                </div>
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <p>• Header wajib: <code>phone_number</code></p>
                <p>• Format nomor akan dinormalisasi otomatis</p>
                <p>• Duplikasi nomor akan dihapus</p>
                <p>• Max 1000 nomor per file</p>
              </div>
            </div>
          </div>

          {/* Tips */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              💡 Tips
            </h3>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
              <li>• Gunakan format CSV untuk performa terbaik</li>
              <li>• Pastikan koneksi internet stabil</li>
              <li>• Progress akan ditampilkan real-time</li>
              <li>• Hasil dapat diunduh setelah selesai</li>
              <li>• Notifikasi akan dikirim saat selesai</li>
            </ul>
          </div>

          {/* Quick Stats */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Info className="h-5 w-5 mr-2" />
              Statistik
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">File dipilih</span>
                <span className="font-medium text-gray-900 dark:text-white">{files.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Total baris</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {files.reduce((total, file) => {
                    if (file.preview) {
                      const lines = file.preview.split('\n').filter(line => line.trim());
                      return total + Math.max(0, lines.length - 1);
                    }
                    return total;
                  }, 0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Ukuran total</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {formatFileSize(files.reduce((total, file) => total + file.file.size, 0))}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BulkCheck;