import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { 
  Shield, 
  Server, 
  Database, 
  Activity, 
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  HardDrive,
  Cpu,
  Monitor,
  Trash2
} from 'lucide-react';
import { toast } from 'react-toastify';

const SystemHealth = () => {
  const { user } = useAuth();
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [clearingCache, setClearingCache] = useState(false);

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchSystemHealth();
    }
  }, [user]);

  useEffect(() => {
    let interval;
    if (autoRefresh && user?.role === 'admin') {
      interval = setInterval(fetchSystemHealth, 30000); // Refresh every 30 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, user]);

  const fetchSystemHealth = async () => {
    try {
      const data = await apiCall('/api/admin/system-health');
      setHealthData(data);
    } catch (error) {
      console.error('Error fetching system health:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearValidationCache = async () => {
    if (!window.confirm('Apakah Anda yakin ingin menghapus semua cache validasi? Semua nomor akan divalidasi ulang pada pengecekan berikutnya.')) {
      return;
    }

    setClearingCache(true);
    try {
      const result = await apiCall('/api/admin/clear-validation-cache', 'POST');
      toast.success(`Cache berhasil dihapus! ${result.deleted_count} entri cache dihapus.`);
      
      // Refresh system health after clearing cache
      fetchSystemHealth();
    } catch (error) {
      console.error('Error clearing cache:', error);
      toast.error('Gagal menghapus cache: ' + (error.response?.data?.detail || error.message));
    } finally {
      setClearingCache(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'error':
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900';
      case 'error':
      case 'unhealthy':
        return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900';
      default:
        return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900';
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (user?.role !== 'admin') {
    return (
      <div className="card p-12 text-center">
        <Shield className="h-16 w-16 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Access Denied
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          You do not have permission to access system health monitoring
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading system health...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <div className="p-2 bg-white/20 rounded-lg mr-4">
              <Monitor className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">System Health Monitor</h1>
              <p className="text-blue-100">
                Real-time system status and performance monitoring
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoRefresh"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="autoRefresh" className="text-sm text-blue-100">
                Auto-refresh (30s)
              </label>
            </div>
            <button
              onClick={fetchSystemHealth}
              className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
              title="Refresh now"
            >
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>
        
        {healthData && (
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              {getStatusIcon(healthData.overall_status)}
              <span className="font-semibold">Overall Status: {healthData.overall_status}</span>
            </div>
            <div className="text-blue-200 text-sm">
              Last updated: {new Date(healthData.timestamp).toLocaleTimeString()}
            </div>
          </div>
        )}
      </div>

      {healthData && (
        <>
          {/* System Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Database Health */}
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                  <Database className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
                {getStatusIcon(healthData.database.status)}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Database
                </h3>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(healthData.database.status)}`}>
                      {healthData.database.status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Response:</span>
                    <span className="font-medium">{healthData.database.response_time_ms}ms</span>
                  </div>
                </div>
              </div>
            </div>

            {/* API Health */}
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  <Server className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                {getStatusIcon(healthData.api.status)}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  API Server
                </h3>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(healthData.api.status)}`}>
                      {healthData.api.status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Response:</span>
                    <span className="font-medium">{healthData.api.response_time_ms}ms</span>
                  </div>
                </div>
              </div>
            </div>

            {/* CPU Usage */}
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                  <Cpu className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                </div>
                {getStatusIcon(healthData.server.cpu_usage_percent > 80 ? 'warning' : 'healthy')}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  CPU Usage
                </h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Current:</span>
                    <span className="font-medium">{healthData.server.cpu_usage_percent}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        healthData.server.cpu_usage_percent > 80 ? 'bg-red-500' :
                        healthData.server.cpu_usage_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${healthData.server.cpu_usage_percent}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Memory Usage */}
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                  <HardDrive className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                {getStatusIcon(healthData.server.memory_usage_percent > 80 ? 'warning' : 'healthy')}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Memory Usage
                </h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Used:</span>
                    <span className="font-medium">
                      {healthData.server.memory_used_gb}GB / {healthData.server.memory_total_gb}GB
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        healthData.server.memory_usage_percent > 80 ? 'bg-red-500' :
                        healthData.server.memory_usage_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${healthData.server.memory_usage_percent}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {healthData.server.memory_usage_percent}% used
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Detailed System Info */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Server Resources */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Server className="h-5 w-5 mr-2" />
                Server Resources
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Disk Usage</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {healthData.server.disk_used_gb}GB / {healthData.server.disk_total_gb}GB
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900 dark:text-white">
                      {healthData.server.disk_usage_percent}%
                    </p>
                    <div className="w-20 bg-gray-200 dark:bg-gray-600 rounded-full h-2 mt-1">
                      <div 
                        className={`h-2 rounded-full ${
                          healthData.server.disk_usage_percent > 80 ? 'bg-red-500' :
                          healthData.server.disk_usage_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${healthData.server.disk_usage_percent}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">System Uptime</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Estimated server uptime
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900 dark:text-white">
                      {healthData.application.uptime_hours}h
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Application Status */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Activity className="h-5 w-5 mr-2" />
                Application Status
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Active Jobs</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Currently running validation jobs
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900 dark:text-white">
                      {healthData.application.active_jobs}
                    </p>
                  </div>
                </div>

                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Total Users</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Registered users in system
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900 dark:text-white">
                      {healthData.application.total_users}
                    </p>
                  </div>
                </div>

                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Database Connection</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Connection pool status
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(healthData.database.status)}`}>
                      {healthData.database.connection_pool}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SystemHealth;