#!/usr/bin/env python3
"""
Focused validation testing for production readiness assessment
"""

import requests
import json
import time
from datetime import datetime

class ValidationTester:
    def __init__(self, base_url="https://verify-connect-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.demo_token = None
        
    def authenticate(self):
        """Authenticate users"""
        print("🔐 Authenticating...")
        
        # Admin login
        response = requests.post(f"{self.base_url}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if response.status_code == 200:
            self.admin_token = response.json()['token']
            print("   ✅ Admin authenticated")
        else:
            print(f"   ❌ Admin auth failed: {response.text}")
            return False
            
        # Demo login
        response = requests.post(f"{self.base_url}/api/auth/login", json={
            "username": "demo",
            "password": "demo123"
        })
        
        if response.status_code == 200:
            self.demo_token = response.json()['token']
            print("   ✅ Demo authenticated")
        else:
            print(f"   ❌ Demo auth failed: {response.text}")
            return False
            
        return True
    
    def test_whatsapp_validation_methods(self):
        """Test WhatsApp validation methods"""
        print("\n💬 TESTING WHATSAPP VALIDATION METHODS")
        print("="*60)
        
        test_phone = "+6281234567890"
        
        # Test standard WhatsApp validation
        print(f"\n🔍 Testing Standard WhatsApp Validation for {test_phone}")
        response = requests.post(f"{self.base_url}/api/validation/quick-check", 
            json={
                "phone_inputs": [test_phone],
                "validate_whatsapp": True,
                "validate_telegram": False,
                "validation_method": "standard"
            },
            headers={'Authorization': f'Bearer {self.demo_token}'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Standard validation successful")
            print(f"   📊 Response keys: {list(result.keys())}")
            
            if 'whatsapp' in result:
                wa_result = result['whatsapp']
                print(f"   📊 WhatsApp status: {wa_result.get('status')}")
                print(f"   📊 WhatsApp provider: {wa_result.get('details', {}).get('provider', 'unknown')}")
                print(f"   📊 WhatsApp confidence: {wa_result.get('details', {}).get('confidence_score', 'N/A')}")
            else:
                print(f"   ❌ No WhatsApp result in response")
                print(f"   📊 Full response: {result}")
        else:
            print(f"   ❌ Standard validation failed: {response.status_code} - {response.text}")
        
        # Test deep link profile validation
        print(f"\n🔍 Testing Deep Link Profile WhatsApp Validation for {test_phone}")
        response = requests.post(f"{self.base_url}/api/validation/quick-check", 
            json={
                "phone_inputs": [test_phone],
                "validate_whatsapp": True,
                "validate_telegram": False,
                "validation_method": "deeplink_profile"
            },
            headers={'Authorization': f'Bearer {self.demo_token}'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Deep link validation successful")
            print(f"   📊 Response keys: {list(result.keys())}")
            
            if 'whatsapp' in result:
                wa_result = result['whatsapp']
                print(f"   📊 WhatsApp status: {wa_result.get('status')}")
                print(f"   📊 WhatsApp provider: {wa_result.get('details', {}).get('provider', 'unknown')}")
                print(f"   📊 WhatsApp confidence: {wa_result.get('details', {}).get('confidence_score', 'N/A')}")
            else:
                print(f"   ❌ No WhatsApp result in response")
                print(f"   📊 Full response: {result}")
        else:
            print(f"   ❌ Deep link validation failed: {response.status_code} - {response.text}")
    
    def test_telegram_validation_methods(self):
        """Test Telegram validation methods"""
        print("\n📱 TESTING TELEGRAM VALIDATION METHODS")
        print("="*60)
        
        test_phone = "+6281234567890"
        
        # Test standard Telegram validation
        print(f"\n🔍 Testing Standard Telegram Validation for {test_phone}")
        response = requests.post(f"{self.base_url}/api/validation/quick-check", 
            json={
                "phone_inputs": [test_phone],
                "validate_whatsapp": False,
                "validate_telegram": True,
                "telegram_validation_method": "standard"
            },
            headers={'Authorization': f'Bearer {self.demo_token}'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Standard Telegram validation successful")
            print(f"   📊 Response keys: {list(result.keys())}")
            
            if 'telegram' in result:
                tg_result = result['telegram']
                print(f"   📊 Telegram status: {tg_result.get('status')}")
                print(f"   📊 Telegram provider: {tg_result.get('details', {}).get('provider', 'unknown')}")
                print(f"   📊 Telegram details: {tg_result.get('details', {})}")
            else:
                print(f"   ❌ No Telegram result in response")
                print(f"   📊 Full response: {result}")
        else:
            print(f"   ❌ Standard Telegram validation failed: {response.status_code} - {response.text}")
        
        # Test MTP Telegram validation
        print(f"\n🔍 Testing MTP Telegram Validation for {test_phone}")
        response = requests.post(f"{self.base_url}/api/validation/quick-check", 
            json={
                "phone_inputs": [test_phone],
                "validate_whatsapp": False,
                "validate_telegram": True,
                "telegram_validation_method": "mtp"
            },
            headers={'Authorization': f'Bearer {self.demo_token}'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ MTP Telegram validation successful")
            print(f"   📊 Response keys: {list(result.keys())}")
            
            if 'telegram' in result:
                tg_result = result['telegram']
                print(f"   📊 Telegram status: {tg_result.get('status')}")
                print(f"   📊 Telegram provider: {tg_result.get('details', {}).get('provider', 'unknown')}")
                print(f"   📊 Telegram details: {tg_result.get('details', {})}")
            else:
                print(f"   ❌ No Telegram result in response")
                print(f"   📊 Full response: {result}")
        else:
            print(f"   ❌ MTP Telegram validation failed: {response.status_code} - {response.text}")
        
        # Test MTP Profile Deep validation
        print(f"\n🔍 Testing MTP Profile Deep Telegram Validation for {test_phone}")
        response = requests.post(f"{self.base_url}/api/validation/quick-check", 
            json={
                "phone_inputs": [test_phone],
                "validate_whatsapp": False,
                "validate_telegram": True,
                "telegram_validation_method": "mtp_profile"
            },
            headers={'Authorization': f'Bearer {self.demo_token}'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ MTP Profile Deep validation successful")
            print(f"   📊 Response keys: {list(result.keys())}")
            
            if 'telegram' in result:
                tg_result = result['telegram']
                print(f"   📊 Telegram status: {tg_result.get('status')}")
                print(f"   📊 Telegram provider: {tg_result.get('details', {}).get('provider', 'unknown')}")
                print(f"   📊 Telegram details: {tg_result.get('details', {})}")
            else:
                print(f"   ❌ No Telegram result in response")
                print(f"   📊 Full response: {result}")
        else:
            print(f"   ❌ MTP Profile Deep validation failed: {response.status_code} - {response.text}")
    
    def test_combined_validation(self):
        """Test combined WhatsApp and Telegram validation"""
        print("\n🔗 TESTING COMBINED VALIDATION")
        print("="*60)
        
        test_phone = "+6281234567890"
        
        print(f"\n🔍 Testing Combined Validation for {test_phone}")
        response = requests.post(f"{self.base_url}/api/validation/quick-check", 
            json={
                "phone_inputs": [test_phone],
                "validate_whatsapp": True,
                "validate_telegram": True,
                "validation_method": "standard",
                "telegram_validation_method": "standard"
            },
            headers={'Authorization': f'Bearer {self.demo_token}'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Combined validation successful")
            print(f"   📊 Response keys: {list(result.keys())}")
            
            if 'whatsapp' in result:
                wa_result = result['whatsapp']
                print(f"   📊 WhatsApp status: {wa_result.get('status')}")
                print(f"   📊 WhatsApp provider: {wa_result.get('details', {}).get('provider', 'unknown')}")
            else:
                print(f"   ❌ No WhatsApp result in response")
                
            if 'telegram' in result:
                tg_result = result['telegram']
                print(f"   📊 Telegram status: {tg_result.get('status')}")
                print(f"   📊 Telegram provider: {tg_result.get('details', {}).get('provider', 'unknown')}")
            else:
                print(f"   ❌ No Telegram result in response")
                
            if 'providers_used' in result:
                providers = result['providers_used']
                print(f"   📊 Providers used: {providers}")
            else:
                print(f"   ❌ No providers_used field in response")
                
        else:
            print(f"   ❌ Combined validation failed: {response.status_code} - {response.text}")
    
    def test_bulk_validation(self):
        """Test bulk validation functionality"""
        print("\n📋 TESTING BULK VALIDATION")
        print("="*60)
        
        # Create test CSV data
        test_csv_data = "name,phone_number\nTest User 1,+6281234567890\nTest User 2,+6289876543210"
        
        print(f"\n🔍 Testing Bulk Validation with CSV")
        
        try:
            files = {'file': ('test.csv', test_csv_data, 'text/csv')}
            data = {
                'validate_whatsapp': 'true',
                'validate_telegram': 'true',
                'validation_method': 'standard'
            }
            
            response = requests.post(
                f"{self.base_url}/api/validation/bulk-check",
                files=files,
                data=data,
                headers={'Authorization': f'Bearer {self.demo_token}'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Bulk validation submitted successfully")
                print(f"   📊 Response keys: {list(result.keys())}")
                
                job_id = result.get('job_id')
                if job_id:
                    print(f"   📊 Job ID: {job_id}")
                    
                    # Wait a bit and check job status
                    time.sleep(3)
                    job_response = requests.get(
                        f"{self.base_url}/api/jobs/{job_id}",
                        headers={'Authorization': f'Bearer {self.demo_token}'}
                    )
                    
                    if job_response.status_code == 200:
                        job_data = job_response.json()
                        print(f"   📊 Job status: {job_data.get('status')}")
                        print(f"   📊 Job progress: {job_data.get('processed_numbers', 0)}/{job_data.get('total_numbers', 0)}")
                        
                        if job_data.get('status') == 'completed':
                            results = job_data.get('results', {})
                            print(f"   📊 WhatsApp active: {results.get('whatsapp_active', 0)}")
                            print(f"   📊 Telegram active: {results.get('telegram_active', 0)}")
                            print(f"   📊 Inactive: {results.get('inactive', 0)}")
                            print(f"   📊 Errors: {results.get('errors', 0)}")
                    else:
                        print(f"   ❌ Job status check failed: {job_response.status_code}")
                else:
                    print(f"   ❌ No job_id in response")
            else:
                print(f"   ❌ Bulk validation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Bulk validation error: {str(e)}")
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("🧪 VALIDATION SYSTEM TESTING")
        print("="*80)
        
        if not self.authenticate():
            print("❌ Authentication failed")
            return False
        
        self.test_whatsapp_validation_methods()
        self.test_telegram_validation_methods()
        self.test_combined_validation()
        self.test_bulk_validation()
        
        print("\n✅ All validation tests completed")
        return True

if __name__ == "__main__":
    tester = ValidationTester()
    tester.run_all_tests()