import aiohttp
import asyncio
from datetime import datetime
import json
import brotli
import re

class WhatsAppTesterOptimal:
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
            "082253767671",   # Known active
            "089689547785",   # Known active (business)
            "6285586712458",  # Known inactive
            "6281261623389",
            "6282151118348"
        ]
    
    def normalize_phone(self, phone):
        """Normalize phone number format"""
        phone = phone.strip().replace('+', '').replace('-', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif not phone.startswith('62'):
            phone = '62' + phone
        return phone
    
    async def method_optimal_detection(self, session, phone):
        """OPTIMAL Method: Refined pattern detection based on findings"""
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
                    return {"status": "error", "method": "optimal", "http_status": response.status}
                
                html = await response.text()
                
                print(f"  🔍 Analyzing response for {phone} ({len(html)} chars)")
                
                # ENHANCED ERROR DETECTION - more comprehensive patterns
                error_patterns = [
                    # Indonesian patterns (more specific)
                    r'nomor\s+telepon\s+yang\s+dibagikan\s+via\s+tautan\s+tidak\s+valid',
                    r'nomor\s+tidak\s+valid',
                    r'tidak\s+valid',
                    r'tidak\s+tersedia',
                    r'tidak\s+ditemukan',
                    
                    # English patterns
                    r'phone\s+number\s+shared\s+via\s+url\s+is\s+invalid',
                    r'phone\s+number\s+is\s+invalid',
                    r'invalid\s+number',
                    r'number\s+not\s+found',
                    r'not\s+available',
                    
                    # Generic error patterns
                    r'error\s*:\s*invalid',
                    r'gagal',
                    r'failed'
                ]
                
                # Check each pattern individually for debugging
                detected_errors = []
                for pattern in error_patterns:
                    if re.search(pattern, html, re.IGNORECASE):
                        detected_errors.append(pattern)
                
                has_error_message = len(detected_errors) > 0
                
                # ENHANCED POSITIVE INDICATORS
                # Check for WhatsApp redirect functionality
                has_send_redirect = bool(re.search(r'web\.whatsapp\.com/send', html))
                has_whatsapp_scheme = bool(re.search(r'whatsapp://send', html))
                
                # Check for main content vs fallback display
                main_block_pattern = r'<[^>]*class="[^"]*main[^"]*"[^>]*(?:style="[^"]*display:\s*none|style="[^"]*display:\s*block)'
                main_visible = not bool(re.search(r'main_block[^>]*style="[^"]*display:\s*none', html))
                
                fallback_pattern = r'fallback[^>]*style="[^"]*display:\s*block'
                fallback_displayed = bool(re.search(fallback_pattern, html))
                
                # Check for phone parameter in response
                has_phone_param = f'phone={phone}' in html or phone in html
                
                # Business API detection
                is_business_api = bool(re.search(r'utm_campaign=wa_api_send_v1', html))
                
                # Check for app download prompts (usually indicates invalid number)
                has_app_download = bool(re.search(r'download.*whatsapp|install.*whatsapp', html, re.IGNORECASE))
                
                indicators = {
                    'has_send_redirect': has_send_redirect,
                    'has_whatsapp_scheme': has_whatsapp_scheme,
                    'main_visible': main_visible,
                    'fallback_not_displayed': not fallback_displayed,
                    'has_phone_param': has_phone_param,
                    'is_business_api': is_business_api,
                    'no_error_message': not has_error_message,
                    'no_app_download': not has_app_download
                }
                
                score = sum(indicators.values())
                
                print(f"    📊 Score: {score}/8")
                print(f"    🚨 Errors detected: {detected_errors}")
                print(f"    📱 Main visible: {main_visible}")
                print(f"    📱 Fallback displayed: {fallback_displayed}")
                print(f"    💼 Business API: {is_business_api}")
                
                # REFINED DECISION LOGIC
                if has_error_message:
                    status = "inactive"
                    confidence = "high"
                    reason = "Error message detected"
                elif fallback_displayed and not main_visible:
                    status = "inactive"  
                    confidence = "high"
                    reason = "Fallback displayed, main hidden"
                elif is_business_api:
                    status = "active"
                    confidence = "high"
                    reason = "Business API detected"
                elif score >= 6:
                    status = "active"
                    confidence = "high"
                    reason = f"High score ({score}/8)"
                elif score >= 4:
                    status = "active"
                    confidence = "medium"
                    reason = f"Medium score ({score}/8)"
                elif score <= 2:
                    status = "inactive"
                    confidence = "medium"
                    reason = f"Low score ({score}/8)"
                else:
                    status = "unclear"
                    confidence = "low"
                    reason = f"Unclear score ({score}/8)"
                
                print(f"    ✅ Decision: {status} ({confidence}) - {reason}")
                
                return {
                    "status": status,
                    "confidence": confidence,
                    "reason": reason,
                    "method": "optimal",
                    "score": f"{score}/8",
                    "indicators": indicators,
                    "detected_errors": detected_errors,
                    "is_business_api": is_business_api,
                    "raw_response_length": len(html)
                }
                
        except Exception as e:
            return {"status": "error", "method": "optimal", "error": str(e)}
    
    async def test_optimal_method(self):
        """Test optimal method with focus on accuracy"""
        print("🚀 Starting OPTIMAL WhatsApp validation testing...")
        print("🎯 Goal: Achieve >90% accuracy with refined pattern detection")
        print("=" * 80)
        
        connector = aiohttp.TCPConnector(limit=5)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for i, phone in enumerate(self.test_numbers, 1):
                expected = self.known_status.get(phone, "unknown")
                print(f"\n📞 Testing {phone} ({i}/{len(self.test_numbers)}) - Expected: {expected}")
                print("-" * 60)
                
                try:
                    result = await self.method_optimal_detection(session, phone)
                    self.results[phone] = result
                    
                    status = result.get('status', 'unknown')
                    confidence = result.get('confidence', 'unknown')
                    reason = result.get('reason', '')
                    
                    # Check accuracy for known numbers
                    if expected != "unknown":
                        is_correct = "✅ CORRECT" if status == expected else "❌ WRONG"
                        print(f"    🎯 Result: {status} ({confidence}) - {reason}")
                        print(f"    📊 Accuracy: {is_correct}")
                    else:
                        print(f"    🎯 Result: {status} ({confidence}) - {reason}")
                    
                    # Add delay to avoid rate limiting
                    if i < len(self.test_numbers):
                        print("    ⏳ Waiting 4 seconds...")
                        await asyncio.sleep(4)
                    
                except Exception as e:
                    self.results[phone] = {"status": "error", "error": str(e)}
                    print(f"    ❌ Error: {str(e)}")
        
        return self.results
    
    def analyze_final_accuracy(self):
        """Analyze final accuracy"""
        print("\n" + "=" * 80)
        print("🏆 FINAL ACCURACY ANALYSIS")
        print("=" * 80)
        
        correct = 0
        total = 0
        
        for phone, result in self.results.items():
            if phone in self.known_status:
                expected = self.known_status[phone]
                actual = result.get('status', 'error')
                confidence = result.get('confidence', '')
                reason = result.get('reason', '')
                
                total += 1
                if actual == expected:
                    correct += 1
                    print(f"✅ {phone}: {actual} ({confidence}) - CORRECT")
                else:
                    print(f"❌ {phone}: {actual} vs expected {expected} ({confidence})")
                    print(f"   Reason: {reason}")
        
        if total > 0:
            accuracy = (correct / total) * 100
            print(f"\n🎯 FINAL ACCURACY: {correct}/{total} ({accuracy:.1f}%)")
            
            if accuracy >= 90:
                print("🏆 EXCELLENT! Target accuracy achieved!")
            elif accuracy >= 75:
                print("✅ GOOD! Close to target accuracy")
            else:
                print("⚠️ NEEDS IMPROVEMENT - Below target accuracy")
        
        # Show results for unknown numbers
        print(f"\n🔍 PREDICTIONS FOR UNKNOWN NUMBERS:")
        for phone, result in self.results.items():
            if phone not in self.known_status:
                status = result.get('status', 'error')
                confidence = result.get('confidence', '')
                reason = result.get('reason', '')
                print(f"📱 {phone}: {status} ({confidence}) - {reason}")
    
    def save_results(self):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/whatsapp_testing_optimal_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename

# Run the optimal testing
async def main():
    tester = WhatsAppTesterOptimal()
    results = await tester.test_optimal_method()
    tester.analyze_final_accuracy()
    tester.save_results()

if __name__ == "__main__":
    asyncio.run(main())