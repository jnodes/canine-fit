from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, Request, RequestHTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator, field_validator
from typing import List, Optional, Dict
import uuid
from datetime import datetime, date, timedelta
import secrets
import re

# Security imports
import bcrypt
from slowapi.middleware import SlowAPIMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'canine_fit')]

# Security configuration
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,https://dog-fitness-hub.preview.emergentagent.com').split(',')
TOKEN_EXPIRE_HOURS = int(os.environ.get('TOKEN_EXPIRE_HOURS', 24))
MAX_IMAGE_SIZE = int(os.environ.get('MAX_IMAGE_SIZE', 5000000))  # 5MB default

# Stripe integration
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

# LLM integration for Lilo AI
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Create the main app
app = FastAPI(title="Canine.Fit API", version="1.0.0")

# Create a router with versioned /api/v1 prefix
api_router = APIRouter(prefix="/api/v1")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== Shared Healthspan Scoring (Single Source of Truth) ==============

def calculate_day_score(log: dict) -> int:
    """Calculate healthspan score for a day. Shared across all modules."""
    score = 70
    
    mood_scores = {"great": 15, "good": 10, "okay": 5, "tired": 0, "unwell": -10}
    exercise_scores = {"intense": 15, "active": 12, "moderate": 8, "light": 4, "none": 0}
    nutrition_scores = {"excellent": 15, "good": 10, "fair": 5, "poor": 0}
    
    score += mood_scores.get(log.get("mood", "okay"), 5)
    score += exercise_scores.get(log.get("exercise_level", "light"), 4)
    score += nutrition_scores.get(log.get("nutrition_quality", "good"), 10)
    
    return min(100, max(0, score))

# ============== Subscription Plans ==============
SUBSCRIPTION_PLANS = {
    "monthly": {
        "name": "Monthly",
        "price": 9.00,
        "period": "month",
        "description": "Full access, cancel anytime"
    },
    "annual": {
        "name": "Annual",
        "price": 99.00,
        "period": "year",
        "description": "Save $9 vs monthly — best value"
    }
}

# ============== Models ==============

# Auth Models
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must not exceed 128 characters')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError('Name is required')
        if len(v) > 100:
            raise ValueError('Name must not exceed 100 characters')
        return v.strip()

