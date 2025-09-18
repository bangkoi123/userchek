// EMERGENCY FIX: Temporary admin data fetcher
// Menggunakan endpoint /api/health yang confirmed working

// 1. Buat fungsi untuk fetch admin data via health endpoint
const fetchAdminDataViaHealth = async (dataType) => {
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/health?admin_data=${dataType}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.status === 'admin_data') {
      return data;
    }
    
    throw new Error('Unable to fetch admin data');
  } catch (error) {
    console.error('Admin data fetch error:', error);
    throw error;
  }
};

// 2. Override API calls di localStorage untuk emergency fix
if (typeof window !== 'undefined') {
  window.emergencyAdminFix = {
    getUsers: () => fetchAdminDataViaHealth('users'),
    getStats: () => fetchAdminDataViaHealth('stats')
  };
  
  console.log('🚨 EMERGENCY ADMIN FIX LOADED');
  console.log('Use: window.emergencyAdminFix.getUsers() or window.emergencyAdminFix.getStats()');
}

// 3. Test function
const testEmergencyFix = async () => {
  try {
    console.log('Testing emergency admin fix...');
    
    const users = await fetchAdminDataViaHealth('users');
    console.log('✅ Users data:', users);
    
    const stats = await fetchAdminDataViaHealth('stats');
    console.log('✅ Stats data:', stats);
    
  } catch (error) {
    console.error('❌ Emergency fix test failed:', error);
  }
};

// Auto-test if in browser console
if (typeof window !== 'undefined' && window.location.hostname.includes('phonecheck')) {
  setTimeout(testEmergencyFix, 2000);
}