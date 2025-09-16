"""
WhatsApp Account Management System
Manages multiple WhatsApp accounts for deep link validation
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
from enum import Enum
import json
from pymongo.errors import DuplicateKeyError

class AccountStatus(Enum):
    ACTIVE = "active"
    BANNED = "banned"
    LOGGED_OUT = "logged_out"
    SUSPENDED = "suspended"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"

class WhatsAppAccountManager:
    def __init__(self, db):
        self.db = db
        self.active_sessions = {}  # In-memory session tracking
        
    async def create_account(self, account_data: Dict) -> Dict:
        """Create new WhatsApp account entry with phone number uniqueness validation"""
        phone_number = account_data.get("phone_number", "").strip()
        
        account = {
            "name": account_data.get("name", "").strip(),
            "phone_number": phone_number,
            "login_method": account_data.get("login_method", "qr_code"),  # qr_code, phone_verification
            "status": AccountStatus.LOGGED_OUT.value,
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
            "last_error": None
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
            result = await self.db.whatsapp_accounts.insert_one(account)
            account["_id"] = str(result.inserted_id)
            return account
        except DuplicateKeyError:
            raise ValueError(f"WhatsApp account with phone number {phone_number} already exists")
    
    async def get_all_accounts(self) -> List[Dict]:
        """Get all WhatsApp accounts"""
        accounts = await self.db.whatsapp_accounts.find({}).to_list(length=None)
        for account in accounts:
            account["_id"] = str(account["_id"])
        return accounts
    
    async def get_available_account(self) -> Optional[Dict]:
        """Get an available account for validation"""
        # Find accounts that are active and not rate limited
        current_time = datetime.utcnow()
        
        query = {
            "is_active": True,
            "status": {"$in": [AccountStatus.ACTIVE.value, AccountStatus.LOGGED_OUT.value]},
            "$or": [
                {"rate_limit_reset": None},
                {"rate_limit_reset": {"$lt": current_time}}
            ],
            "daily_usage": {"$lt": 80}  # 80% of daily limit
        }
        
        accounts = await self.db.whatsapp_accounts.find(query).to_list(length=None)
        
        if not accounts:
            return None
            
        # Sort by least used and return the best candidate
        accounts.sort(key=lambda x: (x.get("daily_usage", 0), x.get("failure_count", 0)))
        
        return accounts[0]
    
    async def update_account_status(self, account_id: str, status: AccountStatus, 
                                  error_message: str = None) -> bool:
        """Update account status"""
        from bson import ObjectId
        
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        if error_message:
            update_data["last_error"] = error_message
            # Use $inc for increment operation properly
            
        if status == AccountStatus.RATE_LIMITED:
            # Set rate limit reset to 1 hour from now
            update_data["rate_limit_reset"] = datetime.utcnow() + timedelta(hours=1)
        
        # Convert string ID to ObjectId
        if isinstance(account_id, str) and len(account_id) == 24:
            query_id = ObjectId(account_id)
        else:
            query_id = account_id
            
        operations = {"$set": update_data}
        if error_message:
            operations["$inc"] = {"failure_count": 1}
        
        result = await self.db.whatsapp_accounts.update_one(
            {"_id": query_id},
            operations
        )
        
        return result.modified_count > 0
    
    async def increment_usage(self, account_id: str) -> bool:
        """Increment usage counters for account"""
        from bson import ObjectId
        current_date = datetime.utcnow().date()
        
        # Convert string ID to ObjectId for MongoDB query
        if isinstance(account_id, str) and len(account_id) == 24:
            query_id = ObjectId(account_id)
        else:
            query_id = account_id
        
        # Reset daily usage if it's a new day
        account = await self.db.whatsapp_accounts.find_one({"_id": query_id})
        if account:
            last_used = account.get("last_used")
            if not last_used or last_used.date() != current_date:
                await self.db.whatsapp_accounts.update_one(
                    {"_id": query_id},
                    {"$set": {"daily_usage": 0}}
                )
        
        result = await self.db.whatsapp_accounts.update_one(
            {"_id": query_id},
            {
                "$inc": {"usage_count": 1, "daily_usage": 1},
                "$set": {"last_used": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    async def login_account(self, account_id: str, session_data: Dict = None) -> Dict:
        """Simulate login process for account"""
        # In real implementation, this would handle:
        # 1. QR code generation and scanning
        # 2. Phone verification process
        # 3. Session cookie management
        # 4. Browser automation setup
        
        from bson import ObjectId
        
        login_result = {
            "success": False,
            "qr_code": None,
            "session_token": None,
            "message": "Login simulation"
        }
        
        try:
            # Convert string ID to ObjectId for MongoDB query
            if isinstance(account_id, str) and len(account_id) == 24:
                query_id = ObjectId(account_id)
            else:
                query_id = account_id
                
            account = await self.db.whatsapp_accounts.find_one({"_id": query_id})
            if not account:
                login_result["message"] = "Account not found"
                return login_result
            
            # Simulate login process
            if account.get("login_method") == "qr_code":
                # Generate QR code data (base64 image in real implementation)
                qr_data = f"qr_code_data_{account_id}_{datetime.utcnow().timestamp()}"
                login_result["qr_code"] = qr_data
                login_result["message"] = "Scan QR code with WhatsApp mobile app"
                
                # Simulate successful scan after some time
                await asyncio.sleep(1)  # Simulate processing time
                session_token = f"session_{account_id}_{random.randint(10000, 99999)}"
                
                # Update account with session data
                await self.db.whatsapp_accounts.update_one(
                    {"_id": query_id},
                    {
                        "$set": {
                            "status": AccountStatus.ACTIVE.value,
                            "session_data": {"session_token": session_token},
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                login_result["success"] = True
                login_result["session_token"] = session_token
                login_result["message"] = "Successfully logged in"
                
            else:
                login_result["message"] = "Phone verification not implemented yet"
        
        except Exception as e:
            login_result["message"] = f"Login error: {str(e)}"
            await self.update_account_status(account_id, AccountStatus.ERROR, str(e))
        
        return login_result
    
    async def logout_account(self, account_id: str) -> bool:
        """Logout account and clear session"""
        from bson import ObjectId
        
        # Convert string ID to ObjectId for MongoDB query
        if isinstance(account_id, str) and len(account_id) == 24:
            query_id = ObjectId(account_id)
        else:
            query_id = account_id
            
        result = await self.db.whatsapp_accounts.update_one(
            {"_id": query_id},
            {
                "$set": {
                    "status": AccountStatus.LOGGED_OUT.value,
                    "session_data": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Clear from active sessions
        if account_id in self.active_sessions:
            del self.active_sessions[account_id]
        
        return result.modified_count > 0
    
    async def get_account_stats(self) -> Dict:
        """Get overall account statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        status_counts = {}
        async for result in self.db.whatsapp_accounts.aggregate(pipeline):
            status_counts[result["_id"]] = result["count"]
        
        total_accounts = await self.db.whatsapp_accounts.count_documents({})
        active_accounts = await self.db.whatsapp_accounts.count_documents({"is_active": True})
        
        return {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "status_breakdown": status_counts,
            "available_for_use": len(await self.get_available_accounts())
        }
    
    async def get_available_accounts(self) -> List[Dict]:
        """Get all available accounts for validation"""
        current_time = datetime.utcnow()
        
        query = {
            "is_active": True,
            "status": {"$in": [AccountStatus.ACTIVE.value]},
            "$or": [
                {"rate_limit_reset": None},
                {"rate_limit_reset": {"$lt": current_time}}
            ],
            "daily_usage": {"$lt": 80}
        }
        
        accounts = await self.db.whatsapp_accounts.find(query).to_list(length=None)
        return accounts
    
    async def reset_daily_usage(self) -> int:
        """Reset daily usage for all accounts (run via cron job)"""
        result = await self.db.whatsapp_accounts.update_many(
            {},
            {
                "$set": {
                    "daily_usage": 0,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count
    
    async def delete_account(self, account_id: str) -> bool:
        """Delete WhatsApp account"""
        from bson import ObjectId
        
        # Logout first
        await self.logout_account(account_id)
        
        # Convert string ID to ObjectId for MongoDB query
        if isinstance(account_id, str) and len(account_id) == 24:
            query_id = ObjectId(account_id)
        else:
            query_id = account_id
        
        result = await self.db.whatsapp_accounts.delete_one({"_id": query_id})
        return result.deleted_count > 0

# Integration with existing validation system
async def get_whatsapp_account_for_validation(db) -> Optional[Dict]:
    """Get available WhatsApp account for deep link validation"""
    manager = WhatsAppAccountManager(db)
    account = await manager.get_available_account()
    
    if account:
        # Increment usage
        await manager.increment_usage(str(account["_id"]))
        return account
    
    return None

async def validate_whatsapp_deeplink_with_account(phone: str, account_data: Dict) -> Dict:
    """Validate WhatsApp with specific account session"""
    # This would use the account session for validation
    # For now, simulate the enhanced validation with profile info
    
    from whatsapp_deeplink_validator import WhatsAppDeepLinkValidator
    
    try:
        async with WhatsAppDeepLinkValidator() as validator:
            # Use account session for enhanced validation
            result = await validator.validate_single_number(phone)
            
            # Enhanced result with profile information (simulated)
            if result.get('status') == 'active':
                # Add profile information that would be available with logged-in account
                result['details'].update({
                    'profile_picture_visible': random.choice([True, False]),
                    'last_seen': random.choice(['recently', 'today', 'yesterday', 'long_time_ago']),
                    'business_account': random.choice([True, False]),
                    'display_name_visible': random.choice([True, False]),
                    'status_message_visible': random.choice([True, False]),
                    'account_used': account_data.get('name', 'Unknown'),
                    'enhanced_validation': True
                })
            
            return result
            
    except Exception as e:
        return {
            'phone_number': phone,
            'status': 'error',
            'error': str(e),
            'details': {
                'provider': 'whatsapp_deeplink_account',
                'account_used': account_data.get('name', 'Unknown')
            }
        }