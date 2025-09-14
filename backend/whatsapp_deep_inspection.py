import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
import re

class WhatsAppDeepInspector:
    def __init__(self):
        self.results = {}
        # Known status for testing
        self.known_status = {
            "082253767671": "active",
            "089689547785": "active",  # wa business
            "6285586712458": "inactive"
        }
    
    def normalize_phone(self, phone):
        """Normalize phone number format"""
        phone = phone.strip().replace('+', '').replace('-', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif not phone.startswith('62'):
            phone = '62' + phone
        return phone
    
    async def deep_inspect_whatsapp(self, phone):
        """Deep inspection of WhatsApp validation with comprehensive analysis"""
        phone = self.normalize_phone(phone)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,  # Use headless for server environment
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768}
            )
            
            page = await context.new_page()
            
            # Track network requests
            network_requests = []
            network_responses = []
            
            page.on("request", lambda request: network_requests.append({
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "post_data": request.post_data
            }))
            
            page.on("response", lambda response: network_responses.append({
                "url": response.url,
                "status": response.status,
                "headers": dict(response.headers)
            }))
            
            # Track console messages
            console_messages = []
            page.on("console", lambda msg: console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location
            }))
            
            try:
                print(f"  🔍 DEEP INSPECTION: wa.me/{phone}")
                
                # Navigate to wa.me
                wa_url = f"https://wa.me/{phone}"
                response = await page.goto(wa_url, wait_until='networkidle', timeout=30000)
                
                print(f"    📡 Response: {response.status}")
                print(f"    🔗 Final URL: {page.url}")
                
                # Wait for JavaScript execution and dynamic content
                await page.wait_for_timeout(5000)
                
                # === 1. COMPREHENSIVE DOM INSPECTION ===
                print(f"    🔍 Analyzing DOM structure...")
                
                # Get full page content
                page_content = await page.content()
                
                # Check all elements with specific attributes
                dom_analysis = {}
                
                # Look for main content blocks
                main_elements = await page.locator('[class*="main"], [id*="main"]').all()
                dom_analysis['main_elements'] = len(main_elements)
                
                # Look for fallback/error blocks  
                fallback_elements = await page.locator('[class*="fallback"], [class*="error"]').all()
                dom_analysis['fallback_elements'] = len(fallback_elements)
                
                # Check for specific WhatsApp elements
                whatsapp_elements = await page.locator('[class*="whatsapp"], [data-testid*="whatsapp"]').all()
                dom_analysis['whatsapp_elements'] = len(whatsapp_elements)
                
                # Look for hidden elements
                hidden_elements = await page.locator('[style*="display: none"], [hidden]').all()
                dom_analysis['hidden_elements'] = len(hidden_elements)
                
                # === 2. JAVASCRIPT VARIABLE INSPECTION ===
                print(f"    📊 Checking JavaScript variables...")
                
                js_variables = await page.evaluate("""
                    () => {
                        const vars = {};
                        
                        // Check window variables
                        if (window.__INITIAL_DATA__) vars.initial_data = window.__INITIAL_DATA__;
                        if (window.__CONFIG__) vars.config = window.__CONFIG__;
                        if (window.require) vars.has_require = true;
                        
                        // Check for WhatsApp specific variables
                        const possibleVars = ['WA', 'whatsapp', 'phoneNumber', 'isValid', 'hasError', 'userExists'];
                        possibleVars.forEach(varName => {
                            if (window[varName] !== undefined) {
                                vars[varName] = window[varName];
                            }
                        });
                        
                        // Check document variables
                        vars.readyState = document.readyState;
                        vars.title = document.title;
                        
                        return vars;
                    }
                """)
                
                # === 3. ELEMENT VISIBILITY & ATTRIBUTES ===
                print(f"    👁️ Checking element visibility...")
                
                element_checks = {}
                
                # Check for common button/link selectors
                selectors_to_check = [
                    'button',
                    'a[href*="web.whatsapp.com"]',
                    '[class*="btn"]',
                    '[class*="button"]',
                    '[data-testid]',
                    '[class*="chat"]',
                    '[class*="send"]',
                    '[class*="continue"]',
                    '[class*="download"]',
                    '[class*="install"]'
                ]
                
                for selector in selectors_to_check:
                    try:
                        elements = await page.locator(selector).all()
                        element_info = []
                        
                        for element in elements[:3]:  # Check first 3 elements
                            try:
                                is_visible = await element.is_visible()
                                text_content = await element.text_content()
                                class_name = await element.get_attribute('class')
                                
                                element_info.append({
                                    'visible': is_visible,
                                    'text': text_content[:100] if text_content else None,
                                    'class': class_name
                                })
                            except:
                                pass
                        
                        if element_info:
                            element_checks[selector] = element_info
                    except:
                        pass
                
                # === 4. CSS CLASS ANALYSIS ===
                print(f"    🎨 Analyzing CSS classes...")
                
                css_analysis = await page.evaluate("""
                    () => {
                        const allElements = document.querySelectorAll('*');
                        const classNames = new Set();
                        const suspiciousClasses = [];
                        
                        allElements.forEach(el => {
                            if (el.className && typeof el.className === 'string') {
                                el.className.split(' ').forEach(cls => {
                                    if (cls) classNames.add(cls);
                                });
                                
                                // Look for suspicious patterns
                                const className = el.className.toLowerCase();
                                if (className.includes('error') || 
                                    className.includes('invalid') || 
                                    className.includes('disabled') ||
                                    className.includes('hidden') ||
                                    className.includes('active') ||
                                    className.includes('inactive')) {
                                    suspiciousClasses.push({
                                        tag: el.tagName,
                                        class: el.className,
                                        visible: el.offsetParent !== null,
                                        text: el.textContent ? el.textContent.substring(0, 100) : ''
                                    });
                                }
                            }
                        });
                        
                        return {
                            total_classes: classNames.size,
                            suspicious_classes: suspiciousClasses
                        };
                    }
                """)
                
                # === 5. NETWORK REQUEST ANALYSIS ===
                print(f"    🌐 Analyzing network requests...")
                
                # Filter relevant requests
                relevant_requests = []
                for req in network_requests:
                    if any(keyword in req['url'].lower() for keyword in ['whatsapp', 'wa.me', 'api', 'send', 'phone']):
                        relevant_requests.append(req)
                
                relevant_responses = []
                for resp in network_responses:
                    if any(keyword in resp['url'].lower() for keyword in ['whatsapp', 'wa.me', 'api', 'send', 'phone']):
                        relevant_responses.append(resp)
                
                # === 6. DYNAMIC CONTENT CHANGES ===
                print(f"    🔄 Waiting for dynamic changes...")
                
                # Take screenshot of current state
                await page.screenshot(path=f"/app/whatsapp_inspect_{phone}.png")
                
                # Wait for potential dynamic loading
                await page.wait_for_timeout(3000)
                
                # Check if content changed
                new_content = await page.content()
                content_changed = len(new_content) != len(page_content)
                
                # === 7. SPECIFIC PATTERN DETECTION ===
                print(f"    🎯 Detecting specific patterns...")
                
                pattern_analysis = await page.evaluate("""
                    () => {
                        const content = document.body.innerHTML;
                        const text = document.body.textContent || '';
                        
                        return {
                            // Indonesian error patterns
                            has_indonesian_error: /tidak valid|nomor tidak valid|tidak tersedia|tidak ditemukan/i.test(text),
                            
                            // English error patterns  
                            has_english_error: /invalid|not found|not available|error/i.test(text),
                            
                            // Success patterns
                            has_continue_chat: /continue.*chat|chat.*now|send.*message/i.test(text),
                            
                            // Download patterns
                            has_download_prompt: /download.*whatsapp|install.*whatsapp|get.*whatsapp/i.test(text),
                            
                            // URL patterns in content
                            has_web_whatsapp_url: content.includes('web.whatsapp.com'),
                            has_whatsapp_scheme: content.includes('whatsapp://'),
                            
                            // Meta tag analysis
                            meta_description: document.querySelector('meta[name="description"]')?.content || '',
                            meta_title: document.title,
                            
                            // Body class analysis
                            body_classes: document.body.className
                        };
                    }
                """)
                
                await browser.close()
                
                # === COMPILE COMPREHENSIVE ANALYSIS ===
                analysis_result = {
                    "phone": phone,
                    "final_url": page.url,
                    "dom_analysis": dom_analysis,
                    "js_variables": js_variables,
                    "element_checks": element_checks,
                    "css_analysis": css_analysis,
                    "network_requests": relevant_requests,
                    "network_responses": relevant_responses,
                    "console_messages": console_messages,
                    "pattern_analysis": pattern_analysis,
                    "content_changed": content_changed,
                    "content_length": len(new_content)
                }
                
                # === DECISION LOGIC BASED ON DEEP ANALYSIS ===
                decision_factors = []
                score = 0
                
                # Factor 1: Error patterns
                if pattern_analysis['has_indonesian_error'] or pattern_analysis['has_english_error']:
                    decision_factors.append("ERROR_DETECTED")
                    score -= 3
                
                # Factor 2: Success patterns
                if pattern_analysis['has_continue_chat'] and not pattern_analysis['has_download_prompt']:
                    decision_factors.append("CHAT_AVAILABLE")
                    score += 2
                
                # Factor 3: Download prompts (usually indicates invalid)
                if pattern_analysis['has_download_prompt']:
                    decision_factors.append("DOWNLOAD_PROMPT")
                    score -= 2
                
                # Factor 4: WhatsApp URLs
                if pattern_analysis['has_web_whatsapp_url']:
                    decision_factors.append("HAS_WEB_URL")
                    score += 1
                
                # Factor 5: Suspicious CSS classes
                suspicious_error_classes = [cls for cls in css_analysis['suspicious_classes'] 
                                          if 'error' in cls['class'].lower() or 'invalid' in cls['class'].lower()]
                if suspicious_error_classes:
                    decision_factors.append("ERROR_CLASSES")
                    score -= 2
                
                # Factor 6: Network response analysis
                error_responses = [resp for resp in relevant_responses if resp['status'] >= 400]
                if error_responses:
                    decision_factors.append("HTTP_ERRORS")
                    score -= 1
                
                # Final decision
                if score <= -2:
                    status = "inactive"
                    confidence = "high"
                elif score >= 2:
                    status = "active"
                    confidence = "high"
                elif score >= 0:
                    status = "active"
                    confidence = "medium"
                else:
                    status = "inactive"
                    confidence = "medium"
                
                return {
                    "status": status,
                    "confidence": confidence,
                    "score": score,
                    "decision_factors": decision_factors,
                    "method": "deep_inspection",
                    "analysis": analysis_result
                }
                
            except Exception as e:
                await browser.close()
                return {
                    "status": "error",
                    "method": "deep_inspection", 
                    "error": str(e)
                }
    
    async def test_deep_inspection(self):
        """Test deep inspection on known numbers"""
        print("🔬 DEEP WHATSAPP INSPECTION - Element & Code Analysis")
        print("🎯 Looking for hidden elements, JS variables, and patterns")
        print("=" * 70)
        
        test_numbers = ["082253767671", "6285586712458"]  # One active, one inactive
        
        for i, phone in enumerate(test_numbers, 1):
            expected = self.known_status.get(phone, "unknown")
            print(f"\n📞 DEEP INSPECTION {phone} ({i}/{len(test_numbers)}) - Expected: {expected}")
            print("=" * 70)
            
            try:
                result = await self.deep_inspect_whatsapp(phone)
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
                
                # Show key findings
                analysis = result.get('analysis', {})
                pattern_analysis = analysis.get('pattern_analysis', {})
                
                print(f"    🔍 KEY FINDINGS:")
                print(f"      - Indonesian error: {pattern_analysis.get('has_indonesian_error', False)}")
                print(f"      - English error: {pattern_analysis.get('has_english_error', False)}")
                print(f"      - Continue chat: {pattern_analysis.get('has_continue_chat', False)}")
                print(f"      - Download prompt: {pattern_analysis.get('has_download_prompt', False)}")
                
                if i < len(test_numbers):
                    print(f"    ⏳ Waiting before next inspection...")
                    await asyncio.sleep(5)
                
            except Exception as e:
                self.results[phone] = {"status": "error", "error": str(e)}
                print(f"    ❌ Error: {str(e)}")
        
        return self.results
    
    def save_detailed_results(self):
        """Save comprehensive results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/whatsapp_deep_inspection_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {filename}")
        return filename

# Run deep inspection
async def main():
    inspector = WhatsAppDeepInspector()
    await inspector.test_deep_inspection()
    inspector.save_detailed_results()

if __name__ == "__main__":
    asyncio.run(main())