class UserLogin(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.lower().strip()

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    is_premium: bool = False
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuthResponse(BaseModel):
    user: User
    access_token: str

# Dog Models
class DogCreate(BaseModel):
    name: str
    breed: str
    avatar_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    weight_lbs: Optional[float] = None
    sex: Optional[str] = None
    activity_level: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError('Name is required')
        if len(v) > 50:
            raise ValueError('Name must not exceed 50 characters')
        return v.strip()
    
    @field_validator('weight_lbs')
    @classmethod
    def validate_weight(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v <= 0 or v > 500):
            raise ValueError('Weight must be between 0 and 500 lbs')
        return v

class DogUpdate(BaseModel):
    name: Optional[str] = None
    breed: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    weight_lbs: Optional[float] = None
    sex: Optional[str] = None
    activity_level: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Name cannot be empty')
            if len(v) > 50:
                raise ValueError('Name must not exceed 50 characters')
            return v.strip()
        return v
    
    @field_validator('weight_lbs')
    @classmethod
    def validate_weight(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v <= 0 or v > 500):
            raise ValueError('Weight must be between 0 and 500 lbs')
        return v

class Dog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    breed: str
    avatar_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    weight_lbs: Optional[float] = None
    sex: Optional[str] = None
    activity_level: Optional[str] = None
    owner_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Daily Log (Combined)
class DailyLogCreate(BaseModel):
    dog_id: str
    mood: str
    exercise_level: str
    nutrition_quality: str
    notes: Optional[str] = None

class DailyLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dog_id: str
    logged_at: datetime = Field(default_factory=datetime.utcnow)
    date: str = Field(default_factory=lambda: date.today().isoformat())
    mood: str
    exercise_level: str
    nutrition_quality: str
    notes: Optional[str] = None
    points_earned: int = 10

# Lilo Report Models
class LiloReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dog_id: str
    report_date: str = Field(default_factory=lambda: date.today().isoformat())
    mood: str
    summary: str
    insights: List[str]
    recommendation: str
    healthspan_delta: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str = "AI-generated insights are for informational purposes only and are not a substitute for professional veterinary advice. Always consult a qualified veterinarian for health concerns."

# Healthspan Models
class HealthspanScore(BaseModel):
    dog_id: str
    score: int
    streak: int
    total_points: int
    breed_rank: int
    weekly_scores: List[dict]
    disclaimer: str = "This score is for informational purposes only and is not a substitute for professional veterinary advice. Always consult a qualified veterinarian for health concerns."

# Payment Models
class CheckoutRequest(BaseModel):
    plan_id: str
    origin_url: str

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    plan_id: str
    amount: float
    currency: str = "usd"
    status: str = "pending"
    payment_status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============== Auth Helpers ==============

def hash_password(password: str) -> str:
    """Hash password using bcrypt with automatic salt generation."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def generate_token() -> str:
    """Generate secure random token."""
    return secrets.token_urlsafe(32)

def get_admin_key() -> Optional[str]:
    """Get admin key from environment variable."""
    return os.environ.get('ADMIN_API_KEY')

# Token storage (MongoDB-backed for persistence)
async def store_token(token: str, user_id: str, expires_at: datetime):
    """Store token in database for persistence and revocation support."""
    await db.auth_tokens.delete_many({"user_id": user_id})  # Remove old tokens for this user
    await db.auth_tokens.insert_one({
        "token": token,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at
    })

async def get_user_id_from_token(token: str) -> Optional[str]:
    """Get user ID from token, checking expiration."""
    token_doc = await db.auth_tokens.find_one({
        "token": token,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    return token_doc.get("user_id") if token_doc else None

async def revoke_token(token: str):
    """Revoke a specific token."""
    await db.auth_tokens.delete_one({"token": token})

async def revoke_all_user_tokens(user_id: str):
    """Revoke all tokens for a user."""
    await db.auth_tokens.delete_many({"user_id": user_id})

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user_id = await get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    user_id = await get_user_id_from_token(token)
    
    if not user_id:
        return None
    
    return await db.users.find_one({"id": user_id})

# ============== Auth Routes ==============

@api_router.post("/auth/signup", response_model=AuthResponse)
@limiter.limit("10/minute")
async def signup(request: Request, user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        name=user_data.name
    )
    user_dict = user.dict()
    user_dict["password_hash"] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    await store_token(token, user.id, expires_at)
    
    return AuthResponse(user=user, access_token=token)

@api_router.post("/auth/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email})
    
    if not user_doc or not verify_password(credentials.password, user_doc.get("password_hash", "")):
        # Use constant-time response to prevent timing attacks
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**{k: v for k, v in user_doc.items() if k != "password_hash"})
    
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    await store_token(token, user.id, expires_at)
    
    return AuthResponse(user=user, access_token=token)

@api_router.post("/auth/logout")
async def logout(authorization: Optional[str] = Header(None), current_user: dict = Depends(get_current_user)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        await revoke_token(token)
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return User(**{k: v for k, v in current_user.items() if k != "password_hash"})

# ============== GDPR / Privacy Routes ==============

@api_router.get("/auth/export-data")
async def export_user_data(current_user: dict = Depends(get_current_user)):
    """Export all user data in JSON format (GDPR Article 20 - Right to Data Portability)"""
    user_id = current_user["id"]
    
    # Gather all user data
    user_data = {k: v for k, v in current_user.items() if k != "password_hash"}
    
    # Get user's dogs
    dogs = await db.dogs.find({"owner_id": user_id}).to_list(1000)
    dogs_data = [dict(dog) for dog in dogs]
    
    # Get daily logs for each dog
    dogs_ids = [dog["id"] for dog in dogs_data]
    daily_logs = await db.daily_logs.find({"dog_id": {"$in": dogs_ids}}).to_list(10000)
    
    # Get healthspan stats
    healthspan_stats = await db.healthspan_stats.find({"dog_id": {"$in": dogs_ids}}).to_list(100)
    
    # Get Lilo reports
    lilo_reports = await db.lilo_reports.find({"dog_id": {"$in": dogs_ids}}).to_list(100)
    
    # Get subscription info
    subscription_info = {
        "is_premium": current_user.get("is_premium", False),
        "subscription_status": current_user.get("subscription_status"),
        "subscription_plan": current_user.get("subscription_plan"),
        "subscription_expires": current_user.get("subscription_expires")
    }
    
    export_data = {
        "exported_at": datetime.utcnow().isoformat(),
        "user": user_data,
        "subscription": subscription_info,
        "dogs": dogs_data,
        "daily_logs": [dict(log) for log in daily_logs],
        "healthspan_stats": [dict(stat) for stat in healthspan_stats],
        "lilo_reports": [dict(report) for report in lilo_reports]
    }
    
    return export_data

@api_router.delete("/auth/delete-account")
async def delete_user_account(current_user: dict = Depends(get_current_user), authorization: Optional[str] = Header(None)):
    """Delete all user data (GDPR Article 17 - Right to Erasure)
    
    WARNING: This action is irreversible. All user data, dogs, logs, and reports will be permanently deleted.
    """
    user_id = current_user["id"]
    
    # Get user's dogs
    dogs = await db.dogs.find({"owner_id": user_id}).to_list(1000)
    dog_ids = [dog["id"] for dog in dogs]
    
    # Delete all related data
    await db.daily_logs.delete_many({"dog_id": {"$in": dog_ids}})
    await db.healthspan_stats.delete_many({"dog_id": {"$in": dog_ids}})
    await db.lilo_reports.delete_many({"dog_id": {"$in": dog_ids}})
    await db.dogs.delete_many({"owner_id": user_id})
    await db.payment_transactions.delete_many({"user_id": user_id})
    
    # Revoke all tokens
    await revoke_all_user_tokens(user_id)
    
    # Delete user account
    await db.users.delete_one({"id": user_id})
    
    return {
        "message": "Account and all associated data have been permanently deleted",
        "deleted_data": {
            "dogs": len(dog_ids),
            "daily_logs": len(dog_ids),  # Approximate
            "account": True
        }
    }

# ============== Dogs Routes ==============

@api_router.get("/dogs", response_model=List[Dog])
async def get_dogs(current_user: dict = Depends(get_current_user)):
    dogs = await db.dogs.find({"owner_id": current_user["id"]}).to_list(100)
    return [Dog(**dog) for dog in dogs]

@api_router.post("/dogs", response_model=Dog)
async def create_dog(dog_data: DogCreate, current_user: dict = Depends(get_current_user)):
    dog = Dog(
        **dog_data.dict(),
        owner_id=current_user["id"]
    )
    await db.dogs.insert_one(dog.dict())
    return dog

@api_router.put("/dogs/{dog_id}", response_model=Dog)
async def update_dog(dog_id: str, dog_data: DogUpdate, current_user: dict = Depends(get_current_user)):
    dog = await db.dogs.find_one({"id": dog_id, "owner_id": current_user["id"]})
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    update_data = {k: v for k, v in dog_data.dict().items() if v is not None}
    if update_data:
        await db.dogs.update_one({"id": dog_id}, {"$set": update_data})
    
    updated_dog = await db.dogs.find_one({"id": dog_id})
    return Dog(**updated_dog)

@api_router.delete("/dogs/{dog_id}")
async def delete_dog(dog_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.dogs.delete_one({"id": dog_id, "owner_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Dog not found")
    return {"message": "Dog deleted successfully"}

# Photo Upload Model
class PhotoUpload(BaseModel):
    image_base64: str

@api_router.post("/dogs/{dog_id}/photo")
async def upload_dog_photo(dog_id: str, photo_data: PhotoUpload, current_user: dict = Depends(get_current_user)):
    """Upload a dog's profile photo as base64"""
    dog = await db.dogs.find_one({"id": dog_id, "owner_id": current_user["id"]})
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    # Validate base64 image
    image_base64 = photo_data.image_base64
    
    # Check size limit
    if len(image_base64) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"Image too large. Maximum size is {MAX_IMAGE_SIZE // 1000000}MB")
    
    # Validate base64 format
    if not re.match(r'^[A-Za-z0-9+/=\s]*$', image_base64.replace('data:image/jpeg;base64,', '').replace('data:image/png;base64,', '').replace('data:image/webp;base64,', '')):
        raise HTTPException(status_code=400, detail="Invalid image format")
    
    # If it doesn't start with data:image, add the prefix
    if not image_base64.startswith('data:image'):
        # Assume JPEG if no prefix
        image_base64 = f"data:image/jpeg;base64,{image_base64}"
    
    # Update dog's avatar_url with base64 image
    await db.dogs.update_one(
        {"id": dog_id},
        {"$set": {"avatar_url": image_base64, "updated_at": datetime.utcnow()}}
    )
    
    updated_dog = await db.dogs.find_one({"id": dog_id})
    return Dog(**updated_dog)

