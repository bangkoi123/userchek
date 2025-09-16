"""
Real WhatsApp Browser Automation Manager
Handles real WhatsApp Web login, QR code generation, and session management
"""

import asyncio
import json
import base64
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import random
from whatsapp_account_manager import AccountStatus, WhatsAppAccountManager

class WhatsAppBrowserManager:
    def __init__(self, db, headless: bool = True):
        self.db = db
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}  # account_id -> context
        self.pages: Dict[str, Page] = {}  # account_id -> page
        self.playwright = None
        self.sessions_dir = "/app/backend/whatsapp_sessions"
        
        # Create sessions directory
        os.makedirs(self.sessions_dir, exist_ok=True)
        
    async def __aenter__(self):
        """Async context manager setup"""
        self.playwright = await async_playwright().start()
        
        # Launch browser with enhanced stealth settings for WhatsApp compatibility
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-features=VizDisplayCompositor',
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager cleanup"""
        # Close all contexts and pages
        for page in self.pages.values():
            try:
                await page.close()
            except:
                pass
                
        for context in self.contexts.values():
            try:
                await context.close()
            except:
                pass
        
        if self.browser:
            await self.browser.close()
            
        if self.playwright:
            await self.playwright.stop()
    
    def get_session_path(self, account_id: str) -> str:
        """Get session storage path for account"""
        return os.path.join(self.sessions_dir, f"session_{account_id}")
    
    async def create_context_for_account(self, account_id: str) -> BrowserContext:
        """Create browser context with session for account"""
        session_path = self.get_session_path(account_id)
        
        # Check if storage state exists
        storage_state_file = f"{session_path}/storage_state.json"
        storage_state = None
        
        if os.path.exists(storage_state_file):
            try:
                import json
                with open(storage_state_file, 'r') as f:
                    storage_state = json.load(f)
                print(f"📁 Loading existing session for account {account_id}")
            except Exception as e:
                print(f"⚠️ Could not load storage state: {str(e)}")
        
        # Create context with anti-detection measures
        import random
        
        # Random user agents to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Random viewport sizes
        viewports = [
            {'width': 1366, 'height': 768},
            {'width': 1920, 'height': 1080},
            {'width': 1440, 'height': 900},
            {'width': 1280, 'height': 720}
        ]
        
        selected_ua = random.choice(user_agents)
        selected_viewport = random.choice(viewports)
        
        print(f"🎭 Using user agent: {selected_ua[:50]}...")
        print(f"📱 Using viewport: {selected_viewport}")
        
        context = await self.browser.new_context(
            viewport=selected_viewport,
            user_agent=selected_ua,
            java_script_enabled=True,
            accept_downloads=False,
            ignore_https_errors=True,
            locale='en-US',
            timezone_id='Asia/Jakarta',
            storage_state=storage_state,
            # Additional anti-detection measures
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        )
        
        # Add stealth scripts to avoid detection
        await context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock languages and plugins
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
        self.contexts[account_id] = context
        return context
    
    async def login_account(self, account_id: str) -> Dict:
        """Real WhatsApp login with QR code (with anti-detection measures)"""
        try:
            print(f"🚀 Starting real WhatsApp login for account: {account_id}")
            
            # Create context for this account
            context = await self.create_context_for_account(account_id)
            page = await context.new_page()
            self.pages[account_id] = page
            
            # Add random delay to appear more human-like
            import random
            initial_delay = random.uniform(2, 5)
            print(f"⏳ Random delay: {initial_delay:.1f}s")
            await asyncio.sleep(initial_delay)
            
            # Navigate to WhatsApp Web with human-like behavior
            print("📱 Navigating to WhatsApp Web...")
            await page.goto('https://web.whatsapp.com', timeout=30000)
            
            # Wait for page to load with random delay
            await page.wait_for_load_state('networkidle')
            human_delay = random.uniform(3, 7)
            print(f"⏳ Human-like delay: {human_delay:.1f}s")
            await asyncio.sleep(human_delay)
            
            # Check if already logged in
            try:
                await page.wait_for_selector('[data-testid="chat"]', timeout=10000)
                print("✅ Already logged in!")
                
                # Update account status
                manager = WhatsAppAccountManager(self.db)
                await manager.update_account_status(account_id, AccountStatus.ACTIVE)
                
                return {
                    "success": True,
                    "already_logged_in": True,
                    "message": "Account already logged in",
                    "qr_code": None
                }
                
            except:
                print("🔍 Not logged in, need QR code scan...")
            
            # Wait for QR code with multiple selectors and better error handling
            try:
                print("🔍 Looking for QR code with multiple selectors...")
                
                # Try multiple QR code selectors
                qr_selectors = [
                    'canvas[aria-label="Scan this QR code to link a device!"]',
                    'canvas[aria-label*="QR"]',
                    'canvas[role="img"]',
                    '[data-testid="qr-code"]',
                    'canvas'
                ]
                
                qr_element = None
                for selector in qr_selectors:
                    try:
                        print(f"🎯 Trying selector: {selector}")
                        qr_element = await page.wait_for_selector(selector, timeout=8000)
                        if qr_element:
                            print(f"✅ Found QR code with selector: {selector}")
                            break
                    except:
                        continue
                
                if not qr_element:
                    # Try to find any canvas element and screenshot the page
                    print("⚠️ No QR code canvas found, trying page screenshot...")
                    full_screenshot = await page.screenshot()
                    qr_base64 = base64.b64encode(full_screenshot).decode('utf-8')
                    
                    return {
                        "success": True,
                        "already_logged_in": False,
                        "message": "Page screenshot captured (QR code location detection failed)",
                        "qr_code": f"data:image/png;base64,{qr_base64}",
                        "account_id": account_id,
                        "expires_in": 240,
                        "fallback": True
                    }
                
                print("📷 QR Code element found, capturing...")
                
                # Small delay before screenshot
                await asyncio.sleep(2)
                
                # Screenshot QR code area with retry logic
                qr_screenshot = None
                for attempt in range(3):
                    try:
                        qr_screenshot = await qr_element.screenshot()
                        break
                    except Exception as screenshot_error:
                        print(f"⚠️ Screenshot attempt {attempt + 1} failed: {str(screenshot_error)}")
                        if attempt < 2:
                            await asyncio.sleep(1)
                        else:
                            # Use full page screenshot as fallback
                            qr_screenshot = await page.screenshot()
                
                if not qr_screenshot:
                    raise Exception("Could not capture QR code screenshot")
                
                qr_base64 = base64.b64encode(qr_screenshot).decode('utf-8')
                
                print("✅ QR Code captured successfully")
                print(f"📊 QR Code size: {len(qr_base64)} characters")
                
                # Start monitoring for login completion (non-blocking)
                asyncio.create_task(self._monitor_login_completion(page, account_id))
                
                return {
                    "success": True,
                    "already_logged_in": False,
                    "message": "QR Code generated - scan with WhatsApp mobile app",
                    "qr_code": f"data:image/png;base64,{qr_base64}",
                    "account_id": account_id,
                    "expires_in": 240  # 4 minutes instead of 5
                }
                
            except Exception as qr_error:
                print(f"❌ QR Code not found: {str(qr_error)}")
                
                # Check for other states
                page_content = await page.content()
                if "Phone number banned" in page_content or "banned" in page_content.lower():
                    manager = WhatsAppAccountManager(self.db)
                    await manager.update_account_status(account_id, AccountStatus.BANNED, "Phone number banned")
                    
                    return {
                        "success": False,
                        "message": "Phone number is banned from WhatsApp",
                        "banned": True
                    }
                
                return {
                    "success": False,
                    "message": f"Could not load QR code: {str(qr_error)}"
                }
                
        except Exception as e:
            print(f"❌ Login error for account {account_id}: {str(e)}")
            
            # Update account status
            manager = WhatsAppAccountManager(self.db)
            await manager.update_account_status(account_id, AccountStatus.ERROR, str(e))
            
            return {
                "success": False,
                "message": f"Login error: {str(e)}"
            }
    
    async def _monitor_login_completion(self, page: Page, account_id: str):
        """Monitor page for login completion"""
        try:
            print(f"⏳ Monitoring login completion for {account_id}...")
            
            # Wait for either chat interface or timeout (5 minutes)
            await page.wait_for_selector('[data-testid="chat"]', timeout=300000)
            
            print(f"✅ Login successful for account {account_id}!")
            
            # Update account status
            manager = WhatsAppAccountManager(self.db)
            await manager.update_account_status(account_id, AccountStatus.ACTIVE)
            
            # Save session data
            await self._save_session_data(account_id)
            
        except asyncio.TimeoutError:
            print(f"⏰ Login timeout for account {account_id}")
            manager = WhatsAppAccountManager(self.db)
            await manager.update_account_status(account_id, AccountStatus.LOGGED_OUT, "QR code expired")
            
        except Exception as e:
            print(f"❌ Login monitoring error for {account_id}: {str(e)}")
            manager = WhatsAppAccountManager(self.db)
            await manager.update_account_status(account_id, AccountStatus.ERROR, str(e))
    
    async def _save_session_data(self, account_id: str):
        """Save session data to database and storage state"""
        try:
            session_token = f"session_{account_id}_{datetime.utcnow().timestamp()}"
            
            # Save storage state for session persistence
            if self.context:
                storage_state = await self.context.storage_state()
                session_path = self.get_session_path(account_id)
                
                # Save storage state to file
                import json
                with open(f"{session_path}/storage_state.json", 'w') as f:
                    json.dump(storage_state, f)
            
            # Update database
            await self.db.whatsapp_accounts.update_one(
                {"_id": account_id},
                {
                    "$set": {
                        "session_data": {
                            "session_token": session_token,
                            "logged_in_at": datetime.utcnow(),
                            "session_path": self.get_session_path(account_id),
                            "storage_state_available": True
                        }
                    }
                }
            )
            
            print(f"💾 Session data saved for account {account_id}")
            
        except Exception as e:
            print(f"❌ Error saving session data: {str(e)}")
    
    async def logout_account(self, account_id: str) -> bool:
        """Logout WhatsApp account"""
        try:
            print(f"🚪 Logging out account: {account_id}")
            
            # Close page and context if exists
            if account_id in self.pages:
                await self.pages[account_id].close()
                del self.pages[account_id]
                
            if account_id in self.contexts:
                await self.contexts[account_id].close()
                del self.contexts[account_id]
            
            # Remove session files
            session_path = self.get_session_path(account_id)
            if os.path.exists(session_path):
                import shutil
                shutil.rmtree(session_path, ignore_errors=True)
                print(f"🗑️ Session files removed for {account_id}")
            
            # Update account status
            manager = WhatsAppAccountManager(self.db)
            await manager.update_account_status(account_id, AccountStatus.LOGGED_OUT)
            
            return True
            
        except Exception as e:
            print(f"❌ Logout error for {account_id}: {str(e)}")
            return False
    
    async def validate_with_account(self, account_id: str, phone_number: str) -> Dict:
        """Validate phone number using logged-in WhatsApp account"""
        try:
            if account_id not in self.pages:
                return {
                    "success": False,
                    "error": "Account not logged in"
                }
            
            page = self.pages[account_id]
            
            # Clean phone number
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            
            print(f"🔍 Validating {phone_number} using account {account_id}")
            
            # Navigate to WhatsApp chat URL
            chat_url = f"https://web.whatsapp.com/send?phone={clean_phone}"
            await page.goto(chat_url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Check for various indicators
            page_content = await page.content()
            
            # Check for invalid number message
            invalid_indicators = [
                "Phone number shared via url is invalid",
                "Nomor telepon yang dibagikan via tautan tidak valid",
                "El número de teléfono compartido",
                "not exist on WhatsApp",
                "não existe no WhatsApp"
            ]
            
            for indicator in invalid_indicators:
                if indicator.lower() in page_content.lower():
                    return {
                        "success": True,
                        "status": "inactive",
                        "phone_number": phone_number,
                        "details": {
                            "provider": "whatsapp_browser",
                            "detection_method": "invalid_number_message",
                            "indicator": indicator,
                            "account_used": account_id
                        }
                    }
            
            # Check for chat interface (indicates valid number)
            try:
                await page.wait_for_selector('[data-testid="conversation-compose-box-input"]', timeout=10000)
                
                # Try to extract profile information
                profile_info = await self._extract_profile_info(page)
                
                return {
                    "success": True,
                    "status": "active",
                    "phone_number": phone_number,
                    "details": {
                        "provider": "whatsapp_browser",
                        "detection_method": "chat_interface_loaded",
                        "account_used": account_id,
                        **profile_info
                    }
                }
                
            except:
                # Ambiguous result
                return {
                    "success": True,
                    "status": "unknown",
                    "phone_number": phone_number,
                    "details": {
                        "provider": "whatsapp_browser",
                        "detection_method": "ambiguous_response",
                        "account_used": account_id
                    }
                }
                
        except Exception as e:
            print(f"❌ Validation error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _extract_profile_info(self, page: Page) -> Dict:
        """Extract profile information from WhatsApp chat"""
        profile_info = {
            "profile_picture_visible": False,
            "last_seen_visible": False,
            "business_account": False,
            "display_name": None,
            "status_message": None
        }
        
        try:
            # Check for profile picture
            try:
                await page.wait_for_selector('[data-testid="default-user"]', timeout=3000)
                profile_info["profile_picture_visible"] = False
            except:
                try:
                    await page.wait_for_selector('img[src*="blob:"]', timeout=3000)
                    profile_info["profile_picture_visible"] = True
                except:
                    pass
            
            # Check for last seen info
            try:
                last_seen_element = await page.wait_for_selector('[title*="last seen"], [title*="online"]', timeout=3000)
                if last_seen_element:
                    last_seen_text = await last_seen_element.get_attribute('title')
                    profile_info["last_seen_visible"] = True
                    profile_info["last_seen"] = last_seen_text
            except:
                pass
                
            # Check for business account
            try:
                await page.wait_for_selector('[data-testid="business-info"]', timeout=3000)
                profile_info["business_account"] = True
            except:
                pass
            
            # Try to get display name
            try:
                name_element = await page.wait_for_selector('[data-testid="conversation-info-header-chat-title"]', timeout=3000)
                if name_element:
                    display_name = await name_element.inner_text()
                    profile_info["display_name"] = display_name.strip()
            except:
                pass
                
        except Exception as e:
            print(f"⚠️ Error extracting profile info: {str(e)}")
        
        return profile_info
    
    async def check_account_health(self, account_id: str) -> Dict:
        """Check if account is still healthy and logged in"""
        try:
            if account_id not in self.pages:
                return {"healthy": False, "reason": "No active session"}
            
            page = self.pages[account_id]
            
            # Navigate to WhatsApp Web main page
            await page.goto('https://web.whatsapp.com', timeout=30000)
            await asyncio.sleep(3)
            
            # Check if still logged in
            try:
                await page.wait_for_selector('[data-testid="chat"]', timeout=10000)
                return {"healthy": True, "status": "active"}
            except:
                # Check for QR code (logged out)
                try:
                    await page.wait_for_selector('canvas[aria-label="Scan this QR code to link a device!"]', timeout=5000)
                    return {"healthy": False, "reason": "Logged out", "needs_login": True}
                except:
                    # Check for ban
                    page_content = await page.content()
                    if "banned" in page_content.lower():
                        return {"healthy": False, "reason": "Account banned", "banned": True}
                    
                    return {"healthy": False, "reason": "Unknown state"}
                    
        except Exception as e:
            return {"healthy": False, "reason": f"Health check error: {str(e)}"}

# Integration functions
async def real_whatsapp_login(account_id: str, db) -> Dict:
    """Real WhatsApp login function for API"""
    async with WhatsAppBrowserManager(db, headless=True) as browser_manager:
        result = await browser_manager.login_account(account_id)
        return result

async def validate_with_real_whatsapp_account(phone_number: str, account_id: str, db) -> Dict:
    """Validate using real WhatsApp browser session"""
    async with WhatsAppBrowserManager(db, headless=True) as browser_manager:
        result = await browser_manager.validate_with_account(account_id, phone_number)
        return result

async def logout_real_whatsapp_account(account_id: str, db) -> bool:
    """Logout real WhatsApp account"""
    async with WhatsAppBrowserManager(db, headless=True) as browser_manager:
        result = await browser_manager.logout_account(account_id)
        return result