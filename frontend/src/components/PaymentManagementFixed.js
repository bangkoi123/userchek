import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { 
  CreditCard, 
  Bank,
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

  const showMessage = (message, type = 'success') => {
    // Simple alert instead of toast for now
    alert(message);
  };

  const fetchPaymentData = async () => {
    try {
      // In a real app, these would be separate API calls
      // For now, we'll simulate with existing transaction data
      const transactionData = await apiCall('/api/admin/credit-management');
      setTransactions(Array.isArray(transactionData.recent_transactions) ? transactionData.recent_transactions : []);
      
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
      showMessage('Failed to load payment data', 'error');
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
        showMessage('Bank account updated successfully');
      } else {
        // Add new bank account
        const newBank = {
          id: Date.now().toString(),
          ...bankForm,
          created_at: new Date().toISOString()
        };
        setBankAccounts(prev => [...prev, newBank]);
        showMessage('Bank account added successfully');
      }
      
      setShowBankModal(false);
      setBankForm({ bank_name: '', account_number: '', account_name: '', branch: '', is_active: true });
      setSelectedBank(null);
    } catch (error) {
      showMessage('Failed to save bank account', 'error');
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
        showMessage('Payment method updated successfully');
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
        showMessage('Payment method added successfully');
      }
      
      setShowMethodModal(false);
      setMethodForm({ method_name: '', provider: '', api_key: '', webhook_url: '', is_active: true });
      setSelectedMethod(null);
    } catch (error) {
      showMessage('Failed to save payment method', 'error');
    }
  };

  const deleteBankAccount = (bankId) => {
    if (window.confirm('Are you sure you want to delete this bank account?')) {
      setBankAccounts(prev => prev.filter(bank => bank.id !== bankId));
      showMessage('Bank account deleted successfully');
    }
  };

  const deletePaymentMethod = (methodId) => {
    if (window.confirm('Are you sure you want to delete this payment method?')) {
      setPaymentMethods(prev => prev.filter(method => method.id !== methodId));
      showMessage('Payment method deleted successfully');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
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
    </div>
  );
};

export default PaymentManagement;