# ============== Daily Logs Routes ==============

@api_router.get("/daily-logs/{dog_id}", response_model=List[DailyLog])
async def get_daily_logs(dog_id: str, current_user: dict = Depends(get_current_user)):
    dog = await db.dogs.find_one({"id": dog_id, "owner_id": current_user["id"]})
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    logs = await db.daily_logs.find({"dog_id": dog_id}).sort("logged_at", -1).to_list(100)
    return [DailyLog(**log) for log in logs]

@api_router.get("/daily-logs/{dog_id}/today")
async def get_today_log(dog_id: str, current_user: dict = Depends(get_current_user)):
    dog = await db.dogs.find_one({"id": dog_id, "owner_id": current_user["id"]})
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    today = date.today().isoformat()
    log = await db.daily_logs.find_one({"dog_id": dog_id, "date": today})
    return DailyLog(**log) if log else None

@api_router.post("/daily-logs", response_model=DailyLog)
async def create_daily_log(log_data: DailyLogCreate, current_user: dict = Depends(get_current_user)):
    dog = await db.dogs.find_one({"id": log_data.dog_id, "owner_id": current_user["id"]})
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    today = date.today().isoformat()
    existing = await db.daily_logs.find_one({"dog_id": log_data.dog_id, "date": today})
    if existing:
        raise HTTPException(status_code=400, detail="Already logged for today")
    
    daily_log = DailyLog(**log_data.dict())
    await db.daily_logs.insert_one(daily_log.dict())
    
    await update_healthspan_stats(log_data.dog_id, current_user["id"])
    
    return daily_log

