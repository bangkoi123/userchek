import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { 
  CreditCard, 
  Package, 
  Zap, 
  ArrowRight,
  Check,
  Star,
  Crown,
  Building2
} from 'lucide-react';
import toast from 'react-hot-toast';

const CreditTopup = () => {
  const { user, updateUser } = useAuth();
  const [packages, setPackages] = useState({});
  const [selectedPackage, setSelectedPackage] = useState('');
  const [loading, setLoading] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    fetchCreditPackages();
    fetchTransactions();
    
    // Check for payment completion
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    const paymentStatus = urlParams.get('payment_status');
    
    if (sessionId && paymentStatus === 'success') {
      checkPaymentStatus(sessionId);
    }
  }, []);

  const fetchCreditPackages = async () => {
    try {
      const data = await apiCall('/api/credit-packages');
      setPackages(data);
      setSelectedPackage('professional'); // Default selection
    } catch (error) {
      console.error('Error fetching credit packages:', error);
      toast.error('Failed to load credit packages');
    }
  };

  const fetchTransactions = async () => {
    try {
      const data = await apiCall('/api/payments/transactions');
      setTransactions(data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkPaymentStatus = async (sessionId) => {
    setPaymentLoading(true);
    let attempts = 0;
    const maxAttempts = 5;
    
    const pollPaymentStatus = async () => {
      try {
        const response = await apiCall(`/api/payments/status/${sessionId}`);
        
        if (response.payment_status === 'paid') {
          toast.success(`🎉 Payment successful! ${response.credits_amount.toLocaleString()} credits added to your account!`);
          
          // Update user credits in context
          const updatedUser = { ...user, credits: user.credits + response.credits_amount };
          updateUser(updatedUser);
          
          // Refresh transactions
          fetchTransactions();
          
          // Clean URL
          window.history.replaceState({}, document.title, window.location.pathname);
          return;
        } else if (response.status === 'expired') {
          toast.error('Payment session expired. Please try again.');
          return;
        }
        
        // Continue polling if payment is still pending
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(pollPaymentStatus, 2000);
        } else {
          toast.error('Payment status check timed out. Please check your email for confirmation.');
        }
        
      } catch (error) {
        console.error('Error checking payment status:', error);
        toast.error('Error checking payment status');
      }
    };
    
    await pollPaymentStatus();
    setPaymentLoading(false);
  };

  const handlePurchase = async () => {
    if (!selectedPackage) {
      toast.error('Please select a credit package');
      return;
    }

    setPaymentLoading(true);
    
    try {
      const originUrl = window.location.origin;
      
      const response = await apiCall('/api/payments/create-checkout', 'POST', {
        package_id: selectedPackage,
        origin_url: originUrl
      });
      
      // Redirect to Stripe Checkout
      window.location.href = response.url;
      
    } catch (error) {
      console.error('Error creating checkout:', error);
      const message = error.response?.data?.detail || 'Failed to create payment session';
      toast.error(message);
      setPaymentLoading(false);
    }
  };

  const getPackageIcon = (packageId) => {
    switch (packageId) {
      case 'starter':
        return <Zap className="h-8 w-8" />;
      case 'professional':
        return <Star className="h-8 w-8" />;
      case 'enterprise':
        return <Crown className="h-8 w-8" />;
      default:
        return <Package className="h-8 w-8" />;
    }
  };

  const getPackageColor = (packageId) => {
    switch (packageId) {
      case 'starter':
        return 'blue';
      case 'professional':
        return 'purple';
      case 'enterprise':
        return 'yellow';
      default:
        return 'gray';
    }
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading credit packages...</p>
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
            <h1 className="text-2xl font-bold">Credit Top-up</h1>
            <p className="text-green-100">
              Purchase credits to validate phone numbers
            </p>
          </div>
        </div>
        
        <div className="bg-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">Current Balance</p>
              <p className="text-2xl font-bold">{user?.credits?.toLocaleString() || 0} credits</p>
            </div>
            <div className="text-right">
              <p className="text-green-100 text-sm">Validation Cost</p>
              <p className="text-lg font-semibold">2 credits per number</p>
            </div>
          </div>
        </div>
      </div>

      {/* Payment Loading */}
      {paymentLoading && (
        <div className="card p-6 text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Processing payment...</p>
        </div>
      )}

      {/* Credit Packages */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Object.entries(packages).map(([packageId, packageData]) => {
          const isSelected = selectedPackage === packageId;
          const color = getPackageColor(packageId);
          const isPopular = packageId === 'professional';
          
          return (
            <div
              key={packageId}
              className={`
                relative card p-6 cursor-pointer transition-all duration-200 border-2
                ${isSelected 
                  ? `border-${color}-500 bg-${color}-50 dark:bg-${color}-900/20` 
                  : 'border-transparent hover:border-gray-300 dark:hover:border-gray-600'
                }
              `}
              onClick={() => setSelectedPackage(packageId)}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-purple-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                    Most Popular
                  </span>
                </div>
              )}
              
              <div className="text-center">
                <div className={`p-3 bg-${color}-100 dark:bg-${color}-900 rounded-full inline-flex mb-4`}>
                  <div className={`text-${color}-600 dark:text-${color}-400`}>
                    {getPackageIcon(packageId)}
                  </div>
                </div>
                
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {packageData.name}
                </h3>
                
                <div className="mb-4">
                  <span className="text-3xl font-bold text-gray-900 dark:text-white">
                    {packageData.credits.toLocaleString()}
                  </span>
                  <span className="text-gray-600 dark:text-gray-400 ml-1">credits</span>
                </div>
                
                <div className="mb-6">
                  <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                    ${packageData.price}
                  </span>
                  <span className="text-gray-600 dark:text-gray-400 ml-1">USD</span>
                </div>
                
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  <p>≈ {Math.floor(packageData.credits / 2).toLocaleString()} validations</p>
                  <p className="text-xs mt-1">
                    ${(packageData.price / packageData.credits * 1000).toFixed(2)} per 1K credits
                  </p>
                </div>
                
                {isSelected && (
                  <div className={`flex items-center justify-center text-${color}-600 dark:text-${color}-400 mb-4`}>
                    <Check className="h-5 w-5 mr-1" />
                    <span className="font-medium">Selected</span>
                  </div>
                )}
                
                <div className="space-y-2 text-xs text-gray-500 dark:text-gray-400">
                  {packageId === 'starter' && (
                    <>
                      <p>• Perfect for testing</p>
                      <p>• Basic features</p>
                      <p>• Email support</p>
                    </>
                  )}
                  {packageId === 'professional' && (
                    <>
                      <p>• Regular business use</p>
                      <p>• All features included</p>
                      <p>• Priority support</p>
                    </>
                  )}
                  {packageId === 'enterprise' && (
                    <>
                      <p>• High volume validation</p>
                      <p>• Bulk processing</p>
                      <p>• Premium support</p>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Purchase Button */}
      <div className="text-center">
        <button
          onClick={handlePurchase}
          disabled={!selectedPackage || paymentLoading}
          className="btn-primary px-8 py-3 text-lg inline-flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <CreditCard className="h-5 w-5 mr-2" />
          {paymentLoading ? 'Processing...' : 'Purchase Credits'}
          <ArrowRight className="h-5 w-5 ml-2" />
        </button>
        
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
          Secure payment powered by Stripe • Credits added instantly
        </p>
      </div>

      {/* Transaction History */}
      {transactions.length > 0 && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Transactions
          </h2>
          
          <div className="space-y-4">
            {transactions.slice(0, 5).map((transaction) => (
              <div 
                key={transaction._id}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-white dark:bg-gray-800 rounded-lg">
                    <Package className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {transaction.package_name}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {transaction.credits_amount.toLocaleString()} credits • ${transaction.amount} USD
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500">
                      {formatDate(transaction.created_at)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(transaction.payment_status)}`}>
                    {transaction.payment_status.charAt(0).toUpperCase() + transaction.payment_status.slice(1)}
                  </span>
                </div>
              </div>
            ))}
          </div>
          
          {transactions.length > 5 && (
            <div className="text-center mt-4">
              <button
                onClick={() => window.location.href = '/dashboard'}
                className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 text-sm font-medium"
              >
                View All Transactions
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CreditTopup;