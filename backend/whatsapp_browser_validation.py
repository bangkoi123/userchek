import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
import random

class WhatsAppBrowserValidator:
    def __init__(self):
        self.results = {}
        # Known status from Bob's manual testing for calibration
        self.known_status = {
            "082253767671": "active",
            "089689547785": "active",  # wa business
            "6285586712458": "inactive"
        }
        
        # Test numbers for comprehensive validation
        self.test_numbers = [
            "082253767671",   # Known active
            "089689547785",   # Known active (business)  
            "6285586712458",  # Known inactive
            "6281261623389",  # Unknown
            "6282151118348"   # Unknown
        ]
    
    def normalize_phone(self, phone):
        """Normalize phone number format"""
        phone = phone.strip().replace('+', '').replace('-', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif not phone.startswith('62'):
            phone = '62' + phone
        return phone
    
    async def validate_whatsapp_browser(self, phone):
        """Validate WhatsApp number using browser automation WITHOUT account"""
        phone = self.normalize_phone(phone)
        
        async with async_playwright() as p:
            # Launch browser with realistic settings
            browser = await p.chromium.launch(
                headless=True,  # Run in headless mode for server
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with realistic user agent
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768},
                locale='en-US'
            )
            
            page = await context.new_page()
            
            try:
                print(f"  🌐 Opening wa.me/{phone} in browser...")
                
                # Navigate to wa.me URL (NO LOGIN REQUIRED)
                wa_url = f"https://wa.me/{phone}"
                response = await page.goto(wa_url, wait_until='networkidle', timeout=30000)
                
                print(f"    📡 Response status: {response.status}")
                print(f"    🔗 Final URL: {page.url}")
                
                # Wait for page to fully load and execute JavaScript
                await page.wait_for_timeout(3000)
                
                # Check for various indicators after JavaScript execution
                indicators = {}
                
                # 1. Check if redirected to WhatsApp Web chat
                current_url = page.url
                is_whatsapp_chat = 'web.whatsapp.com/send' in current_url
                indicators['redirected_to_chat'] = is_whatsapp_chat
                
                # 2. Check for chat/send buttons
                chat_button_selectors = [
                    'text=Continue to Chat',
                    'text=Send Message', 
                    'text=Open in WhatsApp',
                    'text=Chat',
                    '[data-testid="chat-button"]',
                    'a[href*="web.whatsapp.com"]'
                ]
                
                has_chat_button = False
                for selector in chat_button_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=1000):
                            has_chat_button = True
                            print(f"    ✅ Found chat button: {selector}")
                            break
                    except:
                        continue
                
                indicators['has_chat_button'] = has_chat_button
                
                # 3. Check for error messages
                error_selectors = [
                    'text=Phone number shared via url is invalid',
                    'text=Nomor telepon yang dibagikan via tautan tidak valid',
                    'text=Invalid number',
                    'text=Number not found',
                    'text=Tidak valid',
                    '[class*="error"]',
                    '[data-testid="error"]'
                ]
                
                has_error_message = False
                detected_error = None
                for selector in error_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=1000):
                            has_error_message = True
                            detected_error = selector
                            print(f"    ❌ Found error message: {selector}")
                            break
                    except:
                        continue
                
                indicators['has_error_message'] = has_error_message
                
                # 4. Check for WhatsApp download/install prompts (usually indicates invalid)
                download_selectors = [
                    'text=Download WhatsApp',
                    'text=Install WhatsApp',
                    'text=Get WhatsApp',
                    'text=Dapatkan WhatsApp'
                ]
                
                has_download_prompt = False
                for selector in download_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=1000):
                            has_download_prompt = True
                            print(f"    📲 Found download prompt: {selector}")
                            break
                    except:
                        continue
                
                indicators['has_download_prompt'] = has_download_prompt
                
                # 5. Check page title and meta tags
                page_title = await page.title()
                has_whatsapp_title = 'whatsapp' in page_title.lower()
                indicators['has_whatsapp_title'] = has_whatsapp_title
                
                # 6. Check if page contains phone number
                page_content = await page.content()
                phone_in_content = phone in page_content
                indicators['phone_in_content'] = phone_in_content
                
                # 7. Advanced: Check for dynamic content loading
                await page.wait_for_timeout(2000)  # Wait for any delayed loading
                
                # Check final state after all loading
                final_url = page.url
                url_changed = final_url != wa_url
                indicators['url_changed'] = url_changed
                
                print(f"    📊 Indicators: {indicators}")
                
                # DECISION LOGIC based on browser behavior
                score = 0
                confidence = "low"
                reason = ""
                
                # High confidence indicators
                if has_error_message:
                    status = "inactive"
                    confidence = "high"
                    reason = f"Error message detected: {detected_error}"
                elif is_whatsapp_chat:
                    status = "active"
                    confidence = "high" 
                    reason = "Redirected to WhatsApp Web chat"
                elif has_chat_button and not has_download_prompt:
                    status = "active"
                    confidence = "high"
                    reason = "Chat button found without download prompt"
                elif has_download_prompt and not has_chat_button:
                    status = "inactive"
                    confidence = "medium"
                    reason = "Download prompt found without chat functionality"
                else:
                    # Medium confidence scoring
                    positive_score = sum([
                        indicators['has_chat_button'],
                        indicators['has_whatsapp_title'],
                        indicators['phone_in_content'],
                        indicators['url_changed']
                    ])
                    
                    negative_score = sum([
                        indicators['has_error_message'],
                        indicators['has_download_prompt']
                    ])
                    
                    if positive_score >= 3 and negative_score == 0:
                        status = "active"
                        confidence = "medium"
                        reason = f"Positive indicators: {positive_score}/4"
                    elif negative_score > 0:
                        status = "inactive"  
                        confidence = "medium"
                        reason = f"Negative indicators detected"
                    elif positive_score >= 2:
                        status = "active"
                        confidence = "low"
                        reason = f"Some positive indicators: {positive_score}/4"
                    else:
                        status = "unclear"
                        confidence = "low"
                        reason = f"Insufficient indicators"
                
                await browser.close()
                
                return {
                    "status": status,
                    "confidence": confidence,
                    "reason": reason,
                    "method": "browser_automation",
                    "indicators": indicators,
                    "final_url": final_url,
                    "page_title": page_title,
                    "detected_error": detected_error
                }
                
            except Exception as e:
                await browser.close()
                return {
                    "status": "error", 
                    "method": "browser_automation",
                    "error": str(e)
                }
    
    async def test_browser_validation(self):
        """Test browser validation method with known samples"""
        print("🚀 Starting WhatsApp Browser Validation (NO ACCOUNT REQUIRED)")
        print("🎯 Testing with real browser automation for accurate results")
        print("=" * 75)
        
        for i, phone in enumerate(self.test_numbers, 1):
            expected = self.known_status.get(phone, "unknown")
            print(f"\n📞 Testing {phone} ({i}/{len(self.test_numbers)}) - Expected: {expected}")
            print("-" * 60)
            
            try:
                result = await self.validate_whatsapp_browser(phone)
                self.results[phone] = result
                
                status = result.get('status', 'error')
                confidence = result.get('confidence', '')
                reason = result.get('reason', '')
                
                # Check accuracy for known numbers
                if expected != "unknown":
                    is_correct = "✅ CORRECT" if status == expected else "❌ WRONG"
                    print(f"    🎯 Result: {status} ({confidence})")
                    print(f"    💡 Reason: {reason}")
                    print(f"    📊 Accuracy: {is_correct}")
                else:
                    print(f"    🎯 Result: {status} ({confidence})")
                    print(f"    💡 Reason: {reason}")
                
                # Add delay between tests to avoid detection
                if i < len(self.test_numbers):
                    delay = random.randint(3, 7)
                    print(f"    ⏳ Waiting {delay} seconds before next test...")
                    await asyncio.sleep(delay)
                
            except Exception as e:
                self.results[phone] = {"status": "error", "error": str(e)}
                print(f"    ❌ Error: {str(e)}")
        
        return self.results
    
    def analyze_browser_accuracy(self):
        """Analyze accuracy of browser method"""
        print("\n" + "=" * 75)
        print("🏆 BROWSER VALIDATION ACCURACY ANALYSIS")
        print("=" * 75)
        
        correct = 0
        total_known = 0
        
        print("\n📊 Results Summary:")
        for phone, result in self.results.items():
            expected = self.known_status.get(phone, "unknown")
            status = result.get('status', 'error')
            confidence = result.get('confidence', '')
            reason = result.get('reason', '')
            
            if expected != "unknown":
                total_known += 1
                if status == expected:
                    correct += 1
                    print(f"✅ {phone}: {status} ({confidence}) - CORRECT")
                else:
                    print(f"❌ {phone}: {status} vs expected {expected} ({confidence})")
                    print(f"   Reason: {reason}")
            else:
                print(f"🔍 {phone}: {status} ({confidence}) - {reason}")
        
        if total_known > 0:
            accuracy = (correct / total_known) * 100
            print(f"\n🎯 OVERALL ACCURACY: {correct}/{total_known} ({accuracy:.1f}%)")
            
            if accuracy >= 90:
                print("🏆 EXCELLENT! Target accuracy achieved!")
                print("✅ Ready for production implementation!")
            elif accuracy >= 75:
                print("✅ GOOD! Acceptable accuracy for production use")
            elif accuracy >= 50:
                print("⚠️ FAIR - May need refinement")
            else:
                print("❌ POOR - Needs significant improvement")
        
        return accuracy if total_known > 0 else 0
    
    def save_results(self):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/whatsapp_browser_validation_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename

# Run browser validation testing
async def main():
    validator = WhatsAppBrowserValidator()
    await validator.test_browser_validation()
    accuracy = validator.analyze_browser_accuracy()
    validator.save_results()
    
    print(f"\n🎯 FINAL CONCLUSION:")
    if accuracy >= 75:
        print("✅ Browser automation method is VIABLE for production!")
        print("📝 Ready to integrate into main application")
    else:
        print("⚠️ Method needs refinement or alternative approach")

if __name__ == "__main__":
    asyncio.run(main())