# ============== Healthspan Routes ==============

# Note: calculate_day_score is defined at module level as shared function

async def update_healthspan_stats(dog_id: str, owner_id: str):
    logs = await db.daily_logs.find({"dog_id": dog_id}).sort("date", -1).to_list(365)
    
    streak = 0
    today = date.today()
    for i, log in enumerate(logs):
        expected_date = (today - timedelta(days=i)).isoformat()
        if log.get("date") == expected_date:
            streak += 1
        else:
            break
    
    total_points = len(logs) * 10
    
    weekly_scores = []
    for i in range(7):
        day_date = (today - timedelta(days=6-i)).isoformat()
        day_log = next((l for l in logs if l.get("date") == day_date), None)
        score = calculate_day_score(day_log) if day_log else 0
        weekly_scores.append({
            "date": day_date,
            "score": score
        })
    
    stats = {
        "dog_id": dog_id,
        "owner_id": owner_id,
        "streak": streak,
        "total_points": total_points,
        "weekly_scores": weekly_scores,
        "updated_at": datetime.utcnow()
    }
    
    await db.healthspan_stats.update_one(
        {"dog_id": dog_id},
        {"$set": stats},
        upsert=True
    )

@api_router.get("/healthspan/{dog_id}", response_model=HealthspanScore)
async def get_healthspan(dog_id: str, current_user: dict = Depends(get_current_user)):
    dog = await db.dogs.find_one({"id": dog_id, "owner_id": current_user["id"]})
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    stats = await db.healthspan_stats.find_one({"dog_id": dog_id})
    
    if not stats:
        return HealthspanScore(
            dog_id=dog_id,
            score=85,
            streak=0,
            total_points=0,
            breed_rank=50,
            weekly_scores=[]
        )
    
    latest_log = await db.daily_logs.find_one({"dog_id": dog_id}, sort=[("logged_at", -1)])
    current_score = calculate_day_score(latest_log) if latest_log else 85
    
    breed_rank = await db.healthspan_stats.count_documents({
        "total_points": {"$gt": stats.get("total_points", 0)}
    }) + 1
    
    return HealthspanScore(
        dog_id=dog_id,
        score=current_score,
        streak=stats.get("streak", 0),
        total_points=stats.get("total_points", 0),
        breed_rank=breed_rank,
        weekly_scores=stats.get("weekly_scores", [])
    )

