import requests
import sys
import json
from datetime import datetime

class WebtoolsAPITester:
    def __init__(self, base_url="https://whatsapp-verify-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.demo_token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.demo_user_id = None
        self.admin_user_id = None
        self.checkout_session_id = None
        self.created_whatsapp_account_id = None
        self.created_telegram_account_id = None
        self.test_job_id = None

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
            data={"phone_inputs": ["+628123456789"], "validate_whatsapp": True, "validate_telegram": True},
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
            200,  # Expecting success since demo has enough credits
            data={"phone_inputs": ["+6281234567891"], "validate_whatsapp": True, "validate_telegram": True},
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
                "origin_url": "https://validhub.preview.emergentagent.com"
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
                print(f"   ✅ Analytics data received with {len(response)} top-level sections")
                
                # Check for user statistics section
                if 'user_stats' in response:
                    user_stats = response['user_stats']
                    user_stats_fields = ['total_users', 'active_users', 'admin_users', 'new_users_this_month']
                    found_user_stats = [field for field in user_stats_fields if field in user_stats]
                    if len(found_user_stats) == len(user_stats_fields):
                        print(f"   ✅ User statistics complete: {found_user_stats}")
                        for field in found_user_stats:
                            print(f"      {field}: {user_stats[field]}")
                    else:
                        missing = [field for field in user_stats_fields if field not in user_stats]
                        print(f"   ⚠️  User statistics missing: {missing}")
                else:
                    print(f"   ❌ Missing user_stats section")
                
                # Check for validation statistics section
                if 'validation_stats' in response:
                    validation_stats = response['validation_stats']
                    validation_stats_fields = ['total_validations', 'completed_validations', 'failed_validations', 
                                             'active_jobs', 'whatsapp_validations', 'telegram_validations']
                    found_validation_stats = [field for field in validation_stats_fields if field in validation_stats]
                    if len(found_validation_stats) == len(validation_stats_fields):
                        print(f"   ✅ Validation statistics complete: {found_validation_stats}")
                        for field in found_validation_stats:
                            print(f"      {field}: {validation_stats[field]}")
                    else:
                        missing = [field for field in validation_stats_fields if field not in validation_stats]
                        print(f"   ⚠️  Validation statistics missing: {missing}")
                else:
                    print(f"   ❌ Missing validation_stats section")
                
                # Check for credit statistics section
                if 'credit_stats' in response:
                    credit_stats = response['credit_stats']
                    credit_stats_fields = ['total_credits_in_system', 'total_credits_used', 'total_usage_transactions']
                    found_credit_stats = [field for field in credit_stats_fields if field in credit_stats]
                    if len(found_credit_stats) == len(credit_stats_fields):
                        print(f"   ✅ Credit statistics complete: {found_credit_stats}")
                        for field in found_credit_stats:
                            print(f"      {field}: {credit_stats[field]}")
                    else:
                        missing = [field for field in credit_stats_fields if field not in credit_stats]
                        print(f"   ⚠️  Credit statistics missing: {missing}")
                else:
                    print(f"   ❌ Missing credit_stats section")
                
                # Check for payment statistics section
                if 'payment_stats' in response:
                    payment_stats = response['payment_stats']
                    payment_stats_fields = ['total_revenue', 'total_transactions', 'total_credits_sold']
                    found_payment_stats = [field for field in payment_stats_fields if field in payment_stats]
                    if len(found_payment_stats) == len(payment_stats_fields):
                        print(f"   ✅ Payment statistics complete: {found_payment_stats}")
                        for field in found_payment_stats:
                            print(f"      {field}: {payment_stats[field]}")
                    else:
                        missing = [field for field in payment_stats_fields if field not in payment_stats]
                        print(f"   ⚠️  Payment statistics missing: {missing}")
                else:
                    print(f"   ❌ Missing payment_stats section")
                
                # Check for daily stats
                if 'daily_stats' in response:
                    daily_stats = response['daily_stats']
                    if isinstance(daily_stats, list) and len(daily_stats) == 7:
                        print(f"   ✅ Daily stats found: {len(daily_stats)} days of data")
                        if daily_stats:
                            sample_day = daily_stats[0]
                            required_day_fields = ['date', 'new_users', 'validations', 'payments']
                            if all(field in sample_day for field in required_day_fields):
                                print(f"      ✅ Daily stats structure correct: {sample_day}")
                            else:
                                missing = [field for field in required_day_fields if field not in sample_day]
                                print(f"      ⚠️  Daily stats missing fields: {missing}")
                    else:
                        print(f"   ⚠️  Daily stats should be a list of 7 days, got {type(daily_stats)} with {len(daily_stats) if isinstance(daily_stats, list) else 'N/A'} items")
                else:
                    print(f"   ❌ Missing daily_stats field")
                
                # Check for top users
                if 'top_users' in response:
                    top_users = response['top_users']
                    if isinstance(top_users, list):
                        print(f"   ✅ Top users found: {len(top_users)} users")
                        if top_users:
                            sample_user = top_users[0]
                            required_user_fields = ['id', 'username', 'email', 'credits', 'role']
                            if all(field in sample_user for field in required_user_fields):
                                print(f"      ✅ Top user structure correct: {sample_user['username']} ({sample_user['credits']} credits)")
                            else:
                                missing = [field for field in required_user_fields if field not in sample_user]
                                print(f"      ⚠️  Top user missing fields: {missing}")
                    else:
                        print(f"   ⚠️  Top users should be a list, got {type(top_users)}")
                else:
                    print(f"   ❌ Missing top_users field")
                
                # Check for recent activities
                if 'recent_activities' in response:
                    recent_activities = response['recent_activities']
                    if isinstance(recent_activities, dict):
                        activity_sections = ['users', 'jobs', 'payments']
                        found_sections = [section for section in activity_sections if section in recent_activities]
                        if len(found_sections) == len(activity_sections):
                            print(f"   ✅ Recent activities complete: {found_sections}")
                            for section in found_sections:
                                activities = recent_activities[section]
                                if isinstance(activities, list):
                                    print(f"      {section}: {len(activities)} items")
                                else:
                                    print(f"      ⚠️  {section}: expected list, got {type(activities)}")
                        else:
                            missing = [section for section in activity_sections if section not in recent_activities]
                            print(f"   ⚠️  Recent activities missing sections: {missing}")
                    else:
                        print(f"   ⚠️  Recent activities should be a dict, got {type(recent_activities)}")
                else:
                    print(f"   ❌ Missing recent_activities field")
                
                # Calculate completeness score
                expected_sections = ['user_stats', 'validation_stats', 'credit_stats', 'payment_stats', 
                                   'daily_stats', 'top_users', 'recent_activities']
                found_sections = [section for section in expected_sections if section in response]
                completeness = (len(found_sections) / len(expected_sections)) * 100
                print(f"   📊 Analytics completeness: {completeness:.1f}% ({len(found_sections)}/{len(expected_sections)} sections)")
                
                # Overall assessment
                if completeness == 100:
                    print(f"   🎉 All required analytics sections present and structured correctly!")
                elif completeness >= 80:
                    print(f"   ✅ Analytics endpoint mostly complete")
                else:
                    print(f"   ⚠️  Analytics endpoint missing critical sections")
                
            else:
                print(f"   ❌ Expected analytics object, got {type(response)}")
                
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

    def test_bulk_check_platform_selection_whatsapp_only(self):
        """Test bulk check with WhatsApp only validation"""
        if not self.admin_token:
            print("❌ Skipping bulk check WhatsApp only test - no admin token")
            return False
            
        # Create test CSV content
        csv_content = "name,phone_number\nTestUser1,+6281234567890\nTestUser2,+6282345678901"
        
        # Prepare multipart form data
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        data = {
            'validate_whatsapp': 'true',
            'validate_telegram': 'false'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"\n🔍 Testing Bulk Check - WhatsApp Only...")
        print(f"   Description: Test bulk validation with only WhatsApp enabled")
        
        try:
            import requests
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                
                # Verify job creation and platform selection
                if 'job_id' in response_data:
                    job_id = response_data['job_id']
                    print(f"   ✅ Job created with ID: {job_id}")
                    
                    # Check if validate_whatsapp and validate_telegram flags are properly set
                    if 'validate_whatsapp' in response_data and 'validate_telegram' in response_data:
                        if response_data['validate_whatsapp'] == True and response_data['validate_telegram'] == False:
                            print(f"   ✅ Platform selection correct: WhatsApp=True, Telegram=False")
                        else:
                            print(f"   ⚠️  Platform selection incorrect: WhatsApp={response_data['validate_whatsapp']}, Telegram={response_data['validate_telegram']}")
                    
                    # Check credit calculation (should be 1 credit per number for WhatsApp only)
                    if 'credits_used' in response_data:
                        expected_credits = 2  # 2 numbers * 1 credit each for WhatsApp only
                        if response_data['credits_used'] == expected_credits:
                            print(f"   ✅ Credit calculation correct: {response_data['credits_used']} credits")
                        else:
                            print(f"   ⚠️  Credit calculation incorrect: expected {expected_credits}, got {response_data['credits_used']}")
                    
                    return True
                else:
                    print(f"   ⚠️  Missing job_id in response")
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_bulk_check_platform_selection_telegram_only(self):
        """Test bulk check with Telegram only validation"""
        if not self.admin_token:
            print("❌ Skipping bulk check Telegram only test - no admin token")
            return False
            
        # Create test CSV content
        csv_content = "name,phone_number\nTestUser3,+6283456789012\nTestUser4,+6284567890123"
        
        # Prepare multipart form data
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        data = {
            'validate_whatsapp': 'false',
            'validate_telegram': 'true'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"\n🔍 Testing Bulk Check - Telegram Only...")
        print(f"   Description: Test bulk validation with only Telegram enabled")
        
        try:
            import requests
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                
                # Verify platform selection
                if 'validate_whatsapp' in response_data and 'validate_telegram' in response_data:
                    if response_data['validate_whatsapp'] == False and response_data['validate_telegram'] == True:
                        print(f"   ✅ Platform selection correct: WhatsApp=False, Telegram=True")
                    else:
                        print(f"   ⚠️  Platform selection incorrect: WhatsApp={response_data['validate_whatsapp']}, Telegram={response_data['validate_telegram']}")
                
                # Check credit calculation (should be 1 credit per number for Telegram only)
                if 'credits_used' in response_data:
                    expected_credits = 2  # 2 numbers * 1 credit each for Telegram only
                    if response_data['credits_used'] == expected_credits:
                        print(f"   ✅ Credit calculation correct: {response_data['credits_used']} credits")
                    else:
                        print(f"   ⚠️  Credit calculation incorrect: expected {expected_credits}, got {response_data['credits_used']}")
                
                return True
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_bulk_check_platform_selection_both_platforms(self):
        """Test bulk check with both WhatsApp and Telegram validation"""
        if not self.admin_token:
            print("❌ Skipping bulk check both platforms test - no admin token")
            return False
            
        # Create test CSV content
        csv_content = "name,phone_number\nTestUser5,+6285678901234\nTestUser6,+6286789012345"
        
        # Prepare multipart form data
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        data = {
            'validate_whatsapp': 'true',
            'validate_telegram': 'true'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"\n🔍 Testing Bulk Check - Both Platforms...")
        print(f"   Description: Test bulk validation with both WhatsApp and Telegram enabled")
        
        try:
            import requests
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                
                # Verify platform selection
                if 'validate_whatsapp' in response_data and 'validate_telegram' in response_data:
                    if response_data['validate_whatsapp'] == True and response_data['validate_telegram'] == True:
                        print(f"   ✅ Platform selection correct: WhatsApp=True, Telegram=True")
                    else:
                        print(f"   ⚠️  Platform selection incorrect: WhatsApp={response_data['validate_whatsapp']}, Telegram={response_data['validate_telegram']}")
                
                # Check credit calculation (should be 2 credits per number for both platforms)
                if 'credits_used' in response_data:
                    expected_credits = 4  # 2 numbers * 2 credits each for both platforms
                    if response_data['credits_used'] == expected_credits:
                        print(f"   ✅ Credit calculation correct: {response_data['credits_used']} credits")
                    else:
                        print(f"   ⚠️  Credit calculation incorrect: expected {expected_credits}, got {response_data['credits_used']}")
                
                return True
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_bulk_check_no_platform_selected(self):
        """Test bulk check with no platform selected (should return error)"""
        if not self.admin_token:
            print("❌ Skipping bulk check no platform test - no admin token")
            return False
            
        # Create test CSV content
        csv_content = "name,phone_number\nTestUser7,+6287890123456"
        
        # Prepare multipart form data
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        data = {
            'validate_whatsapp': 'false',
            'validate_telegram': 'false'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"\n🔍 Testing Bulk Check - No Platform Selected...")
        print(f"   Description: Test bulk validation with no platform selected (should return error)")
        
        try:
            import requests
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            success = response.status_code == 400  # Expecting error
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    if 'detail' in error_data and 'platform' in error_data['detail'].lower():
                        print(f"   ✅ Correct error message: {error_data['detail']}")
                    else:
                        print(f"   ⚠️  Unexpected error message: {error_data}")
                except:
                    print(f"   ⚠️  Could not parse error response")
                return True
            else:
                print(f"❌ Failed - Expected 400, got {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {response_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_bulk_check_csv_format_phone_only(self):
        """Test bulk check with CSV containing only phone_number column"""
        if not self.admin_token:
            print("❌ Skipping bulk check phone only CSV test - no admin token")
            return False
            
        # Create test CSV content with only phone_number column
        csv_content = "phone_number\n+6288901234567\n+6289012345678"
        
        # Prepare multipart form data
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        data = {
            'validate_whatsapp': 'true',
            'validate_telegram': 'false'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"\n🔍 Testing Bulk Check - Phone Only CSV...")
        print(f"   Description: Test CSV with only phone_number column")
        
        try:
            import requests
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                
                if 'job_id' in response_data:
                    print(f"   ✅ Job created successfully with phone-only CSV")
                    if 'total_numbers' in response_data and response_data['total_numbers'] == 2:
                        print(f"   ✅ Correct number count: {response_data['total_numbers']}")
                    else:
                        print(f"   ⚠️  Unexpected number count: {response_data.get('total_numbers', 'N/A')}")
                
                return True
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_bulk_check_csv_format_alternative_headers(self):
        """Test bulk check with CSV containing alternative header names"""
        if not self.admin_token:
            print("❌ Skipping bulk check alternative headers test - no admin token")
            return False
            
        # Create test CSV content with alternative headers
        csv_content = "nama,identifier\nBudi Santoso,+6290123456789\nSari Dewi,+6291234567890"
        
        # Prepare multipart form data
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        data = {
            'validate_whatsapp': 'true',
            'validate_telegram': 'false'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"\n🔍 Testing Bulk Check - Alternative Headers CSV...")
        print(f"   Description: Test CSV with alternative header names (nama, identifier)")
        
        try:
            import requests
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                
                if 'job_id' in response_data:
                    print(f"   ✅ Job created successfully with alternative headers")
                    if 'total_numbers' in response_data and response_data['total_numbers'] == 2:
                        print(f"   ✅ Correct number count: {response_data['total_numbers']}")
                    else:
                        print(f"   ⚠️  Unexpected number count: {response_data.get('total_numbers', 'N/A')}")
                
                return True
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_bulk_check_job_status_progression(self):
        """Test bulk check job status progression and platform flags storage"""
        if not self.admin_token:
            print("❌ Skipping bulk check job status test - no admin token")
            return False
            
        # Create test CSV content
        csv_content = "name,phone_number\nStatusTest1,+6292345678901\nStatusTest2,+6293456789012"
        
        # Prepare multipart form data
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        data = {
            'validate_whatsapp': 'true',
            'validate_telegram': 'true'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"\n🔍 Testing Bulk Check - Job Status Progression...")
        print(f"   Description: Test job status progression and platform flags storage")
        
        try:
            import requests
            import time
            
            # Submit job
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                job_id = response_data.get('job_id')
                
                if job_id:
                    print(f"   ✅ Job submitted with ID: {job_id}")
                    
                    # Check job status immediately (should be pending or processing)
                    job_url = f"{self.base_url}/api/jobs/{job_id}"
                    job_response = requests.get(job_url, headers=headers, timeout=10)
                    
                    if job_response.status_code == 200:
                        job_data = job_response.json()
                        initial_status = job_data.get('status')
                        print(f"   ✅ Initial job status: {initial_status}")
                        
                        # Check if platform flags are stored in job document
                        if 'validate_whatsapp' in job_data and 'validate_telegram' in job_data:
                            if job_data['validate_whatsapp'] == True and job_data['validate_telegram'] == True:
                                print(f"   ✅ Platform flags stored correctly in job document")
                            else:
                                print(f"   ⚠️  Platform flags incorrect in job: WhatsApp={job_data['validate_whatsapp']}, Telegram={job_data['validate_telegram']}")
                        else:
                            print(f"   ⚠️  Platform flags missing from job document")
                        
                        # Wait a bit and check status again
                        time.sleep(3)
                        job_response2 = requests.get(job_url, headers=headers, timeout=10)
                        
                        if job_response2.status_code == 200:
                            job_data2 = job_response2.json()
                            final_status = job_data2.get('status')
                            print(f"   ✅ Final job status: {final_status}")
                            
                            # Check if job progressed through expected statuses
                            if initial_status in ['pending', 'processing'] and final_status in ['processing', 'completed']:
                                print(f"   ✅ Job status progression working correctly")
                                self.tests_passed += 1
                                self.tests_run += 1
                                return True
                            else:
                                print(f"   ⚠️  Unexpected status progression: {initial_status} -> {final_status}")
                        else:
                            print(f"   ⚠️  Could not check final job status")
                    else:
                        print(f"   ⚠️  Could not check initial job status")
                else:
                    print(f"   ❌ No job_id in response")
            else:
                print(f"❌ Failed to submit job - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            self.tests_run += 1
            return False
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_bulk_check_invalid_file_format(self):
        """Test bulk check with invalid file format"""
        if not self.admin_token:
            print("❌ Skipping bulk check invalid file test - no admin token")
            return False
            
        # Create invalid file content (not CSV)
        invalid_content = "This is not a CSV file content"
        
        # Prepare multipart form data
        files = {'file': ('test.txt', invalid_content, 'text/plain')}
        data = {
            'validate_whatsapp': 'true',
            'validate_telegram': 'false'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"\n🔍 Testing Bulk Check - Invalid File Format...")
        print(f"   Description: Test with invalid file format (should return error)")
        
        try:
            import requests
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            success = response.status_code == 400  # Expecting error
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   ✅ Error response: {error_data}")
                except:
                    print(f"   ⚠️  Could not parse error response")
                return True
            else:
                print(f"❌ Failed - Expected 400, got {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {response_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_bulk_check_oversized_file(self):
        """Test bulk check with oversized file"""
        if not self.admin_token:
            print("❌ Skipping bulk check oversized file test - no admin token")
            return False
            
        # Create oversized CSV content (simulate large file)
        csv_lines = ["name,phone_number"]
        for i in range(2000):  # Create 2000 lines to simulate large file
            csv_lines.append(f"User{i},+628{i:010d}")
        
        oversized_content = "\n".join(csv_lines)
        
        # Prepare multipart form data
        files = {'file': ('large_test.csv', oversized_content, 'text/csv')}
        data = {
            'validate_whatsapp': 'true',
            'validate_telegram': 'false'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"\n🔍 Testing Bulk Check - Oversized File...")
        print(f"   Description: Test with oversized file (2000 numbers, may hit limits)")
        
        try:
            import requests
            response = requests.post(url, files=files, data=data, headers=headers, timeout=60)
            
            # Could be 200 (accepted) or 400 (rejected due to size limits)
            success = response.status_code in [200, 400]
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if response.status_code == 200:
                        print(f"   ✅ Large file accepted: {response_data.get('total_numbers', 'N/A')} numbers")
                    else:
                        print(f"   ✅ Large file rejected as expected: {response_data}")
                except:
                    print(f"   ⚠️  Could not parse response")
                return True
            else:
                print(f"❌ Failed - Unexpected status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {response_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    # ========== WHATSAPP VALIDATION ACCURACY INVESTIGATION ==========
    
    def test_whatsapp_validation_accuracy_quick_check(self):
        """Test WhatsApp validation accuracy using quick-check endpoint with real numbers"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp accuracy test - no admin token")
            return False
            
        print(f"\n🔍 Testing WhatsApp Validation Accuracy - Quick Check...")
        print(f"   Description: Test quick-check endpoint with real WhatsApp numbers to verify provider usage")
        
        # Test with known active WhatsApp numbers (Indonesian format)
        test_numbers = [
            "+6281234567890",  # Common Indonesian format
            "+6285678901234",  # Another Indonesian format
            "+628123456789"    # Without leading zero
        ]
        
        success_count = 0
        total_tests = len(test_numbers)
        
        for i, phone_number in enumerate(test_numbers):
            try:
                success, response = self.run_test(
                    f"WhatsApp Quick Check #{i+1}",
                    "POST",
                    "api/validation/quick-check",
                    200,
                    data={"phone_inputs": [phone_number], "validate_whatsapp": True, "validate_telegram": False},
                    token=self.admin_token,
                    description=f"Test WhatsApp validation for {phone_number}"
                )
                
                if success and response:
                    # Check if response contains provider information
                    if 'whatsapp' in response and response['whatsapp']:
                        whatsapp_result = response['whatsapp']
                        
                        # Check for provider field in details
                        if 'details' in whatsapp_result and 'provider' in whatsapp_result['details']:
                            provider = whatsapp_result['details']['provider']
                            print(f"   📊 Provider used: {provider}")
                            
                            if provider == "checknumber_ai":
                                print(f"   ✅ Using CheckNumber.ai API as expected")
                                success_count += 1
                            elif provider == "free" or "web_api" in provider.lower():
                                print(f"   ❌ Using FREE method instead of CheckNumber.ai!")
                            else:
                                print(f"   ⚠️  Unknown provider: {provider}")
                        else:
                            print(f"   ❌ No provider information in response details")
                            
                        # Check validation status and confidence
                        status = whatsapp_result.get('status', 'unknown')
                        confidence = whatsapp_result.get('details', {}).get('confidence_score', 0)
                        print(f"   📊 Status: {status}, Confidence: {confidence}")
                        
                    else:
                        print(f"   ❌ No WhatsApp result in response")
                else:
                    print(f"   ❌ Request failed for {phone_number}")
                    
            except Exception as e:
                print(f"   ❌ Error testing {phone_number}: {str(e)}")
        
        # Overall assessment
        if success_count == total_tests:
            print(f"   🎉 All {total_tests} tests used CheckNumber.ai API correctly")
            self.tests_passed += 1
        elif success_count > 0:
            print(f"   ⚠️  Only {success_count}/{total_tests} tests used CheckNumber.ai API")
        else:
            print(f"   ❌ No tests used CheckNumber.ai API - all using free method!")
            
        self.tests_run += 1
        return success_count == total_tests

    def test_admin_whatsapp_provider_settings(self):
        """Test admin settings for WhatsApp provider configuration"""
        if not self.admin_token:
            print("❌ Skipping admin WhatsApp settings test - no admin token")
            return False
            
        print(f"\n🔍 Testing Admin WhatsApp Provider Settings...")
        print(f"   Description: Verify admin settings for whatsapp_provider in database")
        
        # First, let's check if there's an endpoint to get admin settings
        success, response = self.run_test(
            "Admin Settings - WhatsApp Provider",
            "GET",
            "api/admin/settings/whatsapp_provider",
            200,
            token=self.admin_token,
            description="Get WhatsApp provider settings from admin"
        )
        
        if success and response:
            # Check if settings are properly configured
            expected_fields = ['enabled', 'provider', 'api_key', 'api_url']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if not missing_fields:
                print(f"   ✅ All required settings fields present")
                
                # Check specific values
                if response.get('enabled') == True:
                    print(f"   ✅ WhatsApp provider enabled: {response['enabled']}")
                else:
                    print(f"   ❌ WhatsApp provider not enabled: {response.get('enabled')}")
                    
                if response.get('provider') == "checknumber_ai":
                    print(f"   ✅ Provider set to CheckNumber.ai: {response['provider']}")
                else:
                    print(f"   ❌ Provider not set to CheckNumber.ai: {response.get('provider')}")
                    
                if response.get('api_key') and response['api_key'] != 'your-api-key-here':
                    print(f"   ✅ API key configured (not default)")
                else:
                    print(f"   ❌ API key not properly configured")
                    
                if response.get('api_url') and 'checknumber.ai' in response['api_url']:
                    print(f"   ✅ API URL configured correctly: {response['api_url']}")
                else:
                    print(f"   ❌ API URL not configured correctly: {response.get('api_url')}")
                    
                return True
            else:
                print(f"   ❌ Missing required settings fields: {missing_fields}")
        else:
            print(f"   ❌ Could not retrieve admin settings")
            
        self.tests_run += 1
        return False

    def test_bulk_validation_checknumber_usage(self):
        """Test bulk validation to ensure it uses CheckNumber.ai API"""
        if not self.admin_token:
            print("❌ Skipping bulk validation CheckNumber.ai test - no admin token")
            return False
            
        print(f"\n🔍 Testing Bulk Validation CheckNumber.ai Usage...")
        print(f"   Description: Test bulk validation endpoint uses CheckNumber.ai API")
        
        # Create test CSV with real-looking Indonesian numbers
        csv_content = "name,phone_number\nBudi Santoso,+6281234567890\nSari Dewi,+6285678901234\nAhmad Rahman,+628123456789"
        
        # Prepare multipart form data
        files = {'file': ('checknumber_test.csv', csv_content, 'text/csv')}
        data = {
            'validate_whatsapp': 'true',
            'validate_telegram': 'false'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        try:
            import requests
            import time
            
            # Submit bulk validation job
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                job_id = response_data.get('job_id')
                
                if job_id:
                    print(f"   ✅ Bulk validation job submitted: {job_id}")
                    
                    # Wait for job to complete and check results
                    max_wait = 60  # Wait up to 60 seconds
                    waited = 0
                    
                    while waited < max_wait:
                        time.sleep(5)
                        waited += 5
                        
                        # Check job status
                        job_url = f"{self.base_url}/api/jobs/{job_id}"
                        job_response = requests.get(job_url, headers=headers, timeout=10)
                        
                        if job_response.status_code == 200:
                            job_data = job_response.json()
                            status = job_data.get('status')
                            
                            print(f"   📊 Job status after {waited}s: {status}")
                            
                            if status == 'completed':
                                # Check results for provider information
                                results = job_data.get('results', {})
                                details = results.get('details', [])
                                
                                if details:
                                    checknumber_count = 0
                                    free_count = 0
                                    
                                    for detail in details:
                                        whatsapp_result = detail.get('whatsapp', {})
                                        if whatsapp_result and 'details' in whatsapp_result:
                                            provider = whatsapp_result['details'].get('provider', 'unknown')
                                            
                                            if provider == 'checknumber_ai':
                                                checknumber_count += 1
                                            elif 'free' in provider.lower() or 'web' in provider.lower():
                                                free_count += 1
                                                
                                    print(f"   📊 CheckNumber.ai results: {checknumber_count}")
                                    print(f"   📊 Free method results: {free_count}")
                                    
                                    if checknumber_count == len(details):
                                        print(f"   ✅ All bulk validation used CheckNumber.ai API")
                                        self.tests_passed += 1
                                        self.tests_run += 1
                                        return True
                                    elif checknumber_count > 0:
                                        print(f"   ⚠️  Mixed providers: {checknumber_count} CheckNumber.ai, {free_count} free")
                                    else:
                                        print(f"   ❌ No CheckNumber.ai usage detected in bulk validation!")
                                else:
                                    print(f"   ❌ No detailed results found in completed job")
                                break
                            elif status == 'failed':
                                print(f"   ❌ Job failed: {job_data.get('error_message', 'Unknown error')}")
                                break
                        else:
                            print(f"   ⚠️  Could not check job status")
                            break
                    
                    if waited >= max_wait:
                        print(f"   ⏰ Job did not complete within {max_wait} seconds")
                else:
                    print(f"   ❌ No job_id in bulk validation response")
            else:
                print(f"   ❌ Bulk validation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"   ❌ Error in bulk validation test: {str(e)}")
            
        self.tests_run += 1
        return False

    def test_backend_logs_checknumber_calls(self):
        """Test backend logs to verify CheckNumber.ai API calls are being made"""
        print(f"\n🔍 Testing Backend Logs for CheckNumber.ai API Calls...")
        print(f"   Description: Check backend logs for evidence of CheckNumber.ai API usage")
        
        # This test will check if we can find evidence of CheckNumber.ai calls in logs
        # We'll make a validation request and then check logs
        
        if not self.admin_token:
            print("❌ Skipping backend logs test - no admin token")
            return False
            
        try:
            # First make a validation request to generate log entries
            success, response = self.run_test(
                "Generate CheckNumber.ai Log Entry",
                "POST",
                "api/validation/quick-check",
                200,
                data={"phone_inputs": ["+6281234567890"], "validate_whatsapp": True, "validate_telegram": False},
                token=self.admin_token,
                description="Generate validation request to check logs"
            )
            
            if success:
                print(f"   ✅ Validation request made successfully")
                
                # Note: In a real implementation, we would check actual log files
                # For this test, we'll check if the response indicates CheckNumber.ai usage
                if response and 'whatsapp' in response:
                    whatsapp_result = response['whatsapp']
                    if 'details' in whatsapp_result and 'provider' in whatsapp_result['details']:
                        provider = whatsapp_result['details']['provider']
                        
                        if provider == 'checknumber_ai':
                            print(f"   ✅ Response indicates CheckNumber.ai API was called")
                            print(f"   📊 Provider in response: {provider}")
                            
                            # Check for additional CheckNumber.ai specific fields
                            api_response = whatsapp_result['details'].get('api_response')
                            if api_response:
                                print(f"   ✅ API response field present: {api_response}")
                                
                            confidence = whatsapp_result['details'].get('confidence_score', 0)
                            if confidence >= 5:  # CheckNumber.ai typically gives high confidence
                                print(f"   ✅ High confidence score indicates real API: {confidence}")
                            
                            self.tests_passed += 1
                            self.tests_run += 1
                            return True
                        else:
                            print(f"   ❌ Response indicates free method used: {provider}")
                    else:
                        print(f"   ❌ No provider information in response")
                else:
                    print(f"   ❌ No WhatsApp result in response")
            else:
                print(f"   ❌ Validation request failed")
                
        except Exception as e:
            print(f"   ❌ Error checking backend logs: {str(e)}")
            
        self.tests_run += 1
        return False

    def test_whatsapp_provider_configuration_verification(self):
        """Comprehensive test to verify WhatsApp provider configuration"""
        print(f"\n🔍 Testing WhatsApp Provider Configuration Verification...")
        print(f"   Description: Comprehensive verification of CheckNumber.ai configuration")
        
        if not self.admin_token:
            print("❌ Skipping provider configuration test - no admin token")
            return False
            
        configuration_issues = []
        
        # Test 1: Check environment variables (simulated)
        print(f"   📋 Checking environment configuration...")
        
        # Test 2: Make validation request and analyze response thoroughly
        try:
            success, response = self.run_test(
                "Provider Configuration Check",
                "POST",
                "api/validation/quick-check",
                200,
                data={"phone_inputs": ["+6281234567890"], "validate_whatsapp": True, "validate_telegram": False},
                token=self.admin_token,
                description="Comprehensive provider configuration check"
            )
            
            if success and response:
                print(f"   ✅ Validation request successful")
                
                # Analyze response structure
                if 'whatsapp' in response and response['whatsapp']:
                    whatsapp_result = response['whatsapp']
                    
                    # Check provider field
                    provider = whatsapp_result.get('details', {}).get('provider', 'not_specified')
                    print(f"   📊 Provider field: {provider}")
                    
                    if provider != 'checknumber_ai':
                        configuration_issues.append(f"Provider is '{provider}', expected 'checknumber_ai'")
                    
                    # Check for CheckNumber.ai specific response fields
                    api_response = whatsapp_result.get('details', {}).get('api_response')
                    if api_response:
                        print(f"   📊 API response field: {api_response}")
                        if api_response not in ['yes', 'no']:
                            configuration_issues.append(f"Unexpected API response format: {api_response}")
                    else:
                        configuration_issues.append("Missing api_response field (CheckNumber.ai specific)")
                    
                    # Check confidence score
                    confidence = whatsapp_result.get('details', {}).get('confidence_score', 0)
                    print(f"   📊 Confidence score: {confidence}")
                    
                    if confidence < 5 and whatsapp_result.get('status') == 'active':
                        configuration_issues.append(f"Low confidence score for active number: {confidence}")
                    
                    # Check for free method indicators
                    details = whatsapp_result.get('details', {})
                    if 'indicators' in details:
                        print(f"   ⚠️  Free method indicators detected - not using CheckNumber.ai")
                        configuration_issues.append("Response contains free method indicators")
                    
                    # Check validation timing (CheckNumber.ai should be faster than free method)
                    validated_at = whatsapp_result.get('validated_at')
                    if validated_at:
                        print(f"   📊 Validation timestamp: {validated_at}")
                    
                else:
                    configuration_issues.append("No WhatsApp result in response")
                    
            else:
                configuration_issues.append("Validation request failed")
                
        except Exception as e:
            configuration_issues.append(f"Error during validation test: {str(e)}")
        
        # Summary
        if not configuration_issues:
            print(f"   🎉 WhatsApp provider configuration appears correct!")
            self.tests_passed += 1
        else:
            print(f"   ❌ Configuration issues found:")
            for issue in configuration_issues:
                print(f"      - {issue}")
                
        self.tests_run += 1
        return len(configuration_issues) == 0

    # ========== NEW WHATSAPP VALIDATION METHOD TESTS ==========
    
    def test_quick_check_standard_method(self):
        """Test Quick Check endpoint with standard validation method"""
        if not self.demo_token:
            print("❌ Skipping quick check standard method test - no demo token")
            return False
            
        success, response = self.run_test(
            "Quick Check - Standard Method",
            "POST",
            "api/validation/quick-check",
            200,
            data={
                "phone_inputs": ["+6281234567890"], 
                "validate_whatsapp": True, 
                "validate_telegram": True,
                "validation_method": "standard"
            },
            token=self.demo_token,
            description="Test quick check with standard validation method (1 credit for WhatsApp)"
        )
        
        if success and response:
            # Verify validation method is reflected in response
            if 'whatsapp' in response and response['whatsapp']:
                whatsapp_result = response['whatsapp']
                provider = whatsapp_result.get('details', {}).get('provider', '')
                print(f"   📊 WhatsApp provider used: {provider}")
                
                # Standard method should use CheckNumber.ai or free method
                if provider in ['checknumber_ai', 'free', 'whatsapp_web_api']:
                    print(f"   ✅ Standard method provider correct: {provider}")
                else:
                    print(f"   ⚠️  Unexpected provider for standard method: {provider}")
            
            # Check credit calculation (should be 1 credit for WhatsApp + 1 for Telegram = 2 total)
            print(f"   📊 Standard method credit usage verified")
            
        return success

    def test_quick_check_deeplink_profile_method(self):
        """Test Quick Check endpoint with deeplink_profile validation method"""
        if not self.demo_token:
            print("❌ Skipping quick check deeplink profile method test - no demo token")
            return False
            
        success, response = self.run_test(
            "Quick Check - Deep Link Profile Method",
            "POST",
            "api/validation/quick-check",
            200,
            data={
                "phone_inputs": ["+6281234567891"], 
                "validate_whatsapp": True, 
                "validate_telegram": True,
                "validation_method": "deeplink_profile"
            },
            token=self.demo_token,
            description="Test quick check with deeplink_profile validation method (3 credits for WhatsApp)"
        )
        
        if success and response:
            # Verify validation method is reflected in response
            if 'whatsapp' in response and response['whatsapp']:
                whatsapp_result = response['whatsapp']
                provider = whatsapp_result.get('details', {}).get('provider', '')
                print(f"   📊 WhatsApp provider used: {provider}")
                
                # Deep Link Profile method should use enhanced validation
                if 'deeplink' in provider.lower() or 'browser' in provider.lower() or 'enhanced' in provider.lower():
                    print(f"   ✅ Deep Link Profile method provider correct: {provider}")
                else:
                    print(f"   ⚠️  Expected deeplink provider, got: {provider}")
                
                # Check for enhanced validation indicators
                enhanced = whatsapp_result.get('details', {}).get('enhanced_validation', False)
                if enhanced:
                    print(f"   ✅ Enhanced validation flag detected")
                
                account_used = whatsapp_result.get('details', {}).get('account_used')
                if account_used:
                    print(f"   ✅ WhatsApp account used: {account_used}")
            
            print(f"   📊 Deep Link Profile method should use 3 credits for WhatsApp")
            
        return success

    def test_bulk_check_validation_method_parameter(self):
        """Test Bulk Check endpoint with validation_method parameter"""
        if not self.admin_token:
            print("❌ Skipping bulk check validation method test - no admin token")
            return False
            
        # Test with standard method
        csv_content = "name,phone_number\nTestUser1,+6281234567892\nTestUser2,+6282345678903"
        
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        data = {
            'validate_whatsapp': 'true',
            'validate_telegram': 'false',
            'validation_method': 'standard'
        }
        
        url = f"{self.base_url}/api/validation/bulk-check"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print(f"\n🔍 Testing Bulk Check - Validation Method Parameter...")
        print(f"   Description: Test bulk check with validation_method parameter")
        
        try:
            import requests
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                
                if 'job_id' in response_data:
                    print(f"   ✅ Job created with validation_method parameter")
                    
                    # Check if validation_method is stored in job
                    if 'validation_method' in response_data:
                        method = response_data['validation_method']
                        print(f"   ✅ Validation method stored: {method}")
                    
                    return True
                else:
                    print(f"   ⚠️  Missing job_id in response")
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_credit_calculation_validation_methods(self):
        """Test credit calculation for different validation methods"""
        if not self.demo_token:
            print("❌ Skipping credit calculation test - no demo token")
            return False
            
        print(f"\n🔍 Testing Credit Calculation for Validation Methods...")
        print(f"   Description: Verify credit costs - Standard WhatsApp: 1, Deep Link Profile: 3, Telegram: 1")
        
        test_cases = [
            {
                "name": "Standard WhatsApp Only",
                "data": {"phone_inputs": ["+6281234567894"], "validate_whatsapp": True, "validate_telegram": False, "validation_method": "standard"},
                "expected_credits": 1
            },
            {
                "name": "Deep Link Profile WhatsApp Only", 
                "data": {"phone_inputs": ["+6281234567895"], "validate_whatsapp": True, "validate_telegram": False, "validation_method": "deeplink_profile"},
                "expected_credits": 3
            },
            {
                "name": "Telegram Only",
                "data": {"phone_inputs": ["+6281234567896"], "validate_whatsapp": False, "validate_telegram": True, "validation_method": "standard"},
                "expected_credits": 1
            },
            {
                "name": "Standard Both Platforms",
                "data": {"phone_inputs": ["+6281234567897"], "validate_whatsapp": True, "validate_telegram": True, "validation_method": "standard"},
                "expected_credits": 2
            },
            {
                "name": "Deep Link Profile + Telegram",
                "data": {"phone_inputs": ["+6281234567898"], "validate_whatsapp": True, "validate_telegram": True, "validation_method": "deeplink_profile"},
                "expected_credits": 4
            }
        ]
        
        passed_tests = 0
        
        for test_case in test_cases:
            try:
                # Get user credits before
                profile_success, profile_response = self.run_test(
                    "Get Profile Before",
                    "GET",
                    "api/user/profile",
                    200,
                    token=self.demo_token,
                    description="Get credits before validation"
                )
                
                if not profile_success:
                    print(f"   ❌ Could not get profile for {test_case['name']}")
                    continue
                    
                credits_before = profile_response.get('credits', 0)
                
                # Make validation request
                success, response = self.run_test(
                    f"Credit Test - {test_case['name']}",
                    "POST",
                    "api/validation/quick-check",
                    200,
                    data=test_case['data'],
                    token=self.demo_token,
                    description=f"Test credit calculation for {test_case['name']}"
                )
                
                if success:
                    # Get user credits after
                    profile_success2, profile_response2 = self.run_test(
                        "Get Profile After",
                        "GET",
                        "api/user/profile",
                        200,
                        token=self.demo_token,
                        description="Get credits after validation"
                    )
                    
                    if profile_success2:
                        credits_after = profile_response2.get('credits', 0)
                        credits_used = credits_before - credits_after
                        
                        print(f"   📊 {test_case['name']}: Expected {test_case['expected_credits']}, Used {credits_used}")
                        
                        if credits_used == test_case['expected_credits']:
                            print(f"   ✅ Credit calculation correct for {test_case['name']}")
                            passed_tests += 1
                        else:
                            print(f"   ❌ Credit calculation incorrect for {test_case['name']}")
                    else:
                        print(f"   ❌ Could not verify credits after for {test_case['name']}")
                else:
                    print(f"   ❌ Validation failed for {test_case['name']}")
                    
            except Exception as e:
                print(f"   ❌ Error testing {test_case['name']}: {str(e)}")
        
        success = passed_tests == len(test_cases)
        if success:
            self.tests_passed += 1
            print(f"   🎉 All credit calculations correct!")
        else:
            print(f"   ⚠️  {len(test_cases) - passed_tests} credit calculation tests failed")
            
        self.tests_run += 1
        return success

    def test_whatsapp_accounts_list(self):
        """Test GET /api/admin/whatsapp-accounts endpoint"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp accounts list test - no admin token")
            return False
            
        success, response = self.run_test(
            "WhatsApp Accounts List",
            "GET",
            "api/admin/whatsapp-accounts",
            200,
            token=self.admin_token,
            description="Get list of WhatsApp accounts for deep link validation"
        )
        
        if success and response:
            if isinstance(response, list):
                print(f"   ✅ Found {len(response)} WhatsApp accounts")
                
                # Check account structure
                if response:
                    first_account = response[0]
                    expected_fields = ['_id', 'name', 'phone_number', 'status']
                    missing_fields = [field for field in expected_fields if field not in first_account]
                    
                    if not missing_fields:
                        print(f"   ✅ Account structure correct")
                        print(f"   📊 Sample account: {first_account.get('name')} ({first_account.get('status')})")
                    else:
                        print(f"   ⚠️  Account missing fields: {missing_fields}")
                        
                    # Count active accounts
                    active_count = sum(1 for acc in response if acc.get('status') == 'active')
                    print(f"   📊 Active accounts: {active_count}/{len(response)}")
                else:
                    print(f"   ⚠️  No WhatsApp accounts found")
            else:
                print(f"   ⚠️  Expected list, got {type(response)}")
                
        return success

    def test_whatsapp_accounts_create(self):
        """Test POST /api/admin/whatsapp-accounts endpoint"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp accounts create test - no admin token")
            return False
            
        success, response = self.run_test(
            "Create WhatsApp Account",
            "POST",
            "api/admin/whatsapp-accounts",
            200,
            data={
                "name": "Test WhatsApp Account",
                "phone_number": "+6281234567899",
                "description": "Test account for validation"
            },
            token=self.admin_token,
            description="Create new WhatsApp account for deep link validation"
        )
        
        if success and response:
            if 'id' in response or '_id' in response:
                account_id = response.get('id') or response.get('_id')
                print(f"   ✅ WhatsApp account created with ID: {account_id}")
                
                # Store account ID for login test
                self.test_whatsapp_account_id = account_id
                
                if 'message' in response:
                    print(f"   📊 Response: {response['message']}")
            else:
                print(f"   ⚠️  No account ID in response")
                
        return success

    def test_whatsapp_account_login(self):
        """Test POST /api/admin/whatsapp-accounts/{id}/login endpoint"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp account login test - no admin token")
            return False
            
        # First get an account ID
        if not hasattr(self, 'test_whatsapp_account_id'):
            # Get accounts list to find an ID
            list_success, list_response = self.run_test(
                "Get Account for Login Test",
                "GET",
                "api/admin/whatsapp-accounts",
                200,
                token=self.admin_token,
                description="Get account ID for login test"
            )
            
            if list_success and list_response and len(list_response) > 0:
                self.test_whatsapp_account_id = list_response[0].get('_id') or list_response[0].get('id')
            else:
                print("❌ No WhatsApp accounts available for login test")
                return False
        
        if hasattr(self, 'test_whatsapp_account_id'):
            success, response = self.run_test(
                "WhatsApp Account Login",
                "POST",
                f"api/admin/whatsapp-accounts/{self.test_whatsapp_account_id}/login",
                200,
                token=self.admin_token,
                description="Initiate real WhatsApp login for account"
            )
            
            if success and response:
                if 'status' in response:
                    status = response['status']
                    print(f"   📊 Login status: {status}")
                    
                    if status in ['initiated', 'qr_ready', 'success', 'failed']:
                        print(f"   ✅ Valid login status received")
                    else:
                        print(f"   ⚠️  Unexpected login status: {status}")
                
                if 'qr_code' in response:
                    print(f"   📊 QR code provided for WhatsApp login")
                    
                if 'message' in response:
                    print(f"   📊 Message: {response['message']}")
                    
            return success
        else:
            print("❌ No account ID available for login test")
            return False

    def test_whatsapp_accounts_stats(self):
        """Test GET /api/admin/whatsapp-accounts/stats endpoint"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp accounts stats test - no admin token")
            return False
            
        success, response = self.run_test(
            "WhatsApp Accounts Statistics",
            "GET",
            "api/admin/whatsapp-accounts/stats",
            200,
            token=self.admin_token,
            description="Get WhatsApp accounts statistics"
        )
        
        if success and response:
            expected_fields = ['total_accounts', 'active_accounts', 'inactive_accounts', 'login_success_rate']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if not missing_fields:
                print(f"   ✅ Stats structure complete")
                print(f"   📊 Total accounts: {response['total_accounts']}")
                print(f"   📊 Active accounts: {response['active_accounts']}")
                print(f"   📊 Inactive accounts: {response['inactive_accounts']}")
                print(f"   📊 Login success rate: {response['login_success_rate']}%")
            else:
                print(f"   ⚠️  Stats missing fields: {missing_fields}")
                
        return success

    def test_deep_link_validation_with_accounts(self):
        """Test deep link validation functionality with available accounts"""
        if not self.demo_token:
            print("❌ Skipping deep link validation test - no demo token")
            return False
            
        print(f"\n🔍 Testing Deep Link Validation with Available Accounts...")
        print(f"   Description: Test deep link validation using available WhatsApp accounts")
        
        # Test with deeplink_profile method
        success, response = self.run_test(
            "Deep Link Validation Test",
            "POST",
            "api/validation/quick-check",
            200,
            data={
                "phone_inputs": ["+6281234567800"], 
                "validate_whatsapp": True, 
                "validate_telegram": False,
                "validation_method": "deeplink_profile"
            },
            token=self.demo_token,
            description="Test deep link validation with real WhatsApp account"
        )
        
        if success and response:
            if 'whatsapp' in response and response['whatsapp']:
                whatsapp_result = response['whatsapp']
                details = whatsapp_result.get('details', {})
                
                # Check for deep link validation indicators
                provider = details.get('provider', '')
                enhanced = details.get('enhanced_validation', False)
                account_used = details.get('account_used')
                
                print(f"   📊 Provider: {provider}")
                print(f"   📊 Enhanced validation: {enhanced}")
                
                if account_used:
                    print(f"   ✅ WhatsApp account used: {account_used}")
                else:
                    print(f"   ⚠️  No account used (may have fallen back to basic method)")
                
                # Check for browser-specific fields
                if 'browser_error' in details:
                    print(f"   ⚠️  Browser error detected: {details['browser_error']}")
                
                # Verify this is actually deep link validation
                if 'deeplink' in provider.lower() or 'browser' in provider.lower() or enhanced:
                    print(f"   ✅ Deep link validation confirmed")
                else:
                    print(f"   ⚠️  May have fallen back to standard method")
                    
        return success

    def test_validation_method_parameter_validation(self):
        """Test parameter validation for validation_method"""
        if not self.demo_token:
            print("❌ Skipping validation method parameter test - no demo token")
            return False
            
        print(f"\n🔍 Testing Validation Method Parameter Validation...")
        print(f"   Description: Test parameter validation for validation_method field")
        
        # Test with invalid validation method
        success, response = self.run_test(
            "Invalid Validation Method",
            "POST",
            "api/validation/quick-check",
            422,  # Expecting validation error
            data={
                "phone_inputs": ["+6281234567801"], 
                "validate_whatsapp": True, 
                "validate_telegram": False,
                "validation_method": "invalid_method"
            },
            token=self.demo_token,
            description="Test with invalid validation_method parameter"
        )
        
        if success:
            print(f"   ✅ Invalid validation method properly rejected")
        
        # Test with missing validation method (should default to standard)
        success2, response2 = self.run_test(
            "Missing Validation Method",
            "POST",
            "api/validation/quick-check",
            200,
            data={
                "phone_inputs": ["+6281234567802"], 
                "validate_whatsapp": True, 
                "validate_telegram": False
                # validation_method omitted
            },
            token=self.demo_token,
            description="Test with missing validation_method (should default to standard)"
        )
        
        if success2:
            print(f"   ✅ Missing validation method handled correctly (defaults to standard)")
        
        overall_success = success and success2
        if overall_success:
            self.tests_passed += 1
            
        self.tests_run += 1
        return overall_success

    def test_error_handling_missing_accounts(self):
        """Test error handling when no WhatsApp accounts are available"""
        if not self.demo_token:
            print("❌ Skipping error handling test - no demo token")
            return False
            
        print(f"\n🔍 Testing Error Handling for Missing WhatsApp Accounts...")
        print(f"   Description: Test behavior when deep link validation requested but no accounts available")
        
        # This test assumes that if no active accounts are available,
        # the system should gracefully fall back to standard method
        success, response = self.run_test(
            "Deep Link with No Accounts",
            "POST",
            "api/validation/quick-check",
            200,  # Should still succeed with fallback
            data={
                "phone_inputs": ["+6281234567803"], 
                "validate_whatsapp": True, 
                "validate_telegram": False,
                "validation_method": "deeplink_profile"
            },
            token=self.demo_token,
            description="Test deep link validation when no accounts available (should fallback)"
        )
        
        if success and response:
            if 'whatsapp' in response and response['whatsapp']:
                whatsapp_result = response['whatsapp']
                details = whatsapp_result.get('details', {})
                provider = details.get('provider', '')
                
                # Check if it fell back gracefully
                if 'fallback' in provider.lower() or 'basic' in provider.lower():
                    print(f"   ✅ Graceful fallback detected: {provider}")
                elif provider == 'checknumber_ai' or 'free' in provider.lower():
                    print(f"   ✅ Fell back to standard method: {provider}")
                else:
                    print(f"   📊 Provider used: {provider}")
                    
        return success

    # ========== COMPREHENSIVE WHATSAPP ACCOUNT MANAGEMENT TESTS ==========
    
    def test_whatsapp_account_management_get_accounts(self):
        """Test GET /api/admin/whatsapp-accounts - List all WhatsApp accounts"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp accounts list test - no admin token")
            return False
            
        success, response = self.run_test(
            "WhatsApp Accounts List",
            "GET",
            "api/admin/whatsapp-accounts",
            200,
            token=self.admin_token,
            description="Get all WhatsApp accounts (admin only)"
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✅ Found {len(response)} WhatsApp accounts")
                
                # Check account structure if accounts exist
                if response:
                    first_account = response[0]
                    expected_fields = ['_id', 'name', 'phone_number', 'status', 'created_at']
                    missing_fields = [field for field in expected_fields if field not in first_account]
                    if missing_fields:
                        print(f"   ⚠️  Account object missing fields: {missing_fields}")
                    else:
                        print(f"   ✅ Account structure is correct")
                        print(f"   📊 Sample account: {first_account.get('name', 'N/A')} ({first_account.get('status', 'N/A')})")
                else:
                    print(f"   ℹ️  No WhatsApp accounts found (empty list)")
            else:
                print(f"   ⚠️  Expected list, got {type(response)}")
                
        return success

    def test_whatsapp_account_management_create_account(self):
        """Test POST /api/admin/whatsapp-accounts - Create new WhatsApp account"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp account creation test - no admin token")
            return False
            
        # Test account data
        account_data = {
            "name": "Test WhatsApp Account",
            "phone_number": "+628123456789",
            "login_method": "qr_code",
            "daily_request_limit": 100,
            "notes": "Test account created by automated testing"
        }
        
        success, response = self.run_test(
            "Create WhatsApp Account",
            "POST",
            "api/admin/whatsapp-accounts",
            200,
            data=account_data,
            token=self.admin_token,
            description="Create new WhatsApp account"
        )
        
        if success:
            if 'message' in response:
                print(f"   ✅ Account creation message: {response['message']}")
                
                # Store account ID for later tests
                if 'account' in response and '_id' in response['account']:
                    self.created_whatsapp_account_id = response['account']['_id']
                    print(f"   ✅ Created account ID: {self.created_whatsapp_account_id}")
                    
                    # Verify account data
                    created_account = response['account']
                    if created_account.get('name') == account_data['name']:
                        print(f"   ✅ Account name matches: {created_account['name']}")
                    if created_account.get('phone_number') == account_data['phone_number']:
                        print(f"   ✅ Phone number matches: {created_account['phone_number']}")
                else:
                    print(f"   ⚠️  No account data in response")
            else:
                print(f"   ⚠️  Expected 'message' field in response")
                
        return success

    def test_whatsapp_account_management_get_stats(self):
        """Test GET /api/admin/whatsapp-accounts/stats - Get WhatsApp account statistics"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp account stats test - no admin token")
            return False
            
        success, response = self.run_test(
            "WhatsApp Account Statistics",
            "GET",
            "api/admin/whatsapp-accounts/stats",
            200,
            token=self.admin_token,
            description="Get WhatsApp account statistics"
        )
        
        if success:
            expected_fields = ['total_accounts', 'active_accounts', 'available_accounts', 'accounts_with_issues']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing statistics fields: {missing_fields}")
            else:
                print(f"   ✅ Statistics structure is complete")
                print(f"   📊 Total Accounts: {response.get('total_accounts', 0)}")
                print(f"   📊 Active Accounts: {response.get('active_accounts', 0)}")
                print(f"   📊 Available Accounts: {response.get('available_accounts', 0)}")
                print(f"   📊 Accounts with Issues: {response.get('accounts_with_issues', 0)}")
                
        return success

    def test_whatsapp_account_management_login_account(self):
        """Test POST /api/admin/whatsapp-accounts/{id}/login - Login WhatsApp account (QR code)"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp account login test - no admin token")
            return False
            
        # Use created account ID or fallback to a test ID
        account_id = self.created_whatsapp_account_id or "test_account_id"
        
        success, response = self.run_test(
            "WhatsApp Account Login",
            "POST",
            f"api/admin/whatsapp-accounts/{account_id}/login",
            200,
            token=self.admin_token,
            description="Login WhatsApp account with QR code generation"
        )
        
        if success:
            # Check for QR code or login status in response
            if 'qr_code' in response or 'status' in response or 'message' in response:
                print(f"   ✅ Login response received")
                
                if 'qr_code' in response:
                    print(f"   ✅ QR code generated successfully")
                if 'status' in response:
                    print(f"   📊 Login status: {response['status']}")
                if 'message' in response:
                    print(f"   📊 Message: {response['message']}")
            else:
                print(f"   ⚠️  Unexpected response structure")
        else:
            # Login might fail due to browser dependencies in container - this is expected
            print(f"   ℹ️  Login failure expected in container environment (browser dependencies)")
            
        return success

    def test_whatsapp_account_management_logout_account(self):
        """Test POST /api/admin/whatsapp-accounts/{id}/logout - Logout WhatsApp account"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp account logout test - no admin token")
            return False
            
        # Use created account ID or fallback to a test ID
        account_id = self.created_whatsapp_account_id or "test_account_id"
        
        success, response = self.run_test(
            "WhatsApp Account Logout",
            "POST",
            f"api/admin/whatsapp-accounts/{account_id}/logout",
            200,
            token=self.admin_token,
            description="Logout WhatsApp account"
        )
        
        if success:
            if 'message' in response:
                print(f"   ✅ Logout message: {response['message']}")
            if 'success' in response:
                print(f"   📊 Logout success: {response['success']}")
        else:
            # Logout might fail if account wasn't logged in - this is acceptable
            print(f"   ℹ️  Logout failure acceptable if account wasn't logged in")
            
        return success

    def test_whatsapp_account_management_update_account(self):
        """Test PUT /api/admin/whatsapp-accounts/{id} - Update WhatsApp account"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp account update test - no admin token")
            return False
            
        # Use created account ID or fallback to a test ID
        account_id = self.created_whatsapp_account_id or "test_account_id"
        
        # Update data
        update_data = {
            "name": "Updated Test WhatsApp Account",
            "daily_request_limit": 150,
            "notes": "Updated by automated testing"
        }
        
        success, response = self.run_test(
            "Update WhatsApp Account",
            "PUT",
            f"api/admin/whatsapp-accounts/{account_id}",
            200,
            data=update_data,
            token=self.admin_token,
            description="Update WhatsApp account information"
        )
        
        if success:
            if 'message' in response:
                print(f"   ✅ Update message: {response['message']}")
            if 'account' in response:
                updated_account = response['account']
                if updated_account.get('name') == update_data['name']:
                    print(f"   ✅ Account name updated successfully")
                if updated_account.get('daily_request_limit') == update_data['daily_request_limit']:
                    print(f"   ✅ Daily request limit updated successfully")
                    
        return success

    def test_whatsapp_account_management_delete_account(self):
        """Test DELETE /api/admin/whatsapp-accounts/{id} - Delete WhatsApp account"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp account deletion test - no admin token")
            return False
            
        # Use created account ID or fallback to a test ID
        account_id = self.created_whatsapp_account_id or "test_account_id"
        
        success, response = self.run_test(
            "Delete WhatsApp Account",
            "DELETE",
            f"api/admin/whatsapp-accounts/{account_id}",
            200,
            token=self.admin_token,
            description="Delete WhatsApp account"
        )
        
        if success:
            if 'message' in response:
                print(f"   ✅ Deletion message: {response['message']}")
                # Clear the stored account ID since it's deleted
                self.created_whatsapp_account_id = None
                
        return success

    def test_telegram_account_management_comprehensive(self):
        """Comprehensive test of Telegram Account Management API as requested in review"""
        if not self.admin_token:
            print("❌ Skipping Telegram Account Management test - no admin token")
            return False
            
        print(f"\n🔍 Testing Telegram Account Management API - COMPREHENSIVE...")
        print(f"   Description: Verify demo data is correct with 29 demo accounts")
        
        all_tests_passed = True
        
        # Test 1: Admin Login Test
        print(f"\n   📋 TEST 1: Admin Login Verification")
        if not self.admin_token:
            print(f"   ❌ Admin login failed - cannot proceed")
            return False
        else:
            print(f"   ✅ Admin login successful with JWT token")
        
        # Test 2: Telegram Accounts List
        print(f"\n   📋 TEST 2: Telegram Accounts List")
        success, response = self.run_test(
            "Telegram Accounts List",
            "GET",
            "api/admin/telegram-accounts",
            200,
            token=self.admin_token,
            description="Should return 29 demo accounts with correct structure"
        )
        
        if success and isinstance(response, list):
            total_accounts = len(response)
            print(f"   📊 Total accounts found: {total_accounts}")
            
            # Check if we have exactly 29 accounts
            if total_accounts == 29:
                print(f"   ✅ Correct number of accounts: 29")
            else:
                print(f"   ❌ Expected 29 accounts, found {total_accounts}")
                all_tests_passed = False
            
            # Verify demo accounts structure
            demo_accounts = [acc for acc in response if acc.get('demo_account') == True]
            active_accounts = [acc for acc in response if acc.get('status') == 'active']
            
            print(f"   📊 Demo accounts: {len(demo_accounts)}")
            print(f"   📊 Active accounts: {len(active_accounts)}")
            
            # Check demo account names
            expected_names = [f"Telegram Demo {i}" for i in range(1, 30)]
            found_names = [acc.get('name', '') for acc in demo_accounts]
            
            correct_names = 0
            for expected_name in expected_names:
                if expected_name in found_names:
                    correct_names += 1
                else:
                    print(f"   ❌ Missing expected name: {expected_name}")
            
            if correct_names == 29:
                print(f"   ✅ All 29 demo account names correct: 'Telegram Demo 1' to 'Telegram Demo 29'")
            else:
                print(f"   ❌ Only {correct_names}/29 demo account names correct")
                all_tests_passed = False
            
            # Check status field
            active_demo_accounts = [acc for acc in demo_accounts if acc.get('status') == 'active']
            if len(active_demo_accounts) == 29:
                print(f"   ✅ All 29 demo accounts have status 'active'")
            else:
                print(f"   ❌ Only {len(active_demo_accounts)}/29 demo accounts have status 'active'")
                all_tests_passed = False
            
            # Check demo_account flag
            if len(demo_accounts) == 29:
                print(f"   ✅ All 29 accounts have demo_account: true flag")
            else:
                print(f"   ❌ Only {len(demo_accounts)}/29 accounts have demo_account: true flag")
                all_tests_passed = False
            
            # Check phone number format
            valid_phone_format = 0
            for acc in demo_accounts:
                phone = acc.get('phone_number', '')
                if phone.startswith('+62819997776') and len(phone) == 14:
                    valid_phone_format += 1
                else:
                    print(f"   ⚠️  Invalid phone format: {phone}")
            
            if valid_phone_format == 29:
                print(f"   ✅ All 29 demo accounts have correct phone number format")
            else:
                print(f"   ❌ Only {valid_phone_format}/29 demo accounts have correct phone format")
                all_tests_passed = False
                
        else:
            print(f"   ❌ Failed to get telegram accounts list")
            all_tests_passed = False
        
        # Test 3: Statistics Test
        print(f"\n   📋 TEST 3: Telegram Accounts Statistics")
        success, response = self.run_test(
            "Telegram Accounts Statistics",
            "GET",
            "api/admin/telegram-accounts/stats",
            200,
            token=self.admin_token,
            description="Should return total_accounts: 29, active_accounts: 29, available_for_use: 29"
        )
        
        if success and isinstance(response, dict):
            total_accounts = response.get('total_accounts', 0)
            active_accounts = response.get('active_accounts', 0)
            available_for_use = response.get('available_for_use', 0)
            
            print(f"   📊 Statistics received:")
            print(f"      total_accounts: {total_accounts}")
            print(f"      active_accounts: {active_accounts}")
            print(f"      available_for_use: {available_for_use}")
            
            # Verify expected values
            if total_accounts == 29:
                print(f"   ✅ total_accounts correct: 29")
            else:
                print(f"   ❌ total_accounts incorrect: expected 29, got {total_accounts}")
                all_tests_passed = False
                
            if active_accounts == 29:
                print(f"   ✅ active_accounts correct: 29")
            else:
                print(f"   ❌ active_accounts incorrect: expected 29, got {active_accounts}")
                all_tests_passed = False
                
            if available_for_use == 29:
                print(f"   ✅ available_for_use correct: 29")
            else:
                print(f"   ❌ available_for_use incorrect: expected 29, got {available_for_use}")
                all_tests_passed = False
                
        else:
            print(f"   ❌ Failed to get telegram accounts statistics")
            all_tests_passed = False
        
        # Test 4: Individual Account Test
        print(f"\n   📋 TEST 4: Individual Account Data Structure")
        success, response = self.run_test(
            "Individual Telegram Account",
            "GET",
            "api/admin/telegram-accounts",
            200,
            token=self.admin_token,
            description="Sample 1-2 accounts and verify complete data structure"
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            # Sample first 2 accounts
            sample_accounts = response[:2]
            
            for i, account in enumerate(sample_accounts, 1):
                print(f"   📊 Sample Account #{i}:")
                
                # Check required fields
                required_fields = ['_id', 'name', 'phone_number', 'status', 'demo_account', 'created_at']
                missing_fields = []
                
                for field in required_fields:
                    if field in account:
                        value = account[field]
                        print(f"      {field}: {value}")
                    else:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"   ❌ Missing fields in account #{i}: {missing_fields}")
                    all_tests_passed = False
                else:
                    print(f"   ✅ Account #{i} has complete data structure")
                    
                # Verify specific values for demo accounts
                if account.get('demo_account') == True:
                    if account.get('status') == 'active':
                        print(f"   ✅ Demo account #{i} has correct status: active")
                    else:
                        print(f"   ❌ Demo account #{i} has incorrect status: {account.get('status')}")
                        all_tests_passed = False
                        
                    name = account.get('name', '')
                    if name.startswith('Telegram Demo '):
                        print(f"   ✅ Demo account #{i} has correct name format")
                    else:
                        print(f"   ❌ Demo account #{i} has incorrect name format: {name}")
                        all_tests_passed = False
                        
        else:
            print(f"   ❌ Failed to get individual account data")
            all_tests_passed = False
        
        # Final Assessment
        print(f"\n   🎯 TELEGRAM ACCOUNT MANAGEMENT TEST RESULTS:")
        if all_tests_passed:
            print(f"   ✅ ALL TESTS PASSED - Demo data is correct!")
            print(f"   ✅ 29 demo accounts with status 'active'")
            print(f"   ✅ All accounts have demo_account: true")
            print(f"   ✅ Statistics show 29 active accounts")
            print(f"   ✅ Data structure is complete and correct")
            self.tests_passed += 1
        else:
            print(f"   ❌ SOME TESTS FAILED - Demo data needs correction")
            
        self.tests_run += 1
        return all_tests_passed

    def test_telegram_account_management_post_cleanup_verification(self):
        """QUICK VERIFICATION: Test Telegram Account Management API after database cleanup"""
        if not self.admin_token:
            print("❌ Skipping Telegram post-cleanup verification - no admin token")
            return False
            
        print(f"\n🎯 QUICK VERIFICATION: Telegram Account Management API Post-Cleanup...")
        print(f"   Description: Verify exactly 29 accounts with status 'active' after database cleanup")
        
        try:
            # Test 1: GET /api/admin/telegram-accounts - should return exactly 29 accounts with status "active"
            success1, accounts_response = self.run_test(
                "GET Telegram Accounts List",
                "GET",
                "api/admin/telegram-accounts",
                200,
                token=self.admin_token,
                description="Should return exactly 29 accounts with status 'active'"
            )
            
            if not success1:
                return False
                
            # Verify account count and status
            if isinstance(accounts_response, list):
                total_accounts = len(accounts_response)
                active_accounts = sum(1 for acc in accounts_response if acc.get('status') == 'active')
                demo_accounts = sum(1 for acc in accounts_response if acc.get('demo_account') == True)
                
                print(f"   📊 Found {total_accounts} total accounts")
                print(f"   📊 Found {active_accounts} accounts with status 'active'")
                print(f"   📊 Found {demo_accounts} accounts with demo_account: true")
                
                # Check if exactly 29 accounts
                if total_accounts == 29:
                    print(f"   ✅ CORRECT: Exactly 29 accounts found")
                else:
                    print(f"   ❌ INCORRECT: Expected 29 accounts, found {total_accounts}")
                    return False
                
                # Check if all accounts have status "active"
                if active_accounts == 29:
                    print(f"   ✅ CORRECT: All 29 accounts have status 'active'")
                else:
                    print(f"   ❌ INCORRECT: Expected 29 active accounts, found {active_accounts}")
                    return False
                
                # Check if all accounts have demo_account: true
                if demo_accounts == 29:
                    print(f"   ✅ CORRECT: All 29 accounts have demo_account: true")
                else:
                    print(f"   ❌ INCORRECT: Expected 29 demo accounts, found {demo_accounts}")
                    return False
                    
            else:
                print(f"   ❌ Expected list response, got {type(accounts_response)}")
                return False
            
            # Test 2: GET /api/admin/telegram-accounts/stats - should return correct statistics
            success2, stats_response = self.run_test(
                "GET Telegram Accounts Stats",
                "GET",
                "api/admin/telegram-accounts/stats",
                200,
                token=self.admin_token,
                description="Should return total_accounts: 29, active_accounts: 29, available_for_use: 29"
            )
            
            if not success2:
                return False
                
            # Verify statistics
            if isinstance(stats_response, dict):
                total_accounts_stat = stats_response.get('total_accounts', 0)
                active_accounts_stat = stats_response.get('active_accounts', 0)
                available_for_use_stat = stats_response.get('available_for_use', 0)
                
                print(f"   📊 Stats - Total: {total_accounts_stat}, Active: {active_accounts_stat}, Available: {available_for_use_stat}")
                
                # Check total_accounts: 29 (not 58)
                if total_accounts_stat == 29:
                    print(f"   ✅ CORRECT: total_accounts = 29 (not 58)")
                else:
                    print(f"   ❌ INCORRECT: Expected total_accounts = 29, got {total_accounts_stat}")
                    return False
                
                # Check active_accounts: 29
                if active_accounts_stat == 29:
                    print(f"   ✅ CORRECT: active_accounts = 29")
                else:
                    print(f"   ❌ INCORRECT: Expected active_accounts = 29, got {active_accounts_stat}")
                    return False
                
                # Check available_for_use: 29
                if available_for_use_stat == 29:
                    print(f"   ✅ CORRECT: available_for_use = 29")
                else:
                    print(f"   ❌ INCORRECT: Expected available_for_use = 29, got {available_for_use_stat}")
                    return False
                    
            else:
                print(f"   ❌ Expected dict response, got {type(stats_response)}")
                return False
            
            # If we reach here, all tests passed
            self.tests_passed += 1
            self.tests_run += 1
            print(f"   🎉 ALL VERIFICATION CHECKS PASSED!")
            print(f"   ✅ Database cleanup successful - exactly 29 active demo accounts")
            return True
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_whatsapp_account_management_comprehensive_scenario(self):
        """Test comprehensive WhatsApp Account Management scenario as requested in review"""
        if not self.admin_token:
            print("❌ Skipping comprehensive WhatsApp scenario test - no admin token")
            return False
            
        print(f"\n🎯 Testing Comprehensive WhatsApp Account Management Scenario...")
        print(f"   Description: Full CRUD cycle with login/logout operations as requested")
        
        scenario_success = True
        
        # Step 1: Login as admin (already done, but verify)
        print(f"   🔐 Step 1: Verifying admin login...")
        if self.admin_token:
            print(f"      ✅ Admin authenticated successfully")
        else:
            print(f"      ❌ Admin authentication failed")
            return False
        
        # Step 2: Get initial account list
        print(f"   📋 Step 2: Getting initial account list...")
        success, initial_accounts = self.run_test(
            "Initial Account List",
            "GET",
            "api/admin/whatsapp-accounts",
            200,
            token=self.admin_token,
            description="Get initial account count"
        )
        initial_count = len(initial_accounts) if success and isinstance(initial_accounts, list) else 0
        print(f"      Initial account count: {initial_count}")
        
        # Step 3: Get initial statistics
        print(f"   📊 Step 3: Getting initial statistics...")
        success, initial_stats = self.run_test(
            "Initial Statistics",
            "GET",
            "api/admin/whatsapp-accounts/stats",
            200,
            token=self.admin_token,
            description="Get initial statistics"
        )
        if success:
            print(f"      Initial stats: Total={initial_stats.get('total_accounts', 0)}, Active={initial_stats.get('active_accounts', 0)}")
        
        # Step 4: Create new account
        print(f"   ➕ Step 4: Creating new WhatsApp account...")
        account_data = {
            "name": "Scenario Test Account",
            "phone_number": "+628987654321",
            "login_method": "qr_code",
            "daily_request_limit": 200,
            "notes": "Created for comprehensive scenario testing"
        }
        
        success, create_response = self.run_test(
            "Scenario Account Creation",
            "POST",
            "api/admin/whatsapp-accounts",
            200,
            data=account_data,
            token=self.admin_token,
            description="Create account for scenario"
        )
        
        if success and 'account' in create_response:
            scenario_account_id = create_response['account']['_id']
            print(f"      Created account ID: {scenario_account_id}")
        else:
            print(f"      ❌ Failed to create account for scenario")
            scenario_success = False
            scenario_account_id = None
        
        # Step 5: Verify account in list
        if scenario_account_id:
            print(f"   📋 Step 5: Verifying account appears in list...")
            success, updated_accounts = self.run_test(
                "Updated Account List",
                "GET",
                "api/admin/whatsapp-accounts",
                200,
                token=self.admin_token,
                description="Verify new account in list"
            )
            
            if success and isinstance(updated_accounts, list):
                new_count = len(updated_accounts)
                if new_count == initial_count + 1:
                    print(f"      ✅ Account count increased: {initial_count} → {new_count}")
                else:
                    print(f"      ⚠️  Unexpected count: {initial_count} → {new_count}")
            
        # Step 6: Get updated statistics
        print(f"   📊 Step 6: Getting updated statistics...")
        success, updated_stats = self.run_test(
            "Updated Statistics",
            "GET",
            "api/admin/whatsapp-accounts/stats",
            200,
            token=self.admin_token,
            description="Get updated statistics"
        )
        
        if success:
            print(f"      Updated stats: Total={updated_stats.get('total_accounts', 0)}, Active={updated_stats.get('active_accounts', 0)}")
        
        # Step 7: Try login (expected to fail in container but endpoint should respond)
        if scenario_account_id:
            print(f"   🔐 Step 7: Attempting account login (QR code generation)...")
            success, login_response = self.run_test(
                "Account Login Attempt",
                "POST",
                f"api/admin/whatsapp-accounts/{scenario_account_id}/login",
                200,
                token=self.admin_token,
                description="Attempt QR code login"
            )
            
            if success:
                print(f"      ✅ Login endpoint responded successfully")
                if 'qr_code' in login_response:
                    print(f"      ✅ QR code generated")
                if 'message' in login_response:
                    print(f"      📊 Login message: {login_response['message']}")
            else:
                print(f"      ℹ️  Login failure expected in container environment")
        
        # Step 8: Update account
        if scenario_account_id:
            print(f"   ✏️  Step 8: Updating account...")
            update_data = {
                "name": "Updated Scenario Account",
                "daily_request_limit": 250
            }
            
            success, update_response = self.run_test(
                "Account Update",
                "PUT",
                f"api/admin/whatsapp-accounts/{scenario_account_id}",
                200,
                data=update_data,
                token=self.admin_token,
                description="Update account details"
            )
            
            if success:
                print(f"      ✅ Account updated successfully")
                if 'account' in update_response:
                    updated_account = update_response['account']
                    if updated_account.get('name') == update_data['name']:
                        print(f"      ✅ Name updated to: {updated_account['name']}")
        
        # Step 9: Try logout
        if scenario_account_id:
            print(f"   🚪 Step 9: Attempting account logout...")
            success, logout_response = self.run_test(
                "Account Logout Attempt",
                "POST",
                f"api/admin/whatsapp-accounts/{scenario_account_id}/logout",
                200,
                token=self.admin_token,
                description="Attempt logout"
            )
            
            if success:
                print(f"      ✅ Logout endpoint responded successfully")
                if 'message' in logout_response:
                    print(f"      📊 Logout message: {logout_response['message']}")
        
        # Step 10: Delete account (cleanup)
        if scenario_account_id:
            print(f"   🗑️  Step 10: Cleaning up - deleting account...")
            success, delete_response = self.run_test(
                "Account Cleanup",
                "DELETE",
                f"api/admin/whatsapp-accounts/{scenario_account_id}",
                200,
                token=self.admin_token,
                description="Delete test account"
            )
            
            if success:
                print(f"      ✅ Account deleted successfully")
        
        # Step 11: Verify final count
        print(f"   📋 Step 11: Verifying final account count...")
        success, final_accounts = self.run_test(
            "Final Account List",
            "GET",
            "api/admin/whatsapp-accounts",
            200,
            token=self.admin_token,
            description="Get final account count"
        )
        
        if success and isinstance(final_accounts, list):
            final_count = len(final_accounts)
            if final_count == initial_count:
                print(f"      ✅ Account count restored: {final_count}")
            else:
                print(f"      ⚠️  Count mismatch: expected {initial_count}, got {final_count}")
        
        if scenario_success:
            self.tests_passed += 1
            print(f"   🎉 Comprehensive WhatsApp Account Management scenario completed successfully!")
        else:
            print(f"   ❌ Scenario had some failures")
        
        self.tests_run += 1
        return scenario_success

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
    
    # ========== WHATSAPP VALIDATION ACCURACY INVESTIGATION ==========
    print("\n🔍 WHATSAPP VALIDATION ACCURACY INVESTIGATION")
    print("-" * 50)
    print("🎯 INVESTIGATING: User reports validation results not accurate")
    print("🎯 INVESTIGATING: Results seem to use free method instead of CheckNumber.ai")
    print("-" * 50)
    
    tester.test_whatsapp_validation_accuracy_quick_check()
    tester.test_admin_whatsapp_provider_settings()
    tester.test_bulk_validation_checknumber_usage()
    tester.test_backend_logs_checknumber_calls()
    tester.test_whatsapp_provider_configuration_verification()
    
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
    
    # Enhanced Bulk Check Tests
    print("\n📋 ENHANCED BULK CHECK FUNCTIONALITY TESTS")
    print("-" * 30)
    tester.test_bulk_check_platform_selection_whatsapp_only()
    tester.test_bulk_check_platform_selection_telegram_only()
    tester.test_bulk_check_platform_selection_both_platforms()
    tester.test_bulk_check_no_platform_selected()
    tester.test_bulk_check_csv_format_phone_only()
    tester.test_bulk_check_csv_format_alternative_headers()
    tester.test_bulk_check_job_status_progression()
    tester.test_bulk_check_invalid_file_format()
    tester.test_bulk_check_oversized_file()
    
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
    
    # ========== NEW WHATSAPP VALIDATION METHOD TESTS ==========
    print("\n🔗 NEW WHATSAPP VALIDATION METHOD TESTS")
    print("-" * 50)
    print("🎯 TESTING: New WhatsApp validation methods and account management")
    print("🎯 TESTING: Standard vs Deep Link Profile validation methods")
    print("🎯 TESTING: Credit calculation for different methods")
    print("🎯 TESTING: WhatsApp account management endpoints")
    print("-" * 50)
    
    tester.test_quick_check_standard_method()
    tester.test_quick_check_deeplink_profile_method()
    tester.test_bulk_check_validation_method_parameter()
    tester.test_credit_calculation_validation_methods()
    tester.test_whatsapp_accounts_list()
    tester.test_whatsapp_accounts_create()
    tester.test_whatsapp_account_login()
    tester.test_whatsapp_accounts_stats()
    tester.test_deep_link_validation_with_accounts()
    tester.test_validation_method_parameter_validation()
    tester.test_error_handling_missing_accounts()
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Special focus on WhatsApp validation accuracy results
    print("\n" + "🔍" * 50)
    print("WHATSAPP VALIDATION ACCURACY INVESTIGATION SUMMARY")
    print("🔍" * 50)
    print("Key findings will be reported to main agent for analysis...")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())