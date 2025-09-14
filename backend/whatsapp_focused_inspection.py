import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json

class WhatsAppFocusedInspector:
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
    
    async def focused_inspect_whatsapp(self, phone):
        """Focused inspection looking for key differentiating elements"""
        phone = self.normalize_phone(phone)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                print(f"  🔍 Inspecting wa.me/{phone}")
                
                # Navigate
                wa_url = f"https://wa.me/{phone}"
                await page.goto(wa_url, wait_until='networkidle', timeout=20000)
                
                print(f"    🔗 Final URL: {page.url}")
                
                # Wait for content to load
                await page.wait_for_timeout(3000)
                
                # === CRITICAL ELEMENT DETECTION ===
                
                # 1. Get full text content
                page_text = await page.evaluate("document.body.textContent")
                print(f"    📝 Page text length: {len(page_text)}")
                
                # 2. Look for specific error messages (case-insensitive)
                error_patterns = [
                    "nomor telepon yang dibagikan via tautan tidak valid",
                    "phone number shared via url is invalid", 
                    "nomor tidak valid",
                    "invalid number",
                    "tidak valid",
                    "not available",
                    "number not found"
                ]
                
                detected_errors = []
                for pattern in error_patterns:
                    if pattern.lower() in page_text.lower():
                        detected_errors.append(pattern)
                        print(f"    ❌ FOUND ERROR: {pattern}")
                
                # 3. Look for positive indicators
                positive_patterns = [
                    "continue to chat",
                    "send message",
                    "chat now",
                    "open in whatsapp"
                ]
                
                detected_positives = []
                for pattern in positive_patterns:
                    if pattern.lower() in page_text.lower():
                        detected_positives.append(pattern)
                        print(f"    ✅ FOUND POSITIVE: {pattern}")
                
                # 4. Check for download/install prompts
                download_patterns = [
                    "download whatsapp",
                    "install whatsapp", 
                    "get whatsapp",
                    "dapatkan whatsapp"
                ]
                
                detected_downloads = []
                for pattern in download_patterns:
                    if pattern.lower() in page_text.lower():
                        detected_downloads.append(pattern)
                        print(f"    📲 FOUND DOWNLOAD: {pattern}")
                
                # 5. Advanced DOM inspection for hidden content
                dom_analysis = await page.evaluate("""
                    () => {
                        // Look for elements with specific classes or IDs that might indicate status
                        const indicators = {
                            main_blocks: [],
                            fallback_blocks: [],
                            error_elements: [],
                            chat_elements: [],
                            hidden_elements: []
                        };
                        
                        // Check all elements
                        const allElements = document.querySelectorAll('*');
                        
                        allElements.forEach(el => {
                            const className = el.className || '';
                            const id = el.id || '';
                            const style = window.getComputedStyle(el);
                            const text = el.textContent || '';
                            
                            // Check for main blocks
                            if (className.includes('main') || id.includes('main')) {
                                indicators.main_blocks.push({
                                    tag: el.tagName,
                                    class: className,
                                    id: id,
                                    visible: style.display !== 'none' && style.visibility !== 'hidden',
                                    text: text.substring(0, 100)
                                });
                            }
                            
                            // Check for fallback blocks
                            if (className.includes('fallback') || id.includes('fallback')) {
                                indicators.fallback_blocks.push({
                                    tag: el.tagName,
                                    class: className,
                                    id: id,
                                    visible: style.display !== 'none' && style.visibility !== 'hidden',
                                    text: text.substring(0, 100)
                                });
                            }
                            
                            // Check for error elements
                            if (className.toLowerCase().includes('error') || 
                                text.toLowerCase().includes('invalid') ||
                                text.toLowerCase().includes('tidak valid')) {
                                indicators.error_elements.push({
                                    tag: el.tagName,
                                    class: className,
                                    id: id,
                                    visible: style.display !== 'none' && style.visibility !== 'hidden',
                                    text: text.substring(0, 200)
                                });
                            }
                            
                            // Check for chat elements
                            if (className.toLowerCase().includes('chat') ||
                                className.toLowerCase().includes('send') ||
                                text.toLowerCase().includes('continue to chat')) {
                                indicators.chat_elements.push({
                                    tag: el.tagName,
                                    class: className,
                                    id: id,
                                    visible: style.display !== 'none' && style.visibility !== 'hidden',
                                    text: text.substring(0, 100)
                                });
                            }
                            
                            // Check for hidden elements with important content
                            if ((style.display === 'none' || style.visibility === 'hidden') &&
                                (text.includes('invalid') || text.includes('error') || text.includes('tidak valid'))) {
                                indicators.hidden_elements.push({
                                    tag: el.tagName,
                                    class: className,
                                    id: id,
                                    text: text.substring(0, 200)
                                });
                            }
                        });
                        
                        return indicators;
                    }
                """)
                
                print(f"    🔍 DOM Analysis:")
                print(f"      - Main blocks: {len(dom_analysis['main_blocks'])}")
                print(f"      - Fallback blocks: {len(dom_analysis['fallback_blocks'])}")
                print(f"      - Error elements: {len(dom_analysis['error_elements'])}")
                print(f"      - Chat elements: {len(dom_analysis['chat_elements'])}")
                print(f"      - Hidden elements: {len(dom_analysis['hidden_elements'])}")
                
                # Show specific error elements found
                for error_el in dom_analysis['error_elements']:
                    if error_el['visible']:
                        print(f"        ❌ VISIBLE ERROR: {error_el['text']}")
                
                # Show specific hidden error content
                for hidden_el in dom_analysis['hidden_elements']:
                    print(f"        🙈 HIDDEN ERROR: {hidden_el['text']}")
                
                # 6. Check for specific JavaScript variables that might indicate status
                js_check = await page.evaluate("""
                    () => {
                        const result = {};
                        
                        // Check common variable names
                        if (typeof window.phoneValid !== 'undefined') result.phoneValid = window.phoneValid;
                        if (typeof window.isValidNumber !== 'undefined') result.isValidNumber = window.isValidNumber;
                        if (typeof window.hasError !== 'undefined') result.hasError = window.hasError;
                        
                        // Check for data attributes on body
                        result.bodyDataAttrs = {};
                        for (let attr of document.body.attributes) {
                            if (attr.name.startsWith('data-')) {
                                result.bodyDataAttrs[attr.name] = attr.value;
                            }
                        }
                        
                        // Check for meta tags with status info
                        result.metaTags = {};
                        const metaTags = document.querySelectorAll('meta');
                        metaTags.forEach(meta => {
                            if (meta.name && (meta.name.includes('phone') || meta.name.includes('status'))) {
                                result.metaTags[meta.name] = meta.content;
                            }
                        });
                        
                        return result;
                    }
                """)
                
                print(f"    🧠 JavaScript Check: {js_check}")
                
                await browser.close()
                
                # === DECISION LOGIC ===
                score = 0
                decision_factors = []
                
                # Strong negative indicators
                if detected_errors:
                    score -= 5
                    decision_factors.append(f"ERROR_MESSAGES: {detected_errors}")
                
                # Check for visible error elements
                visible_errors = [el for el in dom_analysis['error_elements'] if el['visible']]
                if visible_errors:
                    score -= 3
                    decision_factors.append(f"VISIBLE_ERROR_ELEMENTS: {len(visible_errors)}")
                
                # Check for hidden error content
                if dom_analysis['hidden_elements']:
                    score -= 2
                    decision_factors.append(f"HIDDEN_ERROR_CONTENT: {len(dom_analysis['hidden_elements'])}")
                
                # Positive indicators
                if detected_positives:
                    score += 3
                    decision_factors.append(f"POSITIVE_MESSAGES: {detected_positives}")
                
                # Chat elements
                visible_chat = [el for el in dom_analysis['chat_elements'] if el['visible']]
                if visible_chat:
                    score += 2
                    decision_factors.append(f"CHAT_ELEMENTS: {len(visible_chat)}")
                
                # Download prompts (usually bad sign)
                if detected_downloads:
                    score -= 1
                    decision_factors.append(f"DOWNLOAD_PROMPTS: {detected_downloads}")
                
                # Final decision
                if score <= -3:
                    status = "inactive"
                    confidence = "high"
                elif score <= -1:
                    status = "inactive"
                    confidence = "medium"
                elif score >= 3:
                    status = "active"
                    confidence = "high"
                elif score >= 1:
                    status = "active"
                    confidence = "medium"
                else:
                    status = "unclear"
                    confidence = "low"
                
                return {
                    "status": status,
                    "confidence": confidence,
                    "score": score,
                    "decision_factors": decision_factors,
                    "method": "focused_inspection",
                    "detected_errors": detected_errors,
                    "detected_positives": detected_positives,
                    "detected_downloads": detected_downloads,
                    "dom_analysis": dom_analysis,
                    "js_check": js_check,
                    "page_text_length": len(page_text),
                    "final_url": page.url
                }
                
            except Exception as e:
                await browser.close()
                return {
                    "status": "error",
                    "method": "focused_inspection",
                    "error": str(e)
                }
    
    async def test_focused_inspection(self):
        """Test focused inspection method"""
        print("🎯 FOCUSED WHATSAPP INSPECTION")
        print("🔍 Looking for key differentiating elements and patterns")
        print("=" * 60)
        
        test_numbers = ["082253767671", "6285586712458"]
        
        for i, phone in enumerate(test_numbers, 1):
            expected = self.known_status.get(phone, "unknown")
            print(f"\n📞 FOCUSED INSPECTION {phone} ({i}/{len(test_numbers)}) - Expected: {expected}")
            print("-" * 60)
            
            try:
                result = await self.focused_inspect_whatsapp(phone)
                self.results[phone] = result
                
                status = result.get('status', 'error')
                confidence = result.get('confidence', '')
                score = result.get('score', 0)
                factors = result.get('decision_factors', [])
                
                print(f"    🎯 RESULT: {status} ({confidence}) - Score: {score}")
                print(f"    💡 FACTORS: {factors}")
                
                # Check accuracy
                if expected != "unknown":
                    is_correct = "✅ CORRECT" if status == expected else "❌ WRONG"
                    print(f"    📊 ACCURACY: {is_correct}")
                
                if i < len(test_numbers):
                    print(f"    ⏳ Waiting 3 seconds...")
                    await asyncio.sleep(3)
                
            except Exception as e:
                self.results[phone] = {"status": "error", "error": str(e)}
                print(f"    ❌ Error: {str(e)}")
        
        return self.results
    
    def save_results(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/whatsapp_focused_inspection_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename

async def main():
    inspector = WhatsAppFocusedInspector()
    await inspector.test_focused_inspection()
    inspector.save_results()

if __name__ == "__main__":
    asyncio.run(main())