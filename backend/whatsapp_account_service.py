"""
WhatsApp Account Service - Runs in Docker Container
Handles single WhatsApp account with optional proxy support
"""

import asyncio
import os
import json
import aiohttp
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import redis.asyncio as redis
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppAccountService:
    def __init__(self):
        self.app = FastAPI(title="WhatsApp Account Service")
        self.account_id = os.environ.get('ACCOUNT_ID')
        self.proxy_url = os.environ.get('PROXY_URL')
        self.proxy_username = os.environ.get('PROXY_USERNAME') 
        self.proxy_password = os.environ.get('PROXY_PASSWORD')
        self.mongo_url = os.environ.get('MONGO_URL')
        self.main_api_url = os.environ.get('MAIN_API_URL')
        
        # Initialize clients
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.playwright = None
        self.db = None
        self.redis_client = None
        
        # Setup routes
        self.setup_routes()
        self.setup_middleware()
        
        logger.info(f"🚀 WhatsApp Account Service initialized for account: {self.account_id}")
        
    def setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        @self.app.on_event("startup")
        async def startup():
            await self.initialize_services()
            
        @self.app.on_event("shutdown") 
        async def shutdown():
            await self.cleanup_services()
            
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "account_id": self.account_id,
                "proxy_enabled": bool(self.proxy_url),
                "browser_ready": self.browser is not None,
                "context_ready": self.context is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        @self.app.post("/login")
        async def login():
            try:
                result = await self.perform_whatsapp_login()
                
                # Notify main API about login result
                await self.notify_main_api("login_result", result)
                
                return result
            except Exception as e:
                logger.error(f"❌ Login error: {str(e)}")
                return {"success": False, "error": str(e)}
                
        @self.app.post("/logout")
        async def logout():
            try:
                result = await self.perform_whatsapp_logout()
                
                # Notify main API about logout
                await self.notify_main_api("logout_result", result)
                
                return result
            except Exception as e:
                logger.error(f"❌ Logout error: {str(e)}")
                return {"success": False, "error": str(e)}
                
        @self.app.post("/validate/{phone_number}")
        async def validate_phone(phone_number: str):
            try:
                result = await self.validate_whatsapp_number(phone_number)
                return result
            except Exception as e:
                logger.error(f"❌ Validation error: {str(e)}")
                return {"success": False, "error": str(e)}
                
        @self.app.get("/status")
        async def get_status():
            try:
                status = await self.check_whatsapp_status()
                return status
            except Exception as e:
                logger.error(f"❌ Status check error: {str(e)}")
                return {"healthy": False, "error": str(e)}
    
    async def initialize_services(self):
        """Initialize all required services"""
        try:
            # Connect to MongoDB
            mongo_client = AsyncIOMotorClient(self.mongo_url)
            db_name = os.environ.get('DB_NAME', 'webtools_validation')
            self.db = mongo_client[db_name]
            
            # Connect to Redis
            self.redis_client = redis.from_url("redis://redis:6379")
            
            # Initialize Playwright with proxy support
            await self.initialize_browser()
            
            # Register with main API
            await self.register_with_main_api()
            
            logger.info(f"✅ Services initialized for account {self.account_id}")
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {str(e)}")
            raise
    
    async def initialize_browser(self):
        """Initialize Playwright browser with optional proxy"""
        try:
            self.playwright = await async_playwright().start()
            
            # Browser launch options
            launch_options = {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            }
            
            # Add proxy if configured
            if self.proxy_url:
                proxy_config = {'server': self.proxy_url}
                if self.proxy_username and self.proxy_password:
                    proxy_config['username'] = self.proxy_username
                    proxy_config['password'] = self.proxy_password
                
                launch_options['proxy'] = proxy_config
                logger.info(f"🌐 Proxy configured: {self.proxy_url}")
            
            self.browser = await self.playwright.chromium.launch(**launch_options)
            
            # Create context for this account
            session_path = f"/app/sessions/{self.account_id}"
            os.makedirs(session_path, exist_ok=True)
            
            context_options = {
                'user_data_dir': session_path,
                'viewport': {'width': 1366, 'height': 768},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            logger.info(f"✅ Browser initialized for account {self.account_id}")
            
        except Exception as e:
            logger.error(f"❌ Browser initialization failed: {str(e)}")
            raise
    
    async def perform_whatsapp_login(self):
        """Perform real WhatsApp login with QR code"""
        try:
            if not self.context:
                raise Exception("Browser context not initialized")
                
            self.page = await self.context.new_page()
            
            logger.info(f"📱 Starting WhatsApp login for {self.account_id}")
            
            # Navigate to WhatsApp Web
            await self.page.goto('https://web.whatsapp.com', timeout=30000)
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Check if already logged in
            try:
                await self.page.wait_for_selector('[data-testid="chat"]', timeout=10000)
                logger.info(f"✅ Account {self.account_id} already logged in")
                
                return {
                    "success": True,
                    "already_logged_in": True,
                    "message": "Account already logged in",
                    "account_id": self.account_id
                }
                
            except:
                logger.info(f"🔍 Account {self.account_id} needs QR code scan")
            
            # Get QR code
            try:
                qr_element = await self.page.wait_for_selector(
                    'canvas[aria-label="Scan this QR code to link a device!"]', 
                    timeout=15000
                )
                
                # Screenshot QR code
                qr_screenshot = await qr_element.screenshot()
                
                # Convert to base64
                import base64
                qr_base64 = base64.b64encode(qr_screenshot).decode('utf-8')
                
                logger.info(f"📷 QR Code generated for account {self.account_id}")
                
                # Start monitoring for login completion
                asyncio.create_task(self.monitor_login_completion())
                
                return {
                    "success": True,
                    "already_logged_in": False,
                    "message": "QR Code generated - scan with WhatsApp mobile app",
                    "qr_code": f"data:image/png;base64,{qr_base64}",
                    "account_id": self.account_id,
                    "expires_in": 300
                }
                
            except Exception as qr_error:
                logger.error(f"❌ QR Code generation failed: {str(qr_error)}")
                return {
                    "success": False,
                    "message": f"Could not generate QR code: {str(qr_error)}"
                }
                
        except Exception as e:
            logger.error(f"❌ WhatsApp login failed: {str(e)}")
            return {
                "success": False,
                "message": f"Login error: {str(e)}"
            }
    
    async def monitor_login_completion(self):
        """Monitor for login completion"""
        try:
            logger.info(f"⏳ Monitoring login completion for {self.account_id}")
            
            # Wait for chat interface (5 minutes timeout)
            await self.page.wait_for_selector('[data-testid="chat"]', timeout=300000)
            
            logger.info(f"✅ Login successful for account {self.account_id}")
            
            # Update account status in database
            await self.update_account_status("active")
            
            # Notify main API
            await self.notify_main_api("login_completed", {
                "account_id": self.account_id,
                "status": "active",
                "logged_in_at": datetime.utcnow().isoformat()
            })
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Login timeout for account {self.account_id}")
            await self.update_account_status("logged_out", "QR code expired")
            
        except Exception as e:
            logger.error(f"❌ Login monitoring error: {str(e)}")
            await self.update_account_status("error", str(e))
    
    async def perform_whatsapp_logout(self):
        """Logout from WhatsApp"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.context:
                await self.context.close()
                self.context = None
            
            # Clear session files
            import shutil
            session_path = f"/app/sessions/{self.account_id}"
            if os.path.exists(session_path):
                shutil.rmtree(session_path, ignore_errors=True)
                
            await self.update_account_status("logged_out")
            
            logger.info(f"🚪 Account {self.account_id} logged out")
            
            return {
                "success": True,
                "message": "Account logged out successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Logout error: {str(e)}")
            return {
                "success": False,
                "message": f"Logout error: {str(e)}"
            }
    
    async def validate_whatsapp_number(self, phone_number: str):
        """Validate WhatsApp number using this account's session"""
        try:
            if not self.page:
                return {
                    "success": False,
                    "error": "Account not logged in"
                }
            
            # Clean phone number
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            
            logger.info(f"🔍 Validating {phone_number} using account {self.account_id}")
            
            # Navigate to WhatsApp chat URL
            chat_url = f"https://web.whatsapp.com/send?phone={clean_phone}"
            await self.page.goto(chat_url, timeout=30000)
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Check for validation indicators
            page_content = await self.page.content()
            
            # Check for invalid number message
            invalid_indicators = [
                "Phone number shared via url is invalid",
                "Nomor telepon yang dibagikan via tautan tidak valid",
                "not exist on WhatsApp"
            ]
            
            for indicator in invalid_indicators:
                if indicator.lower() in page_content.lower():
                    return {
                        "success": True,
                        "status": "inactive",
                        "phone_number": phone_number,
                        "details": {
                            "provider": "whatsapp_container",
                            "account_used": self.account_id,
                            "detection_method": "invalid_number_message"
                        }
                    }
            
            # Check for chat interface (valid number)
            try:
                await self.page.wait_for_selector('[data-testid="conversation-compose-box-input"]', timeout=10000)
                
                # Extract profile information
                profile_info = await self.extract_profile_info()
                
                return {
                    "success": True,
                    "status": "active",
                    "phone_number": phone_number,
                    "details": {
                        "provider": "whatsapp_container",
                        "account_used": self.account_id,
                        "detection_method": "chat_interface_loaded",
                        **profile_info
                    }
                }
                
            except:
                return {
                    "success": True,
                    "status": "unknown",
                    "phone_number": phone_number,
                    "details": {
                        "provider": "whatsapp_container",
                        "account_used": self.account_id,
                        "detection_method": "ambiguous_response"
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Validation error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def extract_profile_info(self):
        """Extract WhatsApp profile information"""
        profile_info = {
            "profile_picture_visible": False,
            "last_seen_visible": False,
            "business_account": False,
            "display_name": None
        }
        
        try:
            # Check for profile picture
            try:
                await self.page.wait_for_selector('img[src*="blob:"]', timeout=3000)
                profile_info["profile_picture_visible"] = True
            except:
                pass
            
            # Check for last seen
            try:
                last_seen_element = await self.page.wait_for_selector('[title*="last seen"], [title*="online"]', timeout=3000)
                if last_seen_element:
                    profile_info["last_seen_visible"] = True
            except:
                pass
                
            # Check for business account
            try:
                await self.page.wait_for_selector('[data-testid="business-info"]', timeout=3000)
                profile_info["business_account"] = True
            except:
                pass
                
        except Exception as e:
            logger.warning(f"⚠️ Profile info extraction error: {str(e)}")
        
        return profile_info
    
    async def check_whatsapp_status(self):
        """Check WhatsApp account health"""
        try:
            if not self.page:
                return {"healthy": False, "reason": "No active session"}
            
            # Navigate to WhatsApp Web
            await self.page.goto('https://web.whatsapp.com', timeout=30000)
            await asyncio.sleep(3)
            
            # Check if logged in
            try:
                await self.page.wait_for_selector('[data-testid="chat"]', timeout=10000)
                return {"healthy": True, "status": "active"}
            except:
                return {"healthy": False, "reason": "Logged out", "needs_login": True}
                
        except Exception as e:
            return {"healthy": False, "reason": f"Health check error: {str(e)}"}
    
    async def update_account_status(self, status: str, error_message: str = None):
        """Update account status in database"""
        try:
            if not self.db:
                return
                
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if error_message:
                update_data["last_error"] = error_message
            
            await self.db.whatsapp_accounts.update_one(
                {"_id": self.account_id},
                {"$set": update_data}
            )
            
        except Exception as e:
            logger.error(f"❌ Database update error: {str(e)}")
    
    async def notify_main_api(self, event_type: str, data: dict):
        """Notify main API about events"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "account_id": self.account_id,
                    "event_type": event_type,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await session.post(
                    f"{self.main_api_url}/api/internal/account-event",
                    json=payload,
                    timeout=10
                )
                
        except Exception as e:
            logger.error(f"❌ API notification error: {str(e)}")
    
    async def register_with_main_api(self):
        """Register this container with main API"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "account_id": self.account_id,
                    "container_url": f"http://{self.account_id}:8080",
                    "proxy_enabled": bool(self.proxy_url),
                    "status": "starting"
                }
                
                await session.post(
                    f"{self.main_api_url}/api/internal/register-container",
                    json=payload,
                    timeout=10
                )
                
            logger.info(f"✅ Registered with main API: {self.account_id}")
            
        except Exception as e:
            logger.error(f"❌ Registration error: {str(e)}")
    
    async def cleanup_services(self):
        """Cleanup services on shutdown"""
        try:
            if self.page:
                await self.page.close()
                
            if self.context:
                await self.context.close()
                
            if self.browser:
                await self.browser.close()
                
            if self.playwright:
                await self.playwright.stop()
                
            if self.redis_client:
                await self.redis_client.close()
                
            logger.info(f"✅ Services cleaned up for account {self.account_id}")
            
        except Exception as e:
            logger.error(f"❌ Cleanup error: {str(e)}")

# Main service
service = WhatsAppAccountService()
app = service.app

if __name__ == "__main__":
    if not service.account_id:
        raise ValueError("ACCOUNT_ID environment variable is required")
        
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )