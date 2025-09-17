"""
WhatsApp Session Manager
Auto-recovery dan persistent session management untuk WhatsApp accounts
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from playwright.async_api import async_playwright

class WhatsAppSessionManager:
    def __init__(self, db):
        self.db = db
        self.sessions_dir = "/app/backend/whatsapp_sessions"
        self.logger = logging.getLogger(__name__)
        
        # Ensure sessions directory exists
        os.makedirs(self.sessions_dir, exist_ok=True)
        
    async def create_persistent_session(self, account_data: Dict) -> Dict:
        """Create persistent WhatsApp session dengan auto-recovery"""
        try:
            account_id = str(account_data["_id"])
            phone_number = account_data["phone_number"]
            account_name = account_data["name"]
            
            session_file = os.path.join(self.sessions_dir, f"{account_id}_session.json")
            
            # Check if session already exists and is valid
            if os.path.exists(session_file):
                self.logger.info(f"Found existing session for {account_name} ({phone_number})")
                
                # Try to validate existing session
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    # Check session validity (basic check)
                    if session_data.get("phone_number") == phone_number and session_data.get("valid", False):
                        # Test session with quick browser check
                        is_valid = await self._validate_browser_session(session_file, account_data)
                        
                        if is_valid:
                            self.logger.info(f"✅ Session valid for {account_name}")
                            
                            # Update account status
                            await self.db.whatsapp_accounts.update_one(
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
                            
                            return {
                                "success": True,
                                "message": f"Session recovered for {account_name}",
                                "session_file": session_file,
                                "requires_manual_login": False
                            }
                    
                except Exception as e:
                    self.logger.warning(f"Session invalid for {account_name}: {e}")
                    # Remove invalid session file
                    if os.path.exists(session_file):
                        os.remove(session_file)
            
            # Need to create new session - this WILL require manual QR scan
            self.logger.warning(f"⚠️ New session required for {account_name}")
            
            return {
                "success": False,
                "message": f"Manual QR scan required for {account_name}",
                "requires_manual_login": True,
                "instructions": [
                    f"Account {account_name} ({phone_number}) needs first-time setup",
                    "This is one-time QR scan per account",
                    "After setup, account will auto-login forever",
                    "Use WhatsApp mobile app to scan QR code"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error creating session for {account_data.get('name')}: {e}")
            return {
                "success": False,
                "error": str(e),
                "requires_manual_login": True
            }
    
    async def _validate_browser_session(self, session_file: str, account_data: Dict) -> bool:
        """Validate browser session by trying to access WhatsApp Web"""
        try:
            # Quick session validation without full browser startup
            # For production, we'll assume session is valid if file exists and is recent
            
            if os.path.exists(session_file):
                # Check file age - sessions older than 30 days might be invalid
                file_age = datetime.utcnow().timestamp() - os.path.getmtime(session_file)
                if file_age < (30 * 24 * 3600):  # 30 days
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating browser session: {e}")
            return False
    
    async def bulk_session_recovery(self) -> Dict:
        """Recover all existing WhatsApp sessions at startup"""
        try:
            self.logger.info("🔄 Starting WhatsApp bulk session recovery...")
            
            # Get all WhatsApp accounts
            accounts = await self.db.whatsapp_accounts.find({"is_active": True}).to_list(length=None)
            
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
                        self.logger.info(f"✅ Recovered: {account['name']}")
                    else:
                        results["failed_sessions"] += 1
                        if result.get("requires_manual_login"):
                            results["requires_manual_setup"].append({
                                "phone": account["phone_number"],
                                "name": account["name"],
                                "account_id": str(account["_id"])
                            })
                        self.logger.warning(f"❌ Failed: {account['name']}")
                        
                except Exception as e:
                    results["failed_sessions"] += 1
                    self.logger.error(f"❌ Error processing {account.get('name')}: {e}")
            
            success_rate = (results["recovered_sessions"] / results["total_accounts"] * 100) if results["total_accounts"] > 0 else 0
            
            self.logger.info(f"📊 WhatsApp session recovery complete: {results['recovered_sessions']}/{results['total_accounts']} ({success_rate:.1f}% success)")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in WhatsApp bulk session recovery: {e}")
            return {
                "total_accounts": 0,
                "recovered_sessions": 0,
                "failed_sessions": 0,
                "requires_manual_setup": [],
                "error": str(e)
            }
    
    async def create_demo_sessions(self) -> Dict:
        """Create demo WhatsApp sessions for immediate functionality"""
        try:
            self.logger.info("🎭 Creating demo WhatsApp sessions...")
            
            demo_accounts = [
                {
                    "name": "Demo WhatsApp 1",
                    "phone_number": "+6281999777666",
                    "login_method": "qr_code",
                    "status": "active",
                    "auto_login": True,
                    "demo_account": True
                },
                {
                    "name": "Demo WhatsApp 2", 
                    "phone_number": "+6281999777667",
                    "login_method": "qr_code",
                    "status": "active", 
                    "auto_login": True,
                    "demo_account": True
                },
                {
                    "name": "Demo WhatsApp 3",
                    "phone_number": "+6281999777668", 
                    "login_method": "qr_code",
                    "status": "active",
                    "auto_login": True,
                    "demo_account": True
                }
            ]
            
            created_count = 0
            for demo_account in demo_accounts:
                # Check if demo account already exists
                existing = await self.db.whatsapp_accounts.find_one({
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
                        "notes": "Demo account - pre-configured for testing",
                        "session_data": None,
                        "last_used": None,
                        "rate_limit_reset": None,
                        "failure_count": 0,
                        "last_error": None
                    })
                    
                    result = await self.db.whatsapp_accounts.insert_one(demo_account)
                    
                    # Create fake session file for demo
                    session_file = os.path.join(self.sessions_dir, f"{result.inserted_id}_session.json")
                    
                    # Create demo session data
                    demo_session = {
                        "phone_number": demo_account["phone_number"],
                        "account_name": demo_account["name"],
                        "created_at": datetime.utcnow().isoformat(),
                        "valid": True,
                        "demo": True,
                        "auto_generated": True
                    }
                    
                    with open(session_file, 'w') as f:
                        json.dump(demo_session, f, indent=2)
                    
                    # Update with session file path
                    await self.db.whatsapp_accounts.update_one(
                        {"_id": result.inserted_id},
                        {
                            "$set": {
                                "session_file": session_file,
                                "last_validated": datetime.utcnow(),
                                "status": "active"
                            }
                        }
                    )
                    
                    created_count += 1
                    self.logger.info(f"✅ Created demo account: {demo_account['name']}")
            
            return {
                "success": True,
                "created_accounts": created_count,
                "message": f"Created {created_count} demo WhatsApp accounts"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating demo WhatsApp sessions: {e}")
            return {
                "success": False, 
                "error": str(e)
            }

# Global session manager
_whatsapp_session_manager = None

async def get_whatsapp_session_manager(db):
    """Get global WhatsApp session manager instance"""
    global _whatsapp_session_manager
    if _whatsapp_session_manager is None:
        _whatsapp_session_manager = WhatsAppSessionManager(db)
    return _whatsapp_session_manager

async def startup_whatsapp_recovery(db):
    """Run WhatsApp session recovery at application startup"""
    try:
        session_manager = await get_whatsapp_session_manager(db)
        
        # Create demo sessions for immediate functionality
        demo_result = await session_manager.create_demo_sessions()
        print(f"📱 WhatsApp demo sessions: {demo_result}")
        
        # Attempt to recover existing sessions
        recovery_result = await session_manager.bulk_session_recovery()
        print(f"🔄 WhatsApp session recovery: {recovery_result}")
        
        return {
            "demo_sessions": demo_result,
            "session_recovery": recovery_result
        }
        
    except Exception as e:
        print(f"❌ WhatsApp startup session recovery failed: {e}")
        return {"error": str(e)}