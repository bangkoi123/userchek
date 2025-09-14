import aiohttp
import asyncio
from datetime import datetime
import json
import random
import time

class WhatsAppTester:
    def __init__(self):
        self.results = {}
        self.test_numbers = [
            "6281261623389",
            "6282151118348", 
            "6285586712458",
            "62855717536356",
            "6289664393975",
            "6281807801515",
            "6281290529129",
            "6283866651289",
            "6289530706258",
            "6285163631515",
            "6282370723099",
            "62881026999701",
            "6285750437717",
            "6282222208609",
            "089689547785",
            "082253767671"
        ]
    
    def normalize_phone(self, phone):
        """Normalize phone number format"""
        phone = phone.strip().replace('+', '').replace('-', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif not phone.startswith('62'):
            phone = '62' + phone
        return phone
    
    async def method1_wa_me(self, session, phone):
        """Method 1: wa.me endpoint"""
        phone = self.normalize_phone(phone)
        url = f"https://wa.me/{phone}"
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return {"status": "error", "method": "wa.me", "http_status": response.status}
                
                html = await response.text()
                
                # Analysis patterns
                indicators = {
                    'has_chat_link': 'web.whatsapp.com/send' in html,
                    'has_whatsapp_scheme': 'whatsapp://send' in html,
                    'main_block_visible': 'main_block' in html and 'style="display: none"' not in html,
                    'fallback_hidden': 'fallback_block' in html and 'style="display: none"' in html,
                    'no_error_message': 'error' not in html.lower() and 'invalid' not in html.lower()
                }
                
                score = sum(indicators.values())
                is_active = score >= 3
                
                return {
                    "status": "active" if is_active else "inactive",
                    "method": "wa.me",
                    "score": f"{score}/5",
                    "indicators": indicators,
                    "raw_response_length": len(html)
                }
                
        except Exception as e:
            return {"status": "error", "method": "wa.me", "error": str(e)}
    
    async def method2_api_whatsapp(self, session, phone):
        """Method 2: api.whatsapp.com endpoint (current method)"""
        phone = self.normalize_phone(phone)
        url = f"https://api.whatsapp.com/send/?phone={phone}&text&type=phone_number&app_absent=0"
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return {"status": "error", "method": "api.whatsapp.com", "http_status": response.status}
                
                html = await response.text()
                
                # Enhanced error detection
                error_patterns = [
                    'error', 'invalid', 'tidak valid', 'nomor tidak valid', 
                    'phone number is invalid', 'number not found', 'not available',
                    'tidak tersedia', 'tidak ditemukan', 'gagal', 'failed'
                ]
                
                has_error_message = any(pattern in html.lower() for pattern in error_patterns)
                
                indicators = {
                    'has_send_link': 'web.whatsapp.com/send/' in html,
                    'main_block_visible': 'main_block' in html and 'style="display: none"' not in html,
                    'app_absent_0': 'app_absent=0' in html,
                    'no_error_message': not has_error_message,
                    'fallback_hidden': 'fallback_block' in html and 'style="display: none"' in html
                }
                
                score = sum(indicators.values())
                
                # If there's an error message, immediately mark as inactive
                if has_error_message:
                    is_active = False
                else:
                    is_active = score >= 4
                
                return {
                    "status": "active" if is_active else "inactive",
                    "method": "api.whatsapp.com",
                    "score": f"{score}/5",
                    "indicators": indicators,
                    "has_error": has_error_message,
                    "raw_response_length": len(html)
                }
                
        except Exception as e:
            return {"status": "error", "method": "api.whatsapp.com", "error": str(e)}
    
    async def method3_web_whatsapp(self, session, phone):
        """Method 3: web.whatsapp.com direct"""
        phone = self.normalize_phone(phone)
        url = f"https://web.whatsapp.com/send/?phone={phone}&text="
        
        try:
            # Add realistic headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Referer': 'https://web.whatsapp.com/',
            }
            
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status != 200:
                    return {"status": "error", "method": "web.whatsapp.com", "http_status": response.status}
                
                html = await response.text()
                
                # Different analysis for web.whatsapp.com
                indicators = {
                    'has_qr_code': 'qr-code' in html.lower() or 'qr_code' in html.lower(),
                    'has_chat_interface': 'chat' in html.lower(),
                    'no_invalid_number': 'invalid number' not in html.lower(),
                    'has_whatsapp_ui': 'whatsapp' in html.lower(),
                    'no_error_page': '404' not in html and 'error' not in html.lower()
                }
                
                score = sum(indicators.values())
                is_active = score >= 3
                
                return {
                    "status": "active" if is_active else "inactive",
                    "method": "web.whatsapp.com",
                    "score": f"{score}/5",
                    "indicators": indicators,
                    "raw_response_length": len(html)
                }
                
        except Exception as e:
            return {"status": "error", "method": "web.whatsapp.com", "error": str(e)}
    
    async def method4_mobile_api(self, session, phone):
        """Method 4: Mobile API endpoints simulation"""
        phone = self.normalize_phone(phone)
        
        # Try different mobile-like endpoints
        endpoints = [
            f"https://wa.me/{phone}?text=",
            f"https://api.whatsapp.com/send?phone={phone}",
            f"https://chat.whatsapp.com/{phone}"
        ]
        
        results = []
        
        # Mobile-like headers
        headers = {
            'User-Agent': 'WhatsApp/2.21.4.18 A',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        
        for endpoint in endpoints:
            try:
                async with session.get(endpoint, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    html = await response.text()
                    
                    has_valid_response = response.status == 200
                    has_whatsapp_content = 'whatsapp' in html.lower()
                    no_error = 'error' not in html.lower() and 'invalid' not in html.lower()
                    
                    results.append({
                        "endpoint": endpoint,
                        "status_code": response.status,
                        "has_content": has_whatsapp_content,
                        "no_error": no_error,
                        "response_length": len(html)
                    })
                    
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "error": str(e)
                })
        
        # Aggregate results
        successful_endpoints = [r for r in results if r.get('status_code') == 200 and r.get('has_content') and r.get('no_error')]
        is_active = len(successful_endpoints) >= 2
        
        return {
            "status": "active" if is_active else "inactive",
            "method": "mobile_api",
            "successful_endpoints": len(successful_endpoints),
            "total_endpoints": len(endpoints),
            "results": results
        }
    
    async def method5_business_directory(self, session, phone):
        """Method 5: Business directory and profile check"""
        phone = self.normalize_phone(phone)
        
        # Check business profile indicators
        business_endpoints = [
            f"https://business.whatsapp.com/profile/{phone}",
            f"https://wa.me/{phone}?text=hello",
            f"https://api.whatsapp.com/send/?phone={phone}&text=hello"
        ]
        
        business_indicators = {
            'has_business_profile': False,
            'has_profile_pic': False,
            'has_business_hours': False,
            'has_catalog': False,
            'has_about': False
        }
        
        for endpoint in business_endpoints:
            try:
                async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Check for business indicators
                        if 'business' in html.lower():
                            business_indicators['has_business_profile'] = True
                        if 'profile' in html.lower() and 'picture' in html.lower():
                            business_indicators['has_profile_pic'] = True
                        if 'hours' in html.lower() or 'open' in html.lower():
                            business_indicators['has_business_hours'] = True
                        if 'catalog' in html.lower() or 'products' in html.lower():
                            business_indicators['has_catalog'] = True
                        if 'about' in html.lower() or 'description' in html.lower():
                            business_indicators['has_about'] = True
                            
            except Exception:
                continue
        
        score = sum(business_indicators.values())
        is_active = score >= 1  # More lenient for business check
        
        return {
            "status": "active" if is_active else "inactive", 
            "method": "business_directory",
            "score": f"{score}/5",
            "indicators": business_indicators
        }
    
    async def test_all_methods(self):
        """Test all methods for all numbers"""
        print("🚀 Starting comprehensive WhatsApp validation testing...")
        print(f"📱 Testing {len(self.test_numbers)} numbers with 5 methods")
        print("=" * 80)
        
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for i, phone in enumerate(self.test_numbers, 1):
                print(f"\n📞 Testing {phone} ({i}/{len(self.test_numbers)})")
                print("-" * 50)
                
                # Test each method
                methods = [
                    ("Method 1: wa.me", self.method1_wa_me),
                    ("Method 2: api.whatsapp.com", self.method2_api_whatsapp),
                    ("Method 3: web.whatsapp.com", self.method3_web_whatsapp),
                    ("Method 4: mobile_api", self.method4_mobile_api),
                    ("Method 5: business_directory", self.method5_business_directory)
                ]
                
                phone_results = {}
                
                for method_name, method_func in methods:
                    try:
                        print(f"  Testing {method_name}...")
                        result = await method_func(session, phone)
                        phone_results[method_name] = result
                        
                        status = result.get('status', 'unknown')
                        print(f"    Result: {status}")
                        
                        # Add small delay between methods
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        phone_results[method_name] = {"status": "error", "error": str(e)}
                        print(f"    Error: {str(e)}")
                
                self.results[phone] = phone_results
                
                # Add delay between numbers to avoid rate limiting
                if i < len(self.test_numbers):
                    print("  ⏳ Waiting 3 seconds...")
                    await asyncio.sleep(3)
        
        return self.results
    
    def analyze_results(self):
        """Analyze and compare method performance"""
        print("\n" + "=" * 80)
        print("📊 ANALYSIS RESULTS")
        print("=" * 80)
        
        method_stats = {
            "Method 1: wa.me": {"active": 0, "inactive": 0, "error": 0},
            "Method 2: api.whatsapp.com": {"active": 0, "inactive": 0, "error": 0},
            "Method 3: web.whatsapp.com": {"active": 0, "inactive": 0, "error": 0},
            "Method 4: mobile_api": {"active": 0, "inactive": 0, "error": 0},
            "Method 5: business_directory": {"active": 0, "inactive": 0, "error": 0}
        }
        
        # Count results for each method
        for phone, phone_results in self.results.items():
            for method, result in phone_results.items():
                status = result.get('status', 'error')
                if status in method_stats[method]:
                    method_stats[method][status] += 1
        
        # Print method comparison
        print("\n🔍 METHOD COMPARISON:")
        for method, stats in method_stats.items():
            total = sum(stats.values())
            active_pct = (stats['active'] / total * 100) if total > 0 else 0
            error_pct = (stats['error'] / total * 100) if total > 0 else 0
            
            print(f"\n{method}:")
            print(f"  Active: {stats['active']}/{total} ({active_pct:.1f}%)")
            print(f"  Inactive: {stats['inactive']}/{total}")
            print(f"  Errors: {stats['error']}/{total} ({error_pct:.1f}%)")
        
        # Print detailed results for each number
        print(f"\n📱 DETAILED RESULTS PER NUMBER:")
        for phone, phone_results in self.results.items():
            print(f"\n{phone}:")
            for method, result in phone_results.items():
                status = result.get('status', 'unknown')
                method_short = method.split(':')[0]
                print(f"  {method_short:12} → {status}")
        
        return method_stats

    def save_results(self):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/whatsapp_testing_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename

# Run the testing
async def main():
    tester = WhatsAppTester()
    results = await tester.test_all_methods()
    tester.analyze_results()
    tester.save_results()

if __name__ == "__main__":
    asyncio.run(main())