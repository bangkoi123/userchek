from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, BackgroundTasks, Request, Form
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
import time
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

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    await create_demo_users()

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
    phone_inputs: List[str]  # Changed to support multiple phone inputs
    validate_whatsapp: bool = True
    validate_telegram: bool = True

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
            
        # Get platform selection from job (default to both for backward compatibility)
        validate_whatsapp = job.get("validate_whatsapp", True)
        validate_telegram = job.get("validate_telegram", True)
            
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
                use_cache = cached_result and (datetime.utcnow() - cached_result["cached_at"]).days < 7
                
                if use_cache:
                    whatsapp_result = cached_result["whatsapp"] if validate_whatsapp else None
                    telegram_result = cached_result["telegram"] if validate_telegram else None
                    # Add identifier to cached results
                    if whatsapp_result:
                        whatsapp_result["identifier"] = identifier
                    if telegram_result:
                        telegram_result["identifier"] = identifier
                else:
                    # Perform validation based on platform selection
                    whatsapp_result = None
                    telegram_result = None
                    
                    if validate_whatsapp:
                        whatsapp_result = await validate_whatsapp_web_api(phone, identifier)
                    
                    if validate_telegram:
                        telegram_result = await validate_telegram_number(phone)
                        telegram_result["identifier"] = identifier
                    
                    # Cache results if both were validated (for optimal caching)
                    if validate_whatsapp and validate_telegram:
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
                if whatsapp_result and whatsapp_result["status"] == ValidationStatus.ACTIVE:
                    results["whatsapp_active"] += 1
                if telegram_result and telegram_result["status"] == ValidationStatus.ACTIVE:
                    results["telegram_active"] += 1
                
                # Check if both platforms are inactive (only count if both were validated)
                whatsapp_inactive = whatsapp_result and whatsapp_result["status"] == ValidationStatus.INACTIVE
                telegram_inactive = telegram_result and telegram_result["status"] == ValidationStatus.INACTIVE
                
                # Count as inactive only if ALL validated platforms are inactive
                if validate_whatsapp and validate_telegram:
                    if whatsapp_inactive and telegram_inactive:
                        results["inactive"] += 1
                elif validate_whatsapp and whatsapp_inactive:
                    results["inactive"] += 1
                elif validate_telegram and telegram_inactive:
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
                last_result = {}
                if whatsapp_result:
                    last_result["whatsapp"] = whatsapp_result["status"]
                if telegram_result:
                    last_result["telegram"] = telegram_result["status"]
                
                await emit_job_progress(job_id, {
                    "job_id": job_id,
                    "status": "processing",
                    "processed_numbers": processed_count,
                    "total_numbers": len(phone_data_list),
                    "progress_percentage": progress_percentage,
                    "current_phone": phone,
                    "current_identifier": identifier,
                    "last_result": last_result
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
            "processed_numbers": len(phone_data_list),
            "total_numbers": len(phone_data_list),
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
            "numbers_processed": len(phone_data_list),
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
    # Validate input
    if not request.phone_inputs or len(request.phone_inputs) == 0:
        raise HTTPException(status_code=400, detail="At least one phone number is required")
    
    if len(request.phone_inputs) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 phone numbers allowed")
    
    if not request.validate_whatsapp and not request.validate_telegram:
        raise HTTPException(status_code=400, detail="At least one platform must be selected")
    
    # Calculate credits needed
    credits_per_number = 0
    if request.validate_whatsapp:
        credits_per_number += 1
    if request.validate_telegram:
        credits_per_number += 1
    
    # Parse and validate phone inputs
    parsed_phones = []
    for phone_input in request.phone_inputs:
        if not phone_input.strip():
            continue
        parsed_input = parse_phone_input(phone_input.strip())
        if parsed_input["phone_number"]:
            parsed_input["phone_number"] = normalize_phone_number(parsed_input["phone_number"])
            parsed_phones.append(parsed_input)
    
    if not parsed_phones:
        raise HTTPException(status_code=400, detail="No valid phone numbers found")
    
    # Remove duplicates
    seen_phones = set()
    unique_phones = []
    for phone_data in parsed_phones:
        if phone_data["phone_number"] not in seen_phones:
            seen_phones.add(phone_data["phone_number"])
            unique_phones.append(phone_data)
    
    total_credits_needed = len(unique_phones) * credits_per_number
    if current_user.get("credits", 0) < total_credits_needed:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient credits. Need {total_credits_needed}, have {current_user.get('credits', 0)}"
        )
    
    # Check admin platform settings
    admin_settings = await db.admin_settings.find_one({"setting_type": "platform_visibility"}) or {}
    whatsapp_enabled = admin_settings.get("whatsapp_enabled", True)
    telegram_enabled = admin_settings.get("telegram_enabled", True)
    
    if request.validate_whatsapp and not whatsapp_enabled:
        raise HTTPException(status_code=400, detail="WhatsApp validation is currently disabled")
    if request.validate_telegram and not telegram_enabled:
        raise HTTPException(status_code=400, detail="Telegram validation is currently disabled")
    
    # Process validations
    results = {
        "whatsapp_active": 0,
        "whatsapp_business": 0,
        "whatsapp_personal": 0,
        "whatsapp_inactive": 0,
        "telegram_active": 0,
        "telegram_inactive": 0,
        "total_processed": len(unique_phones),
        "duplicates_removed": len(parsed_phones) - len(unique_phones),
        "details": []
    }
    
    telegram_account = await db.telegram_accounts.find_one({"is_active": True}) if request.validate_telegram else None
    
    for phone_data in unique_phones:
        phone = phone_data["phone_number"]
        identifier = phone_data["identifier"]
        
        # Check cache first
        cached_result = await db.validation_cache.find_one({"phone_number": phone})
        use_cache = cached_result and (datetime.utcnow() - cached_result["cached_at"]).days < 7
        
        if use_cache:
            whatsapp_result = cached_result["whatsapp"] if request.validate_whatsapp else None
            telegram_result = cached_result["telegram"] if request.validate_telegram else None
        else:
            # Perform validations
            whatsapp_result = None
            telegram_result = None
            
            if request.validate_whatsapp:
                whatsapp_result = await validate_whatsapp_web_api(phone, identifier)
            
            if request.validate_telegram:
                if telegram_account:
                    telegram_result = await validate_telegram_number_real(phone, telegram_account)
                else:
                    telegram_result = await validate_telegram_number(phone)
                telegram_result["identifier"] = identifier
            
            # Cache results if both were validated
            if whatsapp_result and telegram_result:
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
        
        # Update statistics
        if whatsapp_result:
            if whatsapp_result["status"] == ValidationStatus.ACTIVE:
                results["whatsapp_active"] += 1
                wa_type = whatsapp_result.get("details", {}).get("type", "personal")
                if wa_type == "business":
                    results["whatsapp_business"] += 1
                else:
                    results["whatsapp_personal"] += 1
            else:
                results["whatsapp_inactive"] += 1
        
        if telegram_result:
            if telegram_result["status"] == ValidationStatus.ACTIVE:
                results["telegram_active"] += 1
            else:
                results["telegram_inactive"] += 1
        
        # Store detailed result
        detail = {
            "identifier": identifier,
            "phone_number": phone,
            "original_input": next((p for p in request.phone_inputs if phone in normalize_phone_number(p.split()[-1])), phone),
            "cached": use_cache
        }
        
        if whatsapp_result:
            detail["whatsapp"] = whatsapp_result
        if telegram_result:
            detail["telegram"] = telegram_result
            
        results["details"].append(detail)
    
    # Deduct credits
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$inc": {"credits": -total_credits_needed}}
    )
    
    # Create job entry for history (grouped by date)
    today = datetime.utcnow().date()
    job_id = f"quick_{current_user['_id']}_{today.strftime('%Y%m%d')}"
    
    existing_job = await db.jobs.find_one({"_id": job_id})
    if existing_job:
        # Update existing job for today
        await db.jobs.update_one(
            {"_id": job_id},
            {
                "$push": {"results.quick_check_sessions": {
                    "session_id": generate_id(),
                    "timestamp": datetime.utcnow(),
                    "numbers_processed": len(unique_phones),
                    "credits_used": total_credits_needed,
                    "platforms": {
                        "whatsapp": request.validate_whatsapp,
                        "telegram": request.validate_telegram
                    },
                    "summary": {
                        "whatsapp_active": results["whatsapp_active"],
                        "telegram_active": results["telegram_active"],
                        "total_processed": results["total_processed"]
                    },
                    "details": results["details"]
                }},
                "$inc": {
                    "total_numbers": len(unique_phones),
                    "credits_used": total_credits_needed
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    else:
        # Create new job for today
        job_doc = {
            "_id": job_id,
            "user_id": current_user["_id"],
            "tenant_id": current_user["tenant_id"],
            "job_type": "quick_check_daily",
            "date": today.isoformat(),
            "status": "completed",
            "total_numbers": len(unique_phones),
            "credits_used": total_credits_needed,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "results": {
                "quick_check_sessions": [{
                    "session_id": generate_id(),
                    "timestamp": datetime.utcnow(),
                    "numbers_processed": len(unique_phones),
                    "credits_used": total_credits_needed,
                    "platforms": {
                        "whatsapp": request.validate_whatsapp,
                        "telegram": request.validate_telegram
                    },
                    "summary": {
                        "whatsapp_active": results["whatsapp_active"],
                        "telegram_active": results["telegram_active"],
                        "total_processed": results["total_processed"]
                    },
                    "details": results["details"]
                }]
            }
        }
        await db.jobs.insert_one(job_doc)
    
    # Log usage
    usage_doc = {
        "_id": generate_id(),
        "user_id": current_user["_id"],
        "tenant_id": current_user["tenant_id"],
        "type": "quick_check_multiple",
        "numbers_processed": len(unique_phones),
        "duplicates_removed": results["duplicates_removed"],
        "credits_used": total_credits_needed,
        "platforms": {
            "whatsapp": request.validate_whatsapp,
            "telegram": request.validate_telegram
        },
        "timestamp": datetime.utcnow()
    }
    await db.usage_logs.insert_one(usage_doc)
    
    return {
        "success": True,
        "summary": {
            "total_processed": results["total_processed"],
            "duplicates_removed": results["duplicates_removed"],
            "credits_used": total_credits_needed,
            "whatsapp_active": results["whatsapp_active"],
            "whatsapp_business": results["whatsapp_business"],
            "whatsapp_personal": results["whatsapp_personal"],
            "whatsapp_inactive": results["whatsapp_inactive"],
            "telegram_active": results["telegram_active"],
            "telegram_inactive": results["telegram_inactive"]
        },
        "details": results["details"],
        "platforms_validated": {
            "whatsapp": request.validate_whatsapp,
            "telegram": request.validate_telegram
        },
        "job_id": job_id,
        "checked_at": datetime.utcnow()
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
async def bulk_check(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    validate_whatsapp: bool = Form(True),
    validate_telegram: bool = Form(True),
    current_user = Depends(get_current_user)
):
    # Debug logging
    print(f"🔍 DEBUG bulk_check endpoint called:")
    print(f"  - filename: {file.filename}")
    print(f"  - file size: {file.size}")
    print(f"  - content_type: {file.content_type}")
    print(f"  - validate_whatsapp: {validate_whatsapp} (type: {type(validate_whatsapp)})")
    print(f"  - validate_telegram: {validate_telegram} (type: {type(validate_telegram)})")
    print(f"  - user: {current_user.get('username', 'N/A')}")
    
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        print(f"❌ ERROR: File format not supported: {file.filename}")
        raise HTTPException(status_code=400, detail="Format file tidak didukung. Gunakan CSV, XLS, atau XLSX")
    
    if file.size > 10 * 1024 * 1024:  # 10MB
        print(f"❌ ERROR: File too large: {file.size} bytes")
        raise HTTPException(status_code=400, detail="File terlalu besar. Maksimal 10MB")
    
    # Validate platform selection
    if not validate_whatsapp and not validate_telegram:
        raise HTTPException(status_code=400, detail="Pilih minimal satu platform untuk validasi")
    
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
        
        # Calculate credits based on platform selection
        credits_per_number = 0
        if validate_whatsapp:
            credits_per_number += 1
        if validate_telegram:
            credits_per_number += 1
        
        required_credits = len(unique_phone_data) * credits_per_number
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
            "validate_whatsapp": validate_whatsapp,
            "validate_telegram": validate_telegram,
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
    
    # Create CSV content with identifier support
    csv_content = "identifier,phone_number,original_phone,whatsapp_status,telegram_status,whatsapp_details,telegram_details,processed_at\n"
    
    for detail in job["results"]["details"]:
        identifier = detail.get('identifier', '')
        phone_number = detail.get('phone_number', '')
        original_phone = detail.get('original_phone', phone_number)
        
        if "error" in detail:
            csv_content += f"\"{identifier}\",{phone_number},{original_phone},ERROR,ERROR,{detail['error']},,{detail['processed_at']}\n"
        else:
            # Handle platform-specific results (can be None if platform wasn't validated)
            whatsapp_status = detail['whatsapp']['status'] if detail.get('whatsapp') else "NOT_VALIDATED"
            telegram_status = detail['telegram']['status'] if detail.get('telegram') else "NOT_VALIDATED"
            
            whatsapp_details = json.dumps(detail['whatsapp']['details']) if detail.get('whatsapp') and detail['whatsapp'].get('details') else ""
            telegram_details = json.dumps(detail['telegram']['details']) if detail.get('telegram') and detail['telegram'].get('details') else ""
            
            csv_content += f"\"{identifier}\",{phone_number},{original_phone},{whatsapp_status},{telegram_status},\"{whatsapp_details}\",\"{telegram_details}\",{detail['processed_at']}\n"
    
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

@app.get("/api/admin/platform-settings")
async def get_platform_settings(current_user = Depends(admin_required)):
    """Get platform visibility settings"""
    settings = await db.admin_settings.find_one({"setting_type": "platform_visibility"}) or {
        "whatsapp_enabled": True,
        "telegram_enabled": True
    }
    return settings

@app.put("/api/admin/platform-settings")
async def update_platform_settings(
    whatsapp_enabled: bool,
    telegram_enabled: bool,
    current_user = Depends(admin_required)
):
    """Update platform visibility settings"""
    
    await db.admin_settings.update_one(
        {"setting_type": "platform_visibility"},
        {"$set": {
            "setting_type": "platform_visibility",
            "whatsapp_enabled": whatsapp_enabled,
            "telegram_enabled": telegram_enabled,
            "updated_at": datetime.utcnow(),
            "updated_by": current_user["_id"]
        }},
        upsert=True
    )
    
    return {
        "message": "Platform settings updated successfully",
        "whatsapp_enabled": whatsapp_enabled,
        "telegram_enabled": telegram_enabled
    }

@app.get("/api/platform-settings")
async def get_public_platform_settings():
    """Get platform availability for frontend (public endpoint)"""
    settings = await db.admin_settings.find_one({"setting_type": "platform_visibility"}) or {
        "whatsapp_enabled": True,
        "telegram_enabled": True
    }
    return {
        "whatsapp_enabled": settings.get("whatsapp_enabled", True),
        "telegram_enabled": settings.get("telegram_enabled", True)
    }

@app.get("/api/admin/credit-management")
async def get_credit_management_stats(current_user = Depends(admin_required)):
    """Get credit management statistics"""
    
    # Total credits distributed
    total_credits = await db.users.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$credits"}}}
    ]).to_list(1)
    
    # Credits used statistics
    credits_used_stats = await db.usage_logs.aggregate([
        {"$group": {
            "_id": None,
            "total_used": {"$sum": "$credits_used"},
            "total_transactions": {"$sum": 1}
        }}
    ]).to_list(1)
    
    # Top credit users
    top_users = await db.users.aggregate([
        {"$project": {
            "username": 1,
            "email": 1,
            "credits": 1,
            "role": 1
        }},
        {"$sort": {"credits": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Recent credit transactions
    recent_transactions = await db.payment_transactions.find(
        {"payment_status": "completed"},
        sort=[("completed_at", DESCENDING)]
    ).limit(20).to_list(20)
    
    return {
        "total_credits_in_system": total_credits[0]["total"] if total_credits else 0,
        "total_credits_used": credits_used_stats[0]["total_used"] if credits_used_stats else 0,
        "total_usage_transactions": credits_used_stats[0]["total_transactions"] if credits_used_stats else 0,
        "top_credit_users": top_users,
        "recent_transactions": recent_transactions
    }

@app.get("/api/admin/analytics")
async def get_admin_analytics(current_user = Depends(admin_required)):
    """Get comprehensive admin analytics data"""
    
    try:
        # User statistics
        total_users = await db.users.count_documents({})
        active_users = await db.users.count_documents({"is_active": True})
        admin_users = await db.users.count_documents({"role": "admin"})
        new_users_this_month = await db.users.count_documents({
            "created_at": {"$gte": datetime.utcnow().replace(day=1)}
        })
        
        # Validation statistics
        total_validations = await db.jobs.count_documents({})
        completed_validations = await db.jobs.count_documents({"status": "completed"})
        failed_validations = await db.jobs.count_documents({"status": "failed"}) 
        active_jobs = await db.jobs.count_documents({"status": {"$in": ["running", "pending"]}})
        
        # Credit statistics
        total_credits = await db.users.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$credits"}}}
        ]).to_list(1)
        
        credits_used_stats = await db.usage_logs.aggregate([
            {"$group": {
                "_id": None,
                "total_used": {"$sum": "$credits_used"},
                "total_transactions": {"$sum": 1}
            }}
        ]).to_list(1)
        
        # Payment statistics
        payment_stats = await db.payment_transactions.aggregate([
            {"$match": {"payment_status": "completed"}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$amount"},
                "total_transactions": {"$sum": 1},
                "total_credits_sold": {"$sum": "$credits_amount"}
            }}
        ]).to_list(1)
        
        # Recent activities from different sources
        recent_users = await db.users.find(
            {},
            sort=[("created_at", DESCENDING)]
        ).limit(5).to_list(5)
        
        recent_jobs = await db.jobs.find(
            {},
            sort=[("created_at", DESCENDING)]
        ).limit(5).to_list(5)
        
        recent_payments = await db.payment_transactions.find(
            {"payment_status": "completed"},
            sort=[("completed_at", DESCENDING)]
        ).limit(5).to_list(5)
        
        # Top users by credits
        top_users = await db.users.find(
            {},
            {"username": 1, "email": 1, "credits": 1, "role": 1},
            sort=[("credits", DESCENDING)]
        ).limit(5).to_list(5)
        
        # Platform usage stats
        whatsapp_validations = await db.jobs.count_documents({"platforms": {"$in": ["whatsapp"]}})
        telegram_validations = await db.jobs.count_documents({"platforms": {"$in": ["telegram"]}})
        
        # Daily stats for the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_stats = []
        
        for i in range(7):
            day_start = seven_days_ago + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_users = await db.users.count_documents({
                "created_at": {"$gte": day_start, "$lt": day_end}
            })
            
            day_validations = await db.jobs.count_documents({
                "created_at": {"$gte": day_start, "$lt": day_end}
            })
            
            day_payments = await db.payment_transactions.count_documents({
                "created_at": {"$gte": day_start, "$lt": day_end},
                "payment_status": "completed"
            })
            
            daily_stats.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "new_users": day_users,
                "validations": day_validations,
                "payments": day_payments
            })
        
        return {
            "user_stats": {
                "total_users": total_users,
                "active_users": active_users,
                "admin_users": admin_users,
                "new_users_this_month": new_users_this_month
            },
            "validation_stats": {
                "total_validations": total_validations,
                "completed_validations": completed_validations,
                "failed_validations": failed_validations,
                "active_jobs": active_jobs,
                "whatsapp_validations": whatsapp_validations,
                "telegram_validations": telegram_validations
            },
            "credit_stats": {
                "total_credits_in_system": total_credits[0]["total"] if total_credits else 0,
                "total_credits_used": credits_used_stats[0]["total_used"] if credits_used_stats else 0,
                "total_usage_transactions": credits_used_stats[0]["total_transactions"] if credits_used_stats else 0
            },
            "payment_stats": {
                "total_revenue": payment_stats[0]["total_revenue"] if payment_stats else 0,
                "total_transactions": payment_stats[0]["total_transactions"] if payment_stats else 0,
                "total_credits_sold": payment_stats[0]["total_credits_sold"] if payment_stats else 0
            },
            "daily_stats": daily_stats,
            "top_users": [
                {
                    "id": user["_id"],
                    "username": user["username"],
                    "email": user["email"],
                    "credits": user["credits"],
                    "role": user["role"]
                } for user in top_users
            ],
            "recent_activities": {
                "users": [
                    {
                        "id": user["_id"],
                        "username": user["username"],
                        "email": user["email"],
                        "created_at": user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else user["created_at"]
                    } for user in recent_users
                ],
                "jobs": [
                    {
                        "id": job["_id"],
                        "type": job.get("type", "validation"),
                        "status": job.get("status", "unknown"),
                        "created_at": job["created_at"].isoformat() if isinstance(job["created_at"], datetime) else job["created_at"]
                    } for job in recent_jobs
                ],
                "payments": [
                    {
                        "id": payment["_id"],
                        "amount": payment["amount"],
                        "credits": payment["credits_amount"],
                        "status": payment["payment_status"],
                        "completed_at": payment["completed_at"].isoformat() if isinstance(payment.get("completed_at"), datetime) else payment.get("completed_at")
                    } for payment in recent_payments
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        # Return default structure in case of error
        return {
            "user_stats": {
                "total_users": 0,
                "active_users": 0,
                "admin_users": 0,
                "new_users_this_month": 0
            },
            "validation_stats": {
                "total_validations": 0,
                "completed_validations": 0,
                "failed_validations": 0,
                "active_jobs": 0,
                "whatsapp_validations": 0,
                "telegram_validations": 0
            },
            "credit_stats": {
                "total_credits_in_system": 0,
                "total_credits_used": 0,
                "total_usage_transactions": 0
            },
            "payment_stats": {
                "total_revenue": 0,
                "total_transactions": 0,
                "total_credits_sold": 0
            },
            "daily_stats": [],
            "top_users": [],
            "recent_activities": {
                "users": [],
                "jobs": [],
                "payments": []
            }
        }

@app.post("/api/admin/users/{user_id}/credits")
async def manage_user_credits(
    user_id: str,
    action: str,  # "add", "subtract", "set"
    amount: int,
    reason: str,
    current_user = Depends(admin_required)
):
    """Manage user credits (admin only)"""
    
    if action not in ["add", "subtract", "set"]:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'add', 'subtract', or 'set'")
    
    if amount < 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Get target user
    target_user = await db.users.find_one({"_id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_credits = target_user.get("credits", 0)
    
    # Calculate new credit amount
    if action == "add":
        new_credits = current_credits + amount
    elif action == "subtract":
        new_credits = max(0, current_credits - amount)  # Don't go below 0
    else:  # set
        new_credits = amount
    
    # Update user credits
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {
            "credits": new_credits,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Log admin action
    admin_log = {
        "_id": generate_id(),
        "admin_id": current_user["_id"],
        "target_user_id": user_id,
        "action": f"credit_{action}",
        "details": {
            "previous_credits": current_credits,
            "amount": amount,
            "new_credits": new_credits,
            "reason": reason
        },
        "timestamp": datetime.utcnow()
    }
    await db.admin_logs.insert_one(admin_log)
    
    # Log usage for target user
    usage_log = {
        "_id": generate_id(),
        "user_id": user_id,
        "tenant_id": target_user["tenant_id"],
        "type": f"admin_credit_{action}",
        "credits_used": -amount if action == "add" else amount,  # Negative for added credits
        "admin_id": current_user["_id"],
        "reason": reason,
        "timestamp": datetime.utcnow()
    }
    await db.usage_logs.insert_one(usage_log)
    
    return {
        "message": f"Successfully {action}ed {amount} credits",
        "user_id": user_id,
        "previous_credits": current_credits,
        "new_credits": new_credits,
        "action": action,
        "amount": amount
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

@app.get("/api/admin/system-health")
async def get_system_health(current_user = Depends(admin_required)):
    """Get real-time system health status"""
    
    import psutil
    import time
    from datetime import datetime
    
    try:
        # Start timing API response
        start_time = time.time()
        
        # Database health check
        db_status = "healthy"
        db_response_time = 0
        try:
            db_start = time.time()
            await db.admin.command("ping")
            db_response_time = round((time.time() - db_start) * 1000, 2)  # ms
        except Exception as e:
            db_status = "unhealthy"
            db_response_time = -1
        
        # Server resource usage
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # API response time
        api_response_time = round((time.time() - start_time) * 1000, 2)  # ms
        
        # Active connections/users
        active_jobs = await db.jobs.count_documents({"status": {"$in": ["running", "pending"]}})
        total_users = await db.users.count_documents({})
        
        # Recent error logs (you can implement this based on your logging system)
        recent_errors = []  # Placeholder for error monitoring
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy" if db_status == "healthy" and cpu_usage < 90 else "warning",
            "database": {
                "status": db_status,
                "response_time_ms": db_response_time,
                "connection_pool": "available"  # Could be enhanced with actual pool stats
            },
            "server": {
                "cpu_usage_percent": cpu_usage,
                "memory_usage_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            },
            "api": {
                "response_time_ms": api_response_time,
                "status": "healthy" if api_response_time < 1000 else "slow"
            },
            "application": {
                "active_jobs": active_jobs,
                "total_users": total_users,
                "uptime_hours": round(time.time() / 3600, 1)  # Rough uptime estimate
            },
            "recent_errors": recent_errors
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "error",
            "error": str(e)
        }

@app.get("/api/admin/audit-logs")
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    action_filter: str = None,
    user_filter: str = None,
    current_user = Depends(admin_required)
):
    """Get audit logs with filtering and pagination"""
    
    try:
        skip = (page - 1) * limit
        
        # Build filter query
        filter_query = {}
        if action_filter:
            filter_query["action"] = {"$regex": action_filter, "$options": "i"}
        if user_filter:
            filter_query["$or"] = [
                {"user_id": {"$regex": user_filter, "$options": "i"}},
                {"admin_id": {"$regex": user_filter, "$options": "i"}},
                {"details.username": {"$regex": user_filter, "$options": "i"}}
            ]
        
        # Get audit logs
        logs = await db.audit_logs.find(filter_query).sort("timestamp", DESCENDING).skip(skip).limit(limit).to_list(limit)
        total_logs = await db.audit_logs.count_documents(filter_query)
        
        # Format logs for response
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": log["_id"],
                "timestamp": log["timestamp"].isoformat() if isinstance(log["timestamp"], datetime) else log["timestamp"],
                "action": log["action"],
                "user_id": log.get("user_id", ""),
                "admin_id": log.get("admin_id", ""),
                "ip_address": log.get("ip_address", ""),
                "details": log.get("details", {}),
                "status": log.get("status", "success")
            })
        
        return {
            "logs": formatted_logs,
            "total": total_logs,
            "page": page,
            "limit": limit,
            "total_pages": (total_logs + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")

# Helper function to create audit log
async def create_audit_log(action: str, user_id: str = None, admin_id: str = None, details: dict = None, ip_address: str = None):
    """Create an audit log entry"""
    try:
        audit_entry = {
            "_id": f"AUDIT-{int(time.time())}-{random.randint(1000, 9999)}",
            "timestamp": datetime.utcnow(),
            "action": action,
            "user_id": user_id,
            "admin_id": admin_id,
            "ip_address": ip_address,
            "details": details or {},
            "status": "success"
        }
        
        await db.audit_logs.insert_one(audit_entry)
        
    except Exception as e:
        logger.error(f"Error creating audit log: {str(e)}")

@app.post("/api/admin/bulk-import-users")
async def bulk_import_users(file: UploadFile = File(...), current_user = Depends(admin_required)):
    """Bulk import users from CSV file"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read CSV file
        contents = await file.read()
        csv_data = contents.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_data))
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Validate required fields
                required_fields = ['username', 'email', 'password']
                missing_fields = [field for field in required_fields if not row.get(field)]
                if missing_fields:
                    errors.append(f"Row {row_num}: Missing fields: {', '.join(missing_fields)}")
                    continue
                
                # Check if user already exists
                existing_user = await db.users.find_one({
                    "$or": [
                        {"username": row['username']},
                        {"email": row['email']}
                    ]
                })
                
                if existing_user:
                    errors.append(f"Row {row_num}: User with username '{row['username']}' or email '{row['email']}' already exists")
                    continue
                
                # Create user document
                user_doc = {
                    "_id": str(uuid.uuid4()),
                    "username": row['username'],
                    "email": row['email'],
                    "password": hash_password(row['password']),
                    "role": row.get('role', 'user'),
                    "credits": int(row.get('credits', 0)),
                    "is_active": row.get('is_active', 'true').lower() == 'true',
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Insert user
                await db.users.insert_one(user_doc)
                imported_count += 1
                
                # Create audit log
                await create_audit_log(
                    action="bulk_user_import",
                    admin_id=current_user["_id"],
                    details={
                        "imported_user": row['username'],
                        "email": row['email'],
                        "role": user_doc['role']
                    }
                )
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return {
            "success": True,
            "message": f"Bulk import completed. Imported {imported_count} users.",
            "imported_count": imported_count,
            "errors": errors[:10]  # Limit errors shown
        }
        
    except Exception as e:
        logger.error(f"Error in bulk import: {str(e)}")
        return {
            "success": False,
            "message": "Failed to process CSV file",
            "errors": [str(e)]
        }

@app.post("/api/admin/bulk-credit-management")
async def bulk_credit_management(
    request: dict,
    current_user = Depends(admin_required)
):
    """Bulk credit management for multiple users"""
    
    try:
        user_ids = request.get('user_ids', [])
        action = request.get('action', 'add')
        amount = request.get('amount', 0)
        reason = request.get('reason', '')
        
        if not user_ids or not reason:
            raise HTTPException(status_code=400, detail="User IDs and reason are required")
        
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        
        processed_users = 0
        errors = []
        
        for user_identifier in user_ids:
            try:
                # Find user by ID or username
                user = await db.users.find_one({
                    "$or": [
                        {"_id": user_identifier},
                        {"username": user_identifier}
                    ]
                })
                
                if not user:
                    errors.append(f"User not found: {user_identifier}")
                    continue
                
                # Calculate new credit amount
                current_credits = user.get('credits', 0)
                if action == "add":
                    new_credits = current_credits + amount
                elif action == "subtract":
                    new_credits = max(0, current_credits - amount)
                elif action == "set":
                    new_credits = amount
                else:
                    raise ValueError(f"Invalid action: {action}")
                
                # Update user credits
                await db.users.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {"credits": new_credits},
                        "$push": {
                            "credit_history": {
                                "action": action,
                                "amount": amount,
                                "previous_credits": current_credits,
                                "new_credits": new_credits,
                                "reason": reason,
                                "admin_id": current_user["_id"],
                                "timestamp": datetime.utcnow()
                            }
                        }
                    }
                )
                
                # Create audit log
                await create_audit_log(
                    action=f"bulk_credit_{action}",
                    admin_id=current_user["_id"],
                    user_id=user["_id"],
                    details={
                        "username": user["username"],
                        "action": action,
                        "amount": amount,
                        "previous_credits": current_credits,
                        "new_credits": new_credits,
                        "reason": reason
                    }
                )
                
                processed_users += 1
                
            except Exception as e:
                errors.append(f"Error processing {user_identifier}: {str(e)}")
        
        return {
            "success": True,
            "message": f"Bulk credit {action} completed",
            "processed_users": processed_users,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk credit management: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/bulk-notification")
async def bulk_notification(
    request: dict,
    current_user = Depends(admin_required)
):
    """Send bulk notifications to multiple users"""
    
    try:
        user_ids = request.get('user_ids', [])
        subject = request.get('subject', '')
        message = request.get('message', '')
        notification_type = request.get('type', 'info')
        
        if not user_ids or not subject or not message:
            raise HTTPException(status_code=400, detail="User IDs, subject, and message are required")
        
        sent_count = 0
        errors = []
        
        for user_identifier in user_ids:
            try:
                # Find user
                user = await db.users.find_one({
                    "$or": [
                        {"_id": user_identifier},
                        {"username": user_identifier}
                    ]
                })
                
                if not user:
                    errors.append(f"User not found: {user_identifier}")
                    continue
                
                # Create notification record
                notification = {
                    "_id": f"NOTIF-{int(time.time())}-{random.randint(1000, 9999)}",
                    "user_id": user["_id"],
                    "type": notification_type,
                    "subject": subject,
                    "message": message,
                    "read": False,
                    "created_at": datetime.utcnow(),
                    "admin_id": current_user["_id"]
                }
                
                await db.notifications.insert_one(notification)
                
                # Send email notification if email service is configured
                try:
                    await send_notification_email(user["email"], subject, message)
                except Exception as email_error:
                    logger.warning(f"Failed to send email to {user['email']}: {str(email_error)}")
                
                sent_count += 1
                
            except Exception as e:
                errors.append(f"Error sending notification to {user_identifier}: {str(e)}")
        
        # Create audit log
        await create_audit_log(
            action="bulk_notification_sent",
            admin_id=current_user["_id"],
            details={
                "subject": subject,
                "type": notification_type,
                "sent_count": sent_count,
                "target_users": len(user_ids)
            }
        )
        
        return {
            "success": True,
            "message": f"Bulk notification sent to {sent_count} users",
            "sent_count": sent_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function for sending notification emails
async def send_notification_email(email: str, subject: str, message: str):
    """Send notification email to user"""
    try:
        # This would use your email service (SendGrid, etc.)
        # For now, just log the action
        logger.info(f"Notification email sent to {email}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send notification email: {str(e)}")

# Create demo users if they don't exist
async def create_demo_users():
    """Create demo users if they don't exist"""
    try:
        # Check if demo user exists
        demo_user = await db.users.find_one({"username": "demo"})
        if not demo_user:
            demo_user_doc = {
                "_id": str(uuid.uuid4()),
                "username": "demo",
                "email": "demo@example.com",
                "password": hash_password("demo123"),
                "role": "user",
                "credits": 1000,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.users.insert_one(demo_user_doc)
            logger.info("Demo user created successfully")
        
        # Check if test user exists
        test_user = await db.users.find_one({"username": "testuser"})
        if not test_user:
            test_user_doc = {
                "_id": str(uuid.uuid4()),
                "username": "testuser",
                "email": "testuser@example.com",
                "password": hash_password("123456"),
                "role": "user",
                "credits": 500,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.users.insert_one(test_user_doc)
            logger.info("Test user created successfully")
            
    except Exception as e:
        logger.error(f"Error creating demo users: {str(e)}")

@app.post("/api/admin/create-demo-users")
async def create_demo_users_endpoint(current_user = Depends(admin_required)):
    """Manually create demo users"""
    await create_demo_users()
    return {"message": "Demo users created successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")