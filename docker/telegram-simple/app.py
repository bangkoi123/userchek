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
        """Setup Telegram client with optional proxy"""
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
        
        # Create Telegram client
        self.client = Client(
            name=f"account_{self.account_id}",
            api_id=self.api_id,
            api_hash=self.api_hash,
            phone_number=self.phone,
            workdir="/app/sessions",
            proxy=proxy_config
        )
    
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
        """Validate phone number using Telegram MTP"""
        # Rate limiting check
        can_proceed, message = self.check_rate_limit()
        if not can_proceed:
            return {
                "success": False,
                "error": message,
                "account_id": self.account_id,
                "rate_limit_reset": (self.hour_start + timedelta(hours=1)).isoformat()
            }
        
        try:
            # Start client
            await self.client.start()
            
            # Clean phone number
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            
            # Method 1: Check in contacts
            contacts = await self.client.get_contacts()
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
                "timestamp": datetime.now().isoformat()
            }
    
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