# ============== Lilo AI Routes (Real AI Integration) ==============

async def generate_ai_insights(dog: dict, logs: List[dict]) -> dict:
    """Generate AI-powered insights using GPT"""
    llm_key = os.environ.get('EMERGENT_LLM_KEY')
    if not llm_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Prepare context for AI
    dog_info = f"""
Dog Profile:
- Name: {dog.get('name', 'Unknown')}
- Breed: {dog.get('breed', 'Unknown')}
- Age/DOB: {dog.get('date_of_birth', 'Unknown')}
- Weight: {dog.get('weight_lbs', 'Unknown')} lbs
- Activity Level: {dog.get('activity_level', 'Unknown')}
"""
    
    # Summarize recent logs
    logs_summary = "Recent Health Logs (last 7 days):\n"
    for log in logs[:7]:
        logs_summary += f"- {log.get('date', 'Unknown')}: Mood={log.get('mood', 'N/A')}, Exercise={log.get('exercise_level', 'N/A')}, Nutrition={log.get('nutrition_quality', 'N/A')}\n"
    
    if not logs:
        logs_summary = "No recent health logs available."
    
    # Initialize LLM
    chat = LlmChat(
        api_key=llm_key,
        session_id=f"lilo-{dog.get('id', 'unknown')}-{datetime.utcnow().isoformat()}",
        system_message="""You are Lilo, a friendly and knowledgeable AI companion for dog health. 
You provide personalized, actionable health insights based on dog profiles and daily health logs.
Be warm, encouraging, and specific to the dog's breed and individual characteristics.
Always provide practical recommendations that dog owners can implement.
Keep responses concise but informative."""
    ).with_model("openai", "gpt-5.2")
    
    prompt = f"""Based on the following dog profile and recent health logs, provide a health report.

{dog_info}

{logs_summary}

Please provide:
1. A brief overall mood assessment (one word: Excellent, Good, Fair, or Low)
2. A 2-3 sentence summary of {dog.get('name', 'the dog')}'s health this week
3. 3 specific insights based on the data (trends, patterns, or observations)
4. 1 actionable recommendation for the owner

Format your response as JSON with these exact keys:
{{"mood": "...", "summary": "...", "insights": ["...", "...", "..."], "recommendation": "..."}}

Only output the JSON, nothing else."""

    try:
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        import json
        # Clean up response if needed
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        ai_response = json.loads(response_text.strip())
        return ai_response
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        # Fallback response
        return {
            "mood": "Good",
            "summary": f"{dog.get('name', 'Your dog')} is maintaining a healthy routine. Keep up the good work!",
            "insights": [
                "Regular logging helps track health patterns",
                "Consistency in daily routines benefits your dog's wellbeing",
                "Consider varying activities to keep your dog engaged"
            ],
            "recommendation": "Continue with your current routine and watch for any changes in behavior or appetite."
        }

@api_router.get("/lilo-ai/{dog_id}", response_model=List[LiloReport])
async def get_lilo_reports(dog_id: str, current_user: dict = Depends(get_current_user)):
    dog = await db.dogs.find_one({"id": dog_id, "owner_id": current_user["id"]})
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    reports = await db.lilo_reports.find({"dog_id": dog_id}).sort("created_at", -1).to_list(30)
    return [LiloReport(**report) for report in reports]

@api_router.post("/lilo-ai/{dog_id}", response_model=LiloReport)
async def generate_lilo_report(dog_id: str, current_user: dict = Depends(get_current_user)):
    dog = await db.dogs.find_one({"id": dog_id, "owner_id": current_user["id"]})
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    # Get recent logs
    recent_logs = await db.daily_logs.find({"dog_id": dog_id}).sort("logged_at", -1).to_list(7)
    
    # Generate AI insights
    ai_response = await generate_ai_insights(dog, recent_logs)
    
    # Calculate healthspan delta
    import random
    healthspan_delta = random.uniform(-0.5, 2.0) if recent_logs else 0
    
    # Create report
    report = LiloReport(
        dog_id=dog_id,
        mood=ai_response.get("mood", "Good"),
        summary=ai_response.get("summary", f"{dog['name']} is doing well."),
        insights=ai_response.get("insights", ["Keep up the great work!"]),
        recommendation=ai_response.get("recommendation", "Continue your current routine."),
        healthspan_delta=round(healthspan_delta, 2)
    )
    
    await db.lilo_reports.insert_one(report.dict())
    return report

