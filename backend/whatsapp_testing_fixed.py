import aiohttp
import asyncio
from datetime import datetime
import json
import brotli  # Critical fix for brotli compression
import re

class WhatsAppTesterFixed:
    def __init__(self):
        self.results = {}
        # Known status from Bob's manual testing
        self.known_status = {
            "082253767671": "active",
            "089689547785": "active",  # wa business
            "628123456789": "inactive", 
            "6285586712458": "inactive"
        }
        
        self.test_numbers = [
            "6281261623389",
            "6282151118348", 
            "6285586712458",  # Known inactive
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
            "089689547785",   # Known active (business)
            "082253767671"    # Known active
        ]
    
    def normalize_phone(self, phone):
        """Normalize phone number format"""
        phone = phone.strip().replace('+', '').replace('-', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif not phone.startswith('62'):
            phone = '62' + phone
        return phone
    
    async def method_fixed_wa_me(self, session, phone):
        """FIXED Method: wa.me with proper brotli handling and improved analysis"""
        phone = self.normalize_phone(phone)
        url = f"https://wa.me/{phone}"
        
        # Proper headers to avoid detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',  # Include brotli
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status != 200:
                    return {"status": "error", "method": "wa.me_fixed", "http_status": response.status}
                
                # Read with proper encoding handling
                try:
                    html = await response.text(encoding='utf-8')
                except UnicodeDecodeError:
                    html = await response.text(encoding='latin-1')
                
                # IMPROVED ANALYSIS based on actual WhatsApp patterns
                
                # 1. Check for actual WhatsApp redirect/chat functionality
                has_whatsapp_redirect = bool(re.search(r'web\.whatsapp\.com/send', html))
                has_whatsapp_scheme = bool(re.search(r'whatsapp://send', html))
                has_chat_button = bool(re.search(r'(chat|message|send|continue)', html, re.IGNORECASE))
                
                # 2. Check for error indicators (more precise)
                error_indicators = [
                    r'phone.+number.+invalid', 
                    r'nomor.+tidak.+valid',
                    r'number.+not.+found',
                    r'tidak.+tersedia',
                    r'error.+404',
                    r'page.+not.+found'
                ]
                has_error = any(re.search(pattern, html, re.IGNORECASE) for pattern in error_indicators)
                
                # 3. Check for successful WhatsApp integration
                has_phone_in_url = phone in html
                has_meta_tags = bool(re.search(r'<meta.*whatsapp', html, re.IGNORECASE))
                
                # 4. Business indicators
                is_business = bool(re.search(r'business|verified|official', html, re.IGNORECASE))
                
                # 5. Check main content vs fallback
                main_block_visible = 'style="display: none"' not in html or 'main_block' in html
                fallback_displayed = bool(re.search(r'fallback.*display:\s*block', html))
                
                indicators = {
                    'has_whatsapp_redirect': has_whatsapp_redirect,
                    'has_whatsapp_scheme': has_whatsapp_scheme,
                    'has_chat_button': has_chat_button,
                    'no_error_indicators': not has_error,
                    'has_phone_in_url': has_phone_in_url,
                    'has_meta_tags': has_meta_tags,
                    'main_block_visible': main_block_visible,
                    'fallback_not_displayed': not fallback_displayed
                }
                
                # IMPROVED SCORING SYSTEM
                score = sum(indicators.values())
                
                # Determine status with better logic
                if has_error:
                    status = "inactive"
                    confidence = "high"
                elif score >= 6:
                    status = "active"
                    confidence = "high"
                elif score >= 4:
                    status = "active" 
                    confidence = "medium"
                elif score >= 2:
                    status = "unclear"
                    confidence = "low"
                else:
                    status = "inactive"
                    confidence = "medium"
                
                return {
                    "status": status,
                    "confidence": confidence,
                    "method": "wa.me_fixed",
                    "score": f"{score}/8",
                    "indicators": indicators,
                    "is_business": is_business,
                    "raw_response_length": len(html),
                    "has_error_patterns": has_error
                }
                
        except Exception as e:
            return {"status": "error", "method": "wa.me_fixed", "error": str(e)}
    
    async def method_fixed_api_whatsapp(self, session, phone):
        """FIXED Method: api.whatsapp.com with better pattern recognition"""
        phone = self.normalize_phone(phone)
        url = f"https://api.whatsapp.com/send/?phone={phone}&text&type=phone_number&app_absent=0"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://web.whatsapp.com/',
            'DNT': '1',
            'Connection': 'keep-alive'
        }
        
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status != 200:
                    return {"status": "error", "method": "api.whatsapp_fixed", "http_status": response.status}
                
                html = await response.text()
                
                # CRITICAL: Check for specific Indonesian error messages found in Bob's samples
                indonesian_errors = [
                    'nomor telepon yang dibagikan via tautan tidak valid',
                    'phone number shared via url is invalid',
                    'tidak valid',
                    'invalid number',
                    'number not found'
                ]
                
                has_indonesian_error = any(error.lower() in html.lower() for error in indonesian_errors)
                
                # Check for positive indicators
                has_send_redirect = 'web.whatsapp.com/send' in html
                has_chat_interface = 'main_block' in html
                main_visible = 'main_block' in html and 'style="display: none"' not in html
                fallback_hidden = 'fallback_block' in html and 'style="display: none"' in html
                has_phone_param = f'phone={phone}' in html
                
                # Business API indicators
                is_business_api = 'utm_campaign=wa_api_send_v1' in html
                
                indicators = {
                    'has_send_redirect': has_send_redirect,
                    'main_visible': main_visible,
                    'fallback_hidden': fallback_hidden,
                    'has_phone_param': has_phone_param,
                    'no_indonesian_error': not has_indonesian_error,
                    'is_business_api': is_business_api
                }
                
                score = sum(indicators.values())
                
                # Decision logic based on findings
                if has_indonesian_error:
                    status = "inactive"
                    confidence = "high"
                elif is_business_api:
                    status = "active"
                    confidence = "high"
                elif score >= 5:
                    status = "active"
                    confidence = "high"
                elif score >= 3:
                    status = "active"
                    confidence = "medium" 
                else:
                    status = "inactive"
                    confidence = "medium"
                
                return {
                    "status": status,
                    "confidence": confidence,
                    "method": "api.whatsapp_fixed",
                    "score": f"{score}/6",
                    "indicators": indicators,
                    "has_indonesian_error": has_indonesian_error,
                    "is_business_api": is_business_api,
                    "raw_response_length": len(html)
                }
                
        except Exception as e:
            return {"status": "error", "method": "api.whatsapp_fixed", "error": str(e)}
    
    async def method_browser_simulation(self, session, phone):
        """Method: Simulate real browser behavior more closely"""
        phone = self.normalize_phone(phone)
        
        # Try multiple realistic endpoints
        endpoints_to_try = [
            f"https://wa.me/{phone}",
            f"https://wa.me/{phone}?text=hello",
            f"https://api.whatsapp.com/send/?phone={phone}"
        ]
        
        results = []
        
        # Simulate human-like behavior
        for endpoint in endpoints_to_try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
            
            try:
                # Add realistic delay
                await asyncio.sleep(1)
                
                async with session.get(endpoint, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    html = await response.text()
                    
                    # Comprehensive analysis
                    analysis = {
                        'endpoint': endpoint,
                        'status_code': response.status,
                        'has_whatsapp_content': 'whatsapp' in html.lower(),
                        'has_error_message': any(err in html.lower() for err in ['invalid', 'tidak valid', 'error', 'not found']),
                        'has_redirect': 'web.whatsapp.com' in html,
                        'response_size': len(html),
                        'final_url': str(response.url)
                    }
                    
                    results.append(analysis)
                    
            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'error': str(e)
                })
        
        # Aggregate analysis
        successful_checks = [r for r in results if r.get('status_code') == 200]
        valid_responses = [r for r in successful_checks if r.get('has_whatsapp_content') and not r.get('has_error_message')]
        
        if len(valid_responses) >= 2:
            status = "active"
            confidence = "high"
        elif len(valid_responses) == 1:
            status = "active"
            confidence = "medium"
        elif any(r.get('has_error_message') for r in successful_checks):
            status = "inactive"
            confidence = "high"
        else:
            status = "unclear"
            confidence = "low"
        
        return {
            "status": status,
            "confidence": confidence,
            "method": "browser_simulation",
            "successful_endpoints": len(valid_responses),
            "total_endpoints": len(endpoints_to_try),
            "results": results
        }
    
    async def test_fixed_methods(self):
        """Test improved methods with known samples first"""
        print("🚀 Starting FIXED WhatsApp validation testing...")
        print("🎯 Focus: Accurate detection with brotli support and better patterns")
        print("=" * 80)
        
        # Create session with brotli support
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # First test known status numbers for calibration
            print("\n🧪 CALIBRATION TEST - Testing known status numbers:")
            print("-" * 60)
            
            known_numbers = ["082253767671", "089689547785", "6285586712458"]
            
            for phone in known_numbers:
                expected = self.known_status.get(phone, "unknown")
                print(f"\n📞 Testing {phone} (Expected: {expected})")
                
                methods = [
                    ("Fixed wa.me", self.method_fixed_wa_me),
                    ("Fixed api.whatsapp", self.method_fixed_api_whatsapp),
                    ("Browser simulation", self.method_browser_simulation)
                ]
                
                phone_results = {}
                
                for method_name, method_func in methods:
                    try:
                        print(f"  Testing {method_name}...")
                        result = await method_func(session, phone)
                        phone_results[method_name] = result
                        
                        status = result.get('status', 'unknown')
                        confidence = result.get('confidence', 'unknown')
                        
                        # Check accuracy
                        is_correct = "✅" if status == expected else "❌"
                        print(f"    Result: {status} ({confidence}) {is_correct}")
                        
                        await asyncio.sleep(2)  # Prevent rate limiting
                        
                    except Exception as e:
                        phone_results[method_name] = {"status": "error", "error": str(e)}
                        print(f"    Error: {str(e)}")
                
                self.results[phone] = phone_results
                
                if phone != known_numbers[-1]:
                    print("  ⏳ Waiting 5 seconds before next number...")
                    await asyncio.sleep(5)
            
            # Now test a few more numbers
            print(f"\n🔍 EXTENDED TEST - Testing additional numbers:")
            print("-" * 60)
            
            additional_numbers = ["6281261623389", "6282151118348"]
            
            for phone in additional_numbers:
                print(f"\n📞 Testing {phone}")
                
                phone_results = {}
                
                for method_name, method_func in methods:
                    try:
                        print(f"  Testing {method_name}...")
                        result = await method_func(session, phone)
                        phone_results[method_name] = result
                        
                        status = result.get('status', 'unknown')
                        confidence = result.get('confidence', 'unknown')
                        print(f"    Result: {status} ({confidence})")
                        
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        phone_results[method_name] = {"status": "error", "error": str(e)}
                        print(f"    Error: {str(e)}")
                
                self.results[phone] = phone_results
                
                if phone != additional_numbers[-1]:
                    print("  ⏳ Waiting 5 seconds...")
                    await asyncio.sleep(5)
        
        return self.results
    
    def analyze_accuracy(self):
        """Analyze accuracy against known status"""
        print("\n" + "=" * 80)
        print("🎯 ACCURACY ANALYSIS")
        print("=" * 80)
        
        methods = ["Fixed wa.me", "Fixed api.whatsapp", "Browser simulation"]
        
        for method in methods:
            print(f"\n📊 {method} Accuracy:")
            correct = 0
            total = 0
            
            for phone, phone_results in self.results.items():
                if phone in self.known_status and method in phone_results:
                    expected = self.known_status[phone]
                    actual = phone_results[method].get('status', 'error')
                    
                    total += 1
                    if actual == expected:
                        correct += 1
                        print(f"  ✅ {phone}: {actual} (correct)")
                    else:
                        print(f"  ❌ {phone}: {actual} vs expected {expected}")
            
            if total > 0:
                accuracy = (correct / total) * 100
                print(f"  📈 Overall Accuracy: {correct}/{total} ({accuracy:.1f}%)")
            else:
                print("  ⚠️ No known status numbers tested")
        
        # Detailed results
        print(f"\n📱 DETAILED RESULTS:")
        for phone, phone_results in self.results.items():
            expected = self.known_status.get(phone, "unknown")
            print(f"\n{phone} (Expected: {expected}):")
            for method, result in phone_results.items():
                status = result.get('status', 'error')
                confidence = result.get('confidence', '')
                confidence_str = f" ({confidence})" if confidence else ""
                print(f"  {method:20} → {status}{confidence_str}")
    
    def save_results(self):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/whatsapp_testing_fixed_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename

# Run the fixed testing
async def main():
    tester = WhatsAppTesterFixed()
    results = await tester.test_fixed_methods()
    tester.analyze_accuracy()
    tester.save_results()

if __name__ == "__main__":
    asyncio.run(main())