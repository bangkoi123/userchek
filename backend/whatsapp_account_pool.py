"""
WhatsApp Account Pool Manager
Optimized for single VPS deployment with multiple accounts
"""

import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from whatsapp_browser_manager import WhatsAppBrowserManager
from whatsapp_account_manager import AccountStatus, WhatsAppAccountManager
import logging

class WhatsAppAccountPool:
    def __init__(self, db, max_concurrent_browsers: int = 3):
        self.db = db
        self.max_concurrent_browsers = max_concurrent_browsers
        self.browser_pool: Dict[str, WhatsAppBrowserManager] = {}
        self.account_to_browser: Dict[str, str] = {}  # account_id -> browser_id
        self.browser_usage_count: Dict[str, int] = {}
        self.browser_last_used: Dict[str, datetime] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.logger = logging.getLogger(__name__)
        
    async def get_browser_for_account(self, account_id: str) -> Optional[WhatsAppBrowserManager]:
        """Get or create browser instance for account with pooling optimization"""
        try:
            # Check if account already has a browser assigned
            if account_id in self.account_to_browser:
                browser_id = self.account_to_browser[account_id]
                if browser_id in self.browser_pool:
                    self.browser_last_used[browser_id] = datetime.utcnow()
                    return self.browser_pool[browser_id]
            
            # Find least used browser or create new one
            browser_id = await self._get_available_browser()
            
            if browser_id:
                self.account_to_browser[account_id] = browser_id
                self.browser_usage_count[browser_id] = self.browser_usage_count.get(browser_id, 0) + 1
                self.browser_last_used[browser_id] = datetime.utcnow()
                return self.browser_pool[browser_id]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting browser for account {account_id}: {e}")
            return None
    
    async def _get_available_browser(self) -> Optional[str]:
        """Get available browser from pool or create new one"""
        try:
            # Find browser with lowest usage
            if self.browser_pool:
                least_used_browser = min(
                    self.browser_usage_count.items(), 
                    key=lambda x: x[1]
                )
                if least_used_browser[1] < 5:  # Max 5 accounts per browser
                    return least_used_browser[0]
            
            # Create new browser if under limit
            if len(self.browser_pool) < self.max_concurrent_browsers:
                browser_id = f"browser_{len(self.browser_pool)}"
                browser = WhatsAppBrowserManager(self.db, headless=True)
                await browser.__aenter__()
                
                self.browser_pool[browser_id] = browser
                self.browser_usage_count[browser_id] = 0
                self.browser_last_used[browser_id] = datetime.utcnow()
                
                self.logger.info(f"Created new browser: {browser_id}")
                return browser_id
            
            # Return least recently used browser if at limit
            if self.browser_last_used:
                lru_browser = min(
                    self.browser_last_used.items(),
                    key=lambda x: x[1]
                )[0]
                return lru_browser
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting available browser: {e}")
            return None
    
    async def release_account_browser(self, account_id: str):
        """Release browser assignment for account"""
        try:
            if account_id in self.account_to_browser:
                browser_id = self.account_to_browser[account_id]
                del self.account_to_browser[account_id]
                
                if browser_id in self.browser_usage_count:
                    self.browser_usage_count[browser_id] -= 1
                    
                self.logger.info(f"Released browser for account {account_id}")
                
        except Exception as e:
            self.logger.error(f"Error releasing browser for account {account_id}: {e}")
    
    async def cleanup_idle_browsers(self):
        """Cleanup idle browsers to free resources"""
        try:
            current_time = datetime.utcnow()
            idle_threshold = timedelta(minutes=30)
            
            browsers_to_remove = []
            
            for browser_id, last_used in self.browser_last_used.items():
                if current_time - last_used > idle_threshold:
                    if self.browser_usage_count.get(browser_id, 0) == 0:
                        browsers_to_remove.append(browser_id)
            
            for browser_id in browsers_to_remove:
                if browser_id in self.browser_pool:
                    try:
                        await self.browser_pool[browser_id].__aexit__(None, None, None)
                        del self.browser_pool[browser_id]
                        del self.browser_usage_count[browser_id]
                        del self.browser_last_used[browser_id]
                        
                        self.logger.info(f"Cleaned up idle browser: {browser_id}")
                    except Exception as e:
                        self.logger.error(f"Error cleaning up browser {browser_id}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error during browser cleanup: {e}")
    
    async def get_pool_stats(self) -> Dict:
        """Get current pool statistics"""
        return {
            "total_browsers": len(self.browser_pool),
            "max_browsers": self.max_concurrent_browsers,
            "active_assignments": len(self.account_to_browser),
            "browser_usage": dict(self.browser_usage_count),
            "browser_last_used": {
                browser_id: last_used.isoformat() 
                for browser_id, last_used in self.browser_last_used.items()
            }
        }
    
    async def start_cleanup_task(self):
        """Start background cleanup task"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_idle_browsers()
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
    
    async def shutdown(self):
        """Shutdown all browsers in pool"""
        try:
            for browser_id, browser in self.browser_pool.items():
                try:
                    await browser.__aexit__(None, None, None)
                    self.logger.info(f"Shutdown browser: {browser_id}")
                except Exception as e:
                    self.logger.error(f"Error shutting down browser {browser_id}: {e}")
            
            self.browser_pool.clear()
            self.account_to_browser.clear()
            self.browser_usage_count.clear()
            self.browser_last_used.clear()
            
        except Exception as e:
            self.logger.error(f"Error during pool shutdown: {e}")

# Global pool instance
_whatsapp_pool = None

async def get_whatsapp_pool(db) -> WhatsAppAccountPool:
    """Get global WhatsApp account pool instance"""
    global _whatsapp_pool
    if _whatsapp_pool is None:
        _whatsapp_pool = WhatsAppAccountPool(db, max_concurrent_browsers=3)
        # Start cleanup task
        asyncio.create_task(_whatsapp_pool.start_cleanup_task())
    return _whatsapp_pool

async def optimized_whatsapp_login(account_id: str, db) -> Dict:
    """Optimized WhatsApp login using account pool"""
    pool = await get_whatsapp_pool(db)
    browser = await pool.get_browser_for_account(account_id)
    
    if not browser:
        return {
            "success": False,
            "message": "No browser available - system at capacity"
        }
    
    try:
        result = await browser.login_account(account_id)
        return result
    except Exception as e:
        await pool.release_account_browser(account_id)
        return {
            "success": False,
            "message": f"Login failed: {str(e)}"
        }

async def optimized_whatsapp_validation(phone_number: str, account_id: str, db) -> Dict:
    """Optimized WhatsApp validation using account pool"""
    pool = await get_whatsapp_pool(db)
    browser = await pool.get_browser_for_account(account_id)
    
    if not browser:
        return {
            "success": False,
            "error": "No browser available for validation"
        }
    
    try:
        result = await browser.validate_with_account(account_id, phone_number)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Validation failed: {str(e)}"
        }