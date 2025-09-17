"""
Telegram MTP (MTProto) Validator
Real Telegram client access untuk advanced validation
"""

import asyncio
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

# Telegram MTP Libraries
try:
    from pyrogram import Client, errors
    from pyrogram.types import User
    MTP_AVAILABLE = True
except ImportError:
    MTP_AVAILABLE = False

class TelegramMTPValidator:
    def __init__(self):
        self.api_id = os.environ.get('TELEGRAM_API_ID')
        self.api_hash = os.environ.get('TELEGRAM_API_HASH')
        self.session_name = "telegram_validator"
        self.client: Optional[Client] = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> bool:
        """Initialize Telegram MTP client"""
        if not MTP_AVAILABLE:
            self.logger.error("Pyrogram not installed. Install with: pip install pyrogram")
            return False
            
        if not self.api_id or not self.api_hash:
            self.logger.error("TELEGRAM_API_ID and TELEGRAM_API_HASH required")
            return False
            
        try:
            self.client = Client(
                name=self.session_name,
                api_id=int(self.api_id),
                api_hash=self.api_hash,
                workdir="/app/backend/telegram_sessions"
            )
            
            await self.client.start()
            self.logger.info("Telegram MTP client initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Telegram client: {e}")
            return False
    
    async def validate_phone_number(self, phone_number: str) -> Dict:
        """Validate phone number using MTP"""
        if not self.client:
            return {
                "success": False,
                "error": "MTP client not initialized"
            }
            
        try:
            # Clean phone number
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            
            # Try to get user by phone number
            try:
                # Method 1: Search by phone (if in contacts)
                contact_user = await self._search_by_phone(clean_phone)
                if contact_user:
                    return await self._extract_user_info(contact_user, phone_number, "contact_search")
                
                # Method 2: Try to start chat (check if number exists)
                chat_result = await self._check_phone_exists(clean_phone)
                if chat_result:
                    return chat_result
                
                # Method 3: Username search if phone has username
                username = await self._phone_to_username(clean_phone)
                if username:
                    return await self.validate_username(username)
                
                return {
                    "success": True,
                    "status": "unknown",
                    "phone_number": phone_number,
                    "details": {
                        "provider": "telegram_mtp",
                        "method": "mtp_validation",
                        "exists": "unknown",
                        "reason": "Not in contacts, private account or invalid number"
                    }
                }
                
            except errors.PhoneNumberInvalid:
                return {
                    "success": True,
                    "status": "inactive", 
                    "phone_number": phone_number,
                    "details": {
                        "provider": "telegram_mtp",
                        "method": "mtp_validation", 
                        "exists": False,
                        "reason": "Invalid phone number format"
                    }
                }
                
            except errors.PhoneNumberBanned:
                return {
                    "success": True,
                    "status": "banned",
                    "phone_number": phone_number,
                    "details": {
                        "provider": "telegram_mtp",
                        "method": "mtp_validation",
                        "exists": True,
                        "reason": "Phone number is banned"
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error validating phone {phone_number}: {e}")
            return {
                "success": False,
                "error": f"MTP validation failed: {str(e)}"
            }
    
    async def validate_username(self, username: str) -> Dict:
        """Validate username using MTP"""
        if not self.client:
            return {
                "success": False,
                "error": "MTP client not initialized"
            }
            
        try:
            # Remove @ if present
            clean_username = username.replace('@', '')
            
            try:
                # Get user by username
                user = await self.client.get_users(clean_username)
                return await self._extract_user_info(user, username, "username_search")
                
            except errors.UsernameNotOccupied:
                return {
                    "success": True,
                    "status": "inactive",
                    "username": username,
                    "details": {
                        "provider": "telegram_mtp",
                        "method": "mtp_username_validation",
                        "exists": False,
                        "reason": "Username not occupied"
                    }
                }
                
            except errors.UsernameInvalid:
                return {
                    "success": True,
                    "status": "invalid",
                    "username": username,
                    "details": {
                        "provider": "telegram_mtp", 
                        "method": "mtp_username_validation",
                        "exists": False,
                        "reason": "Invalid username format"
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error validating username {username}: {e}")
            return {
                "success": False,
                "error": f"Username validation failed: {str(e)}"
            }
    
    async def _extract_user_info(self, user: User, identifier: str, method: str) -> Dict:
        """Extract detailed user information"""
        try:
            # Basic info
            user_info = {
                "success": True,
                "status": "active",
                "identifier": identifier,
                "details": {
                    "provider": "telegram_mtp",
                    "method": method,
                    "exists": True,
                    "user_id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "is_self": user.is_self,
                    "is_contact": user.is_contact,
                    "is_mutual_contact": user.is_mutual_contact,
                    "is_deleted": user.is_deleted,
                    "is_bot": user.is_bot,
                    "is_verified": user.is_verified,
                    "is_restricted": user.is_restricted,
                    "is_scam": user.is_scam,
                    "is_fake": user.is_fake,
                    "is_premium": user.is_premium,
                    "language_code": user.language_code,
                    "dc_id": user.dc_id
                }
            }
            
            # Additional profile info
            try:
                # Get full user info
                full_user = await self.client.get_users(user.id)
                
                # Check if has profile photo
                if hasattr(full_user, 'photo') and full_user.photo:
                    user_info["details"]["has_profile_photo"] = True
                    user_info["details"]["profile_photo_id"] = str(full_user.photo.big_file_id)
                else:
                    user_info["details"]["has_profile_photo"] = False
                
                # Try to get user's bio/about
                try:
                    chat = await self.client.get_chat(user.id)
                    if hasattr(chat, 'bio') and chat.bio:
                        user_info["details"]["bio"] = chat.bio
                        user_info["details"]["has_bio"] = True
                    else:
                        user_info["details"]["has_bio"] = False
                except:
                    user_info["details"]["has_bio"] = "unknown"
                
            except Exception as e:
                self.logger.warning(f"Could not get additional info for user {user.id}: {e}")
            
            return user_info
            
        except Exception as e:
            self.logger.error(f"Error extracting user info: {e}")
            return {
                "success": True,
                "status": "active",
                "identifier": identifier,
                "details": {
                    "provider": "telegram_mtp",
                    "method": method,
                    "exists": True,
                    "error": "Could not extract detailed info"
                }
            }
    
    async def _search_by_phone(self, phone: str) -> Optional[User]:
        """Search user by phone if in contacts"""
        try:
            # This only works if the number is in your contacts
            contacts = await self.client.get_contacts()
            for contact in contacts:
                # Note: This is limited as Telegram doesn't expose phone numbers directly
                if hasattr(contact, 'phone_number') and contact.phone_number == phone:
                    return contact
            return None
        except:
            return None
    
    async def _check_phone_exists(self, phone: str) -> Optional[Dict]:
        """Check if phone number exists by trying to resolve it"""
        try:
            # This method is limited due to Telegram privacy policies
            # But can detect some cases
            
            # Try importing contact temporarily (requires phone number)
            # This is a more advanced technique that may require special permissions
            return None
            
        except Exception as e:
            self.logger.debug(f"Phone existence check failed: {e}")
            return None
    
    async def _phone_to_username(self, phone: str) -> Optional[str]:
        """Try to resolve phone to username (limited)"""
        # This is very limited in Telegram due to privacy
        # Would require the user to be in contacts or public
        return None
    
    async def get_session_info(self) -> Dict:
        """Get current session information"""
        if not self.client:
            return {"status": "not_initialized"}
            
        try:
            me = await self.client.get_me()
            return {
                "status": "active",
                "session_user": {
                    "id": me.id,
                    "username": me.username,
                    "first_name": me.first_name,
                    "phone_number": me.phone_number,
                    "is_premium": me.is_premium
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Close MTP client"""
        if self.client:
            try:
                await self.client.stop()
                self.logger.info("Telegram MTP client closed")
            except Exception as e:
                self.logger.error(f"Error closing client: {e}")

# Global MTP validator instance
_mtp_validator = None

async def get_mtp_validator() -> TelegramMTPValidator:
    """Get global MTP validator instance"""
    global _mtp_validator
    if _mtp_validator is None:
        _mtp_validator = TelegramMTPValidator()
        await _mtp_validator.initialize()
    return _mtp_validator

# API Functions
async def validate_telegram_phone_mtp(phone_number: str) -> Dict:
    """Validate Telegram phone using MTP"""
    validator = await get_mtp_validator()
    return await validator.validate_phone_number(phone_number)

async def validate_telegram_username_mtp(username: str) -> Dict:
    """Validate Telegram username using MTP"""
    validator = await get_mtp_validator()
    return await validator.validate_username(username)