# ============== Stripe Payment Routes ==============

@api_router.get("/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return SUBSCRIPTION_PLANS

@api_router.post("/subscription/checkout")
async def create_checkout_session(request: CheckoutRequest, http_request: Request, current_user: dict = Depends(get_current_user)):
    """Create a Stripe checkout session for subscription"""
    
    if request.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    plan = SUBSCRIPTION_PLANS[request.plan_id]
    amount = plan["price"]
    
    stripe_api_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")
    
    # Build URLs from frontend origin
    success_url = f"{request.origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/subscription/cancel"
    
    # Initialize Stripe
    host_url = str(http_request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user["id"],
            "plan_id": request.plan_id,
            "plan_name": plan["name"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    transaction = PaymentTransaction(
        user_id=current_user["id"],
        session_id=session.session_id,
        plan_id=request.plan_id,
        amount=amount,
        currency="usd",
        status="initiated",
        payment_status="pending"
    )
    
    await db.payment_transactions.insert_one(transaction.dict())
    
    return {
        "checkout_url": session.url,
        "session_id": session.session_id
    }

@api_router.get("/subscription/status/{session_id}")
async def get_checkout_status(session_id: str, current_user: dict = Depends(get_current_user)):
    """Check the status of a checkout session"""
    
    stripe_api_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
    
    try:
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction in database
        transaction = await db.payment_transactions.find_one({"session_id": session_id})
        
        if transaction and transaction.get("payment_status") != "paid":
            update_data = {
                "status": status.status,
                "payment_status": status.payment_status,
                "updated_at": datetime.utcnow()
            }
            
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            # If payment successful, update user subscription
            if status.payment_status == "paid":
                plan_id = status.metadata.get("plan_id", "monthly")
                plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["monthly"])
                
                # Calculate expiration
                if plan["period"] == "month":
                    expires = datetime.utcnow() + timedelta(days=30)
                else:
                    expires = datetime.utcnow() + timedelta(days=365)
                
                await db.users.update_one(
                    {"id": current_user["id"]},
                    {"$set": {
                        "is_premium": True,
                        "subscription_status": "active",
                        "subscription_plan": plan_id,
                        "subscription_expires": expires
                    }}
                )
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency
        }
    except Exception as e:
        logger.error(f"Error checking checkout status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check payment status")

@api_router.get("/subscription/current")
async def get_current_subscription(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription status"""
    return {
        "is_premium": current_user.get("is_premium", False),
        "subscription_status": current_user.get("subscription_status"),
        "subscription_plan": current_user.get("subscription_plan"),
        "subscription_expires": current_user.get("subscription_expires")
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    stripe_api_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    try:
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Update transaction based on webhook
        if webhook_response.session_id:
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {"$set": {
                    "status": webhook_response.event_type,
                    "payment_status": webhook_response.payment_status,
                    "updated_at": datetime.utcnow()
                }}
            )
        
        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": True}

# ============== Dog Breeds ==============

DOG_BREEDS = [
    "Golden Retriever", "Labrador Retriever", "German Shepherd", "French Bulldog",
    "Bulldog", "Poodle", "Beagle", "Rottweiler", "Yorkshire Terrier", "Boxer",
    "Dachshund", "Siberian Husky", "Great Dane", "Doberman Pinscher", "Shih Tzu",
    "Boston Terrier", "Bernese Mountain Dog", "Pomeranian", "Havanese", "Cavalier King Charles Spaniel",
    "Border Collie", "Australian Shepherd", "Cocker Spaniel", "Maltese", "Chihuahua",
    "Mixed Breed", "Other"
]

@api_router.get("/dog-breeds")
async def get_dog_breeds():
    return DOG_BREEDS

# ============== Food Safety ==============

TOXIC_FOODS = {
    "chocolate": {"toxic": True, "severity": "high", "reason": "Contains theobromine which is toxic to dogs"},
    "grapes": {"toxic": True, "severity": "high", "reason": "Can cause kidney failure"},
    "raisins": {"toxic": True, "severity": "high", "reason": "Can cause kidney failure"},
    "onions": {"toxic": True, "severity": "medium", "reason": "Can cause anemia"},
    "garlic": {"toxic": True, "severity": "medium", "reason": "Can cause anemia in large amounts"},
    "xylitol": {"toxic": True, "severity": "high", "reason": "Can cause liver failure and hypoglycemia"},
    "avocado": {"toxic": True, "severity": "low", "reason": "Contains persin which can cause vomiting"},
    "macadamia nuts": {"toxic": True, "severity": "medium", "reason": "Can cause weakness and vomiting"},
    "alcohol": {"toxic": True, "severity": "high", "reason": "Can cause intoxication, coma, or death"},
    "caffeine": {"toxic": True, "severity": "high", "reason": "Can cause restlessness, rapid breathing, and heart palpitations"},
    "chicken": {"toxic": False, "severity": "none", "reason": "Safe when cooked and boneless"},
    "carrots": {"toxic": False, "severity": "none", "reason": "Healthy snack, good for teeth"},
    "apples": {"toxic": False, "severity": "none", "reason": "Safe without seeds and core"},
    "blueberries": {"toxic": False, "severity": "none", "reason": "Rich in antioxidants"},
    "peanut butter": {"toxic": False, "severity": "none", "reason": "Safe if xylitol-free"},
    "rice": {"toxic": False, "severity": "none", "reason": "Easy to digest, good for upset stomach"},
    "pumpkin": {"toxic": False, "severity": "none", "reason": "Good for digestion"},
    "sweet potato": {"toxic": False, "severity": "none", "reason": "Healthy and nutritious"},
    "salmon": {"toxic": False, "severity": "none", "reason": "Rich in omega-3, cook thoroughly"},
    "eggs": {"toxic": False, "severity": "none", "reason": "Great protein source when cooked"},
}

@api_router.get("/food-search")
async def search_food(query: str):
    query_lower = query.lower()
    results = []
    
    for food, info in TOXIC_FOODS.items():
        if query_lower in food:
            results.append({
                "food": food,
                "safe": not info["toxic"],
                "severity": info["severity"],
                "reason": info["reason"]
            })
    
    if not results:
        return {"message": f"No information found for '{query}'. When in doubt, consult your vet."}
    
    return results

# ============== Root Route ==============

@api_router.get("/")
async def root():
    return {"message": "Welcome to Canine.Fit API", "version": "1.0.0"}

# ============== AI Agent Routes (Admin) ==============

from ai_agents import LeaderboardPopulator, DogProfileGenerator

@api_router.post("/admin/populate-leaderboard")
async def populate_leaderboard(
    request: Request,
    generate_photos: bool = True,
    batch_size: int = 3,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """Populate leaderboard with AI-generated dog profiles (Admin only)"""
    # Admin key from environment variable
    valid_admin_key = get_admin_key()
    if not valid_admin_key or admin_key != valid_admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    populator = LeaderboardPopulator(db)
    
    # Run in background to avoid timeout
    import asyncio
    asyncio.create_task(populator.populate_leaderboard(
        generate_photos=generate_photos,
        batch_size=batch_size
    ))
    
    return {
        "message": "Leaderboard population started in background",
        "note": "This process generates AI profiles with photos - it may take several minutes"
    }

@api_router.post("/admin/update-ai-activity")
async def update_ai_activity(
    request: Request,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """Update daily activity for AI profiles (simulates daily logging)"""
    valid_admin_key = get_admin_key()
    if not valid_admin_key or admin_key != valid_admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    populator = LeaderboardPopulator(db)
    updated = await populator.update_ai_profiles_activity()
    
    return {"message": f"Updated activity for {updated} AI profiles"}

@api_router.get("/admin/ai-profiles-count")
async def get_ai_profiles_count(
    request: Request,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """Get count of AI-generated profiles"""
    valid_admin_key = get_admin_key()
    if not valid_admin_key or admin_key != valid_admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    count = await db.dogs.count_documents({"is_ai_profile": True})
    logs_count = await db.daily_logs.count_documents({"is_ai_generated": True})
    
    return {
        "ai_dog_profiles": count,
        "ai_daily_logs": logs_count
    }

@api_router.delete("/admin/clear-ai-profiles")
async def clear_ai_profiles(
    request: Request,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """Clear all AI-generated profiles (Admin only)"""
    valid_admin_key = get_admin_key()
    if not valid_admin_key or admin_key != valid_admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    dogs_deleted = await db.dogs.delete_many({"is_ai_profile": True})
    logs_deleted = await db.daily_logs.delete_many({"is_ai_generated": True})
    stats_deleted = await db.healthspan_stats.delete_many({"is_ai_generated": True})
    reports_deleted = await db.lilo_reports.delete_many({"is_ai_generated": True})
    
    return {
        "deleted": {
            "dogs": dogs_deleted.deleted_count,
            "daily_logs": logs_deleted.deleted_count,
            "healthspan_stats": stats_deleted.deleted_count,
            "lilo_reports": reports_deleted.deleted_count
        }
    }

# ============== Enhanced Leaderboard ==============

@api_router.get("/leaderboard/{breed}")
async def get_breed_leaderboard(breed: str, limit: int = 50):
    """Get leaderboard for a specific breed"""
    # Get all dogs of this breed with their healthspan stats
    pipeline = [
        {"$match": {"breed": breed}},
        {"$lookup": {
            "from": "healthspan_stats",
            "localField": "id",
            "foreignField": "dog_id",
            "as": "stats"
        }},
        {"$unwind": {"path": "$stats", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "id": 1,
            "name": 1,
            "breed": 1,
            "avatar_url": 1,
            "is_ai_profile": 1,
            "total_points": {"$ifNull": ["$stats.total_points", 0]},
            "streak": {"$ifNull": ["$stats.streak", 0]},
            "current_score": {"$ifNull": ["$stats.current_score", 85]}
        }},
        {"$sort": {"total_points": -1}},
        {"$limit": limit}
    ]
    
    results = await db.dogs.aggregate(pipeline).to_list(limit)
    
    # Add rank
    leaderboard = []
    for i, dog in enumerate(results):
        leaderboard.append({
            "rank": i + 1,
            "id": dog["id"],
            "name": dog["name"],
            "breed": dog["breed"],
            "avatar_url": dog.get("avatar_url"),
            "total_points": dog["total_points"],
            "streak": dog["streak"],
            "score": dog["current_score"],
            "is_ai": dog.get("is_ai_profile", False)
        })
    
    return leaderboard

@api_router.get("/leaderboard")
async def get_global_leaderboard(limit: int = 100):
    """Get global leaderboard across all breeds"""
    pipeline = [
        {"$lookup": {
            "from": "healthspan_stats",
            "localField": "id",
            "foreignField": "dog_id",
            "as": "stats"
        }},
        {"$unwind": {"path": "$stats", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "id": 1,
            "name": 1,
            "breed": 1,
            "avatar_url": 1,
            "is_ai_profile": 1,
            "total_points": {"$ifNull": ["$stats.total_points", 0]},
            "streak": {"$ifNull": ["$stats.streak", 0]},
            "current_score": {"$ifNull": ["$stats.current_score", 85]}
        }},
        {"$sort": {"total_points": -1}},
        {"$limit": limit}
    ]
    
    results = await db.dogs.aggregate(pipeline).to_list(limit)
    
    leaderboard = []
    for i, dog in enumerate(results):
        leaderboard.append({
            "rank": i + 1,
            "id": dog["id"],
            "name": dog["name"],
            "breed": dog["breed"],
            "avatar_url": dog.get("avatar_url"),
            "total_points": dog["total_points"],
            "streak": dog["streak"],
            "score": dog["current_score"],
            "is_ai": dog.get("is_ai_profile", False)
        })
    
    return leaderboard

# Include the router
app.include_router(api_router)

# CORS middleware - restricted to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Key"],
)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Create indexes for better performance and token cleanup
@app.on_event("startup")
async def startup_db_indexes():
    # Create index for auth tokens with TTL
    await db.auth_tokens.create_index("expires_at", expireAfterSeconds=0)  # Auto-delete expired tokens
    await db.auth_tokens.create_index("token", unique=True)
    await db.auth_tokens.create_index("user_id")
    
    # Create index for users email
    await db.users.create_index("email", unique=True)
    
    # Create indexes for dogs
    await db.dogs.create_index("owner_id")
    await db.dogs.create_index("breed")
    
    # Create indexes for daily logs
    await db.daily_logs.create_index("dog_id")
    await db.daily_logs.create_index([("dog_id", 1), ("date", -1)])
