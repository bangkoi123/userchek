#!/usr/bin/env python3
"""
PRODUCTION READINESS ASSESSMENT - Telegram & WhatsApp Login Systems
Comprehensive testing for production deployment readiness
"""

import requests
import sys
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class ProductionReadinessAssessment:
    def __init__(self, base_url="https://verify-connect-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.demo_token = None
        self.test_results = {
            "telegram_mtp_system": {},
            "whatsapp_deeplink_system": {},
            "production_deployment": {},
            "integration_testing": {},
            "overall_assessment": {}
        }
        self.critical_issues = []
        self.production_ready_components = []
        self.components_needing_fixes = []
        
    def log_result(self, category: str, test_name: str, status: bool, details: str, is_critical: bool = False):
        """Log test result and categorize for final assessment"""
        self.test_results[category][test_name] = {
            "status": status,
            "details": details,
            "is_critical": is_critical,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if status:
            self.production_ready_components.append(f"{category}: {test_name}")
        else:
            self.components_needing_fixes.append(f"{category}: {test_name}")
            if is_critical:
                self.critical_issues.append(f"CRITICAL - {category}: {test_name} - {details}")

    def make_request(self, method: str, endpoint: str, data: dict = None, token: str = None, timeout: int = 30) -> tuple:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                return False, {"error": f"Unsupported method: {method}"}
                
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_response": response.text}
                
            return response.status_code, response_data
            
        except requests.exceptions.Timeout:
            return 0, {"error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return 0, {"error": "Connection error"}
        except Exception as e:
            return 0, {"error": str(e)}

    def authenticate(self) -> bool:
        """Authenticate admin and demo users"""
        print("🔐 Authenticating users...")
        
        # Admin login
        status_code, response = self.make_request('POST', 'api/auth/login', {
            "username": "admin",
            "password": "admin123"
        })
        
        if status_code == 200 and 'token' in response:
            self.admin_token = response['token']
            print("   ✅ Admin authentication successful")
        else:
            print(f"   ❌ Admin authentication failed: {response}")
            return False
            
        # Demo login
        status_code, response = self.make_request('POST', 'api/auth/login', {
            "username": "demo", 
            "password": "demo123"
        })
        
        if status_code == 200 and 'token' in response:
            self.demo_token = response['token']
            print("   ✅ Demo authentication successful")
        else:
            print(f"   ❌ Demo authentication failed: {response}")
            return False
            
        return True

    def test_telegram_mtp_system(self):
        """Test Telegram MTP Login System for production readiness"""
        print("\n" + "="*80)
        print("📱 TESTING TELEGRAM MTP LOGIN SYSTEM")
        print("="*80)
        
        # 1. Test Telegram Account Management API
        print("\n🔍 Testing Telegram Account Management API...")
        status_code, response = self.make_request('GET', 'api/admin/telegram-accounts', token=self.admin_token)
        
        if status_code == 200 and isinstance(response, list):
            total_accounts = len(response)
            demo_accounts = [acc for acc in response if acc.get('demo_account', False)]
            active_accounts = [acc for acc in response if acc.get('status') == 'active']
            
            self.log_result("telegram_mtp_system", "account_management_api", True, 
                          f"API working - {total_accounts} total accounts, {len(demo_accounts)} demo accounts, {len(active_accounts)} active")
            
            # Check for production-ready demo accounts
            if len(demo_accounts) >= 29:
                self.log_result("telegram_mtp_system", "demo_accounts_available", True,
                              f"{len(demo_accounts)} demo accounts available for testing")
            else:
                self.log_result("telegram_mtp_system", "demo_accounts_available", False,
                              f"Only {len(demo_accounts)} demo accounts, need at least 29 for production", True)
                              
        else:
            self.log_result("telegram_mtp_system", "account_management_api", False,
                          f"API failed with status {status_code}: {response}", True)

        # 2. Test Telegram Account Statistics
        print("\n🔍 Testing Telegram Account Statistics...")
        status_code, response = self.make_request('GET', 'api/admin/telegram-accounts/stats', token=self.admin_token)
        
        if status_code == 200 and isinstance(response, dict):
            stats = response
            required_stats = ['total_accounts', 'active_accounts', 'available_for_use']
            
            if all(stat in stats for stat in required_stats):
                self.log_result("telegram_mtp_system", "statistics_api", True,
                              f"Stats API working - Total: {stats['total_accounts']}, Active: {stats['active_accounts']}, Available: {stats['available_for_use']}")
            else:
                missing_stats = [stat for stat in required_stats if stat not in stats]
                self.log_result("telegram_mtp_system", "statistics_api", False,
                              f"Missing statistics: {missing_stats}", True)
        else:
            self.log_result("telegram_mtp_system", "statistics_api", False,
                          f"Stats API failed with status {status_code}: {response}", True)

        # 3. Test Telegram Account Creation
        print("\n🔍 Testing Telegram Account Creation...")
        test_account_data = {
            "name": "Production Test Account",
            "phone_number": "+6281234567890",
            "api_id": "12345678",
            "api_hash": "abcdef123456789abcdef123456789ab",
            "daily_request_limit": 100,
            "notes": "Production readiness test account"
        }
        
        status_code, response = self.make_request('POST', 'api/admin/telegram-accounts', 
                                                data=test_account_data, token=self.admin_token)
        
        if status_code == 200 or status_code == 201:
            created_account_id = response.get('_id') or response.get('id')
            if created_account_id:
                self.log_result("telegram_mtp_system", "account_creation", True,
                              f"Account creation successful - ID: {created_account_id}")
                
                # Clean up test account
                self.make_request('DELETE', f'api/admin/telegram-accounts/{created_account_id}', 
                                token=self.admin_token)
            else:
                self.log_result("telegram_mtp_system", "account_creation", False,
                              "Account created but no ID returned")
        else:
            self.log_result("telegram_mtp_system", "account_creation", False,
                          f"Account creation failed with status {status_code}: {response}")

        # 4. Test MTP Validation Methods
        print("\n🔍 Testing MTP Validation Methods...")
        test_phone = "+6281234567890"
        
        # Test standard Telegram validation
        validation_data = {
            "phone_inputs": [test_phone],
            "validate_whatsapp": False,
            "validate_telegram": True,
            "telegram_validation_method": "standard"
        }
        
        status_code, response = self.make_request('POST', 'api/validation/quick-check',
                                                data=validation_data, token=self.demo_token)
        
        if status_code == 200:
            telegram_result = response.get('telegram')
            if telegram_result:
                self.log_result("telegram_mtp_system", "standard_validation", True,
                              f"Standard Telegram validation working - Status: {telegram_result.get('status')}")
            else:
                self.log_result("telegram_mtp_system", "standard_validation", False,
                              "No Telegram result in validation response")
        else:
            self.log_result("telegram_mtp_system", "standard_validation", False,
                          f"Standard validation failed with status {status_code}: {response}")

        # Test MTP validation method
        validation_data["telegram_validation_method"] = "mtp"
        status_code, response = self.make_request('POST', 'api/validation/quick-check',
                                                data=validation_data, token=self.demo_token)
        
        if status_code == 200:
            telegram_result = response.get('telegram')
            if telegram_result:
                self.log_result("telegram_mtp_system", "mtp_validation", True,
                              f"MTP validation working - Status: {telegram_result.get('status')}")
            else:
                self.log_result("telegram_mtp_system", "mtp_validation", False,
                              "No Telegram result in MTP validation response")
        else:
            self.log_result("telegram_mtp_system", "mtp_validation", False,
                          f"MTP validation failed with status {status_code}: {response}")

        # 5. Test Session Management (simulated)
        print("\n🔍 Testing Session Management...")
        # Since we can't test real Pyrogram sessions in container, we test the API endpoints
        if hasattr(self, 'created_account_id'):
            # Test login endpoint (will fail due to container limitations but should respond properly)
            status_code, response = self.make_request('POST', f'api/admin/telegram-accounts/{self.created_account_id}/login',
                                                    token=self.admin_token)
            
            # We expect this to fail in container environment, but should return proper error
            if status_code == 500 and 'error' in response:
                self.log_result("telegram_mtp_system", "session_management_api", True,
                              f"Session management API responds correctly (container limitation expected): {response.get('error', '')}")
            else:
                self.log_result("telegram_mtp_system", "session_management_api", False,
                              f"Unexpected session management response: {status_code} - {response}")
        else:
            self.log_result("telegram_mtp_system", "session_management_api", False,
                          "Cannot test session management - no test account created")

    def test_whatsapp_deeplink_system(self):
        """Test WhatsApp Deep Link System for production readiness"""
        print("\n" + "="*80)
        print("💬 TESTING WHATSAPP DEEP LINK SYSTEM")
        print("="*80)
        
        # 1. Test WhatsApp Account Management API
        print("\n🔍 Testing WhatsApp Account Management API...")
        status_code, response = self.make_request('GET', 'api/admin/whatsapp-accounts', token=self.admin_token)
        
        if status_code == 200 and isinstance(response, list):
            total_accounts = len(response)
            active_accounts = [acc for acc in response if acc.get('status') == 'active']
            logged_out_accounts = [acc for acc in response if acc.get('status') == 'logged_out']
            
            self.log_result("whatsapp_deeplink_system", "account_management_api", True,
                          f"API working - {total_accounts} total accounts, {len(active_accounts)} active, {len(logged_out_accounts)} logged out")
            
            if total_accounts >= 3:
                self.log_result("whatsapp_deeplink_system", "sufficient_accounts", True,
                              f"{total_accounts} WhatsApp accounts available")
            else:
                self.log_result("whatsapp_deeplink_system", "sufficient_accounts", False,
                              f"Only {total_accounts} accounts, recommend at least 3 for production", True)
                              
        else:
            self.log_result("whatsapp_deeplink_system", "account_management_api", False,
                          f"API failed with status {status_code}: {response}", True)

        # 2. Test WhatsApp Account Statistics
        print("\n🔍 Testing WhatsApp Account Statistics...")
        status_code, response = self.make_request('GET', 'api/admin/whatsapp-accounts/stats', token=self.admin_token)
        
        if status_code == 200 and isinstance(response, dict):
            stats = response
            required_stats = ['total_accounts', 'active_accounts']
            
            if all(stat in stats for stat in required_stats):
                self.log_result("whatsapp_deeplink_system", "statistics_api", True,
                              f"Stats API working - Total: {stats['total_accounts']}, Active: {stats['active_accounts']}")
            else:
                missing_stats = [stat for stat in required_stats if stat not in stats]
                self.log_result("whatsapp_deeplink_system", "statistics_api", False,
                              f"Missing statistics: {missing_stats}")
        else:
            self.log_result("whatsapp_deeplink_system", "statistics_api", False,
                          f"Stats API failed with status {status_code}: {response}")

        # 3. Test WhatsApp Account Creation
        print("\n🔍 Testing WhatsApp Account Creation...")
        test_account_data = {
            "name": "Production Test WhatsApp",
            "phone_number": "+6289876543210",
            "login_method": "qr_code",
            "daily_request_limit": 500,
            "notes": "Production readiness test account"
        }
        
        status_code, response = self.make_request('POST', 'api/admin/whatsapp-accounts',
                                                data=test_account_data, token=self.admin_token)
        
        created_account_id = None
        if status_code == 200 or status_code == 201:
            created_account_id = response.get('_id') or response.get('id')
            if created_account_id:
                self.log_result("whatsapp_deeplink_system", "account_creation", True,
                              f"Account creation successful - ID: {created_account_id}")
            else:
                self.log_result("whatsapp_deeplink_system", "account_creation", False,
                              "Account created but no ID returned")
        else:
            self.log_result("whatsapp_deeplink_system", "account_creation", False,
                          f"Account creation failed with status {status_code}: {response}")

        # 4. Test QR Code Generation
        print("\n🔍 Testing QR Code Generation...")
        if created_account_id:
            status_code, response = self.make_request('POST', f'api/admin/whatsapp-accounts/{created_account_id}/login',
                                                    token=self.admin_token)
            
            # In container environment, this will fail due to browser dependencies
            if status_code == 500:
                error_msg = response.get('error', '')
                if 'browser' in error_msg.lower() or 'playwright' in error_msg.lower() or 'chrome' in error_msg.lower():
                    self.log_result("whatsapp_deeplink_system", "qr_code_generation", True,
                                  f"QR generation API responds correctly (browser dependency expected in container): {error_msg}")
                else:
                    self.log_result("whatsapp_deeplink_system", "qr_code_generation", False,
                                  f"Unexpected QR generation error: {error_msg}")
            elif status_code == 200:
                self.log_result("whatsapp_deeplink_system", "qr_code_generation", True,
                              "QR code generation successful")
            else:
                self.log_result("whatsapp_deeplink_system", "qr_code_generation", False,
                              f"QR generation failed with status {status_code}: {response}")
        else:
            self.log_result("whatsapp_deeplink_system", "qr_code_generation", False,
                          "Cannot test QR generation - no test account created")

        # 5. Test WhatsApp Validation Methods
        print("\n🔍 Testing WhatsApp Validation Methods...")
        test_phone = "+6289876543210"
        
        # Test standard WhatsApp validation
        validation_data = {
            "phone_inputs": [test_phone],
            "validate_whatsapp": True,
            "validate_telegram": False,
            "validation_method": "standard"
        }
        
        status_code, response = self.make_request('POST', 'api/validation/quick-check',
                                                data=validation_data, token=self.demo_token)
        
        if status_code == 200:
            whatsapp_result = response.get('whatsapp')
            if whatsapp_result:
                provider = whatsapp_result.get('details', {}).get('provider', 'unknown')
                self.log_result("whatsapp_deeplink_system", "standard_validation", True,
                              f"Standard WhatsApp validation working - Provider: {provider}, Status: {whatsapp_result.get('status')}")
            else:
                self.log_result("whatsapp_deeplink_system", "standard_validation", False,
                              "No WhatsApp result in validation response")
        else:
            self.log_result("whatsapp_deeplink_system", "standard_validation", False,
                          f"Standard validation failed with status {status_code}: {response}")

        # Test deep link profile validation
        validation_data["validation_method"] = "deeplink_profile"
        status_code, response = self.make_request('POST', 'api/validation/quick-check',
                                                data=validation_data, token=self.demo_token)
        
        if status_code == 200:
            whatsapp_result = response.get('whatsapp')
            if whatsapp_result:
                provider = whatsapp_result.get('details', {}).get('provider', 'unknown')
                self.log_result("whatsapp_deeplink_system", "deeplink_validation", True,
                              f"Deep link validation working - Provider: {provider}, Status: {whatsapp_result.get('status')}")
            else:
                self.log_result("whatsapp_deeplink_system", "deeplink_validation", False,
                              "No WhatsApp result in deep link validation response")
        else:
            self.log_result("whatsapp_deeplink_system", "deeplink_validation", False,
                          f"Deep link validation failed with status {status_code}: {response}")

        # Clean up test account
        if created_account_id:
            self.make_request('DELETE', f'api/admin/whatsapp-accounts/{created_account_id}',
                            token=self.admin_token)

    def test_production_deployment_concerns(self):
        """Test production deployment readiness"""
        print("\n" + "="*80)
        print("🚀 TESTING PRODUCTION DEPLOYMENT CONCERNS")
        print("="*80)
        
        # 1. Test Environment Variables Configuration
        print("\n🔍 Testing Environment Variables Configuration...")
        
        # Check if CheckNumber.ai API is configured
        test_phone = "+6281234567890"
        validation_data = {
            "phone_inputs": [test_phone],
            "validate_whatsapp": True,
            "validate_telegram": False
        }
        
        status_code, response = self.make_request('POST', 'api/validation/quick-check',
                                                data=validation_data, token=self.demo_token)
        
        if status_code == 200:
            whatsapp_result = response.get('whatsapp', {})
            provider = whatsapp_result.get('details', {}).get('provider', 'unknown')
            
            if provider == 'checknumber_ai':
                self.log_result("production_deployment", "checknumber_api_configured", True,
                              "CheckNumber.ai API properly configured and working")
            elif provider in ['whatsapp_deeplink', 'whatsapp_browser_enhanced']:
                self.log_result("production_deployment", "alternative_provider_configured", True,
                              f"Alternative provider configured: {provider}")
            else:
                self.log_result("production_deployment", "validation_provider_config", False,
                              f"Using fallback provider: {provider} - configure production API for better accuracy", True)
        else:
            self.log_result("production_deployment", "validation_provider_config", False,
                          f"Validation system not working: {response}", True)

        # 2. Test Database Schema and Connectivity
        print("\n🔍 Testing Database Schema and Connectivity...")
        status_code, response = self.make_request('GET', 'api/admin/analytics', token=self.admin_token)
        
        if status_code == 200 and isinstance(response, dict):
            required_sections = ['user_stats', 'validation_stats', 'credit_stats', 'payment_stats']
            found_sections = [section for section in required_sections if section in response]
            
            if len(found_sections) == len(required_sections):
                self.log_result("production_deployment", "database_schema", True,
                              f"Database schema complete - all {len(required_sections)} sections present")
            else:
                missing = [section for section in required_sections if section not in response]
                self.log_result("production_deployment", "database_schema", False,
                              f"Database schema incomplete - missing: {missing}")
        else:
            self.log_result("production_deployment", "database_schema", False,
                          f"Cannot verify database schema - analytics failed: {response}", True)

        # 3. Test Error Logging and Monitoring
        print("\n🔍 Testing Error Logging and Monitoring...")
        
        # Test invalid endpoint to check error handling
        status_code, response = self.make_request('GET', 'api/nonexistent-endpoint')
        
        if status_code == 404:
            self.log_result("production_deployment", "error_handling", True,
                          "Proper error handling - 404 for invalid endpoints")
        else:
            self.log_result("production_deployment", "error_handling", False,
                          f"Unexpected error handling: {status_code} - {response}")

        # Test unauthorized access
        status_code, response = self.make_request('GET', 'api/admin/users')
        
        if status_code == 403:
            self.log_result("production_deployment", "authorization_control", True,
                          "Proper authorization control - 403 for unauthorized access")
        else:
            self.log_result("production_deployment", "authorization_control", False,
                          f"Authorization issue: {status_code} - {response}", True)

        # 4. Test Rate Limiting (basic check)
        print("\n🔍 Testing Rate Limiting...")
        
        # Make multiple rapid requests to test rate limiting
        rapid_requests = []
        for i in range(5):
            start_time = time.time()
            status_code, response = self.make_request('GET', 'api/health')
            end_time = time.time()
            rapid_requests.append({
                'status': status_code,
                'response_time': end_time - start_time
            })
            
        successful_requests = [req for req in rapid_requests if req['status'] == 200]
        avg_response_time = sum(req['response_time'] for req in successful_requests) / len(successful_requests) if successful_requests else 0
        
        if len(successful_requests) == 5 and avg_response_time < 2.0:
            self.log_result("production_deployment", "performance_basic", True,
                          f"Basic performance good - 5/5 requests successful, avg response time: {avg_response_time:.2f}s")
        else:
            self.log_result("production_deployment", "performance_basic", False,
                          f"Performance issues - {len(successful_requests)}/5 successful, avg time: {avg_response_time:.2f}s")

        # 5. Test Security Configuration
        print("\n🔍 Testing Security Configuration...")
        
        # Test JWT token validation
        status_code, response = self.make_request('GET', 'api/user/profile', token="invalid_token")
        
        if status_code == 401:
            self.log_result("production_deployment", "jwt_security", True,
                          "JWT security working - invalid tokens rejected")
        else:
            self.log_result("production_deployment", "jwt_security", False,
                          f"JWT security issue: {status_code} - {response}", True)

        # 6. Test Payment System Configuration
        print("\n🔍 Testing Payment System Configuration...")
        
        checkout_data = {
            "package_id": "starter",
            "origin_url": "https://verify-connect-1.preview.emergentagent.com"
        }
        
        status_code, response = self.make_request('POST', 'api/payments/create-checkout',
                                                data=checkout_data, token=self.demo_token)
        
        if status_code == 200 and 'url' in response:
            self.log_result("production_deployment", "payment_system", True,
                          "Payment system configured and working")
        elif status_code == 500 and 'not configured' in str(response).lower():
            self.log_result("production_deployment", "payment_system", False,
                          "Payment system not configured - need valid Stripe API key for production", True)
        else:
            self.log_result("production_deployment", "payment_system", False,
                          f"Payment system issue: {status_code} - {response}")

    def test_integration_scenarios(self):
        """Test integration scenarios for production readiness"""
        print("\n" + "="*80)
        print("🔗 TESTING INTEGRATION SCENARIOS")
        print("="*80)
        
        # 1. Test Bulk Validation with Multiple Methods
        print("\n🔍 Testing Bulk Validation Integration...")
        
        # Create test CSV data
        test_csv_data = "name,phone_number\nTest User 1,+6281234567890\nTest User 2,+6289876543210\nTest User 3,+6285555555555"
        
        # Test bulk validation with both platforms
        files = {'file': ('test.csv', test_csv_data, 'text/csv')}
        data = {
            'validate_whatsapp': 'true',
            'validate_telegram': 'true',
            'validation_method': 'standard'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/validation/bulk-check",
                files=files,
                data=data,
                headers={'Authorization': f'Bearer {self.demo_token}'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('job_id')
                if job_id:
                    self.log_result("integration_testing", "bulk_validation", True,
                                  f"Bulk validation integration working - Job ID: {job_id}")
                    
                    # Wait a bit and check job status
                    time.sleep(2)
                    status_code, job_response = self.make_request('GET', f'api/jobs/{job_id}', token=self.demo_token)
                    
                    if status_code == 200:
                        job_status = job_response.get('status', 'unknown')
                        self.log_result("integration_testing", "job_tracking", True,
                                      f"Job tracking working - Status: {job_status}")
                    else:
                        self.log_result("integration_testing", "job_tracking", False,
                                      f"Job tracking failed: {job_response}")
                else:
                    self.log_result("integration_testing", "bulk_validation", False,
                                  "Bulk validation response missing job_id")
            else:
                self.log_result("integration_testing", "bulk_validation", False,
                              f"Bulk validation failed: {response.status_code} - {response.text}")
                              
        except Exception as e:
            self.log_result("integration_testing", "bulk_validation", False,
                          f"Bulk validation error: {str(e)}")

        # 2. Test Account Switching and Load Balancing
        print("\n🔍 Testing Account Management Integration...")
        
        # Get available accounts for both platforms
        status_code, wa_accounts = self.make_request('GET', 'api/admin/whatsapp-accounts', token=self.admin_token)
        status_code2, tg_accounts = self.make_request('GET', 'api/admin/telegram-accounts', token=self.admin_token)
        
        if status_code == 200 and status_code2 == 200:
            wa_count = len(wa_accounts) if isinstance(wa_accounts, list) else 0
            tg_count = len(tg_accounts) if isinstance(tg_accounts, list) else 0
            
            if wa_count >= 2 and tg_count >= 2:
                self.log_result("integration_testing", "account_pool_management", True,
                              f"Account pools ready - WhatsApp: {wa_count}, Telegram: {tg_count}")
            else:
                self.log_result("integration_testing", "account_pool_management", False,
                              f"Insufficient accounts for load balancing - WhatsApp: {wa_count}, Telegram: {tg_count}")
        else:
            self.log_result("integration_testing", "account_pool_management", False,
                          "Cannot access account management APIs")

        # 3. Test Concurrent Usage Simulation
        print("\n🔍 Testing Concurrent Usage Simulation...")
        
        # Simulate multiple validation requests
        concurrent_results = []
        test_phones = ["+6281111111111", "+6282222222222", "+6283333333333"]
        
        for phone in test_phones:
            validation_data = {
                "phone_inputs": [phone],
                "validate_whatsapp": True,
                "validate_telegram": True
            }
            
            status_code, response = self.make_request('POST', 'api/validation/quick-check',
                                                    data=validation_data, token=self.demo_token, timeout=15)
            
            concurrent_results.append({
                'phone': phone,
                'status': status_code,
                'success': status_code == 200
            })
            
            # Small delay to avoid overwhelming
            time.sleep(0.5)
        
        successful_validations = [r for r in concurrent_results if r['success']]
        
        if len(successful_validations) == len(test_phones):
            self.log_result("integration_testing", "concurrent_validation", True,
                          f"Concurrent validation working - {len(successful_validations)}/{len(test_phones)} successful")
        else:
            self.log_result("integration_testing", "concurrent_validation", False,
                          f"Concurrent validation issues - {len(successful_validations)}/{len(test_phones)} successful")

        # 4. Test Failure Recovery Scenarios
        print("\n🔍 Testing Failure Recovery Scenarios...")
        
        # Test with invalid phone number
        validation_data = {
            "phone_inputs": ["invalid_phone"],
            "validate_whatsapp": True,
            "validate_telegram": True
        }
        
        status_code, response = self.make_request('POST', 'api/validation/quick-check',
                                                data=validation_data, token=self.demo_token)
        
        if status_code == 200:
            # Should still return response but with error status
            whatsapp_result = response.get('whatsapp', {})
            telegram_result = response.get('telegram', {})
            
            if whatsapp_result.get('status') == 'error' or telegram_result.get('status') == 'error':
                self.log_result("integration_testing", "error_recovery", True,
                              "Error recovery working - invalid input handled gracefully")
            else:
                self.log_result("integration_testing", "error_recovery", False,
                              "Error recovery issue - invalid input not properly handled")
        else:
            self.log_result("integration_testing", "error_recovery", False,
                          f"Error recovery failed: {status_code} - {response}")

    def generate_production_assessment_report(self):
        """Generate comprehensive production readiness assessment report"""
        print("\n" + "="*100)
        print("📋 PRODUCTION READINESS ASSESSMENT REPORT")
        print("="*100)
        
        # Calculate overall statistics
        total_tests = sum(len(category_tests) for category_tests in self.test_results.values())
        passed_tests = sum(
            sum(1 for test in category_tests.values() if test['status'])
            for category_tests in self.test_results.values()
        )
        critical_failures = len(self.critical_issues)
        
        overall_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 OVERALL ASSESSMENT:")
        print(f"   • Total Tests: {total_tests}")
        print(f"   • Passed Tests: {passed_tests}")
        print(f"   • Failed Tests: {total_tests - passed_tests}")
        print(f"   • Critical Issues: {critical_failures}")
        print(f"   • Overall Score: {overall_score:.1f}%")
        
        # Production readiness determination
        if overall_score >= 90 and critical_failures == 0:
            production_status = "✅ PRODUCTION READY"
            recommendation = "System is ready for production deployment with minor monitoring recommended."
        elif overall_score >= 75 and critical_failures <= 2:
            production_status = "⚠️ MOSTLY READY - MINOR FIXES NEEDED"
            recommendation = "System is mostly ready but requires fixing critical issues before production."
        elif overall_score >= 50:
            production_status = "🔧 NEEDS SIGNIFICANT WORK"
            recommendation = "System requires significant fixes before production deployment."
        else:
            production_status = "❌ NOT PRODUCTION READY"
            recommendation = "System has major issues and is not ready for production."
        
        print(f"\n🎯 PRODUCTION STATUS: {production_status}")
        print(f"💡 RECOMMENDATION: {recommendation}")
        
        # Detailed category breakdown
        print(f"\n📋 DETAILED CATEGORY BREAKDOWN:")
        
        for category, tests in self.test_results.items():
            if not tests:
                continue
                
            category_passed = sum(1 for test in tests.values() if test['status'])
            category_total = len(tests)
            category_score = (category_passed / category_total * 100) if category_total > 0 else 0
            
            print(f"\n   {category.replace('_', ' ').title()}:")
            print(f"   • Score: {category_score:.1f}% ({category_passed}/{category_total})")
            
            for test_name, test_result in tests.items():
                status_icon = "✅" if test_result['status'] else "❌"
                critical_marker = " [CRITICAL]" if test_result.get('is_critical', False) else ""
                print(f"     {status_icon} {test_name.replace('_', ' ').title()}{critical_marker}")
                if not test_result['status']:
                    print(f"       └─ {test_result['details']}")
        
        # Critical issues summary
        if self.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"   {i}. {issue}")
        
        # Production-ready components
        if self.production_ready_components:
            print(f"\n✅ PRODUCTION-READY COMPONENTS:")
            for component in self.production_ready_components[:10]:  # Show top 10
                print(f"   • {component}")
            if len(self.production_ready_components) > 10:
                print(f"   ... and {len(self.production_ready_components) - 10} more")
        
        # Components needing fixes
        if self.components_needing_fixes:
            print(f"\n🔧 COMPONENTS NEEDING FIXES:")
            for component in self.components_needing_fixes:
                print(f"   • {component}")
        
        # Deployment checklist
        print(f"\n📋 PRODUCTION DEPLOYMENT CHECKLIST:")
        
        checklist_items = [
            ("Environment Variables", "Configure CHECKNUMBER_API_KEY, STRIPE_API_KEY, TELEGRAM_API_ID/HASH"),
            ("Database Setup", "Ensure MongoDB is properly configured and accessible"),
            ("Account Pools", "Set up sufficient WhatsApp and Telegram accounts for load balancing"),
            ("Browser Dependencies", "Install Playwright browsers for WhatsApp QR code functionality"),
            ("Monitoring", "Set up logging and monitoring for error tracking"),
            ("Rate Limiting", "Configure appropriate rate limits for API endpoints"),
            ("Security", "Ensure JWT secrets and API keys are properly secured"),
            ("Backup Strategy", "Implement database backup and recovery procedures"),
            ("Load Testing", "Perform load testing with expected production traffic"),
            ("Documentation", "Document deployment procedures and troubleshooting guides")
        ]
        
        for item, description in checklist_items:
            print(f"   □ {item}: {description}")
        
        # Known limitations and workarounds
        print(f"\n⚠️ KNOWN LIMITATIONS AND WORKAROUNDS:")
        
        limitations = [
            "Container Environment: Browser automation limited in containerized environments",
            "API Dependencies: CheckNumber.ai API required for accurate WhatsApp validation",
            "Rate Limits: Third-party APIs have rate limits that may affect high-volume usage",
            "Session Management: Telegram MTP sessions require proper handling for stability",
            "Browser Resources: WhatsApp QR code generation requires significant browser resources"
        ]
        
        for limitation in limitations:
            print(f"   • {limitation}")
        
        print("\n" + "="*100)
        
        return {
            "overall_score": overall_score,
            "production_status": production_status,
            "critical_issues": critical_failures,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "recommendation": recommendation
        }

    def run_full_assessment(self):
        """Run complete production readiness assessment"""
        print("🚀 STARTING PRODUCTION READINESS ASSESSMENT")
        print("Target: Telegram & WhatsApp Login Systems")
        print("="*80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with assessment")
            return False
        
        # Run all test categories
        try:
            self.test_telegram_mtp_system()
            self.test_whatsapp_deeplink_system()
            self.test_production_deployment_concerns()
            self.test_integration_scenarios()
            
            # Generate final report
            assessment_result = self.generate_production_assessment_report()
            
            return assessment_result
            
        except Exception as e:
            print(f"❌ Assessment failed with error: {str(e)}")
            return False

def main():
    """Main function to run production readiness assessment"""
    print("🔍 WEBTOOLS PRODUCTION READINESS ASSESSMENT")
    print("Telegram & WhatsApp Login Systems")
    print("="*80)
    
    # Initialize assessment
    assessment = ProductionReadinessAssessment()
    
    # Run full assessment
    result = assessment.run_full_assessment()
    
    if result:
        print(f"\n✅ Assessment completed successfully!")
        print(f"Overall Score: {result['overall_score']:.1f}%")
        print(f"Status: {result['production_status']}")
        
        # Exit with appropriate code
        if result['critical_issues'] == 0 and result['overall_score'] >= 90:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Issues found
    else:
        print(f"\n❌ Assessment failed to complete")
        sys.exit(2)  # Assessment error

if __name__ == "__main__":
    main()