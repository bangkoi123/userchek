import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall, downloadFile } from '../utils/api';
import { 
  History, 
  Download, 
  Eye, 
  Trash2,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
  FileText,
  Calendar,
  Filter,
  Search,
  RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { id } from 'date-fns/locale';

const JobHistory = () => {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [selectedJob, setSelectedJob] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const data = await apiCall('/api/jobs');
      setJobs(data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      toast.error('Gagal memuat riwayat pekerjaan');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'pending':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return 'Selesai';
      case 'processing':
        return 'Memproses';
      case 'failed':
        return 'Gagal';
      case 'pending':
        return 'Menunggu';
      default:
        return status;
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'processing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const handleDownload = async (jobId, filename) => {
    try {
      await downloadFile(`/api/jobs/${jobId}/download`, filename);
      toast.success('File berhasil diunduh');
    } catch (error) {
      toast.error('Gagal mengunduh file');
    }
  };

  const handleDelete = async (jobId) => {
    if (!window.confirm('Apakah Anda yakin ingin menghapus pekerjaan ini?')) {
      return;
    }

    try {
      await apiCall(`/api/jobs/${jobId}`, 'DELETE');
      toast.success('Pekerjaan berhasil dihapus');
      fetchJobs();
    } catch (error) {
      toast.error('Gagal menghapus pekerjaan');
    }
  };

  const handleViewDetail = (job) => {
    setSelectedJob(job);
    setShowDetailModal(true);
  };

  const filteredJobs = jobs
    .filter(job => {
      const matchesSearch = job.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           job._id.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || job.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];
      
      if (sortBy === 'created_at') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  const formatNumber = (num) => {
    return new Intl.NumberFormat('id-ID').format(num || 0);
  };

  const getProgressPercentage = (job) => {
    if (job.status === 'completed') return 100;
    if (job.status === 'failed') return 0;
    if (job.total_numbers && job.processed_numbers) {
      return Math.round((job.processed_numbers / job.total_numbers) * 100);
    }
    return 0;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Memuat riwayat pekerjaan...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-700 rounded-lg p-6 text-white">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-white/20 rounded-lg mr-4">
            <History className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Riwayat Pekerjaan</h1>
            <p className="text-purple-100">
              Kelola dan pantau semua pekerjaan validasi Anda
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
            Total: {jobs.length} pekerjaan
          </div>
          <div className="flex items-center">
            <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
            Selesai: {jobs.filter(j => j.status === 'completed').length}
          </div>
          <div className="flex items-center">
            <span className="w-2 h-2 bg-yellow-400 rounded-full mr-2"></span>
            Proses: {jobs.filter(j => j.status === 'processing').length}
          </div>
        </div>
      </div>

      {/* Filters and Controls */}
      <div className="card p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 md:space-x-4">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Cari berdasarkan nama file atau ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field"
            >
              <option value="all">Semua Status</option>
              <option value="pending">Menunggu</option>
              <option value="processing">Memproses</option>
              <option value="completed">Selesai</option>
              <option value="failed">Gagal</option>
            </select>

            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field);
                setSortOrder(order);
              }}
              className="input-field"
            >
              <option value="created_at-desc">Terbaru</option>
              <option value="created_at-asc">Terlama</option>
              <option value="filename-asc">Nama A-Z</option>
              <option value="filename-desc">Nama Z-A</option>
              <option value="total_numbers-desc">Jumlah Nomor ↓</option>
              <option value="total_numbers-asc">Jumlah Nomor ↑</option>
            </select>

            <button
              onClick={fetchJobs}
              className="p-2 btn-secondary"
              title="Refresh"
            >
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Jobs List */}
      {filteredJobs.length > 0 ? (
        <div className="space-y-4">
          {filteredJobs.map((job) => (
            <div key={job._id} className="card p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-4">
                  <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                    <FileText className="h-6 w-6 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {job.filename || 'Unnamed Job'}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      ID: {job._id}
                    </p>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
                      <span className="flex items-center">
                        <Calendar className="h-4 w-4 mr-1" />
                        {format(new Date(job.created_at), 'dd MMM yyyy HH:mm', { locale: id })}
                      </span>
                      <span>
                        {formatNumber(job.total_numbers || 0)} nomor
                      </span>
                      <span>
                        {job.credits_used || 0} kredit
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {getStatusIcon(job.status)}
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(job.status)}`}>
                    {getStatusText(job.status)}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              {(job.status === 'processing' || job.status === 'completed') && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                    <span>Progress</span>
                    <span>{getProgressPercentage(job)}%</span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${getProgressPercentage(job)}%` }}
                    />
                  </div>
                  {job.processed_numbers && job.total_numbers && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {formatNumber(job.processed_numbers)} dari {formatNumber(job.total_numbers)} nomor diproses
                    </p>
                  )}
                </div>
              )}

              {/* Results Summary */}
              {job.status === 'completed' && job.results && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {formatNumber(job.results.whatsapp_active || 0)}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">WhatsApp Aktif</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {formatNumber(job.results.telegram_active || 0)}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Telegram Aktif</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                      {formatNumber(job.results.inactive || 0)}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Tidak Aktif</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                      {formatNumber(job.results.errors || 0)}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Error</p>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {job.status === 'failed' && job.error_message && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-sm text-red-700 dark:text-red-300">
                    <strong>Error:</strong> {job.error_message}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-600">
                <div className="flex items-center space-x-2">
                  {job.status === 'completed' && (
                    <button
                      onClick={() => handleDownload(job._id, job.filename)}
                      className="flex items-center px-3 py-1 text-sm bg-green-100 hover:bg-green-200 dark:bg-green-900 dark:hover:bg-green-800 text-green-700 dark:text-green-300 rounded-lg transition-colors"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Unduh Hasil
                    </button>
                  )}
                  <button 
                    onClick={() => handleViewDetail(job)}
                    className="flex items-center px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 rounded-lg transition-colors"
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    Detail
                  </button>
                </div>

                <button
                  onClick={() => handleDelete(job._id)}
                  className="flex items-center px-3 py-1 text-sm bg-red-100 hover:bg-red-200 dark:bg-red-900 dark:hover:bg-red-800 text-red-700 dark:text-red-300 rounded-lg transition-colors"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Hapus
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <History className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {searchTerm || statusFilter !== 'all' ? 'Tidak ada hasil' : 'Belum ada pekerjaan'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {searchTerm || statusFilter !== 'all' 
              ? 'Coba ubah filter atau kata kunci pencarian'
              : 'Mulai dengan Quick Check atau Bulk Check untuk melihat riwayat di sini'
            }
          </p>
          {(!searchTerm && statusFilter === 'all') && (
            <div className="flex justify-center space-x-4">
              <button className="btn-primary">
                Quick Check
              </button>
              <button className="btn-secondary">
                Bulk Check
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default JobHistory;