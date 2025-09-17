"""
Telegram Account Pool Manager
Multi-session MTP system for maximum validation efficiency
"""

import asyncio
import os
import time
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from telegram_mtp_validator import TelegramMTPValidator
import logging

class TelegramAccountPool:
    def __init__(self, db, max_concurrent_sessions: int = 4):
        self.db = db
        self.max_concurrent_sessions = max_concurrent_sessions
        self.session_pool: Dict[str, TelegramMTPValidator] = {}
        self.account_usage: Dict[str, int] = {}  # account_id -> usage_count
        self.account_last_used: Dict[str, datetime] = {}
        self.rate_limits: Dict[str, List[float]] = {}  # account_id -> timestamps
        self.cleanup_interval = 600  # 10 minutes
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting config
        self.max_requests_per_hour = 100  # Per account
        self.max_concurrent_per_account = 5
        
    async def get_available_account(self) -> Optional[str]:
        """Get available Telegram account for validation"""
        try:
            # Get active accounts from database
            active_accounts = await self.db.telegram_accounts.find({
                "is_active": True,
                "status": {"$in": ["active", "logged_in"]}
            }).to_list(length=None)
            
            if not active_accounts:
                self.logger.warning("No active Telegram accounts available")
                return None
            
            # Find account with lowest usage and not rate limited
            best_account = None
            lowest_usage = float('inf')
            
            for account in active_accounts:
                account_id = str(account["_id"])
                
                # Check rate limits
                if self._is_rate_limited(account_id):
                    continue
                
                # Check concurrent usage
                current_usage = self.account_usage.get(account_id, 0)
                if current_usage >= self.max_concurrent_per_account:
                    continue
                
                # Select account with lowest usage
                if current_usage < lowest_usage:
                    lowest_usage = current_usage
                    best_account = account_id
            
            return best_account
            
        except Exception as e:
            self.logger.error(f"Error getting available account: {e}")
            return None
    
    async def get_session_for_account(self, account_id: str) -> Optional[TelegramMTPValidator]:
        """Get or create MTP session for account"""
        try:
            # Return existing session if available
            if account_id in self.session_pool:
                self.account_last_used[account_id] = datetime.utcnow()
                return self.session_pool[account_id]
            
            # Get account details
            from bson import ObjectId
            account = await self.db.telegram_accounts.find_one({"_id": ObjectId(account_id)})
            if not account:
                self.logger.error(f"Account {account_id} not found")
                return None
            
            # Create new session
            session_name = f"telegram_session_{account_id}"
            validator = TelegramMTPValidator(
                session_name=session_name,
                api_id=account.get("api_id"),
                api_hash=account.get("api_hash"),
                phone_number=account.get("phone_number")
            )
            
            # Initialize session
            if await validator.initialize():
                self.session_pool[account_id] = validator
                self.account_usage[account_id] = 0
                self.account_last_used[account_id] = datetime.utcnow()
                self.rate_limits[account_id] = []
                
                self.logger.info(f"Created MTP session for account: {account_id}")
                return validator
            else:
                self.logger.error(f"Failed to initialize session for account: {account_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating session for account {account_id}: {e}")
            return None
    
    def _is_rate_limited(self, account_id: str) -> bool:
        """Check if account is rate limited"""
        try:
            current_time = time.time()
            hour_ago = current_time - 3600
            
            # Clean old timestamps
            if account_id in self.rate_limits:
                self.rate_limits[account_id] = [
                    ts for ts in self.rate_limits[account_id] 
                    if ts > hour_ago
                ]
                
                # Check if over limit
                if len(self.rate_limits[account_id]) >= self.max_requests_per_hour:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking rate limit for {account_id}: {e}")
            return True
    
    async def record_usage(self, account_id: str):
        """Record API usage for rate limiting"""
        try:
            current_time = time.time()
            
            # Record usage
            if account_id not in self.rate_limits:
                self.rate_limits[account_id] = []
            
            self.rate_limits[account_id].append(current_time)
            self.account_usage[account_id] = self.account_usage.get(account_id, 0) + 1
            
            # Update database usage stats
            await self.db.telegram_accounts.update_one(
                {"_id": ObjectId(account_id)},
                {
                    "$inc": {"usage_count": 1, "daily_usage": 1},
                    "$set": {"last_used": datetime.utcnow()}
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error recording usage for {account_id}: {e}")
    
    async def release_account(self, account_id: str):
        """Release account after validation"""
        try:
            if account_id in self.account_usage:
                self.account_usage[account_id] = max(0, self.account_usage[account_id] - 1)
            
        except Exception as e:
            self.logger.error(f"Error releasing account {account_id}: {e}")
    
    async def cleanup_idle_sessions(self):
        """Cleanup idle sessions to free resources"""
        try:
            current_time = datetime.utcnow()
            idle_threshold = timedelta(minutes=30)
            
            sessions_to_remove = []
            
            for account_id, last_used in self.account_last_used.items():
                if current_time - last_used > idle_threshold:
                    if self.account_usage.get(account_id, 0) == 0:
                        sessions_to_remove.append(account_id)
            
            for account_id in sessions_to_remove:
                if account_id in self.session_pool:
                    try:
                        await self.session_pool[account_id].close()
                        del self.session_pool[account_id]
                        del self.account_usage[account_id]
                        del self.account_last_used[account_id]
                        
                        self.logger.info(f"Cleaned up idle session: {account_id}")
                    except Exception as e:
                        self.logger.error(f"Error cleaning up session {account_id}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error during session cleanup: {e}")
    
    async def get_pool_stats(self) -> Dict:
        """Get pool statistics"""
        return {
            "total_sessions": len(self.session_pool),
            "max_sessions": self.max_concurrent_sessions,
            "active_usage": dict(self.account_usage),
            "rate_limits": {
                account_id: len(timestamps) 
                for account_id, timestamps in self.rate_limits.items()
            },
            "session_last_used": {
                account_id: last_used.isoformat()
                for account_id, last_used in self.account_last_used.items()
            }
        }
    
    async def start_cleanup_task(self):
        """Start background cleanup task"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_idle_sessions()
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
    
    async def shutdown(self):
        """Shutdown all sessions"""
        try:
            for account_id, session in self.session_pool.items():
                try:
                    await session.close()
                    self.logger.info(f"Shutdown session: {account_id}")
                except Exception as e:
                    self.logger.error(f"Error shutting down session {account_id}: {e}")
            
            self.session_pool.clear()
            self.account_usage.clear()
            self.account_last_used.clear()
            self.rate_limits.clear()
            
        except Exception as e:
            self.logger.error(f"Error during pool shutdown: {e}")

# Global pool instance
_telegram_pool = None

async def get_telegram_pool(db) -> TelegramAccountPool:
    """Get global Telegram account pool instance"""
    global _telegram_pool
    if _telegram_pool is None:
        _telegram_pool = TelegramAccountPool(db, max_concurrent_sessions=4)
        # Start cleanup task
        asyncio.create_task(_telegram_pool.start_cleanup_task())
    return _telegram_pool

async def validate_telegram_with_pool(identifier: str, validation_type: str, db) -> Dict:
    """Validate using Telegram account pool"""
    pool = await get_telegram_pool(db)
    account_id = await pool.get_available_account()
    
    if not account_id:
        return {
            "success": False,
            "error": "No Telegram accounts available for validation"
        }
    
    session = await pool.get_session_for_account(account_id)
    if not session:
        return {
            "success": False, 
            "error": "Failed to create session for validation"
        }
    
    try:
        # Record usage for rate limiting
        await pool.record_usage(account_id)
        
        # Perform validation based on type
        if validation_type == "phone":
            result = await session.validate_phone_number(identifier)
        elif validation_type == "username":
            result = await session.validate_username(identifier)
        else:
            result = {
                "success": False,
                "error": f"Unknown validation type: {validation_type}"
            }
        
        # Add pool info to result
        if result.get("success"):
            result["details"]["account_used"] = account_id
            result["details"]["pool_method"] = True
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Pool validation failed: {str(e)}"
        }
    finally:
        await pool.release_account(account_id)