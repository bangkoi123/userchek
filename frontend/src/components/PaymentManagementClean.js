import React from 'react';
import { useAuth } from '../context/AuthContext';

const PaymentManagement = () => {
  const { user } = useAuth();

  if (user?.role !== 'admin') {
    return (
      <div className="card p-12 text-center">
        <div className="h-16 w-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-red-600 text-2xl">🛡️</span>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Access Denied
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          You do not have permission to access payment management
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-lg p-6 text-white">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-white/20 rounded-lg mr-4">
            <span className="text-2xl">💳</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold">Payment Management</h1>
            <p className="text-green-100">
              Manage bank accounts, payment methods, and transaction monitoring
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Payment Methods */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Payment Methods
              </h2>
              <button className="btn-primary flex items-center">
                <span className="mr-2">➕</span>
                Add Method
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Stripe */}
              <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                      <span className="text-purple-600 dark:text-purple-400">💳</span>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        Stripe
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Credit Card Processing
                      </p>
                    </div>
                  </div>
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                    Active
                  </span>
                </div>
                
                <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                  <div className="flex justify-between">
                    <span>Transactions:</span>
                    <span className="font-medium">150</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Revenue:</span>
                    <span className="font-medium">$15,000</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Last used:</span>
                    <span className="font-medium">2 hours ago</span>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2">
                  <button className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                    ✏️
                  </button>
                  <button className="p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
                    🗑️
                  </button>
                </div>
              </div>

              {/* PayPal */}
              <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                      <span className="text-blue-600 dark:text-blue-400">💳</span>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        PayPal
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Digital Wallet
                      </p>
                    </div>
                  </div>
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                    Inactive
                  </span>
                </div>
                
                <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                  <div className="flex justify-between">
                    <span>Transactions:</span>
                    <span className="font-medium">0</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Revenue:</span>
                    <span className="font-medium">$0.00</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Last used:</span>
                    <span className="font-medium">Never</span>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2">
                  <button className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                    ✏️
                  </button>
                  <button className="p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Bank Accounts */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Bank Accounts
              </h2>
              <button className="btn-primary flex items-center">
                <span className="mr-2">➕</span>
                Add Bank Account
              </button>
            </div>

            <div className="space-y-4">
              {/* BCA */}
              <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                      <span className="text-blue-600 dark:text-blue-400 text-xl">🏦</span>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        Bank Central Asia (BCA)
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        1234567890 - PT Webtools Indonesia
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500">
                        Branch: Jakarta Pusat
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                      Active
                    </span>
                    <button className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                      ✏️
                    </button>
                    <button className="p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
                      🗑️
                    </button>
                  </div>
                </div>
              </div>

              {/* Mandiri */}
              <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
                      <span className="text-yellow-600 dark:text-yellow-400 text-xl">🏦</span>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        Bank Mandiri
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        9876543210 - PT Webtools Indonesia
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500">
                        Branch: Surabaya
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                      Inactive
                    </span>
                    <button className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                      ✏️
                    </button>
                    <button className="p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Transactions */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Recent Transactions
              </h2>
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search transactions..."
                    className="input-field pl-10 pr-4 py-2 w-64"
                  />
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</span>
                </div>
                <select className="input-field">
                  <option value="all">All Status</option>
                  <option value="completed">Completed</option>
                  <option value="pending">Pending</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Transaction
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                  <tr className="text-center">
                    <td colSpan="5" className="px-6 py-8 text-gray-500 dark:text-gray-400">
                      No transactions found
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Payment Overview */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Payment Overview
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Total Revenue</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  $15,000.00
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Transactions</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  150
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Active Methods</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  1
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Bank Accounts</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  1
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Quick Actions
            </h3>
            <div className="space-y-3">
              <button className="w-full btn-secondary flex items-center justify-center">
                <span className="mr-2">📥</span>
                Export Transactions
              </button>
              <button className="w-full btn-secondary flex items-center justify-center">
                <span className="mr-2">⚙️</span>
                Payment Settings
              </button>
              <button
                onClick={() => window.location.href = '/admin/settings'}
                className="w-full btn-primary flex items-center justify-center"
              >
                <span className="mr-2">🛡️</span>
                Admin Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentManagement;