#!/usr/bin/env python3
"""
Critical debugging script for phonecheck.gen-ai.fun 500 Internal Server Error
Focus: POST /api/validation/quick-check endpoint crashes
"""

import requests
import json
from datetime import datetime

class PhonecheckDebugger:
    def __init__(self):
        self.base_url = "https://phonecheck.gen-ai.fun"
        self.demo_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_errors = []

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

            # Store response status for error checking
            self.last_response_status = response.status_code
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 300:
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

    def critical_phonecheck_debugging(self):
        """CRITICAL: Debug phonecheck.gen-ai.fun 500 Internal Server Error on quick-check endpoint"""
        print("\n" + "="*80)
        print("🚨 CRITICAL BACKEND DEBUGGING - Quick Check Endpoint 500 Error")
        print("="*80)
        print("PROBLEM: POST /api/validation/quick-check returns 500 Internal Server Error")
        print("SCOPE: Debug authentication, basic endpoints, and validation methods")
        print("BASE URL: https://phonecheck.gen-ai.fun/api")
        print("="*80)
        
        debug_results = {
            "health_endpoint": False,
            "demo_login": False,
            "user_profile": False,
            "quick_check_standard": False,
            "quick_check_deeplink": False,
            "error_analysis": False
        }
        
        # 1. Test Health Endpoint
        print("\n🔍 STEP 1: Testing Basic Health Check")
        try:
            success, response = self.run_test(
                "Health Check",
                "GET",
                "api/health",
                200,
                description="Basic health check endpoint"
            )
            debug_results["health_endpoint"] = success
            if success:
                print("   ✅ Backend is accessible and responding")
            else:
                print("   ❌ Backend health check failed")
                self.critical_errors.append("Backend health check failed")
        except Exception as e:
            print(f"   ❌ Health check error: {str(e)}")
            self.critical_errors.append(f"Health check error: {str(e)}")
        
        # 2. Test Demo Login (demo/demo123)
        print("\n🔍 STEP 2: Testing Authentication Flow")
        try:
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
                demo_user_id = response.get('user', {}).get('id')
                demo_credits = response.get('user', {}).get('credits', 0)
                
                print(f"   ✅ Demo login successful")
                print(f"   📊 Demo User ID: {demo_user_id}")
                print(f"   📊 Demo Credits: {demo_credits}")
                print(f"   📊 JWT Token Length: {len(self.demo_token)} characters")
                debug_results["demo_login"] = True
            else:
                print(f"   ❌ Demo login failed: {response}")
                self.critical_errors.append(f"Demo login failed: {response}")
                
        except Exception as e:
            print(f"   ❌ Demo login error: {str(e)}")
            self.critical_errors.append(f"Demo login error: {str(e)}")
        
        # 3. Test User Profile (JWT Auth Verification)
        if debug_results["demo_login"]:
            print("\n🔍 STEP 3: Testing JWT Authentication")
            try:
                success, response = self.run_test(
                    "User Profile",
                    "GET",
                    "api/user/profile",
                    200,
                    token=self.demo_token,
                    description="Verify JWT auth works"
                )
                debug_results["user_profile"] = success
                if success:
                    print("   ✅ JWT authentication working correctly")
                    user_data = response.get('user', {})
                    print(f"   📊 User: {user_data.get('username', 'N/A')}")
                    print(f"   📊 Credits: {user_data.get('credits', 'N/A')}")
                else:
                    print("   ❌ JWT authentication failed")
                    self.critical_errors.append("JWT authentication failed")
            except Exception as e:
                print(f"   ❌ User profile error: {str(e)}")
                self.critical_errors.append(f"User profile error: {str(e)}")
        else:
            print("\n🔍 STEP 3: Skipping JWT test (login failed)")
        
        # 4. Test Quick Check - Standard Method
        if debug_results["demo_login"]:
            print("\n🔍 STEP 4: Testing Quick Check - Standard Method")
            try:
                success, response = self.run_test(
                    "Quick Check Standard",
                    "POST",
                    "api/validation/quick-check",
                    200,
                    data={
                        "phone_inputs": ["+6281234567890"],
                        "validate_whatsapp": True,
                        "validate_telegram": False,
                        "validation_method": "standard"
                    },
                    token=self.demo_token,
                    description="Test standard validation method"
                )
                
                if success:
                    debug_results["quick_check_standard"] = True
                    print("   ✅ Standard validation working")
                    
                    # Analyze response
                    if 'results' in response and response['results']:
                        result = response['results'][0]
                        whatsapp_data = result.get('whatsapp', {})
                        credits_used = response.get('credits_used', 0)
                        
                        print(f"   📊 Credits used: {credits_used}")
                        print(f"   📊 WhatsApp status: {whatsapp_data.get('status', 'N/A')}")
                        
                        details = whatsapp_data.get('details', {})
                        provider = details.get('provider', 'N/A')
                        print(f"   📊 Provider: {provider}")
                        
                    else:
                        print("   ⚠️  No results in response")
                        
                else:
                    print(f"   ❌ Standard validation failed with status: {self.last_response_status}")
                    if hasattr(self, 'last_response_status') and self.last_response_status == 500:
                        print("   🚨 500 INTERNAL SERVER ERROR DETECTED!")
                        print("   💡 This indicates syntax errors or NameErrors in backend code")
                        self.critical_errors.append("Quick Check Standard: 500 Internal Server Error - likely syntax/name errors")
                    else:
                        self.critical_errors.append(f"Quick Check Standard failed with status: {self.last_response_status}")
                        
            except Exception as e:
                print(f"   ❌ Standard validation error: {str(e)}")
                self.critical_errors.append(f"Standard validation error: {str(e)}")
        else:
            print("\n🔍 STEP 4: Skipping Standard validation test (login failed)")
        
        # 5. Test Quick Check - Deep Link Profile Method
        if debug_results["demo_login"]:
            print("\n🔍 STEP 5: Testing Quick Check - Deep Link Profile Method")
            try:
                success, response = self.run_test(
                    "Quick Check DeepLink Profile",
                    "POST",
                    "api/validation/quick-check",
                    200,
                    data={
                        "phone_inputs": ["+6281234567890"],
                        "validate_whatsapp": True,
                        "validate_telegram": False,
                        "validation_method": "deeplink_profile"
                    },
                    token=self.demo_token,
                    description="Test deeplink_profile validation method (premium)"
                )
                
                if success:
                    debug_results["quick_check_deeplink"] = True
                    print("   ✅ Deep Link Profile validation working")
                    
                    # Analyze response
                    if 'results' in response and response['results']:
                        result = response['results'][0]
                        whatsapp_data = result.get('whatsapp', {})
                        credits_used = response.get('credits_used', 0)
                        
                        print(f"   📊 Credits used: {credits_used} (expected: 3)")
                        print(f"   📊 WhatsApp status: {whatsapp_data.get('status', 'N/A')}")
                        
                        details = whatsapp_data.get('details', {})
                        provider = details.get('provider', 'N/A')
                        print(f"   📊 Provider: {provider}")
                        
                        # Check for premium features
                        premium_fields = ['profile_picture', 'last_seen', 'business_info', 'status_message']
                        found_premium = [field for field in premium_fields if field in details]
                        if found_premium:
                            print(f"   ✅ Premium data fields: {found_premium}")
                        else:
                            print("   ⚠️  No premium data fields detected")
                        
                    else:
                        print("   ⚠️  No results in response")
                        
                else:
                    print(f"   ❌ Deep Link Profile validation failed with status: {self.last_response_status}")
                    if hasattr(self, 'last_response_status') and self.last_response_status == 500:
                        print("   🚨 500 INTERNAL SERVER ERROR DETECTED!")
                        print("   💡 This indicates syntax errors or NameErrors in backend code")
                        self.critical_errors.append("Quick Check DeepLink: 500 Internal Server Error - likely syntax/name errors")
                    else:
                        self.critical_errors.append(f"Quick Check DeepLink failed with status: {self.last_response_status}")
                        
            except Exception as e:
                print(f"   ❌ Deep Link Profile validation error: {str(e)}")
                self.critical_errors.append(f"Deep Link Profile validation error: {str(e)}")
        else:
            print("\n🔍 STEP 5: Skipping Deep Link Profile test (login failed)")
        
        # 6. Error Response Analysis
        print("\n🔍 STEP 6: Error Response Analysis")
        if self.critical_errors:
            debug_results["error_analysis"] = False
            print("   ❌ Critical errors detected:")
            for i, error in enumerate(self.critical_errors, 1):
                print(f"      {i}. {error}")
        else:
            debug_results["error_analysis"] = True
            print("   ✅ No critical errors detected")
        
        # 7. Summary and Diagnosis
        print("\n" + "="*80)
        print("🔍 CRITICAL DEBUGGING SUMMARY")
        print("="*80)
        
        total_tests = len(debug_results)
        passed_tests = sum(debug_results.values())
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"📊 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        for test_name, result in debug_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        # Root Cause Analysis
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        
        if not debug_results["health_endpoint"]:
            print("   🚨 CRITICAL: Backend is completely inaccessible")
            print("   💡 RECOMMENDATION: Check server status and deployment")
        elif not debug_results["demo_login"]:
            print("   🚨 CRITICAL: Authentication system is broken")
            print("   💡 RECOMMENDATION: Check user database and JWT configuration")
        elif not debug_results["user_profile"]:
            print("   🚨 CRITICAL: JWT authentication is broken")
            print("   💡 RECOMMENDATION: Check JWT secret and token validation")
        elif not debug_results["quick_check_standard"] or not debug_results["quick_check_deeplink"]:
            print("   🚨 CRITICAL: Validation endpoints have 500 Internal Server Errors")
            print("   💡 ROOT CAUSE: Syntax errors or NameErrors in backend validation code")
            print("   💡 RECOMMENDATION: Check backend logs for Python syntax/import errors")
            print("   💡 LIKELY ISSUES:")
            print("      - Missing imports (e.g., ValidationStatus, datetime)")
            print("      - Undefined variables or functions")
            print("      - Syntax errors in validation logic")
            print("      - Database connection issues")
        else:
            print("   ✅ All systems appear to be working correctly")
            print("   💡 Issue may be intermittent or environment-specific")
        
        print("="*80)
        
        return debug_results

if __name__ == "__main__":
    print("🚀 STARTING CRITICAL PHONECHECK BACKEND DEBUGGING")
    print("="*80)
    
    # Initialize debugger
    debugger = PhonecheckDebugger()
    
    # Run critical debugging for the 500 error issue
    debug_results = debugger.critical_phonecheck_debugging()
    
    # Final summary
    print("\n" + "="*80)
    print("🎯 FINAL TESTING SUMMARY")
    print("="*80)
    
    total_tests = len(debug_results)
    passed_tests = sum(debug_results.values())
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"📊 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    print(f"🔧 Tests Run: {debugger.tests_run}")
    print(f"✅ Tests Passed: {debugger.tests_passed}")
    print(f"❌ Tests Failed: {debugger.tests_run - debugger.tests_passed}")
    
    if debugger.critical_errors:
        print(f"\n🚨 CRITICAL ISSUES FOUND ({len(debugger.critical_errors)}):")
        for i, error in enumerate(debugger.critical_errors, 1):
            print(f"   {i}. {error}")
    
    # Determine overall status
    if success_rate >= 80:
        print("\n🎉 BACKEND STATUS: HEALTHY")
        print("💡 Most functionality is working correctly")
    elif success_rate >= 50:
        print("\n⚠️  BACKEND STATUS: PARTIAL ISSUES")
        print("💡 Some critical issues need attention")
    else:
        print("\n❌ BACKEND STATUS: CRITICAL ISSUES")
        print("💡 Major problems require immediate fixing")
    
    print("="*80)