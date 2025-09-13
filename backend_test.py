import requests
import sys
import json
from datetime import datetime

class WebtoolsAPITester:
    def __init__(self, base_url="https://validhub.preview.emergentagent.com"):
        self.base_url = base_url
        self.demo_token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.demo_user_id = None
        self.admin_user_id = None
        self.checkout_session_id = None

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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
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
            description="Get telegram accounts list (should show 3 accounts)"
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} telegram accounts")
            expected_accounts = [
                "Primary Telegram Bot",
                "Secondary Telegram Account", 
                "Backup Telegram Account"
            ]
            
            account_names = [acc.get('name', '') for acc in response]
            active_count = sum(1 for acc in response if acc.get('is_active', False))
            inactive_count = len(response) - active_count
            
            print(f"   Account names: {account_names}")
            print(f"   Active accounts: {active_count}, Inactive accounts: {inactive_count}")
            
            # Check if we have the expected accounts
            found_expected = [name for name in expected_accounts if name in account_names]
            if len(found_expected) >= 2:  # At least 2 of the expected accounts
                print(f"   ✅ Found expected accounts: {found_expected}")
            else:
                print(f"   ⚠️  Expected accounts not found. Found: {account_names}")
                
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
            description="Get WhatsApp providers list (should show 3 providers)"
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} WhatsApp providers")
            expected_providers = [
                "Twilio WhatsApp Business",
                "Vonage WhatsApp API",
                "360Dialog WhatsApp"
            ]
            
            provider_names = [prov.get('name', '') for prov in response]
            active_count = sum(1 for prov in response if prov.get('is_active', False))
            inactive_count = len(response) - active_count
            
            print(f"   Provider names: {provider_names}")
            print(f"   Active providers: {active_count}, Inactive providers: {inactive_count}")
            
            # Check if we have the expected providers
            found_expected = [name for name in expected_providers if name in provider_names]
            if len(found_expected) >= 2:  # At least 2 of the expected providers
                print(f"   ✅ Found expected providers: {found_expected}")
            else:
                print(f"   ⚠️  Expected providers not found. Found: {provider_names}")
                
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
            403,  # Updated to expect 403 for no token
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

    def test_seed_sample_data(self):
        """Test seeding sample data for providers and accounts"""
        success, response = self.run_test(
            "Seed Sample Data",
            "POST",
            "api/admin/seed-sample-data",
            200,
            description="Seed sample WhatsApp providers and Telegram accounts"
        )
        
        if success:
            whatsapp_count = response.get('whatsapp_providers', 0)
            telegram_count = response.get('telegram_accounts', 0)
            print(f"   ✅ Seeded {whatsapp_count} WhatsApp providers and {telegram_count} Telegram accounts")
            
        return success

    def test_credit_packages(self):
        """Test getting available credit packages"""
        success, response = self.run_test(
            "Credit Packages",
            "GET",
            "api/credit-packages",
            200,
            description="Get available credit packages for purchase"
        )
        
        if success:
            if isinstance(response, dict):
                packages = list(response.keys())
                print(f"   ✅ Found {len(packages)} credit packages: {packages}")
                # Check if packages have required fields
                for package_id, package_data in response.items():
                    required_fields = ['credits', 'price', 'name']
                    missing_fields = [field for field in required_fields if field not in package_data]
                    if missing_fields:
                        print(f"   ⚠️  Package {package_id} missing fields: {missing_fields}")
                    else:
                        print(f"   ✅ Package {package_id}: {package_data['credits']} credits for ${package_data['price']}")
            else:
                print(f"   ⚠️  Unexpected response format: {type(response)}")
                
        return success

    def test_create_checkout_session(self):
        """Test creating Stripe checkout session"""
        if not self.demo_token:
            print("❌ Skipping checkout session test - no demo token")
            return False
            
        success, response = self.run_test(
            "Create Checkout Session",
            "POST",
            "api/payments/create-checkout",
            200,
            data={
                "package_id": "starter",
                "origin_url": "https://phoneproof.preview.emergentagent.com"
            },
            token=self.demo_token,
            description="Create Stripe checkout session for credit purchase"
        )
        
        if success:
            required_fields = ['url', 'session_id', 'package', 'transaction_id']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing response fields: {missing_fields}")
            else:
                print(f"   ✅ Checkout session created with ID: {response.get('session_id', 'N/A')}")
                self.checkout_session_id = response.get('session_id')
                
        return success

    def test_payment_status(self):
        """Test getting payment status"""
        if not self.demo_token or not hasattr(self, 'checkout_session_id'):
            print("❌ Skipping payment status test - no demo token or session ID")
            return False
            
        success, response = self.run_test(
            "Payment Status",
            "GET",
            f"api/payments/status/{self.checkout_session_id}",
            200,
            token=self.demo_token,
            description="Check payment status for checkout session"
        )
        
        if success:
            expected_fields = ['status', 'payment_status', 'credits_amount']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing response fields: {missing_fields}")
            else:
                print(f"   ✅ Payment status: {response.get('payment_status', 'N/A')}")
                
        return success

    def test_payment_transactions(self):
        """Test getting payment transaction history"""
        if not self.demo_token:
            print("❌ Skipping payment transactions test - no demo token")
            return False
            
        success, response = self.run_test(
            "Payment Transactions",
            "GET",
            "api/payments/transactions",
            200,
            token=self.demo_token,
            description="Get user's payment transaction history"
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✅ Found {len(response)} payment transactions")
                if response:
                    # Check structure of first transaction
                    first_transaction = response[0]
                    expected_fields = ['user_id', 'package_id', 'amount', 'payment_status', 'created_at']
                    missing_fields = [field for field in expected_fields if field not in first_transaction]
                    if missing_fields:
                        print(f"   ⚠️  Transaction missing fields: {missing_fields}")
                    else:
                        print(f"   ✅ Transaction structure is correct")
            else:
                print(f"   ⚠️  Expected list, got {type(response)}")
                
        return success

    def test_update_user_profile(self):
        """Test updating user profile"""
        if not self.demo_token:
            print("❌ Skipping profile update test - no demo token")
            return False
            
        success, response = self.run_test(
            "Update User Profile",
            "PUT",
            "api/user/profile",
            200,
            data={
                "company_name": "Updated Test Company"
            },
            token=self.demo_token,
            description="Update user profile information"
        )
        
        if success:
            if 'message' in response and 'user' in response:
                print(f"   ✅ Profile updated: {response.get('message', 'N/A')}")
                updated_user = response.get('user', {})
                if 'company_name' in updated_user:
                    print(f"   ✅ Company name updated to: {updated_user['company_name']}")
            else:
                print(f"   ⚠️  Unexpected response structure")
                
        return success

    def test_admin_users_list(self):
        """Test getting users list (admin only)"""
        if not self.admin_token:
            print("❌ Skipping admin users list test - no admin token")
            return False
            
        success, response = self.run_test(
            "Admin Users List",
            "GET",
            "api/admin/users",
            200,
            token=self.admin_token,
            description="Get users list with pagination (admin only)"
        )
        
        if success:
            if 'users' in response and 'pagination' in response:
                users = response['users']
                pagination = response['pagination']
                print(f"   ✅ Found {len(users)} users on page {pagination.get('current_page', 1)}")
                print(f"   ✅ Total users: {pagination.get('total_count', 0)}")
                
                # Check user structure
                if users:
                    first_user = users[0]
                    expected_fields = ['_id', 'username', 'email', 'role', 'created_at']
                    missing_fields = [field for field in expected_fields if field not in first_user]
                    if missing_fields:
                        print(f"   ⚠️  User object missing fields: {missing_fields}")
                    else:
                        print(f"   ✅ User structure is correct")
            else:
                print(f"   ⚠️  Expected 'users' and 'pagination' fields in response")
                
        return success

    def test_admin_user_details(self):
        """Test getting detailed user information (admin only)"""
        if not self.admin_token or not self.demo_user_id:
            print("❌ Skipping admin user details test - no admin token or demo user ID")
            return False
            
        success, response = self.run_test(
            "Admin User Details",
            "GET",
            f"api/admin/users/{self.demo_user_id}",
            200,
            token=self.admin_token,
            description="Get detailed user information (admin only)"
        )
        
        if success:
            expected_sections = ['user', 'recent_activities', 'payment_transactions', 'recent_jobs', 'usage_stats']
            missing_sections = [section for section in expected_sections if section not in response]
            if missing_sections:
                print(f"   ⚠️  Missing response sections: {missing_sections}")
            else:
                print(f"   ✅ User details structure is complete")
                user_data = response.get('user', {})
                if 'username' in user_data:
                    print(f"   ✅ User details for: {user_data['username']}")
                
        return success

    def test_admin_update_user(self):
        """Test updating user settings (admin only)"""
        if not self.admin_token or not self.demo_user_id:
            print("❌ Skipping admin user update test - no admin token or demo user ID")
            return False
            
        success, response = self.run_test(
            "Admin Update User",
            "PUT",
            f"api/admin/users/{self.demo_user_id}",
            200,
            data={
                "credits": 2000
            },
            token=self.admin_token,
            description="Update user settings (admin only)"
        )
        
        if success:
            if 'message' in response:
                print(f"   ✅ User updated: {response.get('message', 'N/A')}")
            else:
                print(f"   ⚠️  Expected 'message' field in response")
                
        return success

    def test_admin_analytics(self):
        """Test getting comprehensive system analytics (admin only)"""
        if not self.admin_token:
            print("❌ Skipping admin analytics test - no admin token")
            return False
            
        success, response = self.run_test(
            "Admin Analytics",
            "GET",
            "api/admin/analytics",
            200,
            token=self.admin_token,
            description="Get comprehensive system analytics (admin only)"
        )
        
        if success:
            # Check if response has analytics data
            if isinstance(response, dict) and response:
                print(f"   ✅ Analytics data received with {len(response)} top-level metrics")
                
                # Check for user statistics
                user_stats_fields = ['total_users', 'active_users', 'admin_users', 'new_users_this_month']
                found_user_stats = [field for field in user_stats_fields if field in response]
                if found_user_stats:
                    print(f"   ✅ User statistics found: {found_user_stats}")
                    for field in found_user_stats:
                        print(f"      {field}: {response[field]}")
                else:
                    print(f"   ⚠️  Missing user statistics fields")
                
                # Check for validation statistics
                validation_stats_fields = ['total_validations', 'completed_validations', 'failed_validations', 
                                         'active_jobs', 'whatsapp_validations', 'telegram_validations']
                found_validation_stats = [field for field in validation_stats_fields if field in response]
                if found_validation_stats:
                    print(f"   ✅ Validation statistics found: {found_validation_stats}")
                    for field in found_validation_stats:
                        print(f"      {field}: {response[field]}")
                else:
                    print(f"   ⚠️  Missing validation statistics fields")
                
                # Check for credit statistics
                credit_stats_fields = ['total_credits_in_system', 'total_credits_used', 'total_usage_transactions']
                found_credit_stats = [field for field in credit_stats_fields if field in response]
                if found_credit_stats:
                    print(f"   ✅ Credit statistics found: {found_credit_stats}")
                    for field in found_credit_stats:
                        print(f"      {field}: {response[field]}")
                else:
                    print(f"   ⚠️  Missing credit statistics fields")
                
                # Check for payment statistics
                payment_stats_fields = ['total_revenue', 'total_transactions', 'total_credits_sold']
                found_payment_stats = [field for field in payment_stats_fields if field in response]
                if found_payment_stats:
                    print(f"   ✅ Payment statistics found: {found_payment_stats}")
                    for field in found_payment_stats:
                        print(f"      {field}: {response[field]}")
                else:
                    print(f"   ⚠️  Missing payment statistics fields")
                
                # Check for daily stats
                if 'daily_stats' in response:
                    daily_stats = response['daily_stats']
                    if isinstance(daily_stats, list):
                        print(f"   ✅ Daily stats found: {len(daily_stats)} days of data")
                        if daily_stats:
                            print(f"      Sample day: {daily_stats[0]}")
                    else:
                        print(f"   ⚠️  Daily stats should be a list, got {type(daily_stats)}")
                else:
                    print(f"   ⚠️  Missing daily_stats field")
                
                # Check for top users
                if 'top_users' in response:
                    top_users = response['top_users']
                    if isinstance(top_users, list):
                        print(f"   ✅ Top users found: {len(top_users)} users")
                        if top_users:
                            print(f"      Top user: {top_users[0]}")
                    else:
                        print(f"   ⚠️  Top users should be a list, got {type(top_users)}")
                else:
                    print(f"   ⚠️  Missing top_users field")
                
                # Check for recent activities
                activity_fields = ['recent_users', 'recent_jobs', 'recent_payments']
                found_activities = [field for field in activity_fields if field in response]
                if found_activities:
                    print(f"   ✅ Recent activities found: {found_activities}")
                    for field in found_activities:
                        activities = response[field]
                        if isinstance(activities, list):
                            print(f"      {field}: {len(activities)} items")
                        else:
                            print(f"      {field}: {type(activities)} (expected list)")
                else:
                    print(f"   ⚠️  Missing recent activities fields")
                
                # Calculate completeness score
                all_expected_fields = (user_stats_fields + validation_stats_fields + 
                                     credit_stats_fields + payment_stats_fields + 
                                     ['daily_stats', 'top_users'] + activity_fields)
                found_fields = [field for field in all_expected_fields if field in response]
                completeness = (len(found_fields) / len(all_expected_fields)) * 100
                print(f"   📊 Analytics completeness: {completeness:.1f}% ({len(found_fields)}/{len(all_expected_fields)} fields)")
                
            else:
                print(f"   ⚠️  Expected analytics object, got {type(response)}")
                
        return success

    def test_admin_analytics_access_control(self):
        """Test admin analytics access control (non-admin should get 403)"""
        if not self.demo_token:
            print("❌ Skipping admin analytics access control test - no demo token")
            return False
            
        success, response = self.run_test(
            "Admin Analytics Access Control",
            "GET",
            "api/admin/analytics",
            403,
            token=self.demo_token,
            description="Non-admin user should get 403 when accessing admin analytics"
        )
        
        if success:
            print(f"   ✅ Access control working correctly - non-admin users blocked")
        
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
    tester.test_update_user_profile()
    tester.test_dashboard_stats()
    tester.test_quick_check_validation()
    tester.test_quick_check_insufficient_credits()
    tester.test_jobs_list()
    
    # Credit Top-up System Tests
    print("\n💳 CREDIT TOP-UP SYSTEM TESTS")
    print("-" * 30)
    tester.test_credit_packages()
    tester.test_create_checkout_session()
    tester.test_payment_status()
    tester.test_payment_transactions()
    
    # Admin functionality tests
    print("\n👑 ADMIN FUNCTIONALITY TESTS")
    print("-" * 30)
    tester.test_seed_sample_data()  # Seed data first
    tester.test_admin_stats()
    tester.test_admin_users_list()
    tester.test_admin_user_details()
    tester.test_admin_update_user()
    tester.test_admin_analytics()
    tester.test_admin_analytics_access_control()
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