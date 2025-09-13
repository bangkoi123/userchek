import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { apiCall } from '../utils/api';
import { 
  CreditCard, 
  Zap, 
  TrendingUp, 
  Calendar,
  CheckCircle,
  Clock,
  AlertCircle,
  FileText,
  ArrowUpRight
} from 'lucide-react';
import { format } from 'date-fns';
import { id } from 'date-fns/locale';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const data = await apiCall('/api/dashboard/stats');
      setStats(data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('id-ID').format(num || 0);
  };

  const getJobStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'processing':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getJobStatusText = (status) => {
    switch (status) {
      case 'completed':
        return 'Selesai';
      case 'processing':
        return 'Proses';
      case 'failed':
        return 'Gagal';
      case 'pending':
        return 'Menunggu';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Memuat dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">
          Selamat datang kembali, {user?.username}! 👋
        </h1>
        <p className="text-primary-100">
          Kelola validasi nomor telepon Anda dengan mudah dan efisien
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Credits */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <CreditCard className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <ArrowUpRight className="h-4 w-4 text-green-500" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {formatNumber(stats?.credits_remaining)}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Kredit Tersisa
            </p>
          </div>
        </div>

        {/* Total Checks */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Zap className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <ArrowUpRight className="h-4 w-4 text-blue-500" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {formatNumber(stats?.total_checks)}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Total Validasi
            </p>
          </div>
        </div>

        {/* Monthly Checks */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Calendar className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <ArrowUpRight className="h-4 w-4 text-purple-500" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {formatNumber(stats?.monthly_checks)}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Validasi Bulan Ini
            </p>
          </div>
        </div>

        {/* Credits Used */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
              <TrendingUp className="h-6 w-6 text-orange-600 dark:text-orange-400" />
            </div>
            <ArrowUpRight className="h-4 w-4 text-orange-500" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {formatNumber(stats?.total_credits_used)}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Total Kredit Terpakai
            </p>
          </div>
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Pekerjaan Terbaru
          </h2>
          <button className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 text-sm font-medium">
            Lihat Semua
          </button>
        </div>

        {stats?.recent_jobs && stats.recent_jobs.length > 0 ? (
          <div className="space-y-4">
            {stats.recent_jobs.map((job) => (
              <div 
                key={job._id}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors duration-200"
              >
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-white dark:bg-gray-800 rounded-lg">
                    <FileText className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {job.filename || 'Unnamed Job'}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {formatNumber(job.total_numbers || 0)} nomor • {' '}
                      {job.created_at ? format(new Date(job.created_at), 'dd MMM yyyy HH:mm', { locale: id }) : 'Unknown date'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {getJobStatusIcon(job.status)}
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {getJobStatusText(job.status)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400 mb-2">
              Belum ada pekerjaan
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500">
              Mulai dengan Quick Check atau Bulk Check untuk melihat riwayat di sini
            </p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6">
          <div className="text-center">
            <div className="p-3 bg-primary-100 dark:bg-primary-900 rounded-full inline-flex mb-4">
              <Zap className="h-8 w-8 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Quick Check
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Validasi satu nomor telepon secara instan
            </p>
            <button 
              onClick={() => navigate('/quick-check')}
              className="btn-primary"
            >
              Mulai Quick Check
            </button>
          </div>
        </div>

        <div className="card p-6">
          <div className="text-center">
            <div className="p-3 bg-green-100 dark:bg-green-900 rounded-full inline-flex mb-4">
              <FileText className="h-8 w-8 text-green-600 dark:text-green-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Bulk Check
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Upload file CSV untuk validasi massal
            </p>
            <button 
              onClick={() => navigate('/bulk-check')}
              className="btn-primary"
            >
              Mulai Bulk Check
            </button>
          </div>
        </div>

        <div className="card p-6">
          <div className="text-center">
            <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-full inline-flex mb-4">
              <CreditCard className="h-8 w-8 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Top Up Credits
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Beli kredit untuk validasi lebih banyak
            </p>
            <button 
              onClick={() => navigate('/credit-topup')}
              className="btn-primary"
            >
              Beli Kredit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;