from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
import secrets
import hashlib
import uuid
import pandas as pd
import io
import json
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
import asyncio
from enum import Enum
import requests
import aiohttp
import logging
from email_service import email_service
import socketio
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutStatusResponse, CheckoutSessionRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"wt_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

async def verify_api_key(api_key: str) -> dict:
    """Verify API key and return user info"""
    hashed_key = hash_api_key(api_key)
    
    api_key_doc = await db.api_keys.find_one({
        "key_hash": hashed_key,
        "is_active": True
    })
    
    if not api_key_doc:
        return None
    
    # Update last used timestamp
    await db.api_keys.update_one(
        {"_id": api_key_doc["_id"]},
        {"$set": {"last_used": datetime.utcnow()}}
    )
    
    # Get user info
    user = await db.users.find_one({"_id": api_key_doc["user_id"]})
    if user:
        user["api_key_permissions"] = api_key_doc.get("permissions", [])
    
    return user

# Helper function to generate unique IDs using secrets
def generate_id():
    return str(uuid.uuid4())

def parse_phone_input(input_text: str) -> dict:
    """Parse input: 'nama 08123456789' or '08123456789'"""
    if not input_text or not input_text.strip():
        return {"identifier": None, "phone_number": ""}
    
    parts = input_text.strip().split()
    
    if len(parts) == 1:
        # Only phone number
        return {
            "identifier": None,
            "phone_number": parts[0]
        }
    else:
        # Last part is phone, rest is name (max 12 chars)
        phone = parts[-1]
        name = " ".join(parts[:-1])
        # Truncate name to 12 characters
        name = name[:12] if len(name) > 12 else name
        return {
            "identifier": name,
            "phone_number": phone
        }

async def validate_whatsapp_web_api(phone: str, identifier: str = None) -> Dict[str, Any]:
    """FREE WhatsApp validation using WhatsApp Web API"""
    try:
        # WhatsApp Web API URL
        url = f"https://api.whatsapp.com/send/?phone={phone}&text&type=phone_number&app_absent=0"
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return {
                        'identifier': identifier,
                        'phone_number': phone,
                        'platform': 'whatsapp',
                        'status': ValidationStatus.ERROR,
                        'validated_at': datetime.utcnow(),
                        'error': f'HTTP {response.status}',
                        'details': {}
                    }
                
                html_content = await response.text()
                
                # Pattern detection based on our analysis
                indicators = {
                    'has_send_link': 'web.whatsapp.com/send/' in html_content,
                    'main_block_visible': 'main_block' in html_content and 'style="display: none"' not in html_content,
                    'app_absent_0': 'app_absent=0' in html_content,
                    'no_error_message': 'error' not in html_content.lower() and 'invalid' not in html_content.lower(),
                    'fallback_hidden': 'fallback_block' in html_content and 'style="display: none"' in html_content
                }
                
                # Scoring system
                score = sum(indicators.values())
                
                # Determine status and type
                if score >= 4:
                    # Check for business indicators
                    is_business = any([
                        'business' in html_content.lower(),
                        'verified' in html_content.lower(),
                        'official' in html_content.lower()
                    ])
                    
                    wa_type = 'business' if is_business else 'personal'
                    status = ValidationStatus.ACTIVE
                    
                elif score >= 2:
                    wa_type = 'unknown'
                    status = ValidationStatus.ACTIVE
                else:
                    wa_type = None
                    status = ValidationStatus.INACTIVE
                
                return {
                    'identifier': identifier,
                    'phone_number': phone,
                    'platform': 'whatsapp',
                    'status': status,
                    'validated_at': datetime.utcnow(),
                    'details': {
                        'type': wa_type,
                        'confidence_score': score,
                        'indicators': indicators
                    }
                }
                
    except asyncio.TimeoutError:
        return {
            'identifier': identifier,
            'phone_number': phone,
            'platform': 'whatsapp',
            'status': ValidationStatus.ERROR,
            'validated_at': datetime.utcnow(),
            'error': 'Timeout',
            'details': {}
        }
    except Exception as e:
        return {
            'identifier': identifier,
            'phone_number': phone,
            'platform': 'whatsapp',
            'status': ValidationStatus.ERROR,
            'validated_at': datetime.utcnow(),
            'error': str(e),
            'details': {}
        }

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.webtools_validation

# Socket.IO setup
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode='asgi')
socket_app = socketio.ASGIApp(sio)

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Stripe Configuration
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')

# Credit Packages Configuration (fixed server-side pricing)
CREDIT_PACKAGES = {
    "starter": {"credits": 1000, "price": 10.0, "name": "Starter Package"},
    "professional": {"credits": 5000, "price": 40.0, "name": "Professional Package"},
    "enterprise": {"credits": 25000, "price": 150.0, "name": "Enterprise Package"}
}

app = FastAPI(title="Webtools Validasi Nomor Telepon", version="1.0.0")

# Mount Socket.IO
app.mount("/socket.io", socket_app)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ValidationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    INVALID = "invalid"
    ERROR = "error"

# Models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    company_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class QuickCheckRequest(BaseModel):
    phone_input: str  # Changed from phone_number to support "nama 08123456789" format

class TelegramAccount(BaseModel):
    name: str
    phone_number: str
    api_id: str
    api_hash: str
    bot_token: Optional[str] = None
    is_active: bool = True

class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = ["validation"]  # permissions like "validation", "admin", etc.

class APIKeyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    permissions: List[str]
    key_preview: str  # Only show first 8 characters
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool

class WhatsAppProvider(BaseModel):
    name: str
    api_endpoint: str
    api_key: str
    provider_type: str  # twilio, vonage, etc
    is_active: bool = True

class CreditTopupRequest(BaseModel):
    package_id: str  # starter, professional, enterprise
    origin_url: str  # Frontend origin URL for redirect URLs

class PaymentTransactionCreate(BaseModel):
    user_id: str
    package_id: str
    amount: float
    currency: str = "usd" 
    session_id: str
    payment_status: str = "pending"
    credits_amount: int
    metadata: Optional[Dict[str, Any]] = None

class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None

class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    credits: Optional[int] = None
    role: Optional[UserRole] = None

# Socket.IO Events
@sio.event
async def connect(sid, environ):
    logger.info(f"Client {sid} connected")
    await sio.emit('connected', {'data': 'Connected to Webtools server'}, room=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Client {sid} disconnected")

@sio.event
async def join_job_room(sid, data):
    """Join room for specific job to receive updates"""
    job_id = data.get('job_id')
    if job_id:
        await sio.enter_room(sid, f"job_{job_id}")
        await sio.emit('joined_job_room', {'job_id': job_id}, room=sid)
        logger.info(f"Client {sid} joined room for job {job_id}")

@sio.event
async def leave_job_room(sid, data):
    """Leave job room"""
    job_id = data.get('job_id')
    if job_id:
        await sio.leave_room(sid, f"job_{job_id}")
        await sio.emit('left_job_room', {'job_id': job_id}, room=sid)
        logger.info(f"Client {sid} left room for job {job_id}")

# Helper function to emit job progress
async def emit_job_progress(job_id: str, progress_data: dict):
    """Emit real-time job progress to connected clients"""
    try:
        await sio.emit('job_progress', progress_data, room=f"job_{job_id}")
    except Exception as e:
        logger.error(f"Failed to emit job progress: {e}")

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_data: dict) -> str:
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        'user_id': user_data['_id'],
        'username': user_data['username'],
        'role': user_data['role'],
        'tenant_id': user_data['tenant_id'],
        'exp': expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user_or_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token or API key"""
    token = credentials.credentials
    
    # Try JWT first
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        if user_id:
            user = await db.users.find_one({"_id": user_id})
            if user:
                user["auth_method"] = "jwt"
                return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        pass
    
    # Try API key
    if token.startswith('wt_'):
        user = await verify_api_key(token)
        if user:
            user["auth_method"] = "api_key"
            return user
    
    raise HTTPException(status_code=401, detail="Invalid authentication")

# Keep the original function for backward compatibility
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Legacy function - redirects to new implementation"""
    return await get_current_user_or_api_key(credentials)

