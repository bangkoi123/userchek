import React, { useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/api';
import { 
  Shield, 
  Upload, 
  Download,
  Users,
  CreditCard,
  FileText,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Plus,
  Minus,
  Settings as SettingsIcon,
  UserPlus,
  Mail
} from 'lucide-react';

const BulkUserOperations = () => {
  const { user } = useAuth();
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [importResults, setImportResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [bulkCreditData, setBulkCreditData] = useState({
    user_list: '',
    action: 'add',
    amount: 100,
    reason: ''
  });
  const [notificationData, setNotificationData] = useState({
    user_list: '',
    subject: '',
    message: '',
    type: 'info'
  });

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && (file.type === 'text/csv' || file.name.endsWith('.csv'))) {
      setSelectedFile(file);
      setImportResults(null);
    } else {
      alert('Please select a valid CSV file');
    }
  };

  const downloadTemplate = () => {
    const csvContent = `username,email,password,role,credits,is_active
john_doe,john@example.com,password123,user,1000,true
jane_smith,jane@example.com,password456,user,500,true
admin_user,admin@example.com,admin123,admin,0,true`;
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = 'bulk_users_template.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleImportUsers = async () => {
    if (!selectedFile) {
      alert('Please select a CSV file first');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/bulk-import-users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      const result = await response.json();
      setImportResults(result);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Error importing users:', error);
      setImportResults({
        success: false,
        message: 'Failed to import users',
        errors: [error.message]
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBulkCreditManagement = async () => {
    if (!bulkCreditData.user_list.trim()) {
      alert('Please enter user IDs or usernames');
      return;
    }

    if (!bulkCreditData.reason.trim()) {
      alert('Please provide a reason for the credit change');
      return;
    }

    setLoading(true);
    try {
      const userIds = bulkCreditData.user_list.split('\n').map(id => id.trim()).filter(id => id);
      
      const response = await apiCall('/api/admin/bulk-credit-management', {
        method: 'POST',
        body: JSON.stringify({
          user_ids: userIds,
          action: bulkCreditData.action,
          amount: parseInt(bulkCreditData.amount),
          reason: bulkCreditData.reason
        })
      });

      alert(`Bulk credit ${bulkCreditData.action} completed successfully for ${response.processed_users} users`);
      setBulkCreditData(prev => ({ ...prev, user_list: '' }));
    } catch (error) {
      console.error('Error in bulk credit management:', error);
      alert('Failed to process bulk credit management');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkNotification = async () => {
    if (!notificationData.user_list.trim() || !notificationData.subject.trim() || !notificationData.message.trim()) {
      alert('Please fill in all notification fields');
      return;
    }

    setLoading(true);
    try {
      const userIds = notificationData.user_list.split('\n').map(id => id.trim()).filter(id => id);
      
      const response = await apiCall('/api/admin/bulk-notification', {
        method: 'POST',
        body: JSON.stringify({
          user_ids: userIds,
          subject: notificationData.subject,
          message: notificationData.message,
          type: notificationData.type
        })
      });

      alert(`Bulk notification sent successfully to ${response.sent_count} users`);
      setNotificationData(prev => ({ ...prev, user_list: '', subject: '', message: '' }));
    } catch (error) {
      console.error('Error sending bulk notification:', error);
      alert('Failed to send bulk notification');
    } finally {
      setLoading(false);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <div className="card p-12 text-center">
        <Shield className="h-16 w-16 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Access Denied
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          You do not have permission to access bulk user operations
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-lg p-6 text-white">
        <div className="flex items-center">
          <div className="p-2 bg-white/20 rounded-lg mr-4">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Bulk User Operations</h1>
            <p className="text-green-100">
              Import users, manage credits in bulk, and send notifications
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bulk User Import */}
        <div className="card p-6">
          <div className="flex items-center mb-6">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg mr-3">
              <UserPlus className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Bulk User Import
            </h2>
          </div>

          <div className="space-y-4">
            <div className="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2" />
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  CSV Format Required
                </p>
              </div>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mb-3">
                Upload a CSV file with columns: username, email, password, role, credits, is_active
              </p>
              <button
                onClick={downloadTemplate}
                className="btn-secondary text-sm flex items-center"
              >
                <Download className="h-4 w-4 mr-2" />
                Download Template
              </button>
            </div>

            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                ref={fileInputRef}
                className="hidden"
              />
              <div className="space-y-2">
                <Upload className="h-8 w-8 text-gray-400 mx-auto" />
                <div>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Choose CSV file
                  </button>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    or drag and drop here
                  </p>
                </div>
              </div>
            </div>

            {selectedFile && (
              <div className="bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FileText className="h-5 w-5 text-green-600 dark:text-green-400 mr-2" />
                    <div>
                      <p className="text-sm font-medium text-green-800 dark:text-green-200">
                        {selectedFile.name}
                      </p>
                      <p className="text-sm text-green-600 dark:text-green-400">
                        {(selectedFile.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleImportUsers}
                    disabled={loading}
                    className="btn-primary text-sm"
                  >
                    {loading ? 'Importing...' : 'Import Users'}
                  </button>
                </div>
              </div>
            )}

            {importResults && (
              <div className={`border rounded-lg p-4 ${
                importResults.success 
                  ? 'border-green-200 dark:border-green-700 bg-green-50 dark:bg-green-900'
                  : 'border-red-200 dark:border-red-700 bg-red-50 dark:bg-red-900'
              }`}>
                <div className="flex items-center mb-2">
                  {importResults.success ? (
                    <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mr-2" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600 dark:text-red-400 mr-2" />
                  )}
                  <p className={`font-medium ${
                    importResults.success 
                      ? 'text-green-800 dark:text-green-200'
                      : 'text-red-800 dark:text-red-200'
                  }`}>
                    {importResults.message}
                  </p>
                </div>
                {importResults.imported_count && (
                  <p className="text-sm text-green-700 dark:text-green-300">
                    Successfully imported: {importResults.imported_count} users
                  </p>
                )}
                {importResults.errors && importResults.errors.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm text-red-700 dark:text-red-300 font-medium">Errors:</p>
                    <ul className="text-sm text-red-600 dark:text-red-400 list-disc list-inside">
                      {importResults.errors.slice(0, 5).map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Bulk Credit Management */}
        <div className="card p-6">
          <div className="flex items-center mb-6">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg mr-3">
              <CreditCard className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Bulk Credit Management
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                User IDs/Usernames (one per line)
              </label>
              <textarea
                value={bulkCreditData.user_list}
                onChange={(e) => setBulkCreditData(prev => ({ ...prev, user_list: e.target.value }))}
                placeholder={`user1
user2
admin
demo`}
                rows={4}
                className="input-field w-full"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Action
                </label>
                <select
                  value={bulkCreditData.action}
                  onChange={(e) => setBulkCreditData(prev => ({ ...prev, action: e.target.value }))}
                  className="input-field w-full"
                >
                  <option value="add">Add Credits</option>
                  <option value="subtract">Subtract Credits</option>
                  <option value="set">Set Credits</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Amount
                </label>
                <input
                  type="number"
                  value={bulkCreditData.amount}
                  onChange={(e) => setBulkCreditData(prev => ({ ...prev, amount: e.target.value }))}
                  min="1"
                  className="input-field w-full"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Reason (required)
              </label>
              <input
                type="text"
                value={bulkCreditData.reason}
                onChange={(e) => setBulkCreditData(prev => ({ ...prev, reason: e.target.value }))}
                placeholder="e.g., Bulk credit adjustment for promotion"
                className="input-field w-full"
              />
            </div>

            <button
              onClick={handleBulkCreditManagement}
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center"
            >
              {bulkCreditData.action === 'add' && <Plus className="h-4 w-4 mr-2" />}
              {bulkCreditData.action === 'subtract' && <Minus className="h-4 w-4 mr-2" />}
              {bulkCreditData.action === 'set' && <SettingsIcon className="h-4 w-4 mr-2" />}
              {loading ? 'Processing...' : `${bulkCreditData.action.charAt(0).toUpperCase() + bulkCreditData.action.slice(1)} Credits`}
            </button>
          </div>
        </div>
      </div>

      {/* Bulk Notification */}
      <div className="card p-6">
        <div className="flex items-center mb-6">
          <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg mr-3">
            <Mail className="h-6 w-6 text-orange-600 dark:text-orange-400" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Bulk Notification
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                User IDs/Usernames (one per line)
              </label>
              <textarea
                value={notificationData.user_list}
                onChange={(e) => setNotificationData(prev => ({ ...prev, user_list: e.target.value }))}
                placeholder={`user1
user2
demo`}
                rows={4}
                className="input-field w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Notification Type
              </label>
              <select
                value={notificationData.type}
                onChange={(e) => setNotificationData(prev => ({ ...prev, type: e.target.value }))}
                className="input-field w-full"
              >
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="success">Success</option>
                <option value="error">Error</option>
              </select>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Subject
              </label>
              <input
                type="text"
                value={notificationData.subject}
                onChange={(e) => setNotificationData(prev => ({ ...prev, subject: e.target.value }))}
                placeholder="e.g., Important System Update"
                className="input-field w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Message
              </label>
              <textarea
                value={notificationData.message}
                onChange={(e) => setNotificationData(prev => ({ ...prev, message: e.target.value }))}
                placeholder="Enter your notification message here..."
                rows={4}
                className="input-field w-full"
              />
            </div>

            <button
              onClick={handleBulkNotification}
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center"
            >
              <Mail className="h-4 w-4 mr-2" />
              {loading ? 'Sending...' : 'Send Bulk Notification'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BulkUserOperations;