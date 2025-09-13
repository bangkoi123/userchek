import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { 
  CreditCard, 
  Bank,
  DollarSign,
  Plus,
  Edit2,
  Trash2,
  Eye,
  Download,
  Filter,
  Search,
  CheckCircle,
  XCircle,
  Clock,
  Shield,
  Settings
} from 'lucide-react';
import { toast } from 'react-hot-toast';

const PaymentManagement = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [showBankModal, setShowBankModal] = useState(false);
  const [showMethodModal, setShowMethodModal] = useState(false);
  const [selectedBank, setSelectedBank] = useState(null);
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [bankForm, setBankForm] = useState({
    bank_name: '',
    account_number: '',
    account_name: '',
    branch: '',
    is_active: true
  });
  const [methodForm, setMethodForm] = useState({
    method_name: '',
    provider: '',
    api_key: '',
    webhook_url: '',
    is_active: true
  });

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchPaymentData();
    }
  }, [user]);

  const fetchPaymentData = async () => {
    try {
      // In a real app, these would be separate API calls
      // For now, we'll simulate with existing transaction data
      const transactionData = await apiCall('/api/admin/credit-management');
      setTransactions(transactionData.recent_transactions || []);
      
      // Mock bank accounts and payment methods for demo
      setBankAccounts([
        {
          id: '1',
          bank_name: 'Bank Central Asia (BCA)',
          account_number: '1234567890',
          account_name: 'PT Webtools Indonesia',
          branch: 'Jakarta Pusat',
          is_active: true,
          created_at: new Date().toISOString()
        },
        {
          id: '2', 
          bank_name: 'Bank Mandiri',
          account_number: '9876543210',
          account_name: 'PT Webtools Indonesia',
          branch: 'Surabaya',
          is_active: false,
          created_at: new Date().toISOString()
        }
      ]);
      
      setPaymentMethods([
        {
          id: '1',
          method_name: 'Stripe',
          provider: 'stripe',
          status: 'active',
          last_transaction: new Date().toISOString(),
          total_transactions: 150,
          total_revenue: 15000,
          is_active: true
        },
        {
          id: '2',
          method_name: 'PayPal',  
          provider: 'paypal',
          status: 'inactive',
          last_transaction: null,
          total_transactions: 0,
          total_revenue: 0,
          is_active: false
        }
      ]);
      
    } catch (error) {
      console.error('Error fetching payment data:', error);
      toast.error('Failed to load payment data');
    } finally {
      setLoading(false);
    }
  };

  const handleBankSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (selectedBank) {
        // Update existing bank account
        setBankAccounts(prev => prev.map(bank => 
          bank.id === selectedBank.id ? { ...bank, ...bankForm } : bank
        ));
        toast.success('Bank account updated successfully');
      } else {
        // Add new bank account
        const newBank = {
          id: Date.now().toString(),
          ...bankForm,
          created_at: new Date().toISOString()
        };
        setBankAccounts(prev => [...prev, newBank]);
        toast.success('Bank account added successfully');
      }
      
      setShowBankModal(false);
      setBankForm({ bank_name: '', account_number: '', account_name: '', branch: '', is_active: true });
      setSelectedBank(null);
    } catch (error) {
      toast.error('Failed to save bank account');
    }
  };

  const handleMethodSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (selectedMethod) {
        // Update existing method
        setPaymentMethods(prev => prev.map(method => 
          method.id === selectedMethod.id ? { ...method, ...methodForm } : method
        ));
        toast.success('Payment method updated successfully');
      } else {
        // Add new method
        const newMethod = {
          id: Date.now().toString(),
          ...methodForm,
          status: methodForm.is_active ? 'active' : 'inactive',
          total_transactions: 0,
          total_revenue: 0,
          created_at: new Date().toISOString()
        };
        setPaymentMethods(prev => [...prev, newMethod]);
        toast.success('Payment method added successfully');
      }
      
      setShowMethodModal(false);
      setMethodForm({ method_name: '', provider: '', api_key: '', webhook_url: '', is_active: true });
      setSelectedMethod(null);
    } catch (error) {
      toast.error('Failed to save payment method');
    }
  };

  const deleteBankAccount = (bankId) => {
    if (window.confirm('Are you sure you want to delete this bank account?')) {
      setBankAccounts(prev => prev.filter(bank => bank.id !== bankId));
      toast.success('Bank account deleted successfully');
    }
  };

  const deletePaymentMethod = (methodId) => {
    if (window.confirm('Are you sure you want to delete this payment method?')) {
      setPaymentMethods(prev => prev.filter(method => method.id !== methodId));
      toast.success('Payment method deleted successfully');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900';
      case 'pending':
        return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900';
      case 'failed':
        return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900';
      default:
        return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900';
    }
  };

  const filteredTransactions = (transactions || []).filter(transaction => {
    const matchesSearch = transaction.package_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transaction._id?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || transaction.payment_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (user?.role !== 'admin') {
    return (
      <div className="card p-12 text-center">
        <Shield className="h-16 w-16 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Access Denied
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          You do not have permission to access payment management
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading payment management...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-lg p-6 text-white">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-white/20 rounded-lg mr-4">
            <CreditCard className="h-6 w-6" />
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
          {/* Bank Accounts */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Bank Accounts
              </h2>
              <button
                onClick={() => {
                  setBankForm({ bank_name: '', account_number: '', account_name: '', branch: '', is_active: true });
                  setSelectedBank(null);
                  setShowBankModal(true);
                }}
                className="btn-primary flex items-center"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Bank Account
              </button>
            </div>

            <div className="space-y-4">
              {bankAccounts.map((bank) => (
                <div key={bank.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <Bank className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {bank.bank_name}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {bank.account_number} - {bank.account_name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500">
                          Branch: {bank.branch}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        bank.is_active 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                      }`}>
                        {bank.is_active ? 'Active' : 'Inactive'}
                      </span>
                      <button
                        onClick={() => {
                          setBankForm(bank);
                          setSelectedBank(bank);
                          setShowBankModal(true);
                        }}
                        className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteBankAccount(bank.id)}
                        className="p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Payment Methods */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Payment Methods
              </h2>
              <button
                onClick={() => {
                  setMethodForm({ method_name: '', provider: '', api_key: '', webhook_url: '', is_active: true });
                  setSelectedMethod(null);
                  setShowMethodModal(true);
                }}
                className="btn-primary flex items-center"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Method
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {paymentMethods.map((method) => (
                <div key={method.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                        <CreditCard className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {method.method_name}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {method.provider}
                        </p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(method.status)}`}>
                      {method.status}
                    </span>
                  </div>
                  
                  <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                    <div className="flex justify-between">
                      <span>Transactions:</span>
                      <span className="font-medium">{method.total_transactions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Revenue:</span>
                      <span className="font-medium">{formatCurrency(method.total_revenue)}</span>
                    </div>
                    {method.last_transaction && (
                      <div className="flex justify-between">
                        <span>Last used:</span>
                        <span className="font-medium">{formatDate(method.last_transaction)}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={() => {
                        setMethodForm(method);
                        setSelectedMethod(method);
                        setShowMethodModal(true);
                      }}
                      className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => deletePaymentMethod(method.id)}
                      className="p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Transaction History */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Transaction History
              </h2>
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <input
                    type="text"
                    placeholder="Search transactions..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="input-field pl-10 pr-4 py-2 w-64"
                  />
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="input-field"
                >
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
                  {filteredTransactions.map((transaction) => (
                    <tr key={transaction._id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {transaction.package_name}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            {transaction.credits_amount?.toLocaleString()} credits
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {formatCurrency(transaction.amount)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getStatusIcon(transaction.payment_status)}
                          <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(transaction.payment_status)}`}>
                            {transaction.payment_status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(transaction.completed_at || transaction.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 p-1 rounded hover:bg-primary-50 dark:hover:bg-primary-900"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Payment Stats */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Payment Overview
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Total Revenue</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {formatCurrency((transactions || []).reduce((sum, t) => sum + (t.amount || 0), 0))}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Transactions</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {(transactions || []).length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Active Methods</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {paymentMethods.filter(m => m.is_active).length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Bank Accounts</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {bankAccounts.filter(b => b.is_active).length}
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
                <Download className="h-4 w-4 mr-2" />
                Export Transactions
              </button>
              <button className="w-full btn-secondary flex items-center justify-center">
                <Settings className="h-4 w-4 mr-2" />
                Payment Settings
              </button>
              <button
                onClick={() => window.location.href = '/admin/settings'}
                className="w-full btn-primary flex items-center justify-center"
              >
                <Shield className="h-4 w-4 mr-2" />
                Admin Settings
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Bank Account Modal */}
      {showBankModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full">
            <div className="p-6 border-b border-gray-200 dark:border-gray-600">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {selectedBank ? 'Edit Bank Account' : 'Add Bank Account'}
              </h2>
            </div>
            <form onSubmit={handleBankSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Bank Name
                </label>
                <input
                  type="text"
                  value={bankForm.bank_name}
                  onChange={(e) => setBankForm({ ...bankForm, bank_name: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Bank Central Asia (BCA)"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Account Number
                </label>
                <input
                  type="text"
                  value={bankForm.account_number}
                  onChange={(e) => setBankForm({ ...bankForm, account_number: e.target.value })}
                  className="input-field"
                  placeholder="1234567890"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Account Name
                </label>
                <input
                  type="text"
                  value={bankForm.account_name}
                  onChange={(e) => setBankForm({ ...bankForm, account_name: e.target.value })}
                  className="input-field"
                  placeholder="PT Webtools Indonesia"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Branch
                </label>
                <input
                  type="text"
                  value={bankForm.branch}
                  onChange={(e) => setBankForm({ ...bankForm, branch: e.target.value })}
                  className="input-field"
                  placeholder="Jakarta Pusat"
                  required
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="bank_active"
                  checked={bankForm.is_active}
                  onChange={(e) => setBankForm({ ...bankForm, is_active: e.target.checked })}
                  className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
                />
                <label htmlFor="bank_active" className="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">
                  Active
                </label>
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowBankModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {selectedBank ? 'Update' : 'Add'} Bank Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Payment Method Modal */}
      {showMethodModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full">
            <div className="p-6 border-b border-gray-200 dark:border-gray-600">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {selectedMethod ? 'Edit Payment Method' : 'Add Payment Method'}
              </h2>
            </div>
            <form onSubmit={handleMethodSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Method Name
                </label>
                <input
                  type="text"
                  value={methodForm.method_name}
                  onChange={(e) => setMethodForm({ ...methodForm, method_name: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Stripe"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Provider
                </label>
                <select
                  value={methodForm.provider}
                  onChange={(e) => setMethodForm({ ...methodForm, provider: e.target.value })}
                  className="input-field"
                  required
                >
                  <option value="">Select Provider</option>
                  <option value="stripe">Stripe</option>
                  <option value="paypal">PayPal</option>
                  <option value="xendit">Xendit</option>
                  <option value="midtrans">Midtrans</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  API Key
                </label>
                <input
                  type="password"
                  value={methodForm.api_key}
                  onChange={(e) => setMethodForm({ ...methodForm, api_key: e.target.value })}
                  className="input-field"
                  placeholder="Enter API key"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Webhook URL
                </label>
                <input
                  type="url"
                  value={methodForm.webhook_url}
                  onChange={(e) => setMethodForm({ ...methodForm, webhook_url: e.target.value })}
                  className="input-field"
                  placeholder="https://yourdomain.com/webhook"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="method_active"
                  checked={methodForm.is_active}
                  onChange={(e) => setMethodForm({ ...methodForm, is_active: e.target.checked })}
                  className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
                />
                <label htmlFor="method_active" className="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">
                  Active
                </label>
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowMethodModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {selectedMethod ? 'Update' : 'Add'} Method
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PaymentManagement;