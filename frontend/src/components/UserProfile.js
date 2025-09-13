import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { apiCall } from '../utils/api';
import { 
  User, 
  Mail, 
  Building2, 
  Edit2, 
  Save, 
  X,
  Calendar,
  CreditCard,
  Key,
  Activity,
  Shield,
  Settings
} from 'lucide-react';
import toast from 'react-hot-toast';

const UserProfile = () => {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    username: '',
    email: '',
    company_name: ''
  });
  const [saving, setSaving] = useState(false);
  const [apiKeys, setApiKeys] = useState([]);
  const [showApiKeys, setShowApiKeys] = useState(false);

  useEffect(() => {
    fetchProfile();
    fetchApiKeys();
  }, []);

  const fetchProfile = async () => {
    try {
      const data = await apiCall('/api/user/profile');
      setProfile(data);
      setEditData({
        username: data.username || '',
        email: data.email || '',
        company_name: data.company_name || ''
      });
    } catch (error) {
      console.error('Error fetching profile:', error);
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const fetchApiKeys = async () => {
    try {
      const data = await apiCall('/api/user/api-keys');
      setApiKeys(data);
    } catch (error) {
      console.error('Error fetching API keys:', error);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updates = {};
      
      // Only include changed fields
      if (editData.username !== profile.username) {
        updates.username = editData.username;
      }
      if (editData.email !== profile.email) {
        updates.email = editData.email;
      }
      if (editData.company_name !== profile.company_name) {
        updates.company_name = editData.company_name;
      }
      
      if (Object.keys(updates).length > 0) {
        const response = await apiCall('/api/user/profile', 'PUT', updates);
        setProfile({ ...profile, ...updates });
        
        // Update auth context if username or email changed
        if (updates.username || updates.email) {
          updateUser({ ...user, ...updates });
        }
        
        toast.success('Profile updated successfully');
      }
      
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
      const message = error.response?.data?.detail || 'Failed to update profile';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditData({
      username: profile.username || '',
      email: profile.email || '',
      company_name: profile.company_name || ''
    });
    setIsEditing(false);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin':
        return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900';
      case 'user':
        return 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900';
      default:
        return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 rounded-lg p-6 text-white">
        <div className="flex items-center mb-4">
          <div className="p-3 bg-white/20 rounded-full mr-4">
            <User className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">User Profile</h1>
            <p className="text-indigo-100">
              Manage your account settings and preferences
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Information */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Profile Information
              </h2>
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="btn-secondary flex items-center"
                >
                  <Edit2 className="h-4 w-4 mr-2" />
                  Edit Profile
                </button>
              ) : (
                <div className="flex space-x-2">
                  <button
                    onClick={handleCancel}
                    className="btn-secondary flex items-center"
                    disabled={saving}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    className="btn-primary flex items-center"
                    disabled={saving}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                </div>
              )}
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <User className="h-4 w-4 inline mr-2" />
                    Username
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editData.username}
                      onChange={(e) => setEditData({ ...editData, username: e.target.value })}
                      className="input-field"
                      placeholder="Enter username"
                    />
                  ) : (
                    <p className="text-gray-900 dark:text-white p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      {profile?.username || 'Not set'}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <Mail className="h-4 w-4 inline mr-2" />
                    Email Address
                  </label>
                  {isEditing ? (
                    <input
                      type="email"
                      value={editData.email}
                      onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                      className="input-field"
                      placeholder="Enter email address"
                    />
                  ) : (
                    <p className="text-gray-900 dark:text-white p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      {profile?.email || 'Not set'}
                    </p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Building2 className="h-4 w-4 inline mr-2" />
                  Company Name
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editData.company_name}
                    onChange={(e) => setEditData({ ...editData, company_name: e.target.value })}
                    className="input-field"
                    placeholder="Enter company name (optional)"
                  />
                ) : (
                  <p className="text-gray-900 dark:text-white p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    {profile?.company_name || 'Not specified'}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* API Keys Section */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                API Keys
              </h2>
              <button
                onClick={() => setShowApiKeys(!showApiKeys)}
                className="btn-secondary flex items-center"
              >
                <Key className="h-4 w-4 mr-2" />
                {showApiKeys ? 'Hide' : 'Show'} API Keys
              </button>
            </div>

            {showApiKeys && (
              <div className="space-y-4">
                {apiKeys.length > 0 ? (
                  <div className="space-y-3">
                    {apiKeys.map((apiKey) => (
                      <div key={apiKey.id} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium text-gray-900 dark:text-white">
                              {apiKey.name}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {apiKey.key_preview}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-500">
                              Created: {formatDate(apiKey.created_at)}
                            </p>
                          </div>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            apiKey.is_active 
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          }`}>
                            {apiKey.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Key className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">No API keys found</p>
                    <p className="text-sm text-gray-500 dark:text-gray-500">
                      API keys can be managed by administrators
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Account Stats Sidebar */}
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Account Status
            </h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Role</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleColor(profile?.role)}`}>
                  {profile?.role?.charAt(0).toUpperCase() + profile?.role?.slice(1)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Status</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  profile?.is_active 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}>
                  {profile?.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Member Since</span>
                <span className="text-sm text-gray-900 dark:text-white">
                  {profile?.created_at ? new Date(profile.created_at).toLocaleDateString('id-ID', {
                    year: 'numeric',
                    month: 'short'
                  }) : 'Unknown'}
                </span>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Credit Balance
            </h2>
            
            <div className="text-center">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg mb-4">
                <CreditCard className="h-8 w-8 text-green-600 dark:text-green-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {profile?.credits?.toLocaleString() || 0}
                </p>
                <p className="text-sm text-green-600 dark:text-green-400">
                  Available Credits
                </p>
              </div>
              
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                <p>≈ {Math.floor((profile?.credits || 0) / 2).toLocaleString()} validations remaining</p>
                <p className="text-xs mt-1">2 credits per validation</p>
              </div>
              
              <button
                onClick={() => navigate('/credit-topup')}
                className="btn-primary w-full"
              >
                Top Up Credits
              </button>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Activity className="h-5 w-5 mr-2" />
              Quick Stats
            </h2>
            
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Total Validations</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {profile?.total_validations || 0}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Credits Used</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {profile?.total_credits_used || 0}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Last Login</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {profile?.last_login ? formatDate(profile.last_login) : 'Never'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;