from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
import uuid
import pandas as pd
import io
import json
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
import asyncio
from enum import Enum

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.webtools_validation

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

app = FastAPI(title="Webtools Validasi Nomor Telepon", version="1.0.0")

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
    phone_number: str

class TelegramAccount(BaseModel):
    name: str
    phone_number: str
    api_id: str
    api_hash: str
    bot_token: Optional[str] = None
    is_active: bool = True

class WhatsAppProvider(BaseModel):
    name: str
    api_endpoint: str
    api_key: str
    provider_type: str  # twilio, vonage, etc
    is_active: bool = True

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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"_id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

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

# Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create tenant
    tenant_id = str(uuid.uuid4())
    
    # Create user
    user_doc = {
        "_id": str(uuid.uuid4()),
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
        "created_at": current_user["created_at"]
    }

@app.post("/api/validation/quick-check")
async def quick_check(request: QuickCheckRequest, current_user = Depends(get_current_user)):
    if current_user.get("credits", 0) < 2:
        raise HTTPException(status_code=400, detail="Insufficient credits")
    
    # Normalize phone number
    normalized_phone = normalize_phone_number(request.phone_number)
    
    # Check cache first
    cached_result = await db.validation_cache.find_one({"phone_number": normalized_phone})
    if cached_result and (datetime.utcnow() - cached_result["cached_at"]).days < 7:
        return {
            "phone_number": normalized_phone,
            "whatsapp": cached_result["whatsapp"],
            "telegram": cached_result["telegram"],
            "cached": True,
            "checked_at": cached_result["cached_at"]
        }
    
    # Validate with both platforms
    whatsapp_result = await validate_whatsapp_number(normalized_phone)
    telegram_result = await validate_telegram_number(normalized_phone)
    
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
        "_id": str(uuid.uuid4()),
        "user_id": current_user["_id"],
        "tenant_id": current_user["tenant_id"],
        "type": "quick_check",
        "phone_number": normalized_phone,
        "credits_used": 2,
        "timestamp": datetime.utcnow()
    }
    
    await db.usage_logs.insert_one(usage_doc)
    
    return {
        "phone_number": normalized_phone,
        "whatsapp": whatsapp_result,
        "telegram": telegram_result,
        "cached": False,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)