def normalize_phone_number(phone: str) -> str:
    """Normalize phone number format"""
    # Remove all non-digit characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # Handle Indonesian numbers
    if phone.startswith('62'):
        return '+' + phone
    elif phone.startswith('0'):
        return '+62' + phone[1:]
    elif len(phone) >= 9 and not phone.startswith('+'):
        return '+62' + phone
    
    return '+' + phone if not phone.startswith('+') else phone

async def validate_whatsapp_number(phone: str) -> Dict[str, Any]:
    """Mock WhatsApp validation - replace with actual API calls"""
    await asyncio.sleep(0.5)  # Simulate API delay
    
    # Simple mock logic
    import random
    is_active = random.choice([True, False])
    
    return {
        'phone_number': phone,
        'platform': 'whatsapp',
        'status': ValidationStatus.ACTIVE if is_active else ValidationStatus.INACTIVE,
        'validated_at': datetime.utcnow(),
        'details': {
            'profile_picture': is_active,
            'last_seen': 'recently' if is_active else 'unknown'
        }
    }

async def validate_telegram_number(phone: str) -> Dict[str, Any]:
    """Mock Telegram validation - replace with actual API calls"""
    await asyncio.sleep(0.3)  # Simulate API delay
    
    # Simple mock logic
    import random
    is_active = random.choice([True, False])
    
    return {
        'phone_number': phone,
        'platform': 'telegram',
        'status': ValidationStatus.ACTIVE if is_active else ValidationStatus.INACTIVE,
        'validated_at': datetime.utcnow(),
        'details': {
            'username': f'user_{random.randint(1000, 9999)}' if is_active else None,
            'is_premium': random.choice([True, False]) if is_active else False
        }
    }

async def validate_whatsapp_number_real(phone: str, provider_config: dict = None) -> Dict[str, Any]:
    """Real WhatsApp validation using actual API providers"""
    if not provider_config:
        # Fallback to mock if no provider configured
        return await validate_whatsapp_number(phone)
    
    try:
        provider_type = provider_config.get("provider_type", "").lower()
        
        if provider_type == "twilio":
            return await validate_whatsapp_twilio(phone, provider_config)
        elif provider_type == "vonage":
            return await validate_whatsapp_vonage(phone, provider_config)
        elif provider_type == "360dialog":
            return await validate_whatsapp_360dialog(phone, provider_config)
        else:
            # Fallback to mock
            return await validate_whatsapp_number(phone)
            
    except Exception as e:
        return {
            'phone_number': phone,
            'platform': 'whatsapp',
            'status': ValidationStatus.ERROR,
            'validated_at': datetime.utcnow(),
            'error': str(e),
            'details': {}
        }

async def validate_whatsapp_twilio(phone: str, config: dict) -> Dict[str, Any]:
    """Validate WhatsApp number using Twilio API"""
    try:
        async with aiohttp.ClientSession() as session:
            # Twilio WhatsApp validation endpoint
            url = f"https://lookups.twilio.com/v1/PhoneNumbers/{phone}"
            auth = aiohttp.BasicAuth(config.get("account_sid", ""), config.get("api_key", ""))
            
            params = {
                "Type": "carrier"
            }
            
            async with session.get(url, auth=auth, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if number is capable of WhatsApp
                    carrier = data.get("carrier", {})
                    is_mobile = carrier.get("type") == "mobile"
                    
                    return {
                        'phone_number': phone,
                        'platform': 'whatsapp',
                        'status': ValidationStatus.ACTIVE if is_mobile else ValidationStatus.INACTIVE,
                        'validated_at': datetime.utcnow(),
                        'details': {
                            'carrier': carrier.get("name", "Unknown"),
                            'country': data.get("country_code"),
                            'type': carrier.get("type"),
                            'provider': 'twilio'
                        }
                    }
                else:
                    return {
                        'phone_number': phone,
                        'platform': 'whatsapp',
                        'status': ValidationStatus.INVALID,
                        'validated_at': datetime.utcnow(),
                        'details': {'provider': 'twilio', 'error': f'HTTP {response.status}'}
                    }
                    
    except Exception as e:
        return {
            'phone_number': phone,
            'platform': 'whatsapp',  
            'status': ValidationStatus.ERROR,
            'validated_at': datetime.utcnow(),
            'error': str(e),
            'details': {'provider': 'twilio'}
        }

async def validate_whatsapp_vonage(phone: str, config: dict) -> Dict[str, Any]:
    """Validate WhatsApp number using Vonage API"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.nexmo.com/ni/basic/json"
            
            params = {
                "api_key": config.get("api_key", ""),
                "api_secret": config.get("api_secret", ""),
                "number": phone
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    is_valid = data.get("status") == 0
                    is_mobile = data.get("current_carrier", {}).get("network_type") == "mobile"
                    
                    return {
                        'phone_number': phone,
                        'platform': 'whatsapp',
                        'status': ValidationStatus.ACTIVE if (is_valid and is_mobile) else ValidationStatus.INACTIVE,
                        'validated_at': datetime.utcnow(),
                        'details': {
                            'carrier': data.get("current_carrier", {}).get("name", "Unknown"),
                            'country': data.get("country_name"),
                            'network_type': data.get("current_carrier", {}).get("network_type"),
                            'provider': 'vonage'
                        }
                    }
                else:
                    return {
                        'phone_number': phone,
                        'platform': 'whatsapp',
                        'status': ValidationStatus.INVALID,
                        'validated_at': datetime.utcnow(),
                        'details': {'provider': 'vonage', 'error': f'HTTP {response.status}'}
                    }
                    
    except Exception as e:
        return {
            'phone_number': phone,
            'platform': 'whatsapp',
            'status': ValidationStatus.ERROR,
            'validated_at': datetime.utcnow(),
            'error': str(e),
            'details': {'provider': 'vonage'}
        }

async def validate_whatsapp_360dialog(phone: str, config: dict) -> Dict[str, Any]:
    """Validate WhatsApp number using 360Dialog API"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://waba.360dialog.io/v1/contacts"
            
            headers = {
                "D360-API-KEY": config.get("api_key", ""),
                "Content-Type": "application/json"
            }
            
            data = {
                "blocking": "wait",
                "contacts": [phone],
                "force_check": True
            }
            
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    contacts = result.get("contacts", [])
                    
                    if contacts:
                        contact = contacts[0]
                        wa_id = contact.get("wa_id")
                        status = contact.get("status", "invalid")
                        
                        return {
                            'phone_number': phone,
                            'platform': 'whatsapp',
                            'status': ValidationStatus.ACTIVE if wa_id else ValidationStatus.INACTIVE,
                            'validated_at': datetime.utcnow(),
                            'details': {
                                'wa_id': wa_id,
                                'status': status,
                                'provider': '360dialog'
                            }
                        }
                else:
                    return {
                        'phone_number': phone,
                        'platform': 'whatsapp',
                        'status': ValidationStatus.INVALID,
                        'validated_at': datetime.utcnow(),
                        'details': {'provider': '360dialog', 'error': f'HTTP {response.status}'}
                    }
                    
    except Exception as e:
        return {
            'phone_number': phone,
            'platform': 'whatsapp',
            'status': ValidationStatus.ERROR,
            'validated_at': datetime.utcnow(),
            'error': str(e),
            'details': {'provider': '360dialog'}
        }

async def validate_telegram_number_real(phone: str, bot_config: dict = None) -> Dict[str, Any]:
    """Real Telegram validation using Bot API"""
    if not bot_config or not bot_config.get("bot_token"):
        # Fallback to mock if no bot configured
        return await validate_telegram_number(phone)
        
    try:
        # Note: Telegram Bot API doesn't directly support phone number validation
        # This is a conceptual implementation - real implementation would need different approach
        bot_token = bot_config.get("bot_token")
        
        # For demo purposes, we'll use a heuristic approach
        # In production, you might use Telegram's contact validation or user search
        
        async with aiohttp.ClientSession() as session:
            # This is a placeholder - actual Telegram validation would be more complex
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            
            async with session.get(url) as response:
                if response.status == 200:
                    # Bot is valid, use heuristic for phone validation
                    import random
                    is_active = random.choice([True, False])  # Placeholder logic
                    
                    return {
                        'phone_number': phone,
                        'platform': 'telegram',
                        'status': ValidationStatus.ACTIVE if is_active else ValidationStatus.INACTIVE,
                        'validated_at': datetime.utcnow(),
                        'details': {
                            'method': 'bot_api_heuristic',
                            'provider': 'telegram_bot',
                            'note': 'Real Telegram validation requires different approach'
                        }
                    }
                else:
                    return {
                        'phone_number': phone,
                        'platform': 'telegram',
                        'status': ValidationStatus.ERROR,
                        'validated_at': datetime.utcnow(),
                        'details': {'provider': 'telegram_bot', 'error': 'Bot token invalid'}
                    }
                    
    except Exception as e:
        return {
            'phone_number': phone,
            'platform': 'telegram',
            'status': ValidationStatus.ERROR,
            'validated_at': datetime.utcnow(),
            'error': str(e),
            'details': {'provider': 'telegram_bot'}
        }

# Background task for bulk validation
async def process_bulk_validation(job_id: str):
    """Process bulk validation in background"""
    try:
        # Update job status to processing
        await db.jobs.update_one(
            {"_id": job_id},
            {"$set": {"status": JobStatus.PROCESSING, "updated_at": datetime.utcnow()}}
        )
        
        # Get job details
        job = await db.jobs.find_one({"_id": job_id})
        if not job:
            return
            
        # Handle both old and new data structures for backward compatibility
        if "phone_data" in job:
            phone_data_list = job["phone_data"]
        else:
            # Backward compatibility: convert old phone_numbers to new format
            phone_numbers = job.get("phone_numbers", [])
            phone_data_list = [{"identifier": None, "phone_number": phone, "original_phone": phone} for phone in phone_numbers]
        
        results = {
            "whatsapp_active": 0,
            "telegram_active": 0,
            "inactive": 0,
            "errors": 0,
            "details": []
        }
        
        # Process each phone data entry
        for i, phone_data in enumerate(phone_data_list):
            try:
                phone = phone_data["phone_number"]
                identifier = phone_data.get("identifier")
                
                # Check cache first
                cached_result = await db.validation_cache.find_one({"phone_number": phone})
                if cached_result and (datetime.utcnow() - cached_result["cached_at"]).days < 7:
                    whatsapp_result = cached_result["whatsapp"]
                    telegram_result = cached_result["telegram"]
                    # Add identifier to cached results
                    whatsapp_result["identifier"] = identifier
                    telegram_result["identifier"] = identifier
                else:
                    # Perform validation with identifier support
                    whatsapp_result = await validate_whatsapp_web_api(phone, identifier)
                    telegram_result = await validate_telegram_number(phone)
                    telegram_result["identifier"] = identifier
                    
                    # Cache results
                    cache_doc = {
                        "phone_number": phone,
                        "whatsapp": whatsapp_result,
                        "telegram": telegram_result,
                        "cached_at": datetime.utcnow()
                    }
                    
                    await db.validation_cache.update_one(
                        {"phone_number": phone},
                        {"$set": cache_doc},
                        upsert=True
                    )
                
                # Count results
                if whatsapp_result["status"] == ValidationStatus.ACTIVE:
                    results["whatsapp_active"] += 1
                if telegram_result["status"] == ValidationStatus.ACTIVE:
                    results["telegram_active"] += 1
                if (whatsapp_result["status"] == ValidationStatus.INACTIVE and 
                    telegram_result["status"] == ValidationStatus.INACTIVE):
                    results["inactive"] += 1
                
                # Store detailed result with identifier
                results["details"].append({
                    "identifier": identifier,
                    "phone_number": phone,
                    "original_phone": phone_data.get("original_phone", phone),
                    "whatsapp": whatsapp_result,
                    "telegram": telegram_result,
                    "processed_at": datetime.utcnow()
                })
                
                # Update progress
                processed_count = i + 1
                progress_percentage = round((processed_count / len(phone_data_list)) * 100, 2)
                
                await db.jobs.update_one(
                    {"_id": job_id},
                    {"$set": {
                        "processed_numbers": processed_count,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                # Emit real-time progress
                await emit_job_progress(job_id, {
                    "job_id": job_id,
                    "status": "processing",
                    "processed_numbers": processed_count,
                    "total_numbers": len(phone_data_list),
                    "progress_percentage": progress_percentage,
                    "current_phone": phone,
                    "current_identifier": identifier,
                    "last_result": {
                        "whatsapp": whatsapp_result["status"],
                        "telegram": telegram_result["status"]
                    }
                })
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results["errors"] += 1
                results["details"].append({
                    "identifier": phone_data.get("identifier"),
                    "phone_number": phone_data.get("phone_number", "unknown"),
                    "original_phone": phone_data.get("original_phone", "unknown"),
                    "error": str(e),
                    "processed_at": datetime.utcnow()
                })
        
        # Update job as completed
        await db.jobs.update_one(
            {"_id": job_id},
            {"$set": {
                "status": JobStatus.COMPLETED,
                "results": results,
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Emit final progress notification
        await emit_job_progress(job_id, {
            "job_id": job_id,
            "status": "completed",
            "processed_numbers": len(phone_numbers),
            "total_numbers": len(phone_numbers),
            "progress_percentage": 100,
            "results": results,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        # Get user info for email notification
        user = await db.users.find_one({"_id": job["user_id"]})
        if user and user.get("email"):
            # Send job completion email
            try:
                await email_service.send_job_completion_email(
                    user["email"],
                    user["username"],
                    {**job, "results": results}
                )
            except Exception as e:
                logger.error(f"Failed to send job completion email: {e}")
        
        # Deduct credits from user
        await db.users.update_one(
            {"_id": job["user_id"]},
            {"$inc": {"credits": -job["credits_used"]}}
        )
        
        # Check if credits are low and send alert
        updated_user = await db.users.find_one({"_id": job["user_id"]})
        if updated_user and updated_user.get("credits", 0) <= 100 and updated_user.get("email"):
            try:
                await email_service.send_low_credit_alert(
                    updated_user["email"],
                    updated_user["username"],
                    updated_user["credits"]
                )
            except Exception as e:
                logger.error(f"Failed to send low credit alert: {e}")
        
        # Log usage
        usage_doc = {
            "_id": generate_id(),
            "user_id": job["user_id"],
            "tenant_id": job["tenant_id"],
            "type": "bulk_check",
            "job_id": job_id,
            "numbers_processed": len(phone_numbers),
            "credits_used": job["credits_used"],
            "timestamp": datetime.utcnow()
        }
        
        await db.usage_logs.insert_one(usage_doc)
        
    except Exception as e:
        # Mark job as failed
        await db.jobs.update_one(
            {"_id": job_id},
            {"$set": {
                "status": JobStatus.FAILED,
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }}
        )

# Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/auth/register")
async def register(user_data: UserCreate, background_tasks: BackgroundTasks):
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create tenant
    tenant_id = generate_id()
    
    # Create user
    user_doc = {
        "_id": generate_id(),
        "username": user_data.username,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "role": UserRole.USER,
        "tenant_id": tenant_id,
        "company_name": user_data.company_name,
        "credits": 1000,  # Starting credits
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    await db.users.insert_one(user_doc)
    
    # Create tenant document
    tenant_doc = {
        "_id": tenant_id,
        "name": user_data.company_name or user_data.username,
        "owner_id": user_doc["_id"],
        "created_at": datetime.utcnow(),
        "settings": {
            "rate_limit": 100,  # requests per hour
            "max_bulk_size": 1000
        }
    }
    
    await db.tenants.insert_one(tenant_doc)
    
    # Send welcome email (background task)
    background_tasks.add_task(
        email_service.send_welcome_email,
        user_data.email,
        user_data.username,
        user_doc["credits"]
    )
    
    # Generate token
    token = create_jwt_token(user_doc)
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": user_doc["_id"],
            "username": user_doc["username"],
            "email": user_doc["email"],
            "role": user_doc["role"],
            "credits": user_doc["credits"]
        },
        "token": token
    }

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"username": credentials.username})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    token = create_jwt_token(user)
    
    return {
        "message": "Login successful",
        "user": {
            "id": user["_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "credits": user.get("credits", 0)
        },
        "token": token
    }

@app.get("/api/user/profile")
async def get_profile(current_user = Depends(get_current_user)):
    return {
        "id": current_user["_id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user["role"],
        "credits": current_user.get("credits", 0),
        "company_name": current_user.get("company_name"),
        "created_at": current_user["created_at"],
        "is_active": current_user.get("is_active", True),
        "last_login": current_user.get("last_login"),
        "total_validations": 0  # Will be calculated
    }

@app.put("/api/user/profile")
async def update_profile(profile_data: UserProfileUpdate, current_user = Depends(get_current_user)):
    """Update user profile"""
    
    update_data = {}
    
    # Only update fields that are provided
    if profile_data.username is not None:
        # Check if username is already taken
        existing_user = await db.users.find_one({
            "username": profile_data.username,
            "_id": {"$ne": current_user["_id"]}
        })
        if existing_user:
            raise HTTPException(status_code=400, detail="Username is already taken")
        update_data["username"] = profile_data.username
    
    if profile_data.email is not None:
        # Check if email is already taken
        existing_user = await db.users.find_one({
            "email": profile_data.email,
            "_id": {"$ne": current_user["_id"]}
        })
        if existing_user:
            raise HTTPException(status_code=400, detail="Email is already taken")
        update_data["email"] = profile_data.email
    
    if profile_data.company_name is not None:
        update_data["company_name"] = profile_data.company_name
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
        
        # Get updated user data
        updated_user = await db.users.find_one({"_id": current_user["_id"]})
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user["_id"],
                "username": updated_user["username"],
                "email": updated_user["email"],
                "role": updated_user["role"],
                "credits": updated_user.get("credits", 0),
                "company_name": updated_user.get("company_name"),
                "updated_at": updated_user.get("updated_at")
            }
        }
    
    return {"message": "No changes made"}

# API Key management endpoints
@app.get("/api/user/api-keys")
async def get_user_api_keys(current_user = Depends(get_current_user)):
    """Get all API keys for current user"""
    api_keys = await db.api_keys.find(
        {"user_id": current_user["_id"]},
        {"key_hash": 0}  # Don't return the actual hash
    ).to_list(100)
    
    return [
        APIKeyResponse(
            id=key["_id"],
            name=key["name"],
            description=key.get("description"),
            permissions=key.get("permissions", []),
            key_preview=f"wt_{'*' * 8}...{key['_id'][-4:]}",
            created_at=key["created_at"],
            last_used=key.get("last_used"),
            is_active=key.get("is_active", True)
        ) for key in api_keys
    ]

@app.post("/api/user/api-keys")
async def create_api_key(api_key_data: APIKeyCreate, current_user = Depends(get_current_user)):
    """Create new API key for current user"""
    
    # Check if user already has maximum API keys (limit to 10)
    existing_count = await db.api_keys.count_documents({"user_id": current_user["_id"]})
    if existing_count >= 10:
        raise HTTPException(status_code=400, detail="Maximum API keys limit reached (10)")
    
    # Generate new API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    
    # Create API key document
    api_key_doc = {
        "_id": generate_id(),
        "user_id": current_user["_id"],
        "tenant_id": current_user["tenant_id"],
        "name": api_key_data.name,
        "description": api_key_data.description,
        "permissions": api_key_data.permissions,
        "key_hash": key_hash,
        "created_at": datetime.utcnow(),
        "last_used": None,
        "is_active": True
    }
    
    await db.api_keys.insert_one(api_key_doc)
    
    return {
        "message": "API key created successfully",
        "api_key": api_key,  # Only show the actual key once
        "id": api_key_doc["_id"],
        "name": api_key_data.name,
        "permissions": api_key_data.permissions
    }

@app.put("/api/user/api-keys/{key_id}")
async def update_api_key(key_id: str, api_key_data: APIKeyCreate, current_user = Depends(get_current_user)):
    """Update API key (name, description, permissions)"""
    
    result = await db.api_keys.update_one(
        {"_id": key_id, "user_id": current_user["_id"]},
        {"$set": {
            "name": api_key_data.name,
            "description": api_key_data.description,
            "permissions": api_key_data.permissions,
            "updated_at": datetime.utcnow()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"message": "API key updated successfully"}

@app.delete("/api/user/api-keys/{key_id}")
async def delete_api_key(key_id: str, current_user = Depends(get_current_user)):
    """Delete API key"""
    
    result = await db.api_keys.delete_one({"_id": key_id, "user_id": current_user["_id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"message": "API key deleted successfully"}

@app.post("/api/user/api-keys/{key_id}/toggle")
async def toggle_api_key(key_id: str, current_user = Depends(get_current_user)):
    """Toggle API key active status"""
    
    # Get current status
    api_key = await db.api_keys.find_one({"_id": key_id, "user_id": current_user["_id"]})
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    new_status = not api_key.get("is_active", True)
    
    await db.api_keys.update_one(
        {"_id": key_id},
        {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}}
    )
    
    return {
        "message": f"API key {'activated' if new_status else 'deactivated'} successfully",
        "is_active": new_status
    }

# Credit Top-up and Payment Routes
@app.get("/api/credit-packages")
async def get_credit_packages():
    """Get available credit packages"""
    return CREDIT_PACKAGES

@app.post("/api/payments/create-checkout")
async def create_credit_checkout(request: CreditTopupRequest, current_user = Depends(get_current_user)):
    """Create Stripe checkout session for credit top-up"""
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    # Validate package
    if request.package_id not in CREDIT_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package selected")
    
    package = CREDIT_PACKAGES[request.package_id]
    
    try:
        # Initialize Stripe checkout
        webhook_url = f"{request.origin_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Create success and cancel URLs
        success_url = f"{request.origin_url}/dashboard?session_id={{CHECKOUT_SESSION_ID}}&payment_status=success"
        cancel_url = f"{request.origin_url}/dashboard"
        
        # Create checkout session request
        checkout_request = CheckoutSessionRequest(
            amount=package["price"],
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": current_user["_id"],
                "package_id": request.package_id,
                "credits_amount": str(package["credits"]),
                "source": "credit_topup"
            }
        )
        
        # Create checkout session
        session: CheckoutStatusResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction_doc = {
            "_id": generate_id(),
            "user_id": current_user["_id"],
            "tenant_id": current_user["tenant_id"],
            "package_id": request.package_id,
            "amount": package["price"],
            "currency": "usd",
            "session_id": session.session_id,
            "payment_status": "pending",
            "credits_amount": package["credits"],
            "package_name": package["name"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {
                "user_id": current_user["_id"],
                "package_id": request.package_id,
                "credits_amount": str(package["credits"]),
                "source": "credit_topup"
            }
        }
        
        await db.payment_transactions.insert_one(transaction_doc)
        
        logger.info(f"Created payment transaction {transaction_doc['_id']} for user {current_user['_id']}")
        
        return {
            "url": session.url,
            "session_id": session.session_id,
            "package": package,
            "transaction_id": transaction_doc["_id"]
        }
        
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create payment session: {str(e)}")

@app.get("/api/payments/status/{session_id}")
async def get_payment_status(session_id: str, current_user = Depends(get_current_user)):
    """Get payment status and process if completed"""
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    try:
        # Get transaction from database
        transaction = await db.payment_transactions.find_one({
            "session_id": session_id,
            "user_id": current_user["_id"]
        })
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # If already processed, return status
        if transaction["payment_status"] in ["completed", "failed", "expired"]:
            return {
                "status": transaction["payment_status"],
                "payment_status": transaction["payment_status"],
                "amount_total": int(transaction["amount"] * 100),  # Convert to cents
                "currency": transaction["currency"],
                "credits_amount": transaction["credits_amount"],
                "processed": True
            }
        
        # Check with Stripe
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
        checkout_status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction status
        await db.payment_transactions.update_one(
            {"_id": transaction["_id"]},
            {"$set": {
                "payment_status": checkout_status.payment_status,
                "stripe_status": checkout_status.status,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # If payment is completed and not already processed, add credits
        if (checkout_status.payment_status == "paid" and 
            transaction["payment_status"] != "completed"):
            
            # Add credits to user account
            await db.users.update_one(
                {"_id": current_user["_id"]},
                {"$inc": {"credits": transaction["credits_amount"]}}
            )
            
            # Mark transaction as completed
            await db.payment_transactions.update_one(
                {"_id": transaction["_id"]},
                {"$set": {
                    "payment_status": "completed",
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Log the credit addition
            usage_doc = {
                "_id": generate_id(),
                "user_id": current_user["_id"],
                "tenant_id": current_user["tenant_id"],
                "type": "credit_purchase",
                "transaction_id": transaction["_id"],
                "credits_added": transaction["credits_amount"],
                "amount_paid": transaction["amount"],
                "timestamp": datetime.utcnow()
            }
            
            await db.usage_logs.insert_one(usage_doc)
            
            # Send success email
            try:
                user = await db.users.find_one({"_id": current_user["_id"]})
                if user and user.get("email"):
                    await email_service.send_credit_purchase_email(
                        user["email"],
                        user["username"],
                        transaction["credits_amount"],
                        transaction["amount"],
                        transaction["package_name"]
                    )
            except Exception as e:
                logger.error(f"Failed to send credit purchase email: {e}")
            
            logger.info(f"Added {transaction['credits_amount']} credits to user {current_user['_id']}")
        
        return {
            "status": checkout_status.status,
            "payment_status": checkout_status.payment_status,
            "amount_total": checkout_status.amount_total,
            "currency": checkout_status.currency,
            "credits_amount": transaction["credits_amount"],
            "processed": checkout_status.payment_status == "paid"
        }
        
    except Exception as e:
        logger.error(f"Failed to get payment status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check payment status: {str(e)}")

@app.get("/api/payments/transactions")
async def get_payment_transactions(current_user = Depends(get_current_user)):
    """Get user's payment transaction history"""
    
    transactions = await db.payment_transactions.find(
        {"user_id": current_user["_id"]},
        sort=[("created_at", DESCENDING)]
    ).limit(50).to_list(50)
    
    return transactions

@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    
    if not STRIPE_API_KEY:
        return {"status": "error", "message": "Stripe not configured"}
    
    try:
        body = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            logger.warning("Missing Stripe signature")
            return {"status": "error", "message": "Missing signature"}
        
        # Initialize Stripe checkout for webhook handling
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
        
        # Handle webhook
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        logger.info(f"Stripe webhook received: {webhook_response.event_type}")
        
        # Process based on event type
        if webhook_response.event_type in ["checkout.session.completed", "payment_intent.succeeded"]:
            # Find transaction by session_id
            transaction = await db.payment_transactions.find_one({
                "session_id": webhook_response.session_id
            })
            
            if transaction and transaction["payment_status"] != "completed":
                # Add credits to user
                await db.users.update_one(
                    {"_id": transaction["user_id"]},
                    {"$inc": {"credits": transaction["credits_amount"]}}
                )
                
                # Update transaction
                await db.payment_transactions.update_one(
                    {"_id": transaction["_id"]},
                    {"$set": {
                        "payment_status": "completed",
                        "stripe_status": webhook_response.payment_status,
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "webhook_processed": True
                    }}
                )
                
                logger.info(f"Webhook processed: Added {transaction['credits_amount']} credits to user {transaction['user_id']}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/validation/quick-check")
async def quick_check(request: QuickCheckRequest, current_user = Depends(get_current_user)):
    if current_user.get("credits", 0) < 2:
        raise HTTPException(status_code=400, detail="Insufficient credits")
    
    # Parse input to get identifier and phone number
    parsed_input = parse_phone_input(request.phone_input)
    identifier = parsed_input["identifier"]
    phone_number = parsed_input["phone_number"]
    
    if not phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")
    
    # Normalize phone number
    normalized_phone = normalize_phone_number(phone_number)
    
    # Check cache first
    cached_result = await db.validation_cache.find_one({"phone_number": normalized_phone})
    if cached_result and (datetime.utcnow() - cached_result["cached_at"]).days < 7:
        # Add identifier to cached result
        cached_result["whatsapp"]["identifier"] = identifier
        cached_result["telegram"]["identifier"] = identifier
        
        return {
            "identifier": identifier,
            "phone_number": normalized_phone,
            "whatsapp": cached_result["whatsapp"],
            "telegram": cached_result["telegram"],
            "cached": True,
            "checked_at": cached_result["cached_at"],
            "providers_used": {
                "whatsapp": "WhatsApp Web API (Cached)",
                "telegram": "Mock Provider (Cached)"
            }
        }
    
    # NEW: Use WhatsApp Web API (FREE!)
    whatsapp_result = await validate_whatsapp_web_api(normalized_phone, identifier)
        
    # Keep Telegram validation as before (existing method)
    telegram_account = await db.telegram_accounts.find_one({"is_active": True})
    if telegram_account: 
        telegram_result = await validate_telegram_number_real(normalized_phone, telegram_account)
    else:
        telegram_result = await validate_telegram_number(normalized_phone)
    
    # Add identifier to telegram result
    telegram_result["identifier"] = identifier
    
    # Cache results
    cache_doc = {
        "phone_number": normalized_phone,
        "whatsapp": whatsapp_result,
        "telegram": telegram_result,
        "cached_at": datetime.utcnow()
    }
    
    await db.validation_cache.update_one(
        {"phone_number": normalized_phone},
        {"$set": cache_doc},
        upsert=True
    )
    
    # Deduct credits
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$inc": {"credits": -2}}
    )
    
    # Log usage
    usage_doc = {
        "_id": generate_id(),
        "user_id": current_user["_id"],
        "tenant_id": current_user["tenant_id"],
        "type": "quick_check",
        "phone_number": normalized_phone,
        "identifier": identifier,  # NEW: Log identifier
        "credits_used": 2,
        "timestamp": datetime.utcnow(),
        "providers_used": {
            "whatsapp": "WhatsApp Web API (FREE)",
            "telegram": telegram_account.get("name", "mock") if telegram_account else "mock"
        }
    }
    
    await db.usage_logs.insert_one(usage_doc)
    
    return {
        "identifier": identifier,
        "phone_number": normalized_phone,
        "whatsapp": whatsapp_result,
        "telegram": telegram_result,
        "cached": False,
        "checked_at": datetime.utcnow(),
        "providers_used": {
            "whatsapp": "WhatsApp Web API (FREE)",
            "telegram": telegram_account.get("name", "Mock Provider") if telegram_account else "Mock Provider"
        }
    }

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user = Depends(get_current_user)):
    # Get user stats
    user_stats = await db.usage_logs.aggregate([
        {"$match": {"user_id": current_user["_id"]}},
        {"$group": {
            "_id": None,
            "total_checks": {"$sum": 1},
            "total_credits_used": {"$sum": "$credits_used"}
        }}
    ]).to_list(1)
    
    # Get monthly stats
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_stats = await db.usage_logs.aggregate([
        {"$match": {
            "user_id": current_user["_id"],
            "timestamp": {"$gte": start_of_month}
        }},
        {"$group": {
            "_id": None,
            "monthly_checks": {"$sum": 1},
            "monthly_credits": {"$sum": "$credits_used"}
        }}
    ]).to_list(1)
    
    # Get recent jobs
    recent_jobs = await db.jobs.find(
        {"user_id": current_user["_id"]},
        {"_id": 1, "filename": 1, "status": 1, "created_at": 1, "total_numbers": 1}
    ).sort("created_at", DESCENDING).limit(5).to_list(5)
    
    stats = user_stats[0] if user_stats else {"total_checks": 0, "total_credits_used": 0}
    monthly = monthly_stats[0] if monthly_stats else {"monthly_checks": 0, "monthly_credits": 0}
    
    return {
        "credits_remaining": current_user.get("credits", 0),
        "total_checks": stats["total_checks"],
        "monthly_checks": monthly["monthly_checks"],
        "total_credits_used": stats["total_credits_used"],
        "monthly_credits_used": monthly["monthly_credits"],
        "recent_jobs": recent_jobs
    }

# Bulk Validation Routes
@app.post("/api/validation/bulk-check")
async def bulk_check(background_tasks: BackgroundTasks, file: UploadFile = File(...), current_user = Depends(get_current_user)):
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Format file tidak didukung. Gunakan CSV, XLS, atau XLSX")
    
    if file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File terlalu besar. Maksimal 10MB")
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Flexible column support - check for various column names
        phone_col = None
        name_col = None
        
        # Look for phone number column
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['phone_number', 'nomor', 'phone', 'no_hp', 'telepon']:
                phone_col = col
                break
        
        # Look for name column (optional)
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['name', 'nama', 'identifier', 'username']:
                name_col = col
                break
        
        if phone_col is None:
            raise HTTPException(
                status_code=400, 
                detail="File harus memiliki kolom nomor telepon dengan nama: 'phone_number', 'nomor', 'phone', 'no_hp', atau 'telepon'"
            )
        
        # Extract data with identifiers
        phone_data = []
        for index, row in df.iterrows():
            phone_number = str(row[phone_col]).strip() if pd.notna(row[phone_col]) else ""
            identifier = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else None
            
            if phone_number and phone_number.lower() not in ['nan', 'none', '']:
                # Truncate identifier to 12 characters if provided
                if identifier and len(identifier) > 12:
                    identifier = identifier[:12]
                
                normalized_phone = normalize_phone_number(phone_number)
                phone_data.append({
                    "identifier": identifier,
                    "phone_number": normalized_phone,
                    "original_phone": phone_number
                })
        
        if not phone_data:
            raise HTTPException(status_code=400, detail="Tidak ada nomor telepon valid yang ditemukan")
        
        # Remove duplicates based on normalized phone number (keep first occurrence with identifier)
        seen_phones = set()
        unique_phone_data = []
        
        for item in phone_data:
            if item["phone_number"] not in seen_phones:
                seen_phones.add(item["phone_number"])
                unique_phone_data.append(item)
        
        if len(unique_phone_data) > 1000:
            raise HTTPException(status_code=400, detail="Maksimal 1000 nomor unik per file")
        
        # Check credits
        required_credits = len(unique_phone_data) * 2
        if current_user.get("credits", 0) < required_credits:
            raise HTTPException(
                status_code=400, 
                detail=f"Kredit tidak mencukupi. Dibutuhkan {required_credits} kredit, tersisa {current_user.get('credits', 0)}"
            )
        
        # Create job
        job_doc = {
            "_id": generate_id(),
            "user_id": current_user["_id"],
            "tenant_id": current_user["tenant_id"],
            "filename": file.filename,
            "status": JobStatus.PENDING,
            "total_numbers": len(unique_phone_data),
            "processed_numbers": 0,
            "phone_data": unique_phone_data,  # Store both phone and identifier
            "results": None,
            "credits_used": required_credits,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "duplicates_removed": len(phone_data) - len(unique_phone_data),  # Track duplicates removed
            "error_message": None
        }
        
        await db.jobs.insert_one(job_doc)
        
        # Start background processing
        background_tasks.add_task(process_bulk_validation, job_doc["_id"])
        
        return {
            "message": "File berhasil diupload dan sedang diproses",
            "job_id": job_doc["_id"],
            "total_numbers": len(unique_phone_data),
            "estimated_credits": required_credits,
            "status": "processing_started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.get("/api/jobs")
async def get_jobs(current_user = Depends(get_current_user)):
    jobs = await db.jobs.find(
        {"user_id": current_user["_id"]},
        sort=[("created_at", DESCENDING)]
    ).to_list(50)
    
    return jobs

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, current_user = Depends(get_current_user)):
    job = await db.jobs.find_one({"_id": job_id, "user_id": current_user["_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")
    
    return job

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str, current_user = Depends(get_current_user)):
    result = await db.jobs.delete_one({"_id": job_id, "user_id": current_user["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")
    
    return {"message": "Job berhasil dihapus"}

@app.get("/api/jobs/{job_id}/download")
async def download_job_result(job_id: str, current_user = Depends(get_current_user)):
    job = await db.jobs.find_one({"_id": job_id, "user_id": current_user["_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job belum selesai")
    
    # Generate CSV content from results
    if not job.get("results") or not job["results"].get("details"):
        raise HTTPException(status_code=400, detail="Tidak ada hasil untuk diunduh")
    
    # Create CSV content
    csv_content = "phone_number,whatsapp_status,telegram_status,whatsapp_details,telegram_details,processed_at\n"
    
    for detail in job["results"]["details"]:
        if "error" in detail:
            csv_content += f"{detail['phone_number']},ERROR,ERROR,{detail['error']},,{detail['processed_at']}\n"
        else:
            whatsapp_details = json.dumps(detail['whatsapp']['details']) if detail['whatsapp'].get('details') else ""
            telegram_details = json.dumps(detail['telegram']['details']) if detail['telegram'].get('details') else ""
            csv_content += f"{detail['phone_number']},{detail['whatsapp']['status']},{detail['telegram']['status']},\"{whatsapp_details}\",\"{telegram_details}\",{detail['processed_at']}\n"
    
    # Return CSV as response
    from fastapi.responses import Response
    
    filename = f"validation_results_{job_id[:8]}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/jobs/{job_id}/status")
async def get_job_status(job_id: str, current_user = Depends(get_current_user)):
    job = await db.jobs.find_one({"_id": job_id, "user_id": current_user["_id"]})
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")
    
    progress_percentage = 0
    if job["total_numbers"] > 0:
        progress_percentage = round((job.get("processed_numbers", 0) / job["total_numbers"]) * 100, 2)
    
    return {
        "job_id": job["_id"],
        "status": job["status"],
        "filename": job["filename"],
        "total_numbers": job["total_numbers"],
        "processed_numbers": job.get("processed_numbers", 0),
        "progress_percentage": progress_percentage,
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "results": job.get("results"),
        "error_message": job.get("error_message")
    }

# Admin Routes
async def admin_required(current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@app.get("/api/admin/stats")
async def get_admin_stats(current_user = Depends(admin_required)):
    # Get system stats
    total_users = await db.users.count_documents({})
    total_validations = await db.usage_logs.count_documents({})
    active_jobs = await db.jobs.count_documents({"status": {"$in": ["pending", "processing"]}})
    
    # Get credits used
    credits_used = await db.usage_logs.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$credits_used"}}}
    ]).to_list(1)
    
    # Get recent activities
    recent_activities = await db.usage_logs.aggregate([
        {"$lookup": {
            "from": "users",
            "localField": "user_id", 
            "foreignField": "_id",
            "as": "user"
        }},
        {"$unwind": "$user"},
        {"$sort": {"timestamp": -1}},
        {"$limit": 10},
        {"$project": {
            "message": {
                "$concat": [
                    "$user.username", 
                    " performed ", 
                    "$type",
                    {"$cond": [
                        {"$eq": ["$type", "credit_purchase"]},
                        {
                            "$concat": [
                                " - Added ",
                                {"$toString": "$credits_added"},
                                " credits"
                            ]
                        },
                        {
                            "$concat": [
                                " - Used ",
                                {"$toString": "$credits_used"},
                                " credits"
                            ]
                        }
                    ]}
                ]
            },
            "timestamp": {"$dateToString": {
                "format": "%Y-%m-%d %H:%M:%S",
                "date": "$timestamp"
            }}
        }}
    ]).to_list(10)
    
    return {
        "total_users": total_users,
        "total_validations": total_validations,
        "active_jobs": active_jobs,
        "credits_used": credits_used[0]["total"] if credits_used else 0,
        "recent_activities": recent_activities
    }

@app.get("/api/admin/users")
async def get_admin_users(
    page: int = 1,
    limit: int = 20,
    search: str = None,
    role: str = None,
    current_user = Depends(admin_required)
):
    """Get users with pagination and filtering"""
    
    skip = (page - 1) * limit
    query = {}
    
    # Add search filter
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}}
        ]
    
    # Add role filter
    if role:
        query["role"] = role
    
    # Get users with usage stats
    users = await db.users.aggregate([
        {"$match": query},
        {"$lookup": {
            "from": "usage_logs",
            "localField": "_id",
            "foreignField": "user_id",
            "as": "usage"
        }},
        {"$addFields": {
            "total_validations": {"$size": "$usage"},
            "total_credits_used": {"$sum": "$usage.credits_used"}
        }},
        {"$project": {
            "password": 0,  # Don't include password
            "usage": 0  # Don't include full usage array
        }},
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ]).to_list(limit)
    
    # Get total count
    total_count = await db.users.count_documents(query)
    
    return {
        "users": users,
        "pagination": {
            "current_page": page,
            "total_pages": (total_count + limit - 1) // limit,
            "total_count": total_count,
            "limit": limit
        }
    }

@app.get("/api/admin/users/{user_id}")
async def get_admin_user_details(user_id: str, current_user = Depends(admin_required)):
    """Get detailed user information"""
    
    # Get user details
    user = await db.users.find_one({"_id": user_id}, {"password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's recent activities
    recent_activities = await db.usage_logs.find(
        {"user_id": user_id},
        sort=[("timestamp", DESCENDING)]
    ).limit(20).to_list(20)
    
    # Get user's payment transactions
    payment_transactions = await db.payment_transactions.find(
        {"user_id": user_id},
        sort=[("created_at", DESCENDING)]
    ).limit(10).to_list(10)
    
    # Get user's recent jobs
    recent_jobs = await db.jobs.find(
        {"user_id": user_id},
        sort=[("created_at", DESCENDING)]
    ).limit(10).to_list(10)
    
    # Calculate stats
    usage_stats = await db.usage_logs.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_validations": {"$sum": 1},
            "total_credits_used": {"$sum": "$credits_used"},
            "credits_purchased": {"$sum": "$credits_added"}
        }}
    ]).to_list(1)
    
    stats = usage_stats[0] if usage_stats else {
        "total_validations": 0,
        "total_credits_used": 0,
        "credits_purchased": 0
    }
    
    return {
        "user": user,
        "stats": stats,
        "recent_activities": recent_activities,
        "payment_transactions": payment_transactions,
        "recent_jobs": recent_jobs
    }

@app.put("/api/admin/users/{user_id}")
async def update_admin_user(
    user_id: str,
    user_data: AdminUserUpdate,
    current_user = Depends(admin_required)
):
    """Update user settings (admin only)"""
    
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    
    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active
    
    if user_data.credits is not None:
        update_data["credits"] = user_data.credits
    
    if user_data.role is not None:
        update_data["role"] = user_data.role
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        update_data["updated_by"] = current_user["_id"]
        
        await db.users.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        # Log admin action
        log_doc = {
            "_id": generate_id(),
            "admin_id": current_user["_id"],
            "target_user_id": user_id,
            "action": "user_update",
            "changes": update_data,
            "timestamp": datetime.utcnow()
        }
        
        await db.admin_logs.insert_one(log_doc)
    
    return {"message": "User updated successfully"}

@app.get("/api/admin/analytics")
async def get_admin_analytics(
    period: str = "30d",  # 7d, 30d, 90d
    current_user = Depends(admin_required)
):
    """Get system analytics"""
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "7d":
        start_date = now - timedelta(days=7)
    elif period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=30)
    
    # Daily usage stats
    daily_stats = await db.usage_logs.aggregate([
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "type": "$type"
            },
            "count": {"$sum": 1},
            "credits_used": {"$sum": "$credits_used"}
        }},
        {"$sort": {"_id.date": 1}}
    ]).to_list(1000)
    
    # User registration stats
    user_stats = await db.users.aggregate([
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "new_users": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]).to_list(1000)
    
    # Payment stats
    payment_stats = await db.payment_transactions.aggregate([
        {"$match": {
            "created_at": {"$gte": start_date},
            "payment_status": "completed"
        }},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "revenue": {"$sum": "$amount"},
            "transactions": {"$sum": 1},
            "credits_sold": {"$sum": "$credits_amount"}
        }},
        {"$sort": {"_id": 1}}
    ]).to_list(1000)
    
    # Top users by usage
    top_users = await db.usage_logs.aggregate([
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": "$user_id",
            "total_validations": {"$sum": 1},
            "total_credits_used": {"$sum": "$credits_used"}
        }},
        {"$lookup": {
            "from": "users",
            "localField": "_id",
            "foreignField": "_id",
            "as": "user"
        }},
        {"$unwind": "$user"},
        {"$project": {
            "username": "$user.username",
            "email": "$user.email",
            "total_validations": 1,
            "total_credits_used": 1
        }},
        {"$sort": {"total_validations": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    return {
        "period": period,
        "daily_stats": daily_stats,
        "user_stats": user_stats,
        "payment_stats": payment_stats,
        "top_users": top_users
    }

@app.get("/api/admin/telegram-accounts")
async def get_telegram_accounts(current_user = Depends(admin_required)):
    accounts = await db.telegram_accounts.find({}).to_list(100)
    return accounts

@app.post("/api/admin/telegram-accounts")
async def create_telegram_account(account: TelegramAccount, current_user = Depends(admin_required)):
    account_doc = {
        "_id": generate_id(),
        **account.dict(),
        "created_at": datetime.utcnow(),
        "created_by": current_user["_id"]
    }
    
    await db.telegram_accounts.insert_one(account_doc)
    return {"message": "Telegram account created successfully", "id": account_doc["_id"]}

@app.get("/api/admin/whatsapp-providers")
async def get_whatsapp_providers(current_user = Depends(admin_required)):
    providers = await db.whatsapp_providers.find({}).to_list(100)
    return providers

@app.post("/api/admin/whatsapp-providers")
async def create_whatsapp_provider(provider: WhatsAppProvider, current_user = Depends(admin_required)):
    provider_doc = {
        "_id": generate_id(),
        **provider.dict(),
        "created_at": datetime.utcnow(),
        "created_by": current_user["_id"]
    }
    
    await db.whatsapp_providers.insert_one(provider_doc)
    return {"message": "WhatsApp provider created successfully", "id": provider_doc["_id"]}

@app.put("/api/admin/telegram-accounts/{account_id}")
async def update_telegram_account(account_id: str, account: TelegramAccount, current_user = Depends(admin_required)):
    result = await db.telegram_accounts.update_one(
        {"_id": account_id},
        {"$set": {
            **account.dict(),
            "updated_at": datetime.utcnow(),
            "updated_by": current_user["_id"]
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Telegram account not found")
    
    return {"message": "Telegram account updated successfully"}

@app.delete("/api/admin/telegram-accounts/{account_id}")
async def delete_telegram_account(account_id: str, current_user = Depends(admin_required)):
    result = await db.telegram_accounts.delete_one({"_id": account_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Telegram account not found")
    
    return {"message": "Telegram account deleted successfully"}

@app.put("/api/admin/whatsapp-providers/{provider_id}")
async def update_whatsapp_provider(provider_id: str, provider: WhatsAppProvider, current_user = Depends(admin_required)):
    result = await db.whatsapp_providers.update_one(
        {"_id": provider_id},
        {"$set": {
            **provider.dict(),
            "updated_at": datetime.utcnow(),
            "updated_by": current_user["_id"]
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="WhatsApp provider not found")
    
    return {"message": "WhatsApp provider updated successfully"}

@app.delete("/api/admin/whatsapp-providers/{provider_id}")
async def delete_whatsapp_provider(provider_id: str, current_user = Depends(admin_required)):
    result = await db.whatsapp_providers.delete_one({"_id": provider_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="WhatsApp provider not found")
    
    return {"message": "WhatsApp provider deleted successfully"}

@app.get("/api/admin/jobs")
async def get_admin_jobs(current_user = Depends(admin_required)):
    jobs = await db.jobs.find({}, sort=[("created_at", DESCENDING)]).limit(100).to_list(100)
    return jobs

@app.post("/api/admin/create-demo-user")
async def create_demo_user(current_user = Depends(admin_required)):
    # Check if demo user already exists
    existing_demo = await db.users.find_one({"username": "demo"})
    if existing_demo:
        return {"message": "Demo user already exists"}
    
    # Create demo tenant
    tenant_id = generate_id()
    
    # Create demo user
    user_doc = {
        "_id": generate_id(),
        "username": "demo",
        "email": "demo@example.com",
        "password": hash_password("demo123"),
        "role": UserRole.USER,
        "tenant_id": tenant_id,
        "company_name": "Demo Company",
        "credits": 5000,  # Give more credits for demo
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    await db.users.insert_one(user_doc)
    
    # Create tenant document
    tenant_doc = {
        "_id": tenant_id,
        "name": "Demo Company",
        "owner_id": user_doc["_id"],
        "created_at": datetime.utcnow(),
        "settings": {
            "rate_limit": 1000,
            "max_bulk_size": 5000
        }
    }
    
    await db.tenants.insert_one(tenant_doc)
    
    return {"message": "Demo user created successfully", "username": "demo", "password": "demo123"}

@app.post("/api/admin/seed-sample-data")
async def seed_sample_data():
    """Endpoint untuk menambahkan sample data - development only"""
    
    # Sample WhatsApp Providers
    whatsapp_providers = [
        {
            "_id": generate_id(),
            "name": "Twilio WhatsApp Business",
            "api_endpoint": "https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json",
            "api_key": "twilio-api-key-placeholder",
            "provider_type": "twilio",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "created_by": "system"
        },
        {
            "_id": generate_id(),
            "name": "Vonage WhatsApp API",
            "api_endpoint": "https://messages-sandbox.nexmo.com/v1/messages",
            "api_key": "vonage-api-key-placeholder",
            "provider_type": "vonage",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "created_by": "system"
        },
        {
            "_id": generate_id(),
            "name": "360Dialog WhatsApp",
            "api_endpoint": "https://waba.360dialog.io/v1/messages",
            "api_key": "360dialog-api-key-placeholder",
            "provider_type": "360dialog",
            "is_active": False,
            "created_at": datetime.utcnow(),
            "created_by": "system"
        }
    ]
    
    # Sample Telegram Accounts
    telegram_accounts = [
        {
            "_id": generate_id(),
            "name": "Primary Telegram Bot",
            "phone_number": "+6281234567890",
            "api_id": "1234567",
            "api_hash": "abcdef1234567890abcdef1234567890",
            "bot_token": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "created_by": "system"
        },
        {
            "_id": generate_id(),
            "name": "Secondary Telegram Account",
            "phone_number": "+6289876543210",
            "api_id": "9876543",
            "api_hash": "zyxwvu9876543210zyxwvu9876543210",
            "bot_token": "987654321:ZYXwvuTSRqpONMlkJIhGFEdcBA",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "created_by": "system"
        },
        {
            "_id": generate_id(),
            "name": "Backup Telegram Account",
            "phone_number": "+6285555666777",
            "api_id": "5555666",
            "api_hash": "backup1234567890backup1234567890",
            "bot_token": "",
            "is_active": False,
            "created_at": datetime.utcnow(),
            "created_by": "system"
        }
    ]
    
    # Insert data
    await db.whatsapp_providers.insert_many(whatsapp_providers)
    await db.telegram_accounts.insert_many(telegram_accounts)
    
    return {
        "message": "Sample data seeded successfully",
        "whatsapp_providers": len(whatsapp_providers),
        "telegram_accounts": len(telegram_accounts)
    }

@app.post("/api/admin/set-admin-role/{user_id}")
async def set_admin_role(user_id: str):
    """Endpoint untuk mengubah role user menjadi admin - hanya untuk development"""
    result = await db.users.update_one(
        {"_id": user_id},
        {"$set": {"role": UserRole.ADMIN}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User role updated to admin"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")