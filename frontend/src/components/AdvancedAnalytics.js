import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { 
  Shield, 
  TrendingUp,
  Users,
  Activity,
  DollarSign,
  Calendar,
  BarChart3,
  PieChart,
  RefreshCw,
  Download
} from 'lucide-react';

const AdvancedAnalytics = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchAnalytics();
    }
  }, [user, timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const data = await apiCall(`/api/admin/advanced-analytics?range=${timeRange}`);
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('id-ID').format(num || 0);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const exportAnalytics = async () => {
    try {
      // This would generate a comprehensive analytics report
      console.log('Export analytics functionality');
    } catch (error) {
      console.error('Error exporting analytics:', error);
    }
  };

  // Mock data for demonstration (in real app, this would come from backend)
  const mockChartData = {
    dailyUsers: [
      { date: '2024-01-01', users: 12, validations: 45, revenue: 125 },
      { date: '2024-01-02', users: 15, validations: 52, revenue: 142 },
      { date: '2024-01-03', users: 18, validations: 38, revenue: 98 },
      { date: '2024-01-04', users: 22, validations: 65, revenue: 187 },
      { date: '2024-01-05', users: 25, validations: 71, revenue: 203 },
      { date: '2024-01-06', users: 19, validations: 59, revenue: 165 },
      { date: '2024-01-07', users: 28, validations: 82, revenue: 231 }
    ],
    platformUsage: [
      { platform: 'WhatsApp', count: 1250, percentage: 67 },
      { platform: 'Telegram', count: 610, percentage: 33 }
    ],
    userActivity: [
      { hour: '00', activity: 2 },
      { hour: '01', activity: 1 },
      { hour: '02', activity: 0 },
      { hour: '03', activity: 1 },
      { hour: '04', activity: 3 },
      { hour: '05', activity: 8 },
      { hour: '06', activity: 15 },
      { hour: '07', activity: 25 },
      { hour: '08', activity: 35 },
      { hour: '09', activity: 42 },
      { hour: '10', activity: 38 },
      { hour: '11', activity: 45 },
      { hour: '12', activity: 40 },
      { hour: '13', activity: 38 },
      { hour: '14', activity: 44 },
      { hour: '15', activity: 41 },
      { hour: '16', activity: 39 },
      { hour: '17', activity: 35 },
      { hour: '18', activity: 28 },
      { hour: '19', activity: 22 },
      { hour: '20', activity: 18 },
      { hour: '21', activity: 15 },
      { hour: '22', activity: 8 },
      { hour: '23', activity: 5 }
    ]
  };

  if (user?.role !== 'admin') {
    return (
      <div className="card p-12 text-center">
        <Shield className="h-16 w-16 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Access Denied
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          You do not have permission to access advanced analytics
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-700 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <div className="p-2 bg-white/20 rounded-lg mr-4">
              <BarChart3 className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Advanced Analytics</h1>
              <p className="text-purple-100">
                Deep insights into user behavior and platform performance
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-white/20 border border-white/30 rounded-lg px-3 py-2 text-white placeholder-white/70"
            >
              <option value="1d" className="text-gray-900">Last 24 Hours</option>
              <option value="7d" className="text-gray-900">Last 7 Days</option>
              <option value="30d" className="text-gray-900">Last 30 Days</option>
              <option value="90d" className="text-gray-900">Last 90 Days</option>
            </select>
            <button
              onClick={exportAnalytics}
              className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
              title="Export analytics"
            >
              <Download className="h-5 w-5" />
            </button>
            <button
              onClick={fetchAnalytics}
              className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
              title="Refresh"
            >
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="text-green-500 text-sm font-medium flex items-center">
              <TrendingUp className="h-4 w-4 mr-1" />
              +12%
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {formatNumber(analytics?.user_stats?.total_users || 156)}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Active Users ({timeRange})
            </p>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <Activity className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <div className="text-green-500 text-sm font-medium flex items-center">
              <TrendingUp className="h-4 w-4 mr-1" />
              +8%
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {formatNumber(analytics?.validation_stats?.total_validations || 1860)}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Total Validations
            </p>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <DollarSign className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="text-green-500 text-sm font-medium flex items-center">
              <TrendingUp className="h-4 w-4 mr-1" />
              +15%
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {formatCurrency(analytics?.payment_stats?.total_revenue || 2340)}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Revenue ({timeRange})
            </p>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
              <Calendar className="h-6 w-6 text-orange-600 dark:text-orange-400" />
            </div>
            <div className="text-red-500 text-sm font-medium flex items-center">
              <TrendingUp className="h-4 w-4 mr-1 rotate-180" />
              -3%
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              89.2%
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Success Rate
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trends Chart */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Revenue Trends
            </h3>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Last 7 days
            </div>
          </div>
          
          <div className="space-y-4">
            {mockChartData.dailyUsers.map((day, index) => (
              <div key={index} className="flex items-center">
                <div className="w-16 text-sm text-gray-600 dark:text-gray-400">
                  {new Date(day.date).toLocaleDateString('id-ID', { weekday: 'short' })}
                </div>
                <div className="flex-1 mx-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {formatCurrency(day.revenue)}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {day.validations} validations
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full"
                      style={{ width: `${(day.revenue / 250) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Platform Usage */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <PieChart className="h-5 w-5 mr-2" />
              Platform Usage
            </h3>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Total: {formatNumber(mockChartData.platformUsage.reduce((sum, p) => sum + p.count, 0))}
            </div>
          </div>

          <div className="space-y-6">
            {mockChartData.platformUsage.map((platform, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      platform.platform === 'WhatsApp' ? 'bg-green-500' : 'bg-blue-500'
                    }`}></div>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {platform.platform}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-gray-900 dark:text-white">
                      {formatNumber(platform.count)}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {platform.percentage}%
                    </div>
                  </div>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full ${
                      platform.platform === 'WhatsApp' ? 'bg-green-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${platform.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* User Activity Heatmap */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            User Activity Heatmap (24 Hours)
          </h3>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Peak: 9-11 AM
          </div>
        </div>

        <div className="grid grid-cols-12 lg:grid-cols-24 gap-1">
          {mockChartData.userActivity.map((hour, index) => {
            const intensity = Math.min(hour.activity / 45, 1); // Normalize to 0-1
            const opacity = Math.max(intensity, 0.1);
            
            return (
              <div
                key={index}
                className="relative group"
                title={`${hour.hour}:00 - ${hour.activity} users`}
              >
                <div 
                  className="w-full h-8 rounded bg-blue-500 hover:bg-blue-600 transition-colors cursor-pointer"
                  style={{ opacity }}
                ></div>
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
                    {hour.hour}:00<br/>{hour.activity} users
                  </div>
                </div>
                <div className="text-xs text-center text-gray-500 dark:text-gray-400 mt-1">
                  {hour.hour}
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex items-center justify-between mt-4 text-sm text-gray-500 dark:text-gray-400">
          <span>Less active</span>
          <div className="flex items-center space-x-1">
            {[0.2, 0.4, 0.6, 0.8, 1.0].map((opacity, index) => (
              <div
                key={index}
                className="w-3 h-3 bg-blue-500 rounded"
                style={{ opacity }}
              ></div>
            ))}
          </div>
          <span>More active</span>
        </div>
      </div>

      {/* Top Performing Users */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
          <Users className="h-5 w-5 mr-2" />
          Top Performing Users
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Validations
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Revenue
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Success Rate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Last Active
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
              {[
                { user: 'demo', validations: 245, revenue: 612, success_rate: 94.2, last_active: '2 hours ago' },
                { user: 'admin', validations: 189, revenue: 473, success_rate: 91.8, last_active: '5 minutes ago' },
                { user: 'user_123', validations: 167, revenue: 418, success_rate: 89.1, last_active: '1 day ago' },
                { user: 'test_user', validations: 134, revenue: 335, success_rate: 92.5, last_active: '3 hours ago' },
                { user: 'premium_user', validations: 98, revenue: 245, success_rate: 96.1, last_active: '30 minutes ago' }
              ].map((userStat, index) => (
                <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm mr-3">
                        {userStat.user.charAt(0).toUpperCase()}
                      </div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {userStat.user}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {formatNumber(userStat.validations)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {formatCurrency(userStat.revenue)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-3">
                        <div 
                          className={`h-2 rounded-full ${
                            userStat.success_rate > 95 ? 'bg-green-500' :
                            userStat.success_rate > 90 ? 'bg-blue-500' : 'bg-yellow-500'
                          }`}
                          style={{ width: `${userStat.success_rate}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {userStat.success_rate}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {userStat.last_active}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdvancedAnalytics;