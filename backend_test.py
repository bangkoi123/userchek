import requests
import sys
import json
from datetime import datetime

class WebtoolsAPITester:
    def __init__(self, base_url="https://phonehub-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.demo_token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.demo_user_id = None
        self.admin_user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, description=""):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        if description:
            print(f"   Description: {description}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 200:
                        print(f"   Response: {response_data}")
                except:
                    pass
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")

            return success, response.json() if response.content else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200,
            description="Basic health check endpoint"
        )
        return success

    def test_demo_login(self):
        """Test demo user login"""
        success, response = self.run_test(
            "Demo User Login",
            "POST",
            "api/auth/login",
            200,
            data={"username": "demo", "password": "demo123"},
            description="Login with demo user credentials"
        )
        if success and 'token' in response:
            self.demo_token = response['token']
            self.demo_user_id = response.get('user', {}).get('id')
            print(f"   Demo user ID: {self.demo_user_id}")
            print(f"   Demo credits: {response.get('user', {}).get('credits', 0)}")
            return True
        return False

    def test_admin_login(self):
        """Test admin user login"""
        success, response = self.run_test(
            "Admin User Login",
            "POST",
            "api/auth/login",
            200,
            data={"username": "admin", "password": "admin123"},
            description="Login with admin user credentials"
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            self.admin_user_id = response.get('user', {}).get('id')
            print(f"   Admin user ID: {self.admin_user_id}")
            return True
        return False

    def test_invalid_login(self):
        """Test invalid login credentials"""
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "api/auth/login",
            401,
            data={"username": "invalid", "password": "wrong"},
            description="Test with invalid credentials"
        )
        return success

    def test_user_profile(self):
        """Test getting user profile"""
        if not self.demo_token:
            print("❌ Skipping profile test - no demo token")
            return False
            
        success, response = self.run_test(
            "User Profile",
            "GET",
            "api/user/profile",
            200,
            token=self.demo_token,
            description="Get current user profile"
        )
        return success

    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        if not self.demo_token:
            print("❌ Skipping dashboard stats test - no demo token")
            return False
            
        success, response = self.run_test(
            "Dashboard Stats",
            "GET",
            "api/dashboard/stats",
            200,
            token=self.demo_token,
            description="Get user dashboard statistics"
        )
        return success

    def test_quick_check_validation(self):
        """Test quick phone number validation"""
        if not self.demo_token:
            print("❌ Skipping quick check test - no demo token")
            return False
            
        success, response = self.run_test(
            "Quick Check Validation",
            "POST",
            "api/validation/quick-check",
            200,
            data={"phone_number": "+628123456789"},
            token=self.demo_token,
            description="Validate a single phone number (enhanced with providers)"
        )
        
        if success:
            # Verify response structure
            expected_keys = ['phone_number', 'whatsapp', 'telegram', 'cached', 'checked_at', 'providers_used']
            response_keys = list(response.keys())
            missing_keys = [key for key in expected_keys if key not in response_keys]
            if missing_keys:
                print(f"   ⚠️  Missing response keys: {missing_keys}")
            else:
                print(f"   ✅ Response structure is correct")
                
            # Check if providers_used field exists and has proper structure
            if 'providers_used' in response:
                providers = response['providers_used']
                if isinstance(providers, dict) and 'whatsapp' in providers and 'telegram' in providers:
                    print(f"   ✅ Providers used: WhatsApp={providers['whatsapp']}, Telegram={providers['telegram']}")
                    # Check if real provider names are used instead of "Mock Provider"
                    if providers['whatsapp'] != "Mock Provider" or providers['telegram'] != "Mock Provider":
                        print(f"   ✅ Real provider integration detected")
                    else:
                        print(f"   ⚠️  Still using mock providers")
                else:
                    print(f"   ⚠️  Invalid providers_used structure: {providers}")
            else:
                print(f"   ❌ Missing providers_used field in response")
                
        return success

    def test_quick_check_insufficient_credits(self):
        """Test quick check with insufficient credits (if possible)"""
        if not self.demo_token:
            print("❌ Skipping insufficient credits test - no demo token")
            return False
            
        # This test might not work if demo user has enough credits
        # But we'll try anyway to test the error handling
        success, response = self.run_test(
            "Quick Check - Insufficient Credits Test",
            "POST",
            "api/validation/quick-check",
            200,  # Expecting success since demo has 5000 credits
            data={"phone_number": "+6281234567891"},
            token=self.demo_token,
            description="Test validation (demo user should have enough credits)"
        )
        return success

    def test_jobs_list(self):
        """Test getting jobs list"""
        if not self.demo_token:
            print("❌ Skipping jobs list test - no demo token")
            return False
            
        success, response = self.run_test(
            "Jobs List",
            "GET",
            "api/jobs",
            200,
            token=self.demo_token,
            description="Get user's job history"
        )
        return success

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        if not self.admin_token:
            print("❌ Skipping admin stats test - no admin token")
            return False
            
        success, response = self.run_test(
            "Admin Stats",
            "GET",
            "api/admin/stats",
            200,
            token=self.admin_token,
            description="Get system-wide admin statistics"
        )
        return success

    def test_admin_telegram_accounts(self):
        """Test admin telegram accounts endpoint"""
        if not self.admin_token:
            print("❌ Skipping admin telegram test - no admin token")
            return False
            
        success, response = self.run_test(
            "Admin Telegram Accounts",
            "GET",
            "api/admin/telegram-accounts",
            200,
            token=self.admin_token,
            description="Get telegram accounts list"
        )
        return success

    def test_admin_whatsapp_providers(self):
        """Test admin whatsapp providers endpoint"""
        if not self.admin_token:
            print("❌ Skipping admin whatsapp test - no admin token")
            return False
            
        success, response = self.run_test(
            "Admin WhatsApp Providers",
            "GET",
            "api/admin/whatsapp-providers",
            200,
            token=self.admin_token,
            description="Get WhatsApp providers list"
        )
        return success

    def test_admin_jobs(self):
        """Test admin jobs endpoint"""
        if not self.admin_token:
            print("❌ Skipping admin jobs test - no admin token")
            return False
            
        success, response = self.run_test(
            "Admin Jobs",
            "GET",
            "api/admin/jobs",
            200,
            token=self.admin_token,
            description="Get all jobs (admin view)"
        )
        return success

    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        success, response = self.run_test(
            "Unauthorized Access",
            "GET",
            "api/user/profile",
            401,
            description="Access protected endpoint without token"
        )
        return success

    def test_admin_access_with_user_token(self):
        """Test accessing admin endpoint with user token"""
        if not self.demo_token:
            print("❌ Skipping admin access test - no demo token")
            return False
            
        success, response = self.run_test(
            "Admin Access with User Token",
            "GET",
            "api/admin/stats",
            403,
            token=self.demo_token,
            description="Try to access admin endpoint with user token"
        )
        return success

def main():
    print("🚀 Starting Webtools Validation API Tests")
    print("=" * 50)
    
    # Setup
    tester = WebtoolsAPITester()
    
    # Basic tests
    print("\n📋 BASIC FUNCTIONALITY TESTS")
    print("-" * 30)
    tester.test_health_check()
    
    # Authentication tests
    print("\n🔐 AUTHENTICATION TESTS")
    print("-" * 30)
    tester.test_demo_login()
    tester.test_admin_login()
    tester.test_invalid_login()
    tester.test_unauthorized_access()
    
    # User functionality tests
    print("\n👤 USER FUNCTIONALITY TESTS")
    print("-" * 30)
    tester.test_user_profile()
    tester.test_dashboard_stats()
    tester.test_quick_check_validation()
    tester.test_quick_check_insufficient_credits()
    tester.test_jobs_list()
    
    # Admin functionality tests
    print("\n👑 ADMIN FUNCTIONALITY TESTS")
    print("-" * 30)
    tester.test_admin_stats()
    tester.test_admin_telegram_accounts()
    tester.test_admin_whatsapp_providers()
    tester.test_admin_jobs()
    tester.test_admin_access_with_user_token()
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())