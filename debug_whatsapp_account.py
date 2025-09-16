#!/usr/bin/env python3
"""
Quick Test Script - Debug WhatsApp Account Creation Issue
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://checktool.preview.emergentagent.com"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

def test_backend_api():
    """Test backend API functionality"""
    print("🔍 DEBUGGING WHATSAPP ACCOUNT CREATION")
    print("=" * 50)
    
    # Step 1: Test backend health
    print("\n1. Testing Backend Health...")
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is accessible and running")
        else:
            print(f"⚠️ Backend responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend health check failed: {str(e)}")
        return False
    
    # Step 2: Test admin login
    print("\n2. Testing Admin Login...")
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            headers={"Content-Type": "application/json"},
            json=ADMIN_CREDENTIALS,
            timeout=10
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            admin_token = login_data.get("token")
            print("✅ Admin login successful")
            print(f"   Token: {admin_token[:50]}...")
        else:
            print(f"❌ Admin login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Admin login error: {str(e)}")
        return False
    
    # Step 3: Test WhatsApp account creation
    print("\n3. Testing WhatsApp Account Creation...")
    
    test_account_data = {
        "name": f"Debug Test Account {datetime.now().strftime('%H%M%S')}",
        "phone_number": "+628123456789",
        "login_method": "qr_code",
        "max_daily_requests": 100,
        "notes": "Debug test account"
    }
    
    try:
        create_response = requests.post(
            f"{BACKEND_URL}/api/admin/whatsapp-accounts",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=test_account_data,
            timeout=15
        )
        
        print(f"   Response Status: {create_response.status_code}")
        print(f"   Response Headers: {dict(create_response.headers)}")
        
        if create_response.status_code == 200:
            create_data = create_response.json()
            print("✅ WhatsApp account creation successful")
            print(f"   Account ID: {create_data.get('account', {}).get('_id', 'N/A')}")
            print(f"   Message: {create_data.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ WhatsApp account creation failed")
            print(f"   Error Response: {create_response.text}")
            
            # Try to parse error
            try:
                error_data = create_response.json()
                print(f"   Error Detail: {error_data.get('detail', 'Unknown error')}")
            except:
                pass
                
            return False
            
    except Exception as e:
        print(f"❌ WhatsApp account creation error: {str(e)}")
        return False
    
    # Step 4: List existing accounts
    print("\n4. Listing Existing WhatsApp Accounts...")
    try:
        list_response = requests.get(
            f"{BACKEND_URL}/api/admin/whatsapp-accounts",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        
        if list_response.status_code == 200:
            accounts = list_response.json()
            print(f"✅ Found {len(accounts)} WhatsApp accounts:")
            for i, account in enumerate(accounts[-3:], 1):  # Show last 3
                print(f"   {i}. {account.get('name', 'N/A')} - {account.get('phone_number', 'N/A')} [{account.get('status', 'N/A')}]")
        else:
            print(f"⚠️ Could not list accounts: {list_response.status_code}")
            
    except Exception as e:
        print(f"❌ List accounts error: {str(e)}")

def test_frontend_api_call():
    """Simulate frontend API call to debug issue"""
    print("\n" + "=" * 50)
    print("🖥️ TESTING FRONTEND API CALL SIMULATION")
    print("=" * 50)
    
    # Step 1: Get admin token (same as frontend would do)
    print("\n1. Simulating Frontend Login...")
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            headers={"Content-Type": "application/json"},
            json=ADMIN_CREDENTIALS,
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ Frontend login simulation failed: {login_response.status_code}")
            return False
            
        admin_token = login_response.json().get("token")
        print("✅ Frontend login simulation successful")
        
    except Exception as e:
        print(f"❌ Frontend login simulation error: {str(e)}")
        return False
    
    # Step 2: Simulate exact frontend request
    print("\n2. Simulating Frontend WhatsApp Account Creation...")
    
    # This is exactly what frontend sends
    frontend_payload = {
        "name": "Frontend Test",
        "phone_number": "+628968954785",
        "login_method": "qr_code",
        "max_daily_requests": 100,
        "notes": "Optional notes about this account"
    }
    
    # Headers exactly like frontend
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://checktool.preview.emergentagent.com",
        "Referer": "https://checktool.preview.emergentagent.com/admin/whatsapp-accounts"
    }
    
    try:
        print(f"   Request URL: {BACKEND_URL}/api/admin/whatsapp-accounts")
        print(f"   Request Method: POST")
        print(f"   Request Headers: {json.dumps({k: v for k, v in headers.items() if k != 'Authorization'}, indent=2)}")
        print(f"   Request Payload: {json.dumps(frontend_payload, indent=2)}")
        
        response = requests.post(
            f"{BACKEND_URL}/api/admin/whatsapp-accounts",
            headers=headers,
            json=frontend_payload,
            timeout=15
        )
        
        print(f"\n   Response Status: {response.status_code}")
        print(f"   Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Frontend simulation successful!")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Frontend simulation failed")
            print(f"   Error Response: {response.text}")
            
            # Check for CORS issues
            if response.status_code == 403:
                print("   🔍 Possible CORS or authentication issue")
            elif response.status_code == 422:
                print("   🔍 Possible validation error")
            elif response.status_code == 500:
                print("   🔍 Backend server error")
                
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error - backend might not be accessible at {BACKEND_URL}")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout - backend might be slow")
        return False
    except Exception as e:
        print(f"❌ Frontend simulation error: {str(e)}")
        return False

def main():
    """Main test function"""
    print(f"🚀 Starting WhatsApp Account Creation Debug")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    
    # Test backend directly
    backend_success = test_backend_api()
    
    # Test frontend simulation
    frontend_success = test_frontend_api_call()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Backend API Direct: {'✅ PASS' if backend_success else '❌ FAIL'}")
    print(f"Frontend Simulation: {'✅ PASS' if frontend_success else '❌ FAIL'}")
    
    if backend_success and frontend_success:
        print("\n🎉 ALL TESTS PASSED - Issue should be resolved!")
        print("💡 Try creating WhatsApp account again in frontend")
    elif backend_success and not frontend_success:
        print("\n🔍 BACKEND WORKING but FRONTEND ISSUE DETECTED")
        print("💡 Check browser console for errors")
        print("💡 Clear browser cache and cookies")
        print("💡 Check CORS configuration")
    else:
        print("\n❌ BACKEND ISSUE DETECTED")
        print("💡 Check backend logs for errors")
        print("💡 Verify environment variables")
    
    return backend_success and frontend_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)