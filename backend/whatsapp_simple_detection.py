import asyncio
from playwright.async_api import async_playwright
import json

class WhatsAppSimpleDetector:
    def __init__(self):
        self.results = {}
        self.known_status = {
            "082253767671": "active",
            "089689547785": "active", 
            "6285586712458": "inactive"
        }
    
    def normalize_phone(self, phone):
        phone = phone.strip().replace('+', '').replace('-', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif not phone.startswith('62'):
            phone = '62' + phone
        return phone
    
    async def simple_detect_whatsapp(self, phone):
        """Simple but effective detection focusing on key patterns"""
        phone = self.normalize_phone(phone)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = await browser.new_page()
            
            try:
                print(f"  🔍 Testing wa.me/{phone}")
                
                # Navigate to wa.me
                await page.goto(f"https://wa.me/{phone}", wait_until='networkidle', timeout=15000)
                await page.wait_for_timeout(3000)
                
                print(f"    📍 Final URL: {page.url}")
                
                # Get all text content
                full_text = await page.evaluate("document.body.textContent")
                full_html = await page.content()
                
                print(f"    📝 Content length: {len(full_text)} chars")
                
                # === KEY DETECTION PATTERNS ===
                
                analysis = {
                    "phone": phone,
                    "final_url": page.url,
                    "content_length": len(full_text),
                    "patterns": {}
                }
                
                # 1. Indonesian error patterns (most reliable)
                indonesian_errors = [
                    "nomor telepon yang dibagikan via tautan tidak valid",
                    "nomor tidak valid", 
                    "tidak valid",
                    "tidak tersedia",
                    "tidak ditemukan"
                ]
                
                found_indonesian_errors = []
                for error in indonesian_errors:
                    if error.lower() in full_text.lower():
                        found_indonesian_errors.append(error)
                        print(f"    ❌ INDONESIAN ERROR: {error}")
                
                analysis["patterns"]["indonesian_errors"] = found_indonesian_errors
                
                # 2. English error patterns
                english_errors = [
                    "phone number shared via url is invalid",
                    "invalid number",
                    "number not found",
                    "not available"
                ]
                
                found_english_errors = []
                for error in english_errors:
                    if error.lower() in full_text.lower():
                        found_english_errors.append(error)
                        print(f"    ❌ ENGLISH ERROR: {error}")
                
                analysis["patterns"]["english_errors"] = found_english_errors
                
                # 3. Positive chat indicators
                chat_indicators = [
                    "continue to chat",
                    "send message",
                    "chat now",
                    "open in whatsapp"
                ]
                
                found_chat_indicators = []
                for indicator in chat_indicators:
                    if indicator.lower() in full_text.lower():
                        found_chat_indicators.append(indicator)
                        print(f"    ✅ CHAT INDICATOR: {indicator}")
                
                analysis["patterns"]["chat_indicators"] = found_chat_indicators
                
                # 4. Download/install prompts (usually indicates invalid)
                download_prompts = [
                    "download whatsapp",
                    "install whatsapp",
                    "get whatsapp",
                    "dapatkan whatsapp"
                ]
                
                found_download_prompts = []
                for prompt in download_prompts:
                    if prompt.lower() in full_text.lower():
                        found_download_prompts.append(prompt)
                        print(f"    📲 DOWNLOAD PROMPT: {prompt}")
                
                analysis["patterns"]["download_prompts"] = found_download_prompts
                
                # 5. Look for key HTML elements that might differ
                element_check = await page.evaluate("""
                    () => {
                        const result = {
                            main_blocks: 0,
                            fallback_blocks: 0,
                            hidden_elements: 0,
                            visible_buttons: 0,
                            has_whatsapp_link: false
                        };
                        
                        // Count main blocks
                        const mainElements = document.querySelectorAll('[class*="main"], [id*="main"]');
                        result.main_blocks = mainElements.length;
                        
                        // Count fallback blocks  
                        const fallbackElements = document.querySelectorAll('[class*="fallback"], [id*="fallback"]');
                        result.fallback_blocks = fallbackElements.length;
                        
                        // Count hidden elements
                        const allElements = document.querySelectorAll('*');
                        allElements.forEach(el => {
                            const style = window.getComputedStyle(el);
                            if (style.display === 'none' || style.visibility === 'hidden') {
                                result.hidden_elements++;
                            }
                        });
                        
                        // Count visible buttons
                        const buttons = document.querySelectorAll('button, a, [role="button"]');
                        buttons.forEach(btn => {
                            const style = window.getComputedStyle(btn);
                            if (style.display !== 'none' && style.visibility !== 'hidden') {
                                result.visible_buttons++;
                            }
                        });
                        
                        // Check for WhatsApp links
                        result.has_whatsapp_link = document.body.innerHTML.includes('web.whatsapp.com');
                        
                        return result;
                    }
                """)
                
                analysis["element_check"] = element_check
                
                print(f"    🔍 Elements: {element_check}")
                
                # 6. Check page title and meta info
                page_title = await page.title()
                analysis["page_title"] = page_title
                
                print(f"    📄 Title: {page_title}")
                
                await browser.close()
                
                # === DECISION LOGIC ===
                score = 0
                decision_factors = []
                
                # STRONG negative indicators (Indonesian errors are very reliable)
                if found_indonesian_errors:
                    score -= 10
                    decision_factors.append(f"INDONESIAN_ERRORS: {found_indonesian_errors}")
                
                if found_english_errors:
                    score -= 8  
                    decision_factors.append(f"ENGLISH_ERRORS: {found_english_errors}")
                
                # Positive indicators
                if found_chat_indicators:
                    score += 5
                    decision_factors.append(f"CHAT_INDICATORS: {found_chat_indicators}")
                
                # Download prompts (mixed indicator)
                if found_download_prompts:
                    score -= 2
                    decision_factors.append(f"DOWNLOAD_PROMPTS: {found_download_prompts}")
                
                # Element analysis
                if element_check["has_whatsapp_link"]:
                    score += 2
                    decision_factors.append("HAS_WHATSAPP_LINK")
                
                if element_check["visible_buttons"] > 0:
                    score += 1
                    decision_factors.append(f"VISIBLE_BUTTONS: {element_check['visible_buttons']}")
                
                # Final decision with clear thresholds
                if score <= -5:
                    status = "inactive"
                    confidence = "high"
                elif score <= -2:
                    status = "inactive"
                    confidence = "medium"
                elif score >= 5:
                    status = "active"
                    confidence = "high"
                elif score >= 2:
                    status = "active"
                    confidence = "medium"
                else:
                    status = "unclear"
                    confidence = "low"
                
                print(f"    🎯 Score: {score}, Decision: {status} ({confidence})")
                
                return {
                    "status": status,
                    "confidence": confidence,
                    "score": score,
                    "decision_factors": decision_factors,
                    "method": "simple_detection",
                    "analysis": analysis
                }
                
            except Exception as e:
                await browser.close()
                return {
                    "status": "error",
                    "method": "simple_detection",
                    "error": str(e)
                }
    
    async def test_simple_detection(self):
        """Test simple detection method"""
        print("🎯 SIMPLE WHATSAPP DETECTION")
        print("🔍 Focus on reliable text patterns and key elements")
        print("=" * 55)
        
        test_numbers = ["082253767671", "6285586712458", "089689547785"]
        
        for i, phone in enumerate(test_numbers, 1):
            expected = self.known_status.get(phone, "unknown")
            print(f"\n📞 TESTING {phone} ({i}/{len(test_numbers)}) - Expected: {expected}")
            print("-" * 55)
            
            try:
                result = await self.simple_detect_whatsapp(phone)
                self.results[phone] = result
                
                status = result.get('status', 'error')
                confidence = result.get('confidence', '')
                score = result.get('score', 0)
                factors = result.get('decision_factors', [])
                
                print(f"    🏆 RESULT: {status} ({confidence}) - Score: {score}")
                print(f"    💡 FACTORS: {factors}")
                
                # Check accuracy
                if expected != "unknown":
                    is_correct = "✅ CORRECT" if status == expected else "❌ WRONG"
                    print(f"    📊 ACCURACY: {is_correct}")
                
                if i < len(test_numbers):
                    print(f"    ⏳ Waiting 4 seconds...")
                    await asyncio.sleep(4)
                
            except Exception as e:
                self.results[phone] = {"status": "error", "error": str(e)}
                print(f"    ❌ Error: {str(e)}")
        
        # Calculate overall accuracy
        correct = 0
        total = 0
        for phone, result in self.results.items():
            if phone in self.known_status:
                total += 1
                if result.get('status') == self.known_status[phone]:
                    correct += 1
        
        if total > 0:
            accuracy = (correct / total) * 100
            print(f"\n🏆 OVERALL ACCURACY: {correct}/{total} ({accuracy:.1f}%)")
            
            if accuracy >= 80:
                print("✅ EXCELLENT! This method is viable for production!")
            elif accuracy >= 60:
                print("✅ GOOD! Acceptable for production with confidence levels")
            else:
                print("⚠️ NEEDS IMPROVEMENT")
        
        return self.results
    
    def save_results(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/whatsapp_simple_detection_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename

async def main():
    detector = WhatsAppSimpleDetector()
    await detector.test_simple_detection()
    detector.save_results()

if __name__ == "__main__":
    asyncio.run(main())