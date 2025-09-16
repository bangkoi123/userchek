#!/usr/bin/env python3
"""
Debug test to check the actual response format from quick-check endpoint
"""

import requests
import json

def test_response_format():
    base_url = "https://wa-deeplink-check.preview.emergentagent.com"
    
    # Login demo user
    login_response = requests.post(f"{base_url}/api/auth/login", 
                                 json={"username": "demo", "password": "demo123"})
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
        
    token = login_response.json()['token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Test standard method
    print("🔍 Testing Standard Method Response Format...")
    data = {
        "phone_inputs": ["+6281234567890"], 
        "validate_whatsapp": True, 
        "validate_telegram": True,
        "validation_method": "standard"
    }
    
    response = requests.post(f"{base_url}/api/validation/quick-check", 
                           json=data, headers=headers, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response received")
        print(f"📊 Response keys: {list(result.keys())}")
        print(f"📊 Full response:")
        print(json.dumps(result, indent=2, default=str))
        
        # Check if details contain individual results
        if 'details' in result:
            details = result['details']
            if details and len(details) > 0:
                first_detail = details[0]
                print(f"\n📊 First detail keys: {list(first_detail.keys())}")
                if 'whatsapp' in first_detail:
                    print(f"✅ WhatsApp result found in details")
                    whatsapp_result = first_detail['whatsapp']
                    print(f"📊 WhatsApp result: {json.dumps(whatsapp_result, indent=2, default=str)}")
                else:
                    print(f"❌ No WhatsApp result in details")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_response_format()