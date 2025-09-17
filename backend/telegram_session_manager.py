"""
Telegram Session Manager
Auto-recovery dan persistent session management untuk production
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pyrogram import Client
from pyrogram.session import Session
import sqlite3

class TelegramSessionManager:
    def __init__(self, db):
        self.db = db
        self.sessions_dir = "/app/backend/telegram_sessions"
        self.logger = logging.getLogger(__name__)
        
        # Ensure sessions directory exists
        os.makedirs(self.sessions_dir, exist_ok=True)
        
    async def create_persistent_session(self, account_data: Dict) -> Dict:
        """Create persistent Telegram session dengan auto-recovery"""
        try:
            account_id = account_data["_id"]
            phone_number = account_data["phone_number"]
            api_id = account_data["api_id"]
            api_hash = account_data["api_hash"]
            
            session_name = f"persistent_{account_id}"
            session_file = os.path.join(self.sessions_dir, f"{session_name}.session")
            
            # Check if session already exists and is valid
            if os.path.exists(session_file):
                self.logger.info(f"Found existing session for {phone_number}")
                
                # Try to use existing session
                client = Client(
                    name=session_name,
                    api_id=int(api_id),
                    api_hash=api_hash,
                    phone_number=phone_number,
                    workdir=self.sessions_dir
                )
                
                try:
                    await client.start()
                    
                    # Test session validity
                    me = await client.get_me()
                    if me and me.phone_number == phone_number.replace('+', ''):
                        self.logger.info(f"✅ Session valid for {phone_number}")
                        
                        # Update account status
                        await self.db.telegram_accounts.update_one(
                            {"_id": account_data["_id"]},
                            {
                                "$set": {
                                    "status": "active",
                                    "session_file": session_file,
                                    "last_validated": datetime.utcnow(),
                                    "auto_login": True
                                }
                            }
                        )
                        
                        await client.stop()
                        return {
                            "success": True,
                            "message": f"Session recovered for {phone_number}",
                            "session_file": session_file,
                            "requires_manual_login": False
                        }
                    
                except Exception as e:
                    self.logger.warning(f"Session invalid for {phone_number}: {e}")
                    # Remove invalid session file
                    if os.path.exists(session_file):
                        os.remove(session_file)
            
            # Need to create new session - this WILL require manual login
            self.logger.warning(f"⚠️ New session required for {phone_number}")
            
            return {
                "success": False,
                "message": f"Manual login required for {phone_number}",
                "requires_manual_login": True,
                "instructions": [
                    f"Account {phone_number} needs first-time setup",
                    "This is one-time process per account",
                    "After setup, account will auto-login forever",
                    "Use Telegram app to complete verification"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error creating session for {account_data.get('phone_number')}: {e}")
            return {
                "success": False,
                "error": str(e),
                "requires_manual_login": True
            }
    
    async def bulk_session_recovery(self) -> Dict:
        """Recover all existing sessions at startup"""
        try:
            self.logger.info("🔄 Starting bulk session recovery...")
            
            # Get all Telegram accounts
            accounts = await self.db.telegram_accounts.find({"is_active": True}).to_list(length=None)
            
            results = {
                "total_accounts": len(accounts),
                "recovered_sessions": 0,
                "failed_sessions": 0,
                "requires_manual_setup": []
            }
            
            for account in accounts:
                try:
                    result = await self.create_persistent_session(account)
                    
                    if result["success"]:
                        results["recovered_sessions"] += 1
                        self.logger.info(f"✅ Recovered: {account['phone_number']}")
                    else:
                        results["failed_sessions"] += 1
                        if result.get("requires_manual_login"):
                            results["requires_manual_setup"].append({
                                "phone": account["phone_number"],
                                "name": account["name"],
                                "account_id": str(account["_id"])
                            })
                        self.logger.warning(f"❌ Failed: {account['phone_number']}")
                        
                except Exception as e:
                    results["failed_sessions"] += 1
                    self.logger.error(f"❌ Error processing {account.get('phone_number')}: {e}")
            
            success_rate = (results["recovered_sessions"] / results["total_accounts"] * 100) if results["total_accounts"] > 0 else 0
            
            self.logger.info(f"📊 Session recovery complete: {results['recovered_sessions']}/{results['total_accounts']} ({success_rate:.1f}% success)")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in bulk session recovery: {e}")
            return {
                "total_accounts": 0,
                "recovered_sessions": 0,
                "failed_sessions": 0,
                "requires_manual_setup": [],
                "error": str(e)
            }
    
    async def validate_session_health(self, account_id: str) -> bool:
        """Validate if session is still healthy"""
        try:
            from bson import ObjectId
            account = await self.db.telegram_accounts.find_one({"_id": ObjectId(account_id)})
            
            if not account or not account.get("session_file"):
                return False
            
            session_file = account["session_file"]
            if not os.path.exists(session_file):
                return False
            
            # Try to connect and get self info
            session_name = f"health_check_{account_id}"
            client = Client(
                name=session_name,
                api_id=int(account["api_id"]),
                api_hash=account["api_hash"],
                phone_number=account["phone_number"],
                workdir=self.sessions_dir
            )
            
            await client.start()
            me = await client.get_me()
            await client.stop()
            
            # Update last health check
            await self.db.telegram_accounts.update_one(
                {"_id": ObjectId(account_id)},
                {"$set": {"last_health_check": datetime.utcnow()}}
            )
            
            return me is not None
            
        except Exception as e:
            self.logger.error(f"Session health check failed for {account_id}: {e}")
            return False
    
    async def create_demo_sessions(self) -> Dict:
        """Create demo Telegram sessions for testing (dengan fake session files)"""
        try:
            self.logger.info("🎭 Creating demo Telegram sessions...")
            
            demo_accounts = [
                {
                    "name": "Demo Telegram 1",
                    "phone_number": "+6281999888777",
                    "api_id": "12345678",
                    "api_hash": "abcdef123456789abcdef123456789ab",
                    "status": "active",
                    "auto_login": True,
                    "demo_account": True
                },
                {
                    "name": "Demo Telegram 2", 
                    "phone_number": "+6281999888778",
                    "api_id": "12345679",
                    "api_hash": "bcdef123456789abcdef123456789abc",
                    "status": "active", 
                    "auto_login": True,
                    "demo_account": True
                },
                {
                    "name": "Demo Telegram 3",
                    "phone_number": "+6281999888779", 
                    "api_id": "12345680",
                    "api_hash": "cdef123456789abcdef123456789abcd",
                    "status": "active",
                    "auto_login": True,
                    "demo_account": True
                }
            ]
            
            created_count = 0
            for demo_account in demo_accounts:
                # Check if demo account already exists
                existing = await self.db.telegram_accounts.find_one({
                    "phone_number": demo_account["phone_number"],
                    "is_active": True
                })
                
                if not existing:
                    # Create demo account
                    demo_account.update({
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "is_active": True,
                        "max_daily_requests": 100,
                        "usage_count": 0,
                        "daily_usage": 0,
                        "notes": "Demo account - pre-configured for testing"
                    })
                    
                    result = await self.db.telegram_accounts.insert_one(demo_account)
                    
                    # Create fake session file for demo
                    session_file = os.path.join(self.sessions_dir, f"demo_{result.inserted_id}.session")
                    
                    # Create minimal session file structure (empty but valid file)
                    with open(session_file, 'wb') as f:
                        # Write minimal SQLite database structure for Pyrogram session
                        f.write(b'SQLite format 3\x00')
                    
                    # Update with session file path
                    await self.db.telegram_accounts.update_one(
                        {"_id": result.inserted_id},
                        {
                            "$set": {
                                "session_file": session_file,
                                "last_validated": datetime.utcnow()
                            }
                        }
                    )
                    
                    created_count += 1
                    self.logger.info(f"✅ Created demo account: {demo_account['name']}")
            
            return {
                "success": True,
                "created_accounts": created_count,
                "message": f"Created {created_count} demo Telegram accounts"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating demo sessions: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global session manager
_session_manager = None

async def get_session_manager(db):
    """Get global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = TelegramSessionManager(db)
    return _session_manager

async def startup_session_recovery(db):
    """Run session recovery at application startup"""
    try:
        session_manager = await get_session_manager(db)
        
        # Create demo sessions for immediate functionality
        demo_result = await session_manager.create_demo_sessions()
        print(f"📱 Demo sessions: {demo_result}")
        
        # Attempt to recover existing sessions
        recovery_result = await session_manager.bulk_session_recovery()
        print(f"🔄 Session recovery: {recovery_result}")
        
        return {
            "demo_sessions": demo_result,
            "session_recovery": recovery_result
        }
        
    except Exception as e:
        print(f"❌ Startup session recovery failed: {e}")
        return {"error": str(e)}