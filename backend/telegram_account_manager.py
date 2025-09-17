"""
Telegram Account Manager
Database operations for Telegram MTP accounts
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from bson import ObjectId

class TelegramAccountStatus(Enum):
    LOGGED_OUT = "logged_out"
    ACTIVE = "active" 
    BANNED = "banned"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"

class TelegramAccountManager:
    def __init__(self, db):
        self.db = db
        
    async def create_account(self, account_data: Dict) -> Dict:
        """Create new Telegram account entry"""
        phone_number = account_data.get("phone_number", "").strip()
        
        # Check if phone number already exists
        existing_account = await self.db.telegram_accounts.find_one({
            "phone_number": phone_number,
            "is_active": True
        })
        
        if existing_account:
            raise ValueError(f"Telegram account with phone number {phone_number} already exists")
        
        account = {
            "name": account_data.get("name", "").strip(),
            "phone_number": phone_number,
            "api_id": account_data.get("api_id", "").strip(),
            "api_hash": account_data.get("api_hash", "").strip(),
            "status": TelegramAccountStatus.LOGGED_OUT.value,
            "session_data": None,
            "last_used": None,
            "usage_count": 0,
            "daily_usage": 0,
            "rate_limit_reset": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "notes": account_data.get("notes", "").strip(),
            "max_daily_requests": account_data.get("max_daily_requests", 100),
            "failure_count": 0,
            "last_error": None,
            "validation_method": account_data.get("validation_method", "mtp"),
            "account_type": account_data.get("account_type", "personal")  # personal, business
        }
        
        # Add proxy configuration if provided
        if account_data.get("proxy_config"):
            proxy_config = account_data["proxy_config"]
            if proxy_config.get("enabled"):
                account["proxy_config"] = {
                    "enabled": True,
                    "type": proxy_config.get("type", "http"),
                    "url": proxy_config.get("url", "").strip(),
                    "username": proxy_config.get("username", "").strip() or None,
                    "password": proxy_config.get("password", "").strip() or None
                }
        
        try:
            result = await self.db.telegram_accounts.insert_one(account)
            account["_id"] = str(result.inserted_id)
            return account
        except Exception as e:
            if "duplicate key" in str(e).lower():
                raise ValueError(f"Telegram account with phone number {phone_number} already exists")
            raise e

    async def get_accounts(self, active_only: bool = True) -> List[Dict]:
        """Get all Telegram accounts"""
        query = {"is_active": True} if active_only else {}
        accounts = await self.db.telegram_accounts.find(query).to_list(length=None)
        
        for account in accounts:
            account["_id"] = str(account["_id"])
            
        return accounts

    async def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Get account by ID"""
        try:
            from bson import ObjectId
            account = await self.db.telegram_accounts.find_one({"_id": ObjectId(account_id)})
            if account:
                account["_id"] = str(account["_id"])
            return account
        except Exception:
            return None

    async def update_account(self, account_id: str, update_data: Dict) -> bool:
        """Update account"""
        try:
            from bson import ObjectId
            
            # Prepare update data
            update_fields = {
                "name": update_data.get("name"),
                "phone_number": update_data.get("phone_number"),
                "api_id": update_data.get("api_id"),
                "api_hash": update_data.get("api_hash"),
                "max_daily_requests": update_data.get("max_daily_requests", 100),
                "notes": update_data.get("notes", ""),
                "updated_at": datetime.utcnow()
            }
            
            # Add proxy configuration if provided
            if "proxy_config" in update_data:
                update_fields["proxy_config"] = update_data["proxy_config"]
            
            result = await self.db.telegram_accounts.update_one(
                {"_id": ObjectId(account_id)},
                {"$set": update_fields}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error updating account {account_id}: {e}")
            return False

    async def delete_account(self, account_id: str) -> bool:
        """Delete account (soft delete)"""
        try:
            from bson import ObjectId
            result = await self.db.telegram_accounts.update_one(
                {"_id": ObjectId(account_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def update_account_status(self, account_id: str, status: TelegramAccountStatus, error_message: str = None):
        """Update account status"""
        try:
            from bson import ObjectId
            
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow()
            }
            
            if error_message:
                update_data["last_error"] = error_message
                update_data["failure_count"] = {"$inc": {"failure_count": 1}}
            else:
                update_data["last_error"] = None
            
            await self.db.telegram_accounts.update_one(
                {"_id": ObjectId(account_id)},
                {"$set": update_data}
            )
            
        except Exception as e:
            print(f"Error updating account status: {e}")

    async def get_accounts_stats(self) -> Dict:
        """Get accounts statistics"""
        try:
            # Get all active accounts
            accounts = await self.get_accounts(active_only=True)
            
            # Calculate statistics
            total_accounts = len(accounts)
            status_counts = {}
            available_count = 0
            
            for account in accounts:
                status = account.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count available accounts (active and not rate limited)
                if status == "active":
                    # Check if not rate limited
                    daily_usage = account.get("daily_usage", 0)
                    max_daily = account.get("max_daily_requests", 100)
                    if daily_usage < max_daily:
                        available_count += 1
            
            return {
                "total_accounts": total_accounts,
                "active_accounts": len([a for a in accounts if a.get("status") == "active"]),
                "status_breakdown": status_counts,
                "available_for_use": available_count
            }
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                "total_accounts": 0,
                "active_accounts": 0,
                "status_breakdown": {},
                "available_for_use": 0
            }

    async def reset_daily_usage(self):
        """Reset daily usage counters (run daily)"""
        try:
            await self.db.telegram_accounts.update_many(
                {"is_active": True},
                {
                    "$set": {
                        "daily_usage": 0,
                        "rate_limit_reset": None
                    }
                }
            )
        except Exception as e:
            print(f"Error resetting daily usage: {e}")

    async def get_available_accounts(self, limit: int = 10) -> List[Dict]:
        """Get available accounts for validation"""
        try:
            # Get accounts that are active and not rate limited
            pipeline = [
                {"$match": {
                    "is_active": True,
                    "status": "active",
                    "$expr": {"$lt": ["$daily_usage", "$max_daily_requests"]}
                }},
                {"$sort": {"daily_usage": 1, "last_used": 1}},
                {"$limit": limit}
            ]
            
            accounts = await self.db.telegram_accounts.aggregate(pipeline).to_list(length=None)
            
            for account in accounts:
                account["_id"] = str(account["_id"])
                
            return accounts
            
        except Exception as e:
            print(f"Error getting available accounts: {e}")
            return []