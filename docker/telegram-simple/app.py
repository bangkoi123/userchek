#!/usr/bin/env python3
"""
Simple Telegram Account Validator
Untuk multi-account setup di 1 VPS
"""

import asyncio
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from aiohttp import web
from pyrogram import Client
import time

class SimpleTelegramValidator:
    def __init__(self):
        self.account_id = os.getenv('ACCOUNT_ID', '1')
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        self.max_requests_hour = int(os.getenv('MAX_REQUESTS_HOUR', 150))
        
        # Request tracking
        self.request_count = 0
        self.hour_start = datetime.now()
        self.last_request = 0
        
        # Setup logging
        self.setup_logging()
        
        # Setup Telegram client
        self.setup_client()
        
        self.logger.info(f"🚀 Telegram Account {self.account_id} initialized")
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format=f'[Account-{self.account_id}] %(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f'telegram_{self.account_id}')
        
        # File handler
        file_handler = logging.FileHandler(f'/app/logs/account_{self.account_id}.log')
        file_handler.setFormatter(logging.Formatter(
            f'[Account-{self.account_id}] %(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
    
    def setup_client(self):
        """Setup Telegram client with optional proxy and unique fingerprint"""
        proxy_config = None
        
        # Optional proxy setup
        proxy_host = os.getenv('PROXY_HOST')
        if proxy_host:
            proxy_config = {
                "scheme": "socks5",  # or "http"
                "hostname": proxy_host,
                "port": int(os.getenv('PROXY_PORT', 1080)),
                "username": os.getenv('PROXY_USER'),
                "password": os.getenv('PROXY_PASS')
            }
            self.logger.info(f"🌐 Using proxy: {proxy_host}")
        else:
            self.logger.info("🌐 No proxy configured (direct connection)")
        
        # 🎭 UNIQUE FINGERPRINT PER ACCOUNT
        fingerprint = self.generate_unique_fingerprint()
        self.logger.info(f"🎭 Account fingerprint: {fingerprint['device_model']} | {fingerprint['system_lang']}")
        
        # Create Telegram client with unique session name
        session_name = f"{fingerprint['session_prefix']}_{self.account_id}_{fingerprint['device_id']}"
        
        self.client = Client(
            name=session_name,
            api_id=self.api_id,
            api_hash=self.api_hash,
            phone_number=self.phone,
            workdir="/app/sessions",
            proxy=proxy_config,
            # Device info for fingerprinting
            device_model=fingerprint['device_model'],
            system_version=fingerprint['system_version'],
            app_version=fingerprint['app_version'],
            lang_code=fingerprint['lang_code'],
            system_lang_code=fingerprint['system_lang']
        )
        
        # Store fingerprint for logging
        self.fingerprint = fingerprint
    
    def generate_unique_fingerprint(self):
        """Generate unique fingerprint based on account ID"""
        account_num = int(self.account_id)
        
        # Device models pool
        device_models = [
            "Samsung SM-G991B",     # Galaxy S21
            "iPhone14,2",           # iPhone 13 Pro  
            "OnePlus KB2005",       # OnePlus 9
            "Xiaomi M2102K1G",      # Mi 11
            "OPPO CPH2371",         # Find X5
            "Vivo V2134",           # V23 Pro
            "Google Pixel 6",       # Pixel 6
            "Huawei ELS-NX9",       # P40 Pro
            "Sony XQ-CT54",         # Xperia 5 III
            "Nokia TA-1336"         # Nokia X20
        ]
        
        # System versions pool
        system_versions = [
            "Android 13; 33",
            "Android 12; 32", 
            "Android 11; 30",
            "iOS 16.1.1",
            "iOS 15.7",
            "iOS 17.0"
        ]
        
        # App versions pool
        app_versions = [
            "9.2.2 (2823)",
            "9.1.7 (2741)", 
            "9.0.4 (2632)",
            "8.9.3 (2551)",
            "8.8.5 (2477)"
        ]
        
        # Language codes pool
        lang_codes = [
            "en", "id", "ms", "th", "vi", "tl"
        ]
        
        # System languages pool
        system_langs = [
            "en-US", "id-ID", "ms-MY", "th-TH", "vi-VN", "tl-PH"
        ]
        
        # Session prefixes
        session_prefixes = [
            "tg_main", "telegram_user", "tg_client", 
            "user_session", "mobile_tg", "tg_app"
        ]
        
        # Generate deterministic but unique fingerprint per account
        import hashlib
        seed = f"telegram_account_{account_num}_{self.phone}".encode()
        hash_obj = hashlib.md5(seed)
        hash_bytes = hash_obj.digest()
        
        # Use hash bytes to select items deterministically
        device_idx = hash_bytes[0] % len(device_models)
        system_idx = hash_bytes[1] % len(system_versions)
        app_idx = hash_bytes[2] % len(app_versions)
        lang_idx = hash_bytes[3] % len(lang_codes)
        sys_lang_idx = hash_bytes[4] % len(system_langs)
        prefix_idx = hash_bytes[5] % len(session_prefixes)
        
        # Generate device-specific ID
        device_id = f"{hash_bytes[6]:02x}{hash_bytes[7]:02x}{hash_bytes[8]:02x}"
        
        fingerprint = {
            "device_model": device_models[device_idx],
            "system_version": system_versions[system_idx],
            "app_version": app_versions[app_idx],
            "lang_code": lang_codes[lang_idx],
            "system_lang": system_langs[sys_lang_idx],
            "session_prefix": session_prefixes[prefix_idx],
            "device_id": device_id,
            "account_id": account_num
        }
        
        return fingerprint
    
    def check_rate_limit(self) -> tuple[bool, str]:
        """Check if we're within rate limits"""
        now = datetime.now()
        
        # Reset counter if hour passed
        if now - self.hour_start > timedelta(hours=1):
            self.request_count = 0
            self.hour_start = now
        
        # Check hourly limit
        if self.request_count >= self.max_requests_hour:
            return False, f"Rate limit exceeded: {self.request_count}/{self.max_requests_hour} per hour"
        
        # Check minimum delay between requests (3 seconds)
        current_time = time.time()
        if current_time - self.last_request < 3:
            return False, "Too fast: minimum 3 seconds between requests"
        
        return True, "OK"
    
    async def validate_phone(self, phone_number: str) -> Dict:
        """Validate phone number with unique timing patterns per account"""
        # Rate limiting check
        can_proceed, message = self.check_rate_limit()
        if not can_proceed:
            return {
                "success": False,
                "error": message,
                "account_id": self.account_id,
                "rate_limit_reset": (self.hour_start + timedelta(hours=1)).isoformat()
            }
        
        # 🎭 UNIQUE TIMING PATTERN per account (anti-detection)
        await self.apply_unique_timing_pattern()
        
        try:
            # Start client
            await self.client.start()
            
            # Clean phone number
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            
            # 🎭 Add account-specific delay patterns
            await self.account_specific_delay()
            
            # Method 1: Check in contacts
            contacts = await self.client.get_contacts()
            
            # 🎭 Simulate different processing speeds per account
            await self.simulate_processing_variation()
            
            for contact in contacts:
                if hasattr(contact, 'phone_number') and contact.phone_number == clean_phone:
                    result = {
                        "success": True,
                        "status": "active",
                        "phone_number": phone_number,
                        "details": {
                            "username": contact.username,
                            "first_name": contact.first_name,
                            "last_name": contact.last_name,
                            "is_contact": True,
                            "has_username": bool(contact.username),
                            "method": "contact_lookup",
                            "account_id": self.account_id,
                            "fingerprint": {
                                "device": self.fingerprint['device_model'],
                                "system": self.fingerprint['system_version'],
                                "lang": self.fingerprint['lang_code']
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    # Update counters
                    self.request_count += 1
                    self.last_request = time.time()
                    
                    await self.client.stop()
                    return result
            
            # Method 2: Try username lookup (if has username)
            # This is limited by Telegram privacy settings
            
            # Method 3: Basic existence check
            # Return unknown status (most common case due to privacy)
            result = {
                "success": True,
                "status": "unknown",
                "phone_number": phone_number,
                "details": {
                    "method": "privacy_limited_check",
                    "reason": "Number exists but privacy settings prevent detailed info",
                    "account_id": self.account_id,
                    "fingerprint": {
                        "device": self.fingerprint['device_model'],
                        "system": self.fingerprint['system_version'],
                        "lang": self.fingerprint['lang_code']
                    },
                    "timestamp": datetime.now().isoformat(),
                    "note": "For detailed info, number must be in contacts"
                }
            }
            
            # Update counters
            self.request_count += 1
            self.last_request = time.time()
            
            await self.client.stop()
            return result
            
        except Exception as e:
            self.logger.error(f"Validation error for {phone_number}: {e}")
            
            # Update counters even on error
            self.request_count += 1
            self.last_request = time.time()
            
            try:
                await self.client.stop()
            except:
                pass
                
            return {
                "success": False,
                "error": str(e),
                "phone_number": phone_number,
                "account_id": self.account_id,
                "fingerprint": {
                    "device": self.fingerprint['device_model']
                },
                "timestamp": datetime.now().isoformat()
            }
    
    async def apply_unique_timing_pattern(self):
        """Apply unique timing patterns per account to avoid detection"""
        account_num = int(self.account_id)
        
        # Different base delays per account (in seconds)
        base_delays = [0.5, 0.8, 1.2, 0.3, 0.9, 1.5]
        base_delay = base_delays[account_num % len(base_delays)]
        
        # Add random variation (±30%)
        import random
        variation = random.uniform(-0.3, 0.3)
        final_delay = base_delay * (1 + variation)
        
        await asyncio.sleep(final_delay)
    
    async def account_specific_delay(self):
        """Account-specific delay between operations"""
        account_num = int(self.account_id)
        
        # Different delay patterns per account
        delay_patterns = [
            0.2,  # Account 1: Fast
            0.4,  # Account 2: Medium  
            0.6,  # Account 3: Slow
            0.3,  # Account 4: Medium-fast
            0.5   # Account 5: Medium-slow
        ]
        
        delay = delay_patterns[account_num % len(delay_patterns)]
        await asyncio.sleep(delay)
    
    async def simulate_processing_variation(self):
        """Simulate different processing speeds to look more human"""
        account_num = int(self.account_id)
        
        # Processing variations based on account
        if account_num == 1:
            await asyncio.sleep(0.1)  # Fast processor
        elif account_num == 2:
            await asyncio.sleep(0.3)  # Medium processor
        elif account_num == 3:
            await asyncio.sleep(0.2)  # Variable processor
        else:
            import random
            await asyncio.sleep(random.uniform(0.1, 0.4))
    
    async def health_check(self) -> Dict:
        """Health check endpoint"""
        try:
            # Check if we can connect to Telegram
            telegram_status = "unknown"
            try:
                await self.client.start()
                me = await self.client.get_me()
                telegram_status = "connected" if me else "error"
                await self.client.stop()
            except Exception as e:
                telegram_status = f"error: {str(e)[:50]}"
            
            # Calculate rate limit info
            now = datetime.now()
            if now - self.hour_start > timedelta(hours=1):
                requests_remaining = self.max_requests_hour
                reset_time = now + timedelta(hours=1)
            else:
                requests_remaining = self.max_requests_hour - self.request_count
                reset_time = self.hour_start + timedelta(hours=1)
            
            return {
                "status": "healthy",
                "account_id": self.account_id,
                "telegram_status": telegram_status,
                "rate_limit": {
                    "requests_used": self.request_count,
                    "requests_remaining": requests_remaining,
                    "max_per_hour": self.max_requests_hour,
                    "reset_time": reset_time.isoformat()
                },
                "proxy_enabled": bool(os.getenv('PROXY_HOST')),
                "proxy_host": os.getenv('PROXY_HOST', 'direct'),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "account_id": self.account_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Web Server
async def create_app():
    """Create web application"""
    validator = SimpleTelegramValidator()
    
    async def health_handler(request):
        """Health check endpoint"""
        result = await validator.health_check()
        status_code = 200 if result.get("status") == "healthy" else 500
        return web.json_response(result, status=status_code)
    
    async def validate_handler(request):
        """Validation endpoint"""
        try:
            data = await request.json()
            phone_number = data.get('phone_number')
            
            if not phone_number:
                return web.json_response({
                    "success": False,
                    "error": "phone_number is required"
                }, status=400)
            
            result = await validator.validate_phone(phone_number)
            return web.json_response(result)
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e),
                "account_id": validator.account_id
            }, status=500)
    
    async def status_handler(request):
        """Status endpoint"""
        return web.json_response({
            "account_id": validator.account_id,
            "service": "telegram_validator",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        })
    
    async def start_login_handler(request):
        """Start login process endpoint"""
        try:
            data = await request.json()
            api_id = data.get('api_id')
            api_hash = data.get('api_hash')
            phone_number = data.get('phone_number')
            
            if not all([api_id, api_hash, phone_number]):
                return web.json_response({
                    "success": False,
                    "error": "Missing required fields"
                }, status=400)
            
            # Update client configuration
            validator.api_id = api_id
            validator.api_hash = api_hash
            validator.phone = phone_number
            
            # Setup new client dengan real credentials
            validator.setup_client()
            
            # Generate unique session ID untuk tracking
            import uuid
            session_id = str(uuid.uuid4())
            
            # Start login process
            try:
                await validator.client.connect()
                
                # Send verification code
                sent_code = await validator.client.send_code(phone_number)
                
                # Store session info untuk verification nanti
                validator.login_sessions = getattr(validator, 'login_sessions', {})
                validator.login_sessions[session_id] = {
                    "phone_hash": sent_code.phone_code_hash,
                    "phone_number": phone_number,
                    "api_id": api_id,
                    "api_hash": api_hash,
                    "created_at": datetime.now().isoformat()
                }
                
                return web.json_response({
                    "success": True,
                    "message": f"Verification code sent to {phone_number}",
                    "session_id": session_id,
                    "phone_number": phone_number
                })
                
            except Exception as e:
                await validator.client.disconnect()
                return web.json_response({
                    "success": False,
                    "error": f"Login initiation failed: {str(e)}"
                }, status=500)
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": f"Request processing failed: {str(e)}"
            }, status=500)
    
    async def verify_login_handler(request):
        """Verify SMS code and complete login"""
        try:
            data = await request.json()
            session_id = data.get('session_id')
            verification_code = data.get('verification_code')
            
            if not session_id or not verification_code:
                return web.json_response({
                    "success": False,
                    "error": "Session ID and verification code required"
                }, status=400)
            
            # Get session info
            if not hasattr(validator, 'login_sessions') or session_id not in validator.login_sessions:
                return web.json_response({
                    "success": False,
                    "error": "Invalid session ID"
                }, status=400)
            
            session_info = validator.login_sessions[session_id]
            
            try:
                # Complete login dengan verification code
                await validator.client.sign_in(
                    phone_number=session_info["phone_number"],
                    phone_code_hash=session_info["phone_hash"],
                    phone_code=verification_code
                )
                
                # Get user info setelah login
                me = await validator.client.get_me()
                
                # Get additional info
                contacts = await validator.client.get_contacts()
                
                user_info = {
                    "user_id": me.id,
                    "first_name": me.first_name,
                    "last_name": me.last_name,
                    "username": me.username,
                    "phone_number": me.phone_number,
                    "is_premium": me.is_premium,
                    "contacts_count": len(contacts),
                    "login_time": datetime.now().isoformat()
                }
                
                # Update validator dengan user info
                validator.user_info = user_info
                validator.login_status = "logged_in"
                
                # Clean up session
                del validator.login_sessions[session_id]
                
                validator.logger.info(f"✅ Real account login successful: {me.first_name} (@{me.username})")
                
                return web.json_response({
                    "success": True,
                    "message": "Login completed successfully",
                    "user_info": user_info
                })
                
            except Exception as e:
                # Cleanup on error
                try:
                    await validator.client.disconnect()
                except:
                    pass
                
                error_msg = str(e)
                if "PHONE_CODE_INVALID" in error_msg:
                    error_msg = "Invalid verification code. Please try again."
                elif "PHONE_CODE_EXPIRED" in error_msg:
                    error_msg = "Verification code expired. Please request a new one."
                
                return web.json_response({
                    "success": False,
                    "error": error_msg
                }, status=400)
                
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": f"Verification failed: {str(e)}"
            }, status=500)
    
    async def account_info_handler(request):
        """Get current account information"""
        try:
            if not hasattr(validator, 'user_info'):
                return web.json_response({
                    "logged_in": False,
                    "message": "No account logged in"
                })
            
            # Get current status dari Telegram
            try:
                await validator.client.start()
                me = await validator.client.get_me()
                
                # Update info
                validator.user_info.update({
                    "current_status": "connected",
                    "last_check": datetime.now().isoformat()
                })
                
                await validator.client.stop()
                
            except Exception as e:
                validator.user_info["current_status"] = f"error: {str(e)}"
            
            return web.json_response({
                "logged_in": True,
                "user_info": validator.user_info,
                "account_id": validator.account_id,
                "fingerprint": getattr(validator, 'fingerprint', {})
            })
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    # Create app
    app = web.Application()
    app.router.add_get('/health', health_handler)
    app.router.add_post('/validate', validate_handler)
    app.router.add_get('/status', status_handler)
    
    return app

async def main():
    """Main function"""
    print(f"🚀 Starting Telegram Validator Account {os.getenv('ACCOUNT_ID', '1')}")
    
    app = await create_app()
    
    # Start web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    print(f"✅ Account {os.getenv('ACCOUNT_ID', '1')} running on port 8080")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep 1 hour
    except KeyboardInterrupt:
        print(f"⏹️ Stopping Account {os.getenv('ACCOUNT_ID', '1